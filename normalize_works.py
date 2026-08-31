#!/usr/bin/env python3
"""
원작 작품명 정규화 스크립트
WORK_DICTIONARY.json 기반 3단계 매칭: exact → normalized → fuzzy

사용법:
  python3 normalize_works.py --dry-run                     # 전체 매칭 통계만 출력
  python3 normalize_works.py --input 26년_7월_부스정보.csv  # 단일 파일 처리
  python3 normalize_works.py --all                          # 전체 월 일괄 처리
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WORK_DICTIONARY.json")

COLUMN_MAIN = "대표 작품(원작)"
COLUMN_OTHER = "그 외 다루는 작품"


# ============================================================
# 딕셔너리 로드 및 인덱스 구축
# ============================================================

def load_dictionary(dict_path):
    with open(dict_path, encoding="utf-8") as f:
        data = json.load(f)

    works = data["works"]

    # exact index: 소문자 원형 → code
    exact_index = {}
    # normalized index: 공백/특수문자 제거 소문자 → set of codes
    norm_index = defaultdict(set)
    # canonical names: code → canonical_name
    canonical = {}

    for code, w in works.items():
        canonical[code] = w["canonical_name"]
        all_names = [w["canonical_name"]] + w.get("aliases", []) + w.get("abbreviations", [])
        for name in all_names:
            key = name.strip().lower()
            if key:
                exact_index[key] = code
            nkey = normalize_key(name)
            if nkey:
                norm_index[nkey].add(code)

    return data, exact_index, dict(norm_index), canonical


def normalize_key(s):
    """공백, 특수문자, 구분자 제거 + 소문자화"""
    s = re.sub(r'[\s\!\？\?\.\,\:\;\-\~\·\·\(\)（）\[\]\|\′／\@\#\*\^]', '', s)
    return s.lower()


# ============================================================
# Fuzzy matching (Levenshtein)
# ============================================================

def levenshtein(a, b):
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            ins = prev[j + 1] + 1
            dele = curr[j] + 1
            sub = prev[j] + (ca != cb)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


def fuzzy_match(raw, norm_index_keys, threshold=0.75):
    """
    정규화 키 목록과 비교하여 가장 유사한 것 반환.
    threshold: 유사도 (0~1). Levenshtein 기반.
    반환: (key, similarity) or (None, 0)
    """
    raw_norm = normalize_key(raw)
    if not raw_norm:
        return None, 0

    best_key = None
    best_sim = 0

    for key in norm_index_keys:
        if not key:
            continue
        max_len = max(len(raw_norm), len(key))
        if max_len == 0:
            continue
        dist = levenshtein(raw_norm, key)
        sim = 1 - dist / max_len
        if sim > best_sim:
            best_sim = sim
            best_key = key
            if sim >= 1.0:
                break

    if best_sim >= threshold:
        return best_key, best_sim
    return None, 0


# ============================================================
# 다중 작품 분리
# ============================================================

def split_multi_work(raw):
    """
    콤마/구분자로 여러 작품이 표기된 경우 분리.
    '/'는 시리즈명 일부일 수 있으므로 콤마만 분리 기준으로 사용.
    단, 괄호 안의 콤마는 분리하지 않음.
    """
    parts = []
    depth = 0
    buf = []
    for ch in raw:
        if ch in '([{（［':
            depth += 1
            buf.append(ch)
        elif ch in ')]}）］':
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch in ',，' and depth == 0:
            part = ''.join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)
    last = ''.join(buf).strip()
    if last:
        parts.append(last)
    return parts


def strip_parentheses(raw):
    """
    괄호 표기에서 괄호 앞 텍스트와 괄호 안 텍스트 분리.
    '아이돌리쉬세븐(아이나나)' → ('아이돌리쉬세븐', '아이나나')
    '괴담출근(괴담에 떨어져도 출근을 해야 하는구나)' → ('괴담출근', '괴담에 떨어져도 출근을 해야 하는구나')
    괄호 없으면 (raw, None)
    """
    m = re.match(r'^(.+?)[(（](.+?)[)）]\s*$', raw.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw.strip(), None


# ============================================================
# 단일 작품명 정규화
# ============================================================

def normalize_one(raw, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold=0.85):
    """
    단일 작품명 → (정규화 결과, 코드, 매칭 방식, 신뢰도)
    매칭 방식: exact / normalized / fuzzy / unmatched / noise
    """
    raw = raw.strip()
    if not raw:
        return None, None, "empty", 1.0

    # 노이즈 필터
    cleaned = re.sub(r'[\.\,\s]', '', raw)
    if len(cleaned) <= 1 or raw in (".", "..", "..."):
        return None, None, "noise", 1.0
    if raw in ("없음", "미정", "-", "해당없음", "1차", "1차 문구류"):
        return None, None, "noise", 1.0

    def try_match(text):
        """text로 exact → normalized → fuzzy 매칭 시도 → (code, method, conf)"""
        key = text.lower()
        if key in exact_index:
            return exact_index[key], "exact", 1.0
        nkey = normalize_key(text)
        if nkey in norm_index:
            codes = norm_index[nkey]
            if len(codes) == 1:
                return list(codes)[0], "normalized", 0.95
            best = min(codes, key=lambda c: len(canonical[c]))
            return best, "normalized_ambiguous", 0.85
        fk, sim = fuzzy_match(text, fuzzy_keys, threshold=fuzzy_threshold)
        if fk:
            codes = norm_index.get(fk, set())
            if codes:
                return list(codes)[0], "fuzzy", sim
        return None, None, 0.0

    # Step 1: 원본 그대로 매칭
    code, method, conf = try_match(raw)
    if code:
        return canonical[code], code, method, conf

    # Step 2: 괄호 병기 처리 — 괄호 앞 텍스트로 매칭
    front, inner = strip_parentheses(raw)
    if front != raw:
        code, method, conf = try_match(front)
        if code:
            return canonical[code], code, method + "_paren_stripped", conf

    # Step 3: 괄호 안 약칭으로 매칭
    if inner:
        code, method, conf = try_match(inner)
        if code:
            return canonical[code], code, method + "_paren_inner", conf

    # Step 4: unmatched
    return raw, None, "unmatched", 0.0


# ============================================================
# 셀 정규화 (다중 작품 대응)
# ============================================================

def normalize_cell(raw, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold=0.85):
    """
    하나의 셀 값 정규화.
    1. 전체 셀을 단일 작품으로 매칭 시도
    2. 매칭 안 되면 콤마로 분리 후 각각 매칭
    반환: (정규화 결과, [(코드, 매칭방식, 신뢰도), ...])
    """
    if not raw or not raw.strip():
        return "", [(None, "empty", 1.0)]

    # Step 1: 전체 셀을 단일 작품으로 매칭
    norm, code, method, conf = normalize_one(
        raw, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
    )
    if method not in ("unmatched", "noise", "empty"):
        return norm, [(code, method, conf)]

    # Step 2: 콤마로 분리하여 각각 매칭
    parts = split_multi_work(raw)
    if len(parts) <= 1:
        return norm if norm else raw, [(code, method, conf)]

    results = []
    meta = []
    for part in parts:
        p_norm, p_code, p_method, p_conf = normalize_one(
            part, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
        )
        results.append(p_norm if p_norm else part)
        meta.append((p_code, p_method, p_conf))

    return "; ".join(results), meta


# ============================================================
# 메인 처리
# ============================================================

def process_file(filepath, exact_index, norm_index, canonical, fuzzy_keys,
                 columns=None, dry_run=False, fuzzy_threshold=0.85):
    """단일 CSV 파일 처리"""
    if columns is None:
        columns = [COLUMN_MAIN]

    method_counter = Counter()
    unmatched = Counter()
    total_cells = 0

    rows = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    new_fieldnames = list(fieldnames)

    for col in columns:
        out_col = f"{col}_정규화"
        if out_col not in new_fieldnames:
            new_fieldnames.append(out_col)
        code_col = f"{col}_코드"
        if code_col not in new_fieldnames:
            new_fieldnames.append(code_col)

    for row in rows:
        for col in columns:
            raw = row.get(col, "")
            norm_result, meta = normalize_cell(
                raw, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
            )

            row[f"{col}_정규화"] = norm_result

            # 코드값 추출
            codes = [m[0] for m in meta if m[0]]
            row[f"{col}_코드"] = "; ".join(codes) if codes else ""

            total_cells += 1
            for code, method, conf in meta:
                method_counter[method] += 1
                if method == "unmatched":
                    unmatched[raw] += 1

    if not dry_run:
        outpath = filepath.replace(".csv", "_normalized.csv")
        with open(outpath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        print(f"  → 저장: {outpath}")

    return method_counter, unmatched, total_cells


def main():
    parser = argparse.ArgumentParser(description="원작 작품명 정규화")
    parser.add_argument("--input", help="단일 입력 CSV 파일")
    parser.add_argument("--all", action="store_true", help="전체 *_부스정보.csv 처리")
    parser.add_argument("--dry-run", action="store_true", help="결과만 출력 (파일 저장 안 함)")
    parser.add_argument("--columns", nargs="+", default=[COLUMN_MAIN],
                        help=f"정규화 대상 컬럼 (기본: '{COLUMN_MAIN}')")
    parser.add_argument("--fuzzy-threshold", type=float, default=0.85,
                        help="Fuzzy 매칭 임계값 (0~1, 기본: 0.85)")
    parser.add_argument("--dict", default=DICT_PATH, help="딕셔너리 JSON 경로")
    args = parser.parse_args()

    data, exact_index, norm_index, canonical = load_dictionary(args.dict)
    fuzzy_keys = list(norm_index.keys())

    print(f"딕셔너리 로드: {data['metadata']['total_works']}개 작품, "
          f"{len(exact_index)} exact / {len(norm_index)} norm 인덱스")
    print(f"Fuzzy 임계값: {args.fuzzy_threshold}")
    print()

    if args.dry_run and not args.input and not args.all:
        # dry-run + 파일 미지정 → 전체 통계만
        args.all = True

    if args.input:
        files = [args.input]
    elif args.all:
        files = sorted(glob.glob("*_부스정보.csv"))
    else:
        parser.print_help()
        sys.exit(1)

    total_methods = Counter()
    total_unmatched = Counter()
    total_cells = 0

    for f in files:
        if not os.path.exists(f):
            print(f"⚠ 파일 없음: {f}")
            continue

        print(f"처리 중: {f}")
        methods, unmatched, cells = process_file(
            f, exact_index, norm_index, canonical, fuzzy_keys,
            columns=args.columns, dry_run=args.dry_run,
            fuzzy_threshold=args.fuzzy_threshold
        )
        total_methods += methods
        total_unmatched += unmatched
        total_cells += cells

        matched = cells - methods.get("unmatched", 0) - methods.get("noise", 0) - methods.get("empty", 0)
        print(f"  셀 {cells}개 | 매칭 {matched} ({matched/cells*100:.1f}%) | "
              f"unmatched {methods.get('unmatched', 0)}")

    # 전체 통계
    print("\n" + "=" * 60)
    print("전체 매칭 통계")
    print("=" * 60)
    for method, count in total_methods.most_common():
        pct = count / total_cells * 100 if total_cells else 0
        print(f"  {method:25s}: {count:6d} ({pct:5.1f}%)")

    matched = total_cells - total_methods.get("unmatched", 0) - total_methods.get("noise", 0) - total_methods.get("empty", 0)
    print(f"\n  총 셀: {total_cells}")
    print(f"  매칭 성공: {matched} ({matched/total_cells*100:.1f}%)")
    print(f"  미매칭: {total_methods.get('unmatched', 0)}")

    # unmatched Top 30
    if total_unmatched:
        print(f"\n미매칭 고유값 (빈도순 Top 30 / 총 {len(total_unmatched)}개):")
        for val, cnt in total_unmatched.most_common(30):
            print(f"  [{cnt:4d}] {val}")


if __name__ == "__main__":
    main()

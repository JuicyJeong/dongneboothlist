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

# 사전 metadata.noise_terms 로 채워짐 (load_dictionary에서 설정)
NOISE_TERMS = set()
# 사전 metadata.split_stopwords 로 채워짐 (분리 후 버리는 연결어)
SPLIT_STOPWORDS = set()
# 사전 metadata.llm_decisions 로 채워짐 (LLM 2차 확정 분류: value → decision)
LLM_DECISIONS = {}
UNCERTAIN_MARKER = "판단 불가"

# 파트 전체 매칭 실패 시 2차 분리의 기호 경계 (공백은 greedy 토크나이저가 처리)
SECONDARY_SPLIT_RE = re.compile(r'[./&+·|｜／]')


# ============================================================
# 딕셔너리 로드 및 인덱스 구축
# ============================================================

def load_dictionary(dict_path):
    with open(dict_path, encoding="utf-8") as f:
        data = json.load(f)

    works = data["works"]

    # 사전 metadata.noise_terms (작품 외 표기) 로드
    global NOISE_TERMS, SPLIT_STOPWORDS, LLM_DECISIONS
    meta = data.get("metadata", {})
    NOISE_TERMS = {n.strip().lower() for n in meta.get("noise_terms", []) if n.strip()}
    SPLIT_STOPWORDS = {s.strip() for s in meta.get("split_stopwords", []) if s.strip()}
    LLM_DECISIONS = meta.get("llm_decisions", {})

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
    """공백, 특수문자, 구분자, 꺾쇠 괄호 제거 + 소문자화"""
    s = re.sub(r'[\s\!\？\?\.\,\:\;\-\~\·\·\(\)（）\[\]\|\′／\@\#\*\^\<\>《》〈〉「」『』]', '', s)
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

def normalize_one(raw, exact_index, norm_index, canonical, fuzzy_keys,
                  fuzzy_threshold=0.85, allow_fuzzy=True):
    """
    단일 작품명 → (정규화 결과, 코드, 매칭 방식, 신뢰도)
    매칭 방식: exact / normalized / fuzzy / unmatched / noise / uncertain
    allow_fuzzy=False 면 exact/normalized/괄호 처리만 시도 (폴백 분리 토큰용, 오탐 방지)
    """
    raw = raw.strip()
    if not raw:
        return None, None, "empty", 1.0

    # 사전 metadata.noise_terms 기반 노이즈 필터 (작품 외 굿즈/장르 표기)
    if raw.lower() in NOISE_TERMS:
        return None, None, "noise", 1.0

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
        if not allow_fuzzy:
            return None, None, 0.0
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

    # Step 4: LLM 2차 확정 uncertain 판정은 파트 레벨 최종 단계에서 적용
    # (여기서 반환하면 폴백 분리·부분 매칭 기회를 가로막음)

    # Step 5: unmatched
    return raw, None, "unmatched", 0.0


def split_fallback_segments(part):
    """
    파트 전체 매칭 실패 시 2차 분리: 기호 경계(마침표, /, &, +, ·, |)로 세그먼트 분리.
    공백은 세그먼트 내 최장 매칭 토크나이저에서 처리한다.
    """
    return [s for s in SECONDARY_SPLIT_RE.split(part.strip()) if s and s.strip()]


def match_segment_greedy(seg, exact_index, norm_index, canonical, fuzzy_keys,
                         fuzzy_threshold=0.85):
    """
    세그먼트 내 공백 토큰을 최장 우선(greedy longest)으로 재매칭
    (normalize_one의 exact/normalized/괄호 처리 사용, fuzzy는 오탐 방지 위해 미적용).
    반환: [(텍스트, 코드|None, 방식), ...] — 세그먼트가 단일 토큰이면 None(원본 유지)
    """
    toks = seg.split()
    if len(toks) <= 1:
        return None

    results, i = [], 0
    while i < len(toks):
        hit = None
        for j in range(len(toks), i, -1):
            cand = " ".join(toks[i:j]).strip()
            if not cand:
                continue
            _n, code, method, _conf = normalize_one(
                cand, exact_index, norm_index, canonical, fuzzy_keys,
                fuzzy_threshold, allow_fuzzy=False
            )
            if code:
                hit = (j, _n, code, method)
                break
        if hit:
            j, norm_name, code, method = hit
            results.append((norm_name, code, method))
            i = j
        else:
            if toks[i] not in SPLIT_STOPWORDS:
                results.append((toks[i], None, "unmatched"))
            i += 1
    return results


# ============================================================
# 셀 정규화 (다중 작품 대응)
# ============================================================

def _normalize_part(part, exact_index, norm_index, canonical, fuzzy_keys,
                    fuzzy_threshold=0.85):
    """
    콤마 분리된 파트 1개 정규화.
    파트 전체 매칭 실패 시 2차 폴백: 기호 경계 세그먼트 분리 후 공백 토큰 최장
    매칭(exact/normalized만, fuzzy는 오탐 방지를 위해 미적용). 하나라도 매칭되면
    매칭 토큰 + 잔여 텍스트로 구성, 하나도 매칭 없으면 원본 그대로 유지
    (미지 작품명 붕괴 방지).
    반환: (정규화 텍스트, [(코드, 방식, 신뢰도), ...])
    """
    p_norm, p_code, p_method, p_conf = normalize_one(
        part, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
    )
    if p_method not in ("unmatched", "noise"):
        return (p_norm if p_norm else part), [(p_code, p_method, p_conf)]

    segs = split_fallback_segments(part)
    if not segs:
        return (p_norm if p_norm else part), [(p_code, p_method, p_conf)]

    results, meta, matched_any = [], [], False
    seen_codes = set()
    for seg in segs:
        pieces = match_segment_greedy(
            seg, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
        )
        if pieces is None:
            # 단일 토큰 세그먼트: exact/normalized만 재매칭 (fuzzy는 오탐 방지 위해 제외)
            s = seg.strip()
            if not s:
                continue
            s_norm, s_code, s_method, _conf = normalize_one(
                s, exact_index, norm_index, canonical, fuzzy_keys,
                fuzzy_threshold, allow_fuzzy=False
            )
            if s_code:
                if s_code in seen_codes:
                    continue
                seen_codes.add(s_code)
                results.append(s_norm if s_norm else s)
                meta.append((s_code, s_method + "_fallback", 0.9))
                matched_any = True
            else:
                if s_method == "noise":
                    continue
                results.append(s)
                meta.append((None, "unmatched", 0.0))
            continue
        for text, code, method in pieces:
            if code:
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                matched_any = True
                meta.append((code, method + "_fallback", 0.9))
            else:
                meta.append((None, "unmatched", 0.0))
            results.append(text)

    if not matched_any:
        # LLM 2차 확정 uncertain(판단 불가) 분류 적용 — 모든 매칭 시도가 실패한 뒤
        if LLM_DECISIONS.get(part.strip(), {}).get("decision") == "uncertain":
            return UNCERTAIN_MARKER, [(None, "uncertain", 0.0)]
        return (p_norm if p_norm else part), [(p_code, p_method, p_conf)]
    return "; ".join(results), meta


def normalize_cell(raw, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold=0.85):
    """
    하나의 셀 값 정규화.
    1. 전체 셀을 단일 작품으로 매칭 시도
    2. 매칭 안 되면 콤마로 분리 후 각각 매칭
    3. 그래도 실패한 파트는 공백·마침표·기호 재분리(폴백) 후 재매칭
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

    # Step 2: 콤마로 분리하여 각각 매칭 (파트 내 폴백 재분리 포함)
    parts = split_multi_work(raw)
    if len(parts) <= 1:
        return _normalize_part(
            raw, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
        )

    results = []
    meta = []
    for part in parts:
        p_text, p_meta = _normalize_part(
            part, exact_index, norm_index, canonical, fuzzy_keys, fuzzy_threshold
        )
        results.append(p_text)
        meta.extend(p_meta)

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

    # 원문 칼럼 바로 옆에 _코드, _정규화 칼럼 배치 (JWMI-7 사용자 요구)
    for col in columns:
        if col not in new_fieldnames:
            continue
        code_col = f"{col}_코드"
        out_col = f"{col}_정규화"
        new_fieldnames.remove(code_col) if code_col in new_fieldnames else None
        new_fieldnames.remove(out_col) if out_col in new_fieldnames else None
        pos = new_fieldnames.index(col) + 1
        new_fieldnames[pos:pos] = [code_col, out_col]

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
                if method in ("unmatched", "uncertain"):
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

        matched = (cells - methods.get("unmatched", 0) - methods.get("uncertain", 0)
                   - methods.get("noise", 0) - methods.get("empty", 0))
        print(f"  셀 {cells}개 | 매칭 {matched} ({matched/cells*100:.1f}%) | "
              f"unmatched {methods.get('unmatched', 0)} | "
              f"판단 불가 {methods.get('uncertain', 0)}")

    # 전체 통계
    print("\n" + "=" * 60)
    print("전체 매칭 통계")
    print("=" * 60)
    for method, count in total_methods.most_common():
        pct = count / total_cells * 100 if total_cells else 0
        print(f"  {method:25s}: {count:6d} ({pct:5.1f}%)")

    matched = (total_cells - total_methods.get("unmatched", 0)
               - total_methods.get("uncertain", 0)
               - total_methods.get("noise", 0) - total_methods.get("empty", 0))
    print(f"\n  총 셀: {total_cells}")
    print(f"  매칭 성공: {matched} ({matched/total_cells*100:.1f}%)")
    print(f"  미매칭: {total_methods.get('unmatched', 0)} | "
          f"판단 불가: {total_methods.get('uncertain', 0)}")

    # unmatched Top 30
    if total_unmatched:
        print(f"\n미매칭 고유값 (빈도순 Top 30 / 총 {len(total_unmatched)}개):")
        for val, cnt in total_unmatched.most_common(30):
            print(f"  [{cnt:4d}] {val}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
LLM 병렬 배치 2차 처리 도구 (JWMI-5 하이브리드 파이프라인)

규칙 1차(normalize_works.py)에서 미매핑으로 남은 고유 값만 LLM(또는 사람)이
배치로 분류하고, 확정 결과를 WORK_DICTIONARY.json에 반영한다.

4분류:
  alias     확실한 기존 작품 표기 → 사전 별칭 병합 (target=기존 W#### 코드)
  new       사전에 없는 별개 작품 → 신규 코드 부여 (target=W####, 비우면 자동 순차 부여)
  noise     작품 외 표기(굿즈·장르·창작·결측) → metadata.noise_terms 추가
  uncertain 정체 불확실 → 판단 불가 표기 (추측 금지)

사용법:
  # 1. 미매핑 고유 값 배치 입력 내보내기
  python3 scripts/llm_batch_map.py --export --tag v1.2

  # 2. LLM/사람이 analysis/llm_mapping_v1.2.csv 작성
  #    헤더: value,decision,target,reason

  # 3. 검증 후 사전 반영 (v1.1 → v1.2)
  python3 scripts/llm_batch_map.py --apply --mapping analysis/llm_mapping_v1.2.csv \
      --new-version 1.2 [--dry-run]
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from normalize_works import (  # noqa: E402
    load_dictionary,
    normalize_cell,
    strip_parentheses,
    split_multi_work,
    COLUMN_MAIN,
)

OUTPUT_DIR = os.path.join(BASE_DIR, "analysis")
VALID_DECISIONS = {"alias", "new", "noise", "uncertain"}
CODE_RE = re.compile(r"^W\d{4}$")


def collect_unmatched(dict_path):
    """전체 회차에서 규칙 1차 미매핑 고유 값 + 빈도 + 예시 셀 수집"""
    data, exact_index, norm_index, canonical = load_dictionary(dict_path)
    fuzzy_keys = list(norm_index.keys())

    fail = Counter()
    example = {}
    for fpath in sorted(glob.glob(os.path.join(BASE_DIR, "*_부스정보.csv"))):
        with open(fpath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw = (row.get(COLUMN_MAIN) or "").strip()
                if not raw:
                    continue
                _norm, meta = normalize_cell(
                    raw, exact_index, norm_index, canonical, fuzzy_keys
                )
                if any(m[0] for m in meta):
                    continue  # 셀 내 하나라도 매칭되면 배치 대상 아님
                if all(m[1] in ("empty", "noise") for m in meta):
                    continue  # 결측·노이즈 셀 제외
                fail[raw] += 1
                example.setdefault(raw, raw)
    return fail, example, data


def cmd_export(args):
    fail, example, data = collect_unmatched(args.dict)
    tag = args.tag or data["metadata"]["version"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"llm_batch_input_{tag}.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["value", "count", "decision", "target", "reason"])
        for val, cnt in fail.most_common():
            w.writerow([val, cnt, "", "", ""])
    print(f"배치 대상 고유 값 {len(fail)}종 (빈도 합 {sum(fail.values())}셀)")
    print(f"→ {out_path} 에 decision/target/reason 을 채워 넣으세요")
    print("   decision: alias|new|noise|uncertain / target: 코드(alias·new만) / reason: 근거")


def load_mapping(path):
    """매핑 CSV 로드 + 기본 검증 (컬럼: value,decision,target,reason[,origin,category,canonical])"""
    if not os.path.exists(path):
        sys.exit(f"매핑 파일 없음: {path}")
    decisions = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            val = (row.get("value") or "").strip()
            dec = (row.get("decision") or "").strip().lower()
            target = (row.get("target") or "").strip().upper()
            reason = (row.get("reason") or "").strip()
            origin = (row.get("origin") or "").strip().lower() or None
            category = (row.get("category") or "").strip().lower() or None
            canonical = (row.get("canonical") or "").strip() or None
            if not val:
                continue
            if dec not in VALID_DECISIONS:
                sys.exit(f"[{path}:{i}] 잘못된 decision '{dec}' (value: {val!r})")
            if not reason:
                sys.exit(f"[{path}:{i}] reason 누락 (value: {val!r})")
            if dec in ("alias", "new") and not CODE_RE.match(target):
                sys.exit(f"[{path}:{i}] alias/new 는 W#### 코드 target 필요 (value: {val!r})")
            if dec in ("noise", "uncertain") and target:
                sys.exit(f"[{path}:{i}] noise/uncertain 는 target 비움 (value: {val!r})")
            if val in decisions:
                sys.exit(f"[{path}:{i}] value 중복: {val!r}")
            decisions[val] = {"decision": dec, "target": target, "reason": reason,
                              "origin": origin, "category": category, "canonical": canonical}
    return decisions


def validate_against_dict(decisions, data):
    """사전 대조 검증: alias target 존재(신규 예정 포함), new 코드 미사용, value 중복"""
    works = data["works"]
    errors = []

    planned_new = {val: d["target"] for val, d in decisions.items() if d["decision"] == "new"}

    existing_names = {}
    for code, w in works.items():
        for name in [w["canonical_name"]] + w.get("aliases", []) + w.get("abbreviations", []):
            existing_names.setdefault(name, code)

    new_codes = {}
    for val, d in decisions.items():
        if d["decision"] == "alias":
            if d["target"] not in works and d["target"] not in planned_new.values():
                errors.append(f"alias target 코드 없음: {d['target']} ({val!r})")
            else:
                canon = works.get(d["target"], {}).get("canonical_name")
                if canon and val == canon:
                    errors.append(f"alias 값이 canonical과 동일: {val!r}")
        elif d["decision"] == "new":
            if d["target"] in works:
                errors.append(f"new 코드가 이미 사전에 있음: {d['target']} ({val!r})")
            if d["target"] in new_codes:
                errors.append(f"new 코드 중복 할당: {d['target']} ({val!r} vs {new_codes[d['target']]!r})")
            new_codes[d["target"]] = val
    return errors, existing_names


def next_code(works):
    n = max(int(c[1:]) for c in works) + 1
    return f"W{n:04d}"


def cmd_apply(args):
    with open(args.dict, encoding="utf-8") as f:
        data = json.load(f)
    works = data["works"]
    meta = data["metadata"]

    decisions = load_mapping(args.mapping)
    errors, existing_names = validate_against_dict(decisions, data)
    if errors:
        for e in errors:
            print(f"✗ {e}")
        sys.exit(f"검증 실패 {len(errors)}건 — 매핑 파일을 수정하세요")

    # new 코드 자동 할당 (target 비운 경우 순차 부여를 위해 사전 검증 후 처리)
    auto_assigned = []
    for val, d in decisions.items():
        if d["decision"] == "new" and not d["target"]:
            d["target"] = next_code(works)
            auto_assigned.append((d["target"], val))

    changeset = {
        "from_version": meta.get("version"),
        "to_version": args.new_version,
        "alias_merged": [],
        "new_works": [],
        "noise_added": [],
        "uncertain_marked": [],
    }

    # new 먼저 등록 → alias 병합 (alias가 신규 작품 코드를 참조할 수 있음)
    for val, d in decisions.items():
        if d["decision"] != "new":
            continue
        canonical = d.get("canonical") or val
        if canonical in [w["canonical_name"] for w in works.values()]:
            errors_ctx = f"new canonical이 기존 작품명과 충돌: {canonical!r} ({val!r})"
            print(f"✗ {errors_ctx}")
            sys.exit(f"검증 실패 — 매핑 파일을 수정하세요")
        aliases = [] if canonical == val else [val]
        works[d["target"]] = {
            "code": d["target"],
            "canonical_name": canonical,
            "origin": d.get("origin") or "unknown",
            "category": d.get("category") or "unknown",
            "aliases": aliases,
            "abbreviations": [],
            "notes": d["reason"],
        }
        changeset["new_works"].append({
            "code": d["target"], "name": canonical, "aliases": aliases,
            "reason": d["reason"],
        })

    existing_names = {}
    for code, w in works.items():
        for name in [w["canonical_name"]] + w.get("aliases", []) + w.get("abbreviations", []):
            existing_names.setdefault(name, code)

    for val, d in decisions.items():
        dec, target = d["decision"], d["target"]
        if dec == "alias":
            w = works[target]
            if val in existing_names:
                holder = existing_names[val]
                if holder == target:
                    continue  # 이미 동일 코드에 등록됨
                print(f"⚠ '{val}' 은 이미 {holder} 에 등록되어 있어 {target} 병합을 건너뜁니다")
                continue
            w.setdefault("aliases", []).append(val)
            existing_names[val] = target
            changeset["alias_merged"].append({"value": val, "code": target, "reason": d["reason"]})
        elif dec == "noise":
            if val not in meta["noise_terms"]:
                meta["noise_terms"].append(val)
                changeset["noise_added"].append({"value": val, "reason": d["reason"]})
        elif dec == "uncertain":
            changeset["uncertain_marked"].append({"value": val, "reason": d["reason"]})

    # uncertain 결정은 metadata.llm_decisions 로 사전에 영속화 (정규화기가 참조)
    llm_dec = meta.setdefault("llm_decisions", {})
    for val, d in decisions.items():
        llm_dec[val] = {"decision": d["decision"], "target": d["target"], "reason": d["reason"]}

    # 분리 연결어 (사전 데이터화 — 폴백 분리 시 버림)
    meta.setdefault("split_stopwords", ["등", "등등", "등이", "등의", "외", "및", "위주", "드림"])

    meta["version"] = args.new_version
    meta["last_updated"] = args.updated
    meta["total_works"] = len(works)
    # reverse_index 재생성 (신규 이름 반영)
    data["reverse_index"] = build_reverse_index(works)

    if args.dry_run:
        print(f"[dry-run] 별칭 병합 {len(changeset['alias_merged'])}건, "
              f"신규 작품 {len(changeset['new_works'])}건, "
              f"노이즈 {len(changeset['noise_added'])}건, "
              f"판단 불가 {len(changeset['uncertain_marked'])}건")
        if auto_assigned:
            print(f"[dry-run] 자동 코드 할당: {auto_assigned}")
        return

    # 백업 후 저장
    backup = os.path.join(
        OUTPUT_DIR, f"WORK_DICTIONARY_v{changeset['from_version']}_backup.json"
    )
    if not os.path.exists(backup):
        with open(args.dict, encoding="utf-8") as f:
            backup_content = f.read()
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(backup, "w", encoding="utf-8") as f:
            f.write(backup_content)

    with open(args.dict, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    cs_path = os.path.join(OUTPUT_DIR, f"v{args.new_version}_changeset.json")
    with open(cs_path, "w", encoding="utf-8") as f:
        json.dump(changeset, f, ensure_ascii=False, indent=2)

    print(f"사전 갱신 완료: v{changeset['from_version']} → v{args.new_version} "
          f"(총 {len(works)}종)")
    print(f"  별칭 병합 {len(changeset['alias_merged'])} / 신규 {len(changeset['new_works'])} / "
          f"노이즈 {len(changeset['noise_added'])} / 판단 불가 {len(changeset['uncertain_marked'])}")
    print(f"  백업: {backup}")
    print(f"  변경 세트: {cs_path}")


def build_reverse_index(works):
    """code → 정규화 키 목록 역인덱스 재생성"""
    from normalize_works import normalize_key
    rev = {}
    for code, w in works.items():
        keys = set()
        for name in [w["canonical_name"]] + w.get("aliases", []) + w.get("abbreviations", []):
            k = normalize_key(name)
            if k:
                keys.add(k)
            if name.strip().lower():
                keys.add(name.strip().lower())
        rev[code] = sorted(keys)
    return rev


def main():
    parser = argparse.ArgumentParser(description="LLM 배치 2차 처리 (미매핑 → 사전 반영)")
    parser.add_argument("--dict", default=os.path.join(BASE_DIR, "WORK_DICTIONARY.json"))
    parser.add_argument("--export", action="store_true", help="미매핑 고유 값 배치 입력 내보내기")
    parser.add_argument("--apply", action="store_true", help="매핑 파일을 사전에 반영")
    parser.add_argument("--mapping", help="매핑 CSV (value,decision,target,reason)")
    parser.add_argument("--tag", help="export 산출물 태그 (기본: 사전 version)")
    parser.add_argument("--new-version", help="apply 후 사전 버전 (예: 1.2)")
    parser.add_argument("--updated", default=None, help="metadata.last_updated (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.export:
        cmd_export(args)
    elif args.apply:
        if not args.mapping or not args.new_version:
            parser.error("--apply 는 --mapping 과 --new-version 이 필요합니다")
        if not args.updated:
            import datetime
            kst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
            args.updated = kst.strftime("%Y-%m-%d")
        cmd_apply(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

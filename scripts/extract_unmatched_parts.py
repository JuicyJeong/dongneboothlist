#!/usr/bin/env python3
"""
미매핑 셀을 작품 단위 토큰으로 분리해 매칭 실패 단위를 추출한다. (JWMI-4)

analyze_works.py의 미매핑은 '셀 전체' 기준이므로, 다중 작품 병기 셀의 경우
실제 실패 토큰이 묻힌다. 이 스크립트는 콤마 분리 + 괄호 처리 후 각 토큰을
재매칭하여 실패한 토큰만 빈도와 함께 파일로 저장한다.

출력 (analysis/ 하위):
  - unmatched_parts_<태그>.csv : 실패 토큰 (token, count, 예시 셀)

사용법:
  python3 scripts/extract_unmatched_parts.py --tag v1.0
"""

import argparse
import csv
import glob
import json
import os
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from normalize_works import (  # noqa: E402
    load_dictionary,
    normalize_one,
    split_multi_work,
    strip_parentheses,
    COLUMN_MAIN,
)

OUTPUT_DIR = os.path.join(BASE_DIR, "analysis")


def main():
    parser = argparse.ArgumentParser(description="미매핑 토큰 단위 추출")
    parser.add_argument("--dict", default=os.path.join(BASE_DIR, "WORK_DICTIONARY.json"))
    parser.add_argument("--tag", default=None)
    args = parser.parse_args()

    data, exact_index, norm_index, canonical = load_dictionary(args.dict)
    fuzzy_keys = list(norm_index.keys())
    tag = args.tag or data["metadata"]["version"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fail = Counter()
    example = {}

    for fpath in sorted(glob.glob(os.path.join(BASE_DIR, "*_부스정보.csv"))):
        with open(fpath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = (row.get(COLUMN_MAIN) or "").strip()
                if not raw:
                    continue
                norm, code, method, _conf = normalize_one(
                    raw, exact_index, norm_index, canonical, fuzzy_keys
                )
                if method not in ("unmatched", "noise"):
                    continue
                # 셀 전체 실패 → 토큰 분리 후 재매칭
                for part in split_multi_work(raw):
                    front, inner = strip_parentheses(part)
                    candidates = [part]
                    if inner and front:
                        candidates = [front, inner]
                    for cand in candidates:
                        _n2, c2, m2, _ = normalize_one(
                            cand, exact_index, norm_index, canonical, fuzzy_keys
                        )
                        if m2 in ("unmatched", "noise") or c2 is None:
                            key = cand.strip()
                            if key:
                                fail[key] += 1
                                example.setdefault(key, raw)

    out_path = os.path.join(OUTPUT_DIR, f"unmatched_parts_{tag}.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["token", "count", "example_cell"])
        for token, cnt in fail.most_common():
            w.writerow([token, cnt, example[token]])

    print(f"실패 토큰 {len(fail)}종 → {out_path}")


if __name__ == "__main__":
    main()

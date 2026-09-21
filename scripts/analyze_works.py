#!/usr/bin/env python3
"""
11개 회차 대표 작품(원작) 칼럼 전수 분석 스크립트 (JWMI-4)

WORK_DICTIONARY.json 기반 매칭 통계 측정 및 미매핑 목록·빈도 집계를
파일로 영속화한다.

출력 (analysis/ 하위):
  - matching_stats.json      : 회차별/전체 매칭 통계
  - frequency_all.csv        : 전체 값 빈도 (value, count)
  - unmatched_<사전버전>.csv : 미매핑 값 + 빈도 (value, count)
  - matched_works_<사전버전>.csv : 매칭된 작품 코드 + 빈도

사용법:
  python3 scripts/analyze_works.py                    # v1.0 기준 분석
  python3 scripts/analyze_works.py --tag v1.1         # 태그 지정 (산출물 파일명 구분)
"""

import argparse
import csv
import glob
import json
import os
import sys
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from normalize_works import (  # noqa: E402
    load_dictionary,
    normalize_cell,
    COLUMN_MAIN,
)

OUTPUT_DIR = os.path.join(BASE_DIR, "analysis")


def main():
    parser = argparse.ArgumentParser(description="대표 작품 칼럼 전수 분석")
    parser.add_argument("--dict", default=os.path.join(BASE_DIR, "WORK_DICTIONARY.json"))
    parser.add_argument("--tag", default=None, help="산출물 파일명 태그 (기본: 사전 version)")
    args = parser.parse_args()

    data, exact_index, norm_index, canonical = load_dictionary(args.dict)
    fuzzy_keys = list(norm_index.keys())
    dict_version = data["metadata"]["version"]
    tag = args.tag or dict_version

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(BASE_DIR, "*_부스정보.csv")))
    print(f"사전: v{dict_version} ({data['metadata']['total_works']}개 작품) | "
          f"회차 {len(files)}개")

    per_file = {}
    total_methods = Counter()
    total_cells = 0
    freq_all = Counter()                    # 전체 원본 값 빈도
    freq_unmatched = Counter()              # 미매핑 원본 값 빈도
    freq_matched_code = Counter()           # 매칭된 코드 빈도
    unmatched_by_file = defaultdict(Counter)

    for fpath in files:
        fname = os.path.basename(fpath)
        methods = Counter()
        cells = 0
        with open(fpath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = (row.get(COLUMN_MAIN) or "").strip()
                cells += 1
                if raw:
                    freq_all[raw] += 1
                _, meta = normalize_cell(
                    raw, exact_index, norm_index, canonical, fuzzy_keys
                )
                for code, method, _conf in meta:
                    methods[method] += 1
                    if method in ("unmatched", "uncertain"):
                        freq_unmatched[raw] += 1
                        unmatched_by_file[fname][raw] += 1
                    elif code:
                        freq_matched_code[code] += 1
        per_file[fname] = {
            "cells": cells,
            "methods": dict(methods),
            "matched_cells": cells - methods.get("unmatched", 0)
                             - methods.get("uncertain", 0)
                             - methods.get("noise", 0) - methods.get("empty", 0),
        }
        total_methods += methods
        total_cells += cells

        matched = per_file[fname]["matched_cells"]
        print(f"  {fname}: 셀 {cells} | 매칭 {matched} "
              f"({matched / cells * 100:.1f}%) | 미매핑 고유 "
              f"{len(unmatched_by_file[fname])}")

    matched_total = (total_cells - total_methods.get("unmatched", 0)
                     - total_methods.get("uncertain", 0)
                     - total_methods.get("noise", 0) - total_methods.get("empty", 0))
    stats = {
        "dict_version": dict_version,
        "files": per_file,
        "total": {
            "cells": total_cells,
            "methods": dict(total_methods),
            "matched_cells": matched_total,
            "match_rate": round(matched_total / total_cells * 100, 2),
            "unmatched_unique": len(freq_unmatched),
            "matched_unique_works": len(freq_matched_code),
        },
    }
    stats_path = os.path.join(OUTPUT_DIR, f"matching_stats_{tag}.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    freq_path = os.path.join(OUTPUT_DIR, f"frequency_all_{tag}.csv")
    with open(freq_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["value", "count"])
        for val, cnt in freq_all.most_common():
            w.writerow([val, cnt])

    unmatched_path = os.path.join(OUTPUT_DIR, f"unmatched_{tag}.csv")
    with open(unmatched_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["value", "count"])
        for val, cnt in freq_unmatched.most_common():
            w.writerow([val, cnt])

    matched_path = os.path.join(OUTPUT_DIR, f"matched_works_{tag}.csv")
    with open(matched_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "canonical_name", "count"])
        for code, cnt in freq_matched_code.most_common():
            w.writerow([code, canonical[code], cnt])

    print(f"\n총 셀 {total_cells} | 매칭 {matched_total} "
          f"({matched_total / total_cells * 100:.1f}%) | "
          f"미매핑 고유 {len(freq_unmatched)} | 사용 작품 {len(freq_matched_code)}종")
    print(f"산출물: {stats_path}")
    print(f"        {freq_path}")
    print(f"        {unmatched_path}")
    print(f"        {matched_path}")


if __name__ == "__main__":
    main()

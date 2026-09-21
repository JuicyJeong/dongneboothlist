#!/usr/bin/env python3
"""
11개 회차 대표 작품(원작) 칼럼 전수 분석 스크립트 (JWMI-4/JWMI-5)

WORK_DICTIONARY.json 기반 매칭 통계 측정 및 미매핑 목록·빈도 집계를
파일로 영속화한다.

지표는 **셀 단위 분류**를 표준으로 하며, 토큰(세그먼트) 단위 methods는
참고용으로 병기한다. 분류는 아래 정의를 따르고 정의 자체도 stats JSON의
`metric_definitions`에 함께 기록된다.

  셀 단위 분류 (한 셀이 정확히 하나의 버킷에 속함)
  - matched  : 작품 코드 1개 이상 부여된 셀
  - uncertain: 코드 없음 + 정규화 결과가 `판단 불가`
  - noise    : 코드 없음 + 셀 전체 원본 값이 사전 metadata.llm_decisions의
               `noise` 결정값과 정확히 일치 (v1.2 배치에서 작품 외 표기로
               확정된 고유 값). 엔진이 노이즈로 걸러도 LLM 결정이 없는
               값(예: v1.0 시절 noise_terms)은 보수적으로 residual에 남긴다
  - unmatched: 코드 없음 + 위 어디에도 해당 없음 (사람 확인 대상)
  - empty    : 원본 빈 셀

출력 (analysis/ 하위):
  - matching_stats_<tag>.json      : 회차별/전체 매칭 통계 (셀 단위 + 토큰 단위)
  - frequency_all_<tag>.csv        : 전체 원본 값 빈도 (value, count)
  - unmatched_<tag>.csv            : 잔여 미매핑 셀의 원본 값 + 빈도 (사람 확인 목록)
  - matched_works_<tag>.csv        : 매칭된 작품 코드 + 빈도

사용법:
  python3 scripts/analyze_works.py --tag v1.2
  python3 scripts/analyze_works.py --dict <사전.json> --tag <태그>
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
    normalize_cell,
    COLUMN_MAIN,
)

OUTPUT_DIR = os.path.join(BASE_DIR, "analysis")

CELL_CLASSES = ("matched", "unmatched", "uncertain", "noise", "empty")


def classify_cell(raw, meta, llm_noise_values):
    """셀 단위 분류 → matched/unmatched/uncertain/noise/empty"""
    if not raw:
        return "empty"
    if any(m[0] for m in meta):
        return "matched"
    methods = {m[1] for m in meta}
    if "uncertain" in methods:
        return "uncertain"
    if raw in llm_noise_values:
        return "noise"
    return "unmatched"


def main():
    parser = argparse.ArgumentParser(description="대표 작품 칼럼 전수 분석")
    parser.add_argument("--dict", default=os.path.join(BASE_DIR, "WORK_DICTIONARY.json"))
    parser.add_argument("--tag", default=None, help="산출물 파일명 태그 (기본: 사전 version)")
    args = parser.parse_args()

    data, exact_index, norm_index, canonical = load_dictionary(args.dict)
    fuzzy_keys = list(norm_index.keys())
    dict_version = data["metadata"]["version"]
    tag = args.tag or dict_version
    llm_noise_values = {
        v for v, d in data.get("metadata", {}).get("llm_decisions", {}).items()
        if d.get("decision") == "noise"
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(BASE_DIR, "*_부스정보.csv")))
    print(f"사전: v{dict_version} ({data['metadata']['total_works']}개 작품) | "
          f"회차 {len(files)}개 | llm noise 결정 값 {len(llm_noise_values)}종")

    per_file = {}
    total_cells = 0
    total_cell_classes = Counter()
    total_methods = Counter()               # 토큰 단위 매칭 방식 (참고용)
    freq_all = Counter()                    # 전체 원본 값 빈도
    freq_unmatched = Counter()              # 잔여 미매핑 셀의 원본 값 빈도
    freq_matched_code = Counter()           # 매칭된 코드 빈도

    for fpath in files:
        fname = os.path.basename(fpath)
        cell_classes = Counter()
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
                cell_classes[classify_cell(raw, meta, llm_noise_values)] += 1
                for code, method, _conf in meta:
                    methods[method] += 1
                    if code:
                        freq_matched_code[code] += 1
                if classify_cell(raw, meta, llm_noise_values) == "unmatched":
                    # 잔여 미매핑(사람 확인 목록)은 셀 단위 unmatched 셀만 기록
                    freq_unmatched[raw] += 1

        per_file[fname] = {
            "cells": cells,
            "cell_classes": {c: cell_classes.get(c, 0) for c in CELL_CLASSES},
            "methods": dict(methods),
            "matched_cells": cell_classes.get("matched", 0),
        }
        total_cell_classes += cell_classes
        total_methods += methods
        total_cells += cells

        matched = cell_classes.get("matched", 0)
        print(f"  {fname}: 셀 {cells} | 매칭 {matched} "
              f"({matched / cells * 100:.1f}%) | 잔여 미매핑 "
              f"{cell_classes.get('unmatched', 0)}")

    matched_total = total_cell_classes.get("matched", 0)
    effective_cells = total_cells - total_cell_classes.get("empty", 0)
    processing_cells = (matched_total
                        + total_cell_classes.get("uncertain", 0)
                        + total_cell_classes.get("noise", 0))
    stats = {
        "dict_version": dict_version,
        "metric_definitions": {
            "unit": "셀 단위 (대표 작품(원작) 칼럼 1셀 = 1 레코드)",
            "denominator": f"전체 셀 {total_cells:,} (빈 셀 포함)",
            "matched_cell": "작품 코드 1개 이상 부여된 셀",
            "match_rate": "matched_cells / cells (빈 셀 포함 분모)",
            "effective_match_rate": "matched_cells / (cells - empty_cells) — 빈 셀 제외 분모",
            "uncertain_cell": "코드 없음 + 정규화 결과가 '판단 불가' (사전 metadata.llm_decisions uncertain)",
            "noise_cell": ("코드 없음 + 셀 전체 원본 값이 사전 metadata.llm_decisions의 "
                           "noise 결정값과 정확히 일치하는 셀 (v1.2 배치 확정분만 계상, "
                           "엔진 노이즈 필터 분은 보수적으로 residual 유지)"),
            "unmatched_cell": ("코드 없음 + uncertain/noise/empty 어디에도 해당 없는 셀 "
                               "(사람 확인 대상)"),
            "processing_rate": ("(matched + uncertain + noise) / cells — 코드 부여 또는 "
                                "명시 분류(판단 불가·노이즈)까지 완료된 비율"),
            "token_methods": ("methods 키는 토큰(세그먼트) 단위 집계로 병기 셀에서는 "
                              "셀 수보다 많아질 수 있음 (참고용)"),
        },
        "files": per_file,
        "total": {
            "cells": total_cells,
            "cell_classes": {c: total_cell_classes.get(c, 0) for c in CELL_CLASSES},
            "methods": dict(total_methods),
            "matched_cells": matched_total,
            "match_rate": round(matched_total / total_cells * 100, 2),
            "effective_cells": effective_cells,
            "effective_match_rate": round(matched_total / effective_cells * 100, 2),
            "processing_cells": processing_cells,
            "processing_rate": round(processing_cells / total_cells * 100, 2),
            "processing_rate_effective": round(processing_cells / effective_cells * 100, 2),
            "unmatched_cells": total_cell_classes.get("unmatched", 0),
            "unmatched_unique": len(freq_unmatched),
            "uncertain_cells": total_cell_classes.get("uncertain", 0),
            "noise_cells": total_cell_classes.get("noise", 0),
            "empty_cells": total_cell_classes.get("empty", 0),
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
          f"({matched_total / total_cells * 100:.2f}%) | "
          f"유효 셀 기준 {matched_total / effective_cells * 100:.2f}% | "
          f"잔여 미매핑 {total_cell_classes.get('unmatched', 0)}셀 / "
          f"{len(freq_unmatched)}종 | 판단 불가 "
          f"{total_cell_classes.get('uncertain', 0)}셀 | 노이즈 "
          f"{total_cell_classes.get('noise', 0)}셀 | 사용 작품 "
          f"{len(freq_matched_code)}종")
    print(f"산출물: {stats_path}")
    print(f"        {freq_path}")
    print(f"        {unmatched_path}")
    print(f"        {matched_path}")


if __name__ == "__main__":
    main()

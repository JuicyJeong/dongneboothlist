#!/usr/bin/env python3
"""
작품 정규화 → 매핑 DB 파이프라인 (JWMI-5 단일 진입점)

신규 회차 `*_부스정보.csv` 가 들어왔을 때 아래 흐름을 한 번에 실행한다.

  ① 정규화 (규칙 기반, WORK_DICTIONARY.json v1.2+)
     → <회차>_부스정보_normalized.csv (_정규화/_코드 컬럼 추가)
  ② 미매핑 리포트 (사람 확인용)
     → analysis/unmapped_review_<event>.csv
     미매핑·판단 불가 고유 값 + 빈도 + 예시 부스. 조치 가이드 동봉
  ③ DB 반영 (SQLite)
     → works 마스터 갱신 + booth_work/booth_work_raw 적재 (INSERT OR REPLACE, 멱등)

사용법:
  # 신규 회차 1건
  python3 pipeline.py --input 26년_10월_부스정보.csv

  # 전체 회차 재구축
  python3 pipeline.py --all

  # DB 반영 없이 정규화·리포트만
  python3 pipeline.py --input 26년_10월_부스정보.csv --skip-db

  # 사전 갱신이 필요하면 (미매핑 배치 → 검증 → 사전 반영 → 재실행)
  python3 scripts/llm_batch_map.py --export --tag <새태그>
  #   → analysis/llm_batch_input_<태그>.csv 에 decision 채워 넣기 (alias/new/noise/uncertain)
  python3 scripts/llm_batch_map.py --apply --mapping analysis/llm_mapping_<태그>.csv \
      --new-version 1.3
  python3 pipeline.py --all
"""

import argparse
import csv
import glob
import os
import re
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from normalize_works import (  # noqa: E402
    load_dictionary,
    process_file,
    COLUMN_MAIN,
)
from scripts.build_db import (  # noqa: E402
    ensure_schema,
    load_works,
    import_file,
    extract_event,
)

REPORT_DIR = os.path.join(BASE_DIR, "analysis")
UNCERTAIN_MARKER = "판단 불가"


def normalize_files(files, exact_index, norm_index, canonical, fuzzy_keys):
    """① 정규화: 파일별 process_file 실행 → normalized CSV 저장. 결과 통계 반환"""
    results = []
    for path in files:
        fname = os.path.basename(path)
        print(f"① 정규화: {fname}")
        methods, unmatched, cells = process_file(
            path, exact_index, norm_index, canonical, fuzzy_keys
        )
        matched = (cells - methods.get("unmatched", 0) - methods.get("uncertain", 0)
                   - methods.get("noise", 0) - methods.get("empty", 0))
        print(f"   셀 {cells} | 코드 매칭 {matched} ({matched / cells * 100:.1f}%) | "
              f"미매핑 {methods.get('unmatched', 0)} | "
              f"판단 불가 {methods.get('uncertain', 0)} | "
              f"노이즈 {methods.get('noise', 0)}")
        results.append({
            "path": path,
            "outpath": path.replace(".csv", "_normalized.csv"),
            "cells": cells,
            "methods": methods,
            "unmatched": unmatched,
        })
    return results


def write_review_report(result):
    """② 미매핑 리포트: 고유 값 + 빈도 → analysis/unmapped_review_<event>.csv"""
    event = extract_event(result["path"])
    os.makedirs(REPORT_DIR, exist_ok=True)
    out_path = os.path.join(REPORT_DIR, f"unmapped_review_{event}.csv")

    rows = [(val, cnt) for val, cnt in result["unmatched"].most_common()]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["value", "count", "decision", "target", "reason"])
        w.writerow([
            "# 미매핑·판단 불가 고유 값 목록 (사람 확인용)",
            "", "", "", "",
        ])
        w.writerow([
            "# 조치: 확실한 동일 작품이면 scripts/llm_batch_map.py 배치에 alias 병합,",
            "#       작품 외 표기(굿즈·장르)면 noise, 정체 불명이면 uncertain(판단 불가) 유지",
            "", "", "", "",
        ])
        for val, cnt in rows:
            w.writerow([val, cnt, "", "", ""])

    print(f"② 미매핑 리포트: {len(rows)} 고유 값 → {out_path}")
    return out_path, rows


def update_db(dict_path, db_path, normalized_paths):
    """③ DB 반영: works 마스터 갱신 + normalized 파일 적재"""
    import sqlite3

    conn = sqlite3.connect(db_path)
    ensure_schema(conn)
    cur = conn.cursor()

    works_rows, version = load_works(dict_path)
    cur.execute("DELETE FROM works")
    cur.executemany("INSERT INTO works VALUES (?,?,?,?,?,?,?,?,?)", works_rows)
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('dict_version', ?)", (version,))
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (
        __import__("datetime").datetime.now(
            __import__("datetime").timezone(__import__("datetime").timedelta(hours=9))
        ).strftime("%Y-%m-%d %H:%M (KST)"),
    ))
    conn.commit()
    print(f"③ DB: works 마스터 갱신 (사전 v{version}, {len(works_rows)}종)")

    for path in normalized_paths:
        event = extract_event(path)
        n_map, n_raw, skipped = import_file(conn, path, event, cur)
        conn.commit()
        note = f" (링크 없음 제외 {skipped})" if skipped else ""
        print(f"   {event}: 매핑 {n_map}행 / 원문 {n_raw}행{note}")
    conn.close()
    print(f"   DB: {db_path}")


def main():
    parser = argparse.ArgumentParser(
        description="정규화 → 미매핑 리포트 → DB 반영 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("사용법:")[1] if "사용법:" in __doc__ else None,
    )
    parser.add_argument("--input", action="append", default=[],
                        help="입력 *_부스정보.csv (반복 지정 가능)")
    parser.add_argument("--all", action="store_true", help="전체 회차 대상")
    parser.add_argument("--dict", default=os.path.join(BASE_DIR, "WORK_DICTIONARY.json"))
    parser.add_argument("--db", default=os.path.join(BASE_DIR, "works.db"))
    parser.add_argument("--skip-db", action="store_true", help="DB 반영 생략")
    args = parser.parse_args()

    if args.all:
        files = sorted(glob.glob(os.path.join(BASE_DIR, "*_부스정보.csv")))
    elif args.input:
        files = [p if os.path.isabs(p) else os.path.join(BASE_DIR, p) for p in args.input]
    else:
        parser.print_help()
        sys.exit(1)

    for f in files:
        if not os.path.exists(f):
            sys.exit(f"파일 없음: {f}")

    data, exact_index, norm_index, canonical = load_dictionary(args.dict)
    fuzzy_keys = list(norm_index.keys())
    print(f"사전 v{data['metadata']['version']} "
          f"({data['metadata']['total_works']}종) | 대상 {len(files)} 파일\n")

    results = normalize_files(files, exact_index, norm_index, canonical, fuzzy_keys)

    print()
    for r in results:
        write_review_report(r)

    if not args.skip_db:
        print()
        update_db(args.dict, args.db, [r["outpath"] for r in results])

    print("\n완료. 미매핑 값은 analysis/unmapped_review_*.csv 에서 확인하세요.")
    print("사전 갱신 절차는 scripts/llm_batch_map.py --help 참조.")


if __name__ == "__main__":
    main()

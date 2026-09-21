#!/usr/bin/env python3
"""
정규화된 부스정보 CSV → SQLite 매핑 DB 구축 (JWMI-5)

WORK_DICTIONARY.json 으로 works 마스터 테이블을, `*_부스정보_normalized.csv`로
booth_work(부스-작품 매핑)·booth_work_raw(원문 보존) 테이블을 구축한다.

사용법:
  python3 scripts/build_db.py                     # 전체 회차 대상 (기본 works.db)
  python3 scripts/build_db.py --input 26년_7월_부스정보_normalized.csv
  python3 scripts/build_db.py --db works.db --append
"""

import argparse
import csv
import glob
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_PATH = os.path.join(BASE_DIR, "WORK_DICTIONARY.json")
COLUMN_MAIN = "대표 작품(원작)"
LINK_COL = "링크"
UNCERTAIN_MARKER = "판단 불가"


def ensure_schema(conn):
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS works (
            code           TEXT PRIMARY KEY,
            canonical_name TEXT NOT NULL,
            origin         TEXT,
            category       TEXT,
            aliases        TEXT,
            abbreviations  TEXT,
            review_needed  INTEGER DEFAULT 0,
            notes          TEXT,
            dict_version   TEXT
        );

        CREATE TABLE IF NOT EXISTS booth_work (
            event        TEXT NOT NULL,
            booth_link   TEXT NOT NULL,
            work_code    TEXT NOT NULL,
            position     INTEGER DEFAULT 0,
            match_method TEXT,
            confidence   REAL,
            PRIMARY KEY (event, booth_link, work_code, position),
            FOREIGN KEY (work_code) REFERENCES works(code)
        );
        CREATE INDEX IF NOT EXISTS idx_booth_work_code ON booth_work(work_code);
        CREATE INDEX IF NOT EXISTS idx_booth_work_event ON booth_work(event);

        CREATE TABLE IF NOT EXISTS booth_work_raw (
            event      TEXT NOT NULL,
            booth_link TEXT NOT NULL,
            row_index  INTEGER,
            raw_value  TEXT,
            normalized TEXT,
            codes      TEXT,
            status     TEXT,
            PRIMARY KEY (event, booth_link, row_index)
        );
        CREATE INDEX IF NOT EXISTS idx_booth_raw_status ON booth_work_raw(status);

        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    conn.commit()


def load_works(dict_path):
    with open(dict_path, encoding="utf-8") as f:
        data = json.load(f)
    version = data["metadata"]["version"]
    rows = []
    for code, w in data["works"].items():
        rows.append((
            code,
            w["canonical_name"],
            w.get("origin", ""),
            w.get("category", ""),
            json.dumps(w.get("aliases", []), ensure_ascii=False),
            json.dumps(w.get("abbreviations", []), ensure_ascii=False),
            1 if w.get("review_needed") else 0,
            w.get("notes", ""),
            version,
        ))
    return rows, version


def parse_codes(codes_field):
    """코드 컬럼('W0001; W0002') → [W0001, ...]"""
    if not codes_field:
        return []
    return [c.strip() for c in codes_field.split(";") if c.strip()]


def extract_event(path):
    """파일명에서 회차 추출 (예: 26년_7월_부스정보_normalized.csv → 26년_7월)"""
    name = os.path.basename(path)
    m = re.match(r"(.+?)_부스정보", name)
    return m.group(1) if m else name.replace("_부스정보_normalized.csv", "")


def import_file(conn, path, event, batch):
    """normalized CSV 1개 파일을 DB에 적재. 반환 (mapping_rows, raw_rows, skipped)"""
    mapping_rows, raw_rows, skipped = [], [], 0
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            link = (row.get(LINK_COL) or "").strip()
            if not link:
                # 부스 링크 없는 행은 고유 키 부재로 매핑 테이블 제외(원문만 유지)
                skipped += 1
                continue
            raw = (row.get(COLUMN_MAIN) or "").strip()
            norm = (row.get(f"{COLUMN_MAIN}_정규화") or "").strip()
            codes = parse_codes(row.get(f"{COLUMN_MAIN}_코드") or "")

            if not raw:
                status = "empty"
            elif codes:
                status = "matched"
            elif norm == UNCERTAIN_MARKER or UNCERTAIN_MARKER in norm:
                status = "uncertain"
            else:
                status = "unmatched"

            for pos, code in enumerate(codes):
                mapping_rows.append((event, link, code, pos, "normalized", None))
            raw_rows.append((event, link, idx, raw, norm, "; ".join(codes), status))

    batch.executemany(
        "INSERT OR REPLACE INTO booth_work VALUES (?, ?, ?, ?, ?, ?)", mapping_rows
    )
    batch.executemany(
        "INSERT OR REPLACE INTO booth_work_raw VALUES (?, ?, ?, ?, ?, ?, ?)", raw_rows
    )
    return len(mapping_rows), len(raw_rows), skipped


def main():
    parser = argparse.ArgumentParser(description="정규화 CSV → SQLite 매핑 DB 구축")
    parser.add_argument("--input", help="단일 normalized CSV (미지정 시 전체 회차)")
    parser.add_argument("--db", default=os.path.join(BASE_DIR, "works.db"))
    parser.add_argument("--dict", default=DICT_PATH)
    parser.add_argument("--append", action="store_true",
                        help="기존 DB에 추가 (미지정 시 works 테이블 제외 전부 재구축)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    ensure_schema(conn)
    cur = conn.cursor()

    # works 마스터: 항상 사전 기준으로 교체 (사전이 소스 오브 트루스)
    works_rows, version = load_works(args.dict)
    cur.execute("DELETE FROM works")
    cur.executemany("INSERT INTO works VALUES (?,?,?,?,?,?,?,?,?)", works_rows)
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('dict_version', ?)", (version,))
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)",
                (__import__("datetime").datetime.now(
                    __import__("datetime").timezone(__import__("datetime").timedelta(hours=9))
                ).strftime("%Y-%m-%d %H:%M (KST)"),))
    conn.commit()

    if not args.append:
        cur.execute("DELETE FROM booth_work")
        cur.execute("DELETE FROM booth_work_raw")
        conn.commit()

    if args.input:
        files = [args.input]
    else:
        files = sorted(glob.glob(os.path.join(BASE_DIR, "*_부스정보_normalized.csv")))
    if not files:
        sys.exit("입력 파일 없음 — normalize_works.py --all 먼저 실행")

    batch = cur
    total_map, total_raw = 0, 0
    for path in files:
        event = extract_event(path)
        n_map, n_raw, skipped = import_file(conn, path, event, batch)
        conn.commit()
        total_map += n_map
        total_raw += n_raw
        print(f"  {event}: 매핑 {n_map}행 / 원문 {n_raw}행"
              + (f" (링크 없음 제외 {skipped})" if skipped else ""))

    stats = cur.execute(
        """SELECT status, COUNT(*) FROM booth_work_raw GROUP BY status ORDER BY 2 DESC"""
    ).fetchall()
    works_count = cur.execute("SELECT COUNT(*) FROM works").fetchone()[0]
    print(f"\nDB: {args.db} (사전 v{version}, 작품 {works_count}종)")
    print(f"  부스-작품 매핑 {total_map}행 / 원문 레코드 {total_raw}행")
    for status, cnt in stats:
        print(f"  {status}: {cnt}")
    conn.close()


if __name__ == "__main__":
    main()

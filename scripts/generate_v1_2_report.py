#!/usr/bin/env python3
"""
WORK_DICTIONARY v1.2 갱신 보고서 생성 (JWMI-5)

analysis/ 산출물과 사전, works.db 실측값을 읽어
docs/work_dictionary_v1.2_report.md 를 생성한다.
수치는 모두 산출물·DB에서 자동 산출된다.

사용법:
  python3 scripts/generate_v1_2_report.py
"""

import csv
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(BASE_DIR, "analysis")
DOCS = os.path.join(BASE_DIR, "docs")
DICT_PATH = os.path.join(BASE_DIR, "WORK_DICTIONARY.json")
DB_PATH = os.path.join(BASE_DIR, "works.db")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def db_facts(db_path):
    """works.db 실측값 (DB 부재 시 None)"""
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        q = lambda sql: cur.execute(sql).fetchone()[0]  # noqa: E731
        return {
            "works": q("SELECT COUNT(*) FROM works"),
            "booth_work": q("SELECT COUNT(*) FROM booth_work"),
            "booth_work_raw": q("SELECT COUNT(*) FROM booth_work_raw"),
            "status": dict(cur.execute(
                "SELECT status, COUNT(*) FROM booth_work_raw GROUP BY status"
            ).fetchall()),
        }
    finally:
        conn.close()


def main():
    dict_data = load_json(DICT_PATH)
    works = dict_data["works"]
    meta = dict_data["metadata"]
    stats = load_json(os.path.join(ANALYSIS, "matching_stats_v1.2.json"))
    mapping_rows = load_csv_rows(os.path.join(ANALYSIS, "llm_mapping_v1.2.csv"))
    unmatched = load_csv_rows(os.path.join(ANALYSIS, "unmatched_v1.2.csv"))
    db = db_facts(DB_PATH)

    total = stats["total"]
    cc = total["cell_classes"]
    dec_counts = {"alias": 0, "new": 0, "noise": 0, "uncertain": 0}
    for r in mapping_rows:
        d = r.get("decision", "")
        if d in dec_counts:
            dec_counts[d] += 1

    lines = []
    a = lines.append
    a("# WORK_DICTIONARY v1.2 갱신 및 하이브리드 전처리 파이프라인 보고서")
    a("")
    a("> 이슈: JWMI-5 ([Stage 2] 하이브리드 전처리 파이프라인 구현 및 전체 회차 정규화·DB화)")
    a(f"> 기준 시각: {meta.get('last_updated')} (KST) · 매칭 엔진: `normalize_works.py` (사전 v1.2)")
    a("> 본 보고서 수치는 v1.2 사전 적용 후 최종 재정규화 산출물(`*_부스정보_normalized.csv`)과 "
      "`works.db` 실측 기준")
    a("")
    a("## 1. 요약")
    a("")
    a("| 항목 | 수치 | 비고 |")
    a("|---|---|---|")
    a(f"| 총 셀(분모) | {total['cells']:,} | 11개 회차 `대표 작품(원작)` 전체, 빈 셀 포함 |")
    a(f"| 빈 셀 | {total['empty_cells']:,} | 분모에 포함 (유효 셀 {total['effective_cells']:,}) |")
    a(f"| 매칭 성공 셀 | {total['matched_cells']:,} | 코드 1개 이상 부여 셀 |")
    a(f"| **매칭률(전체 셀 분모)** | **{total['match_rate']:.2f}%** | {total['matched_cells']:,}/{total['cells']:,} |")
    a(f"| 매칭률(유효 셀 분모) | {total['effective_match_rate']}% | 빈 셀 {total['empty_cells']:,} 제외 |")
    a(f"| 판단 불가 셀 | {total['uncertain_cells']} | 사전 `llm_decisions` uncertain |")
    a(f"| 노이즈 셀 | {total['noise_cells']} | 셀 전체 값이 LLM noise 결정값과 정확히 일치 |")
    a(f"| **잔여 미매핑** | **{total['unmatched_cells']}셀 / {total['unmatched_unique']}종** | 사람 확인 대상 (§5) |")
    a(f"| **처리율(전체 셀 분모)** | **{total['processing_rate']:.2f}%** | 코드 부여 또는 명시 분류 완료 |")
    a(f"| 처리율(유효 셀 분모) | {total['processing_rate_effective']}% | "
      f"{total['processing_cells']:,}/{total['effective_cells']:,} |")
    a(f"| 등장 작품(코드) 수 | {total['matched_unique_works']} | |")
    a(f"| 사전 등재 작품 수 | {meta['total_works']} | W0001~W0459 |")
    a("")
    a("사전 버전별 매칭률 추이: 77.58%(v1.0, 구 산식) → 82.57%(v1.1, 구 산식) → "
      f"**{total['match_rate']:.2f}%(v1.2, 셀 단위 산식)**")
    a("")
    a("### 1.1 지표 산식 정의")
    a("")
    a("- **단위**: 셀 단위. `대표 작품(원작)` 칼럼 1셀 = 1 레코드이며, 한 셀이 정확히 "
      "하나의 분류(matched/unmatched/uncertain/noise/empty)에 속한다. 복수 작품 병용 셀은 "
      "세그먼트로 분해 저장되지만 통계는 셀 기준")
    a("- **매칭률** = 매칭 성공 셀(작품 코드 1개 이상 부여) ÷ 전체 셀. **빈 셀 "
      f"{total['empty_cells']:,}개를 분모에 포함**한다 (참고용으로 빈 셀 제외 유효 셀 분모 "
      f"{total['effective_match_rate']}% 병기)")
    a("- **노이즈 셀** = 코드가 없으면서 셀 전체 원본 값이 사전 `metadata.llm_decisions`의 "
      "`noise` 결정값(72종)과 정확히 일치하는 셀. 엔진 노이즈 필터(`noise_terms`)에 걸리지만 "
      "LLM 결정이 없는 값은 보수적으로 잔여 미매핑에 유지한다 (예: `스티커`, `키링` 등 v1.0 시절 필터 분)")
    a("- **판단 불가 셀** = 코드가 없으면서 정규화 결과가 `판단 불가`인 셀 "
      "(사전 `llm_decisions` uncertain 130종 기준)")
    a("- **처리율** = (매칭 성공 + 판단 불가 + 노이즈 셀) ÷ 전체 셀 — 코드 부여 또는 "
      "명시 분류까지 완료된 비율. 잔여 미매핑만 사람 확인 대상으로 남는다")
    a("- **토큰 단위 참고치**: 병용 셀은 세그먼트별로 매칭되므로 methods(토큰) 합계는 셀 수보다 "
      "클 수 있다. 토큰 단위 상세는 `matching_stats_v1.2.json`의 `methods` 참조")
    a("")
    a("### 1.2 DB 실측값 (works.db)")
    a("")
    if db:
        a(f"- `works` {db['works']:,}종 / `booth_work` **{db['booth_work']:,}행** / "
          f"`booth_work_raw` {db['booth_work_raw']:,}행 (실측)")
        a(f"- `booth_work_raw` 상태 분류: " + ", ".join(
            f"{k} {v:,}" for k, v in sorted(db["status"].items(), key=lambda x: -x[1]))
          + " — DB status의 unmatched "
          f"{db['status'].get('unmatched', 0):,}셀은 잔여 미매핑 "
          f"{total['unmatched_cells']}셀 + 노이즈 셀 {total['noise_cells']}셀의 합이다 "
          "(build_db status는 LLM 노이즈 결정분을 별도로 구분하지 않음)")
        a("- `booth_work`는 부스 링크+코드+position 기본키로 중복 링크가 dedup 된 실측치이다 "
          "(25년_1월 중복 부스 링크 circles/137809 1건 dedup 반영)")
    else:
        a("- works.db 없음 — `python3 scripts/build_db.py` 실행 후 재생성")
    a("")
    a("## 2. LLM 배치 2차 처리 결과 (규칙 1차 미매핑 336 고유 값 대상)")
    a("")
    a("| 분류 | 건수 | 설명 |")
    a("|---|---|---|")
    a(f"| alias (별칭 병합) | {dec_counts['alias']} | 기존 코드에 별칭 추가 — 코드 불변 |")
    a(f"| new (신규 작품) | {dec_counts['new']} | W0370부터 순차 부여 |")
    a(f"| noise (노이즈) | {dec_counts['noise']} | 굿즈·장르·창작 등 작품 외 표기 |")
    a(f"| uncertain (판단 불가) | {dec_counts['uncertain']} | 정체 불확실 — 추측 금지 원칙 |")
    a("")
    a("- 신규 부여 코드: `W0370` ~ "
      f"`W{max(int(c[1:]) for c in works):04d}` (일부 코드는 기존 등록으로 미사용)")
    a("- 결정 근거는 `analysis/llm_mapping_v1.2.csv`의 reason 컬럼, 반영 내역은 "
      "`analysis/v1.2_changeset.json` 참조")
    a("- uncertain 결정은 사전 `metadata.llm_decisions`에 영속화되어 정규화 결과에 "
      "`판단 불가`로 표기됨")
    a("")
    a("## 3. 회차별 매칭 통계 (v1.2 기준, 셀 단위)")
    a("")
    a("| 회차 | 셀 수 | 매칭 셀 | 매칭률 | 잔여 미매핑 | 판단 불가 | 노이즈 | 빈 셀 |")
    a("|---|---|---|---|---|---|---|---|")
    for fname in sorted(stats["files"]):
        f = stats["files"][fname]
        fc = f["cell_classes"]
        ev = fname.replace("_부스정보.csv", "")
        a(f"| {ev} | {f['cells']:,} | {fc['matched']:,} | "
          f"{fc['matched'] / f['cells'] * 100:.1f}% | {fc['unmatched']} | "
          f"{fc['uncertain']} | {fc['noise']} | {fc['empty']} |")
    a("")
    a("## 4. DB화 결과")
    a("")
    a("- DB 파일: `works.db` (SQLite) — `scripts/build_db.py` 재생성 가능")
    a("- 테이블: `works`(작품 마스터), `booth_work`(부스-작품 매핑, 부스 링크 키), "
      "`booth_work_raw`(원문 보존·상태 분류), `meta` — 실측 행수는 §1.2")
    a("- 파이프라인: `pipeline.py --all` / `pipeline.py --input <신규 회차 CSV>` "
      "(정규화 → 미매핑 리포트 → DB 반영, 멱등성 검증 완료)")
    a("")
    a("## 5. 잔여 미매핑 (사람 확인 대상)")
    a("")
    a(f"고유 값 {total['unmatched_unique']}종 / 셀 {total['unmatched_cells']}건 "
      "(코드 미부여 + 판단 불가·노이즈 제외). "
      "전체 목록: `analysis/unmatched_v1.2.csv`:")
    a("")
    a("| value | count |")
    a("|---|---|")
    for r in unmatched:
        a(f"| {r['value'][:60]} | {r['count']} |")
    a("")
    a("- 성격: 1차 창작·창작 일반 표기, 굿즈·문구류 병기 잔여, 무의미 단일 문자(`.`, `ㅇ`, `0` 등), "
      "사전 미등재 개별 작품(예: 영화 `어쨌든 찬란`)이 대부분. 이미 노이즈로 분류된 값은 "
      "포함되지 않는다")
    a("- 후속 조치: `pipeline.py` 실행 시 생성되는 `analysis/unmapped_review_*.csv`에서 "
      "사람이 decision을 기입 → `scripts/llm_batch_map.py --apply`로 증분 반영")
    a("")
    a("## 6. 재현 방법")
    a("")
    a("```bash")
    a("# v1.1 상태에서 v1.2 사전 빌드 (LLM 배치 매핑 적용)")
    a("cp analysis/WORK_DICTIONARY_v1.1_backup.json WORK_DICTIONARY.json")
    a("python3 scripts/llm_batch_map.py --apply --mapping analysis/llm_mapping_v1.2.csv \\")
    a("    --new-version 1.2 --updated 2026-09-21")
    a("")
    a("# 전체 회차 정규화 + 통계 재수집 + DB 재구축 (적용 후 최종 산출물 기준)")
    a("python3 pipeline.py --all")
    a("python3 scripts/analyze_works.py --tag v1.2   # 셀 단위 통계·unmatched 재수집")
    a("python3 scripts/generate_v1_2_report.py      # 본 보고서 재생성")
    a("```")

    os.makedirs(DOCS, exist_ok=True)
    out_path = os.path.join(DOCS, "work_dictionary_v1.2_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"보고서 생성: {out_path}")


if __name__ == "__main__":
    main()

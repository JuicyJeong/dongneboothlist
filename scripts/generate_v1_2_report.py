#!/usr/bin/env python3
"""
WORK_DICTIONARY v1.2 갱신 보고서 생성 (JWMI-5)

analysis/ 산출물과 사전을 읽어 docs/work_dictionary_v1.2_report.md 를 생성한다.
수치는 모두 산출물에서 자동 산출된다.

사용법:
  python3 scripts/generate_v1_2_report.py
"""

import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(BASE_DIR, "analysis")
DOCS = os.path.join(BASE_DIR, "docs")
DICT_PATH = os.path.join(BASE_DIR, "WORK_DICTIONARY.json")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    dict_data = load_json(DICT_PATH)
    works = dict_data["works"]
    meta = dict_data["metadata"]
    stats = load_json(os.path.join(ANALYSIS, "matching_stats_v1.2.json"))
    stats_prev = load_json(os.path.join(ANALYSIS, "matching_stats_v1.1.json"))
    changeset = load_json(os.path.join(ANALYSIS, "v1.2_changeset.json"))
    mapping_rows = load_csv_rows(os.path.join(ANALYSIS, "llm_mapping_v1.2.csv"))
    unmatched = load_csv_rows(os.path.join(ANALYSIS, "unmatched_v1.2.csv"))

    total = stats["total"]
    total_prev = stats_prev["total"]
    dec_counts = {"alias": 0, "new": 0, "noise": 0, "uncertain": 0}
    for r in mapping_rows:
        d = r.get("decision", "")
        if d in dec_counts:
            dec_counts[d] += 1

    llm_dec = meta.get("llm_decisions", {})
    uncertain_values = [v for v, d in llm_dec.items() if d.get("decision") == "uncertain"]

    lines = []
    a = lines.append
    a("# WORK_DICTIONARY v1.2 갱신 및 하이브리드 전처리 파이프라인 보고서")
    a("")
    a(f"> 이슈: JWMI-5 ([Stage 2] 하이브리드 전처리 파이프라인 구현 및 전체 회차 정규화·DB화)")
    a(f"> 기준 시각: {meta.get('last_updated')} (KST) · 매칭 엔진: `normalize_works.py` (사전 v1.2)")
    a("")
    a("## 1. 요약")
    a("")
    a("| 항목 | v1.1 | v1.2 | 개선 |")
    a("|---|---|---|---|")
    a(f"| 총 셀 | {total_prev['cells']:,} | {total['cells']:,} | - |")
    a(f"| 매칭 성공 셀 | {total_prev['matched_cells']:,} | {total['matched_cells']:,} | "
      f"+{total['matched_cells'] - total_prev['matched_cells']:,} |")
    a(f"| **매칭률** | **{total_prev['match_rate']}%** | **{total['match_rate']}%** | "
      f"**+{round(total['match_rate'] - total_prev['match_rate'], 2)}%p** |")
    a(f"| 미매핑 고유 값 | {total_prev['unmatched_unique']} | {total['unmatched_unique']} | "
      f"-{total_prev['unmatched_unique'] - total['unmatched_unique']} |")
    a(f"| 등장 작품(코드) 수 | {total_prev['matched_unique_works']} | "
      f"{total['matched_unique_works']} | +{total['matched_unique_works'] - total_prev['matched_unique_works']} |")
    a(f"| 사전 등재 작품 수 | 369 | {meta['total_works']} | +{meta['total_works'] - 369} |")
    a("")
    m = total["methods"]
    handled = total["cells"] - m.get("unmatched", 0)
    a(f"- 코드 미부여 잔여(unmatched) {m.get('unmatched', 0)}셀 외에, LLM 2차에서 `판단 불가`로 "
      f"명시 분류된 셀 {m.get('uncertain', 0)}건, 작품 외 표기(노이즈) {m.get('noise', 0)}셀이 분류됨")
    a(f"- **처리율(코드 부여 또는 명시 분류)**: {handled:,}/{total['cells']:,} "
      f"({handled / total['cells'] * 100:.2f}%)")
    fb = sum(v for k, v in m.items() if "fallback" in k)
    a(f"- 폴백 분리(공백·마침표·기호 병기 셀 재매칭)로 추가 매칭된 토큰 {fb}개")
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
    a("## 3. 회차별 매칭 통계 (v1.2 기준)")
    a("")
    a("| 회차 | 셀 수 | 매칭 셀 | 매칭률 | 미매핑 셀 |")
    a("|---|---|---|---|---|")
    for fname in sorted(stats["files"]):
        f = stats["files"][fname]
        fm = f["methods"]
        ev = fname.replace("_부스정보.csv", "")
        a(f"| {ev} | {f['cells']:,} | {f['matched_cells']:,} | "
          f"{f['matched_cells'] / f['cells'] * 100:.1f}% | "
          f"{fm.get('unmatched', 0) + fm.get('uncertain', 0)} |")
    a("")
    a("## 4. DB화 결과")
    a("")
    a("- DB 파일: `works.db` (SQLite) — `scripts/build_db.py` 재생성 가능")
    a("- 테이블: `works`(작품 마스터), `booth_work`(부스-작품 매핑, 부스 링크 키), "
      "`booth_work_raw`(원문 보존·상태 분류), `meta`")
    a("- 파이프라인: `pipeline.py --all` / `pipeline.py --input <신규 회차 CSV>` "
      "(정규화 → 미매핑 리포트 → DB 반영, 멱등성 검증 완료)")
    a("")
    a("## 5. 잔여 미매핑 (사람 확인 대상)")
    a("")
    a(f"고유 값 {total['unmatched_unique']}종 / 셀 {m.get('unmatched', 0)}건. "
      "상위 30건 (전체: `analysis/unmatched_v1.2.csv`):")
    a("")
    a("| value | count |")
    a("|---|---|")
    for r in unmatched[:30]:
        a(f"| {r['value'][:60]} | {r['count']} |")
    a("")
    a("- 성격: 복합 병기 셀의 굿즈·설명 꼬리(예: '등등 게임장르 위주'), Stage 1부터 특정 불가였던 "
      "동명 다수 표기(신삼국·삼국지·갈릴레오 시리즈 등), 초성·약칭의 미확인 표기가 대부분")
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
    a("# 전체 회차 정규화 + DB 구축")
    a("python3 scripts/analyze_works.py --tag v1.2   # 통계 측정")
    a("python3 scripts/build_db.py                    # DB 재구축")
    a("# 또는 단일 진입점: python3 pipeline.py --all")
    a("```")

    os.makedirs(DOCS, exist_ok=True)
    out_path = os.path.join(DOCS, "work_dictionary_v1.2_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"보고서 생성: {out_path}")


if __name__ == "__main__":
    main()

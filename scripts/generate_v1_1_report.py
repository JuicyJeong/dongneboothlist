#!/usr/bin/env python3
"""
WORK_DICTIONARY v1.1 갱신 + 11개 회차 분석 보고서 생성기 (JWMI-4)

analysis/ 산출물(matching_stats, changeset, unmatched CSV)과 WORK_DICTIONARY.json을
읽어 docs/work_dictionary_v1.1_report.md 를 생성한다.

사용법:
  python3 scripts/generate_v1_1_report.py
"""

import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, "docs", "work_dictionary_v1.1_report.md")

# 판단 불가 / 미등록으로 남긴 주요 표기 (검토 기록)
UNRESOLVED_NOTES = [
    ("해파리소녀", "동명 표기 다수(싱글·굿즈 브랜드 등) — 작품 특정 불가"),
    ("신삼국 / 삼국지", "동명 게임·소설 다수 — 세부 특정 불가"),
    ("탑로더 탑꾸 셀 내 혼합 표기", "공예·굿즈 표기와 작품 표기 혼재"),
    ("터무니없는 이야기", "동명 다수 — 특정 불가"),
    ("무해한 과일 친구들", "정체 확인 불가"),
    ("요철세계", "정체 확인 불가"),
    ("잭잔느", "정체 확인 불가"),
    ("BYAKKO", "정체 확인 불가"),
    ("스어유", "정체 확인 불가"),
    ("갈릴레오 시리즈", "정체 확인 불가"),
    ("위닝샷", "동명 다수(영화 등) — 특정 불가"),
    ("레뷰", "정체 확인 불가"),
    ("플레지위치", "TRPG 룰북 가능성 있으나 공식 정보 부재"),
    ("주인감염", "TRPG 시나리오로 추정, 룰/원작 미확인"),
    ("공조살 외 단독 약칭 중 미매칭 잔여", "약칭 출처 불명 — 재검토 대상"),
    ("가히리·모로스 등 단독 인물/작가 추정 표기", "작품 특정 불가"),
    ("디즈니", "기업명 통칭 — 작품 특정 불가"),
    ("엑스맨", "MCU 아님(폭스판) — 별도 코드 미부여, 잔여"),
    ("이영도 소설", "작가명만 표기, 작품 미특정"),
]

SPACE_JOINED_EXAMPLES = [
    "데못죽.플레이브", "괴담출근 데못죽", "뱅드림 아베무지카", "케이팝데몬헌터스 사카모토데이즈",
    "페르소나 아이돌리쉬세븐 우마무스메", "진혼기 반월당", "왕은웃었다 길라잡이의등불",
]


def main():
    dict_path = os.path.join(BASE_DIR, "WORK_DICTIONARY.json")
    with open(dict_path, encoding="utf-8") as f:
        d = json.load(f)

    with open(os.path.join(BASE_DIR, "analysis", "matching_stats_1.0.json"), encoding="utf-8") as f:
        stats10 = json.load(f)
    with open(os.path.join(BASE_DIR, "analysis", "matching_stats_v1.1.json"), encoding="utf-8") as f:
        stats11 = json.load(f)
    with open(os.path.join(BASE_DIR, "analysis", "v1.1_changeset.json"), encoding="utf-8") as f:
        changes = json.load(f)

    with open(os.path.join(BASE_DIR, "analysis", "unmatched_v1.1.csv"), encoding="utf-8") as f:
        unmatched = [(r["value"], int(r["count"])) for r in csv.DictReader(f)]
    with open(os.path.join(BASE_DIR, "analysis", "matched_works_v1.1.csv"), encoding="utf-8") as f:
        matched = [(r["code"], r["canonical_name"], int(r["count"])) for r in csv.DictReader(f)]

    L = []
    a = L.append

    a("# WORK_DICTIONARY v1.1 갱신 및 11개 회차 대표 작품 전수 분석 보고서")
    a("")
    a("> 이슈: JWMI-4 ([Stage 1] 11개 회차 대표 작품 칼럼 전수 분석 및 작품 사전 v1.1 보강)")
    a("> 기준 시각: 2026-09-21 (KST) · 분석 대상: 24년_1월 ~ 26년_7월 `_부스정보.csv` 11개 회차")
    a("> 매칭 엔진: `normalize_works.py` (exact → normalized → fuzzy 0.85), 사전 버전만 교체하여 동일 조건 측정")
    a("")

    # 1. 요약
    t10, t11 = stats10["total"], stats11["total"]
    a("## 1. 요약")
    a("")
    a("| 항목 | v1.0 (211종) | v1.1 (369종) | 개선 |")
    a("|---|---|---|---|")
    a(f"| 총 셀 | {t10['cells']:,} | {t11['cells']:,} | - |")
    a(f"| 매칭 성공 셀 | {t10['matched_cells']:,} | {t11['matched_cells']:,} | +{t11['matched_cells']-t10['matched_cells']:,} |")
    a(f"| **매칭률** | **{t10['match_rate']}%** | **{t11['match_rate']}%** | **+{round(t11['match_rate']-t10['match_rate'],2)}%p** |")
    a(f"| 미매핑 고유 값 | {t10['unmatched_unique']:,} | {t11['unmatched_unique']:,} | -{t10['unmatched_unique']-t11['unmatched_unique']:,} |")
    a(f"| 등장 작품(코드) 수 | {t10['matched_unique_works']} | {t11['matched_unique_works']} | +{t11['matched_unique_works']-t10['matched_unique_works']} |")
    a("")
    a("- 매칭률 분모에서 결측/노이즈 셀은 제외되며, 노이즈 기준은 v1.1부터 사전 `metadata.noise_terms`(60종)로 데이터화됨")
    a("- 이전 세션에서 측정된 별칭 보강 시나리오치(88.4%)는 가상 별칭 세트 기준 추정치였고,")
    a("  실제 웹 검증 기반 v1.1 사전 적용 결과는 **82.6%** (잔여 미매핑 684 고유 / 767 셀)")
    a("")

    # 2. 회차별
    a("## 2. 회차별 매칭 통계 (v1.1 기준)")
    a("")
    a("| 회차 | 셀 수 | 매칭 셀 | 매칭률 | 미매핑 셀 |")
    a("|---|---|---|---|---|")
    for fname, fs in stats11["files"].items():
        a(f"| {fname.replace('_부스정보.csv','')} | {fs['cells']:,} | {fs['matched_cells']:,} "
          f"| {round(fs['matched_cells']/fs['cells']*100,1)}% "
          f"| {fs['methods'].get('unmatched', 0):,} |")
    a("")
    a("> 미매핑 셀 열은 코드 미부여 파트가 포함된 셀 수. 회차별 상세 method 분포는")
    a("> `analysis/matching_stats_v1.1.json` 참조")
    a("")

    # 3. 변경 요약
    a("## 3. 사전 v1.1 변경 요약")
    a("")
    a(f"- **신규 작품 {changes['new_works']}종**: `W0212` ~ `{changes['new_code_range'].split('~')[1]}` 순차 부여 (기존 코드 미변경·미재매핑)")
    a(f"- **별칭 추가**: 기존 {changes['alias_added_works']}개 작품에 {changes['aliases_added']}개 별칭 병합 (기존 aliases/abbreviations 유지)")
    a(f"- **정정 {len(changes['fixed'])}건**: W0117 살파랑 origin(kr→cn, priest의 杀破狼), W0027·W0208·W0177 교차 중복/오귀속 별칭 제거")
    a(f"- **noise_terms 신설**: 작품 외 표기(공예·굿즈·장르명 등) {changes['noise_terms']}종을 `metadata.noise_terms`로 데이터화 — `normalize_works.py`가 참조")
    a(f"- 메타데이터: `version=1.1`, `last_updated=2026-09-21`, `total_works=369`, `reverse_index` 재생성 ({len(d['reverse_index'])}키, 교차 충돌 0건 검증)")
    a("")

    # 4. 웹 검증
    a("## 4. 웹 검증 (2026-09-21, 나무위키·공식 사이트·플랫폼 페이지 기준)")
    a("")
    a("신규 등록 중 웹 검증으로 정체를 확정한 주요 항목:")
    a("")
    a("| 표기 | 확정 원작 | origin/category |")
    a("|---|---|---|")
    verified = [
        ("문송안함", "문과라도 안 죄송한 이세계로 감 (기존 W0070 별칭)", "kr / webnovel"),
        ("백망되", "백작가의 망나니가 되었다 (기존 W0071 별칭)", "kr / webnovel"),
        ("망아살", "망나니 PD 아이돌로 살아남기 (기존 W0172 별칭)", "kr / webnovel"),
        ("섭남파업", "서브 남주가 파업하면 생기는 일 (기존 W0065 별칭)", "kr / webnovel"),
        ("도리벤", "도쿄 리벤저스 (기존 W0079 별칭)", "jp / manga"),
        ("가히리", "가정교사 히트맨 REBORN! (기존 W0050 별칭)", "jp / manga"),
        ("썬더일레븐", "이나즈마 일레븐 (기존 W0073 별칭)", "jp / game"),
        ("살파랑", "priest(핀푸)의 杀破狼 — W0117 origin 정정", "cn / webnovel"),
        ("공조살", "공포소설 속 조연은 사람으로 살고 싶다", "kr / webnovel"),
        ("공회주", "공작님, 회개해주세요!", "kr / webnovel"),
        ("탈(TAL)", "탈(TAL) — 강임 작", "kr / webtoon"),
        ("김아싫", "김 대리는 아이돌이 싫어", "kr / webnovel"),
        ("산나비", "산나비 — 한국 인디 플랫포머 게임 (만화 아님)", "kr / game"),
        ("봄이 오면 꽃이 피고", "오토메 연애 어드벤처 게임 (소설 아님)", "kr / game"),
        ("충사", "蟲師(우루시바라 유키)의 한국 정발명 (웹툰 아님)", "jp / manga"),
        ("취록의 플로리아", "翠緑のフローリア — 일본 TRPG", "jp / trpg"),
        ("인세인", "일본 현대 호러 TRPG 한국어판", "jp / trpg"),
        ("블러드패스·언성 듀엣·둘이서 수사", "일본 TRPG 각각 확정", "jp / trpg"),
        ("위치즈하트·안개비가내리는숲·무색의카이나", "일본 쯔꾸르 프리게임 각각 확정", "jp / game"),
        ("천막의 자두가르", "天幕のジャードゥーガル", "jp / manga"),
        ("다이아몬드의 공죄", "ダイヤモンドの咎 (다이아몬드 에이스와 별개)", "jp / manga"),
        ("명조", "명조: 워더링 웨이브 (쿠로게임즈)", "cn / game"),
        ("천지해", "레진코믹스 웹툰 (핑푸)", "kr / webtoon"),
        ("쇼바이락", "SHOW BY ROCK!! (산리오)", "jp / franchise"),
        ("아이엠스타", "아이카츠! 한국 더빙 제목 → W0177(캐릭캐릭체인지) 오귀속 정정", "jp / anime"),
    ]
    for k, v, oc in verified:
        a(f"| {k} | {v} | {oc} |")
    a("")

    # 5. 신규 코드 목록
    a("## 5. 신규 작품 코드 목록 (158종, W0212~W0369)")
    a("")
    a("| 코드 | 정식명 | origin | category |")
    a("|---|---|---|---|")
    for code in sorted(changes["new_codes"]):
        w = d["works"][code]
        review = " (review_needed)" if w.get("review_needed") else ""
        a(f"| {code} | {w['canonical_name']}{review} | {w['origin']} | {w['category']} |")
    a("")

    # 6. 별칭 추가
    a("## 6. 기존 작품 별칭 추가 내역 (55개 작품 / 98개)")
    a("")
    a("| 코드 | 작품 | 추가 별칭 |")
    a("|---|---|---|")
    # changeset에 별칭 상세는 없으므로 사전 notes 기반 재구성: build_v1_1.py의 ALIAS_ADDITIONS 기준표 사용
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_v1_1", os.path.join(BASE_DIR, "scripts", "build_v1_1.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for code in sorted(mod.ALIAS_ADDITIONS):
        w = d["works"][code]
        added = [x for x in mod.ALIAS_ADDITIONS[code]
                 if x in w.get("aliases", []) or x in w.get("abbreviations", [])]
        a(f"| {code} | {w['canonical_name']} | {', '.join(added)} |")
    a("")

    # 7. 잔여 미매핑
    a("## 7. 잔여 미매핑 목록")
    a("")
    a(f"- 잔여: **{len(unmatched)} 고유 값 / {sum(c for _, c in unmatched)} 셀** (전체 셀의 {round(sum(c for _, c in unmatched)/t11['cells']*100,1)}%)")
    a("- 전체 목록: `analysis/unmatched_v1.1.csv` (빈도순) · 실패 토큰 단위: `analysis/unmatched_parts_v1.1.csv`")
    a("- 성격: 공백/마침표 구분 병기 셀(토크나이저가 콤마만 분리), 판단 불가 표기, 결측·굿즈 묶음 등")
    a("")
    a("빈도 상위 60개:")
    a("")
    a("| 표기(원본 셀) | 빈도 |")
    a("|---|---|")
    for val, cnt in unmatched[:60]:
        a(f"| {val.replace('|','\\|')} | {cnt} |")
    a("")

    # 8. 판단 불가
    a("## 8. 판단 불가·review_needed 항목")
    a("")
    a("사전 내 `review_needed: true`:")
    a("")
    for code in sorted(d["works"]):
        w = d["works"][code]
        if w.get("review_needed"):
            a(f"- `{code}` {w['canonical_name']} — {w.get('notes','')}")
    a("")
    a("미등록(판단 불가) 잔여 주요 표기:")
    a("")
    for k, v in UNRESOLVED_NOTES:
        a(f"- **{k}**: {v}")
    a("")

    # 9. 사용 작품 top
    a("## 9. 부스 빈도 상위 작품 (v1.1 기준 Top 30)")
    a("")
    a("| 코드 | 작품 | 부스 수 |")
    a("|---|---|---|")
    for code, name, cnt in matched[:30]:
        a(f"| {code} | {name} | {cnt} |")
    a("")

    # 10. 재현 방법
    a("## 10. 재현 방법")
    a("")
    a("```bash")
    a("# v1.0 기준 분석 (산출물 analysis/ 저장)")
    a("python3 scripts/analyze_works.py --tag 1.0")
    a("python3 scripts/extract_unmatched_parts.py --tag 1.0")
    a("")
    a("# v1.1 사전 빌드 (analysis/WORK_DICTIONARY_v1.0_backup.json 에서 복원 후 실행 가능)")
    a("python3 scripts/build_v1_1.py [--dry-run]")
    a("")
    a("# v1.1 재측정")
    a("python3 scripts/analyze_works.py --tag v1.1")
    a("python3 scripts/extract_unmatched_parts.py --tag v1.1")
    a("")
    a("# 전체 회차 normalized CSV 재생성이 필요하면:")
    a("python3 normalize_works.py --all")
    a("```")
    a("")
    a("> 기존 `26년_7월_부스정보_normalized.csv`는 v1.0 기준 산출물이므로, 필요 시 위 명령으로 v1.1 기준 재생성")
    a("")

    # 11. 한계
    a("## 11. 한계·후속 과제")
    a("")
    a("- 콤마 외 구분자(공백, 마침표, `/`) 병기는 분리하지 않아 복합 셀 일부가 잔여 미매핑으로 남음")
    a("  (예: " + ", ".join(f"'{x}'" for x in SPACE_JOINED_EXAMPLES) + ")")
    a("- 26년_7월_부스정보_normalized.csv 외 회차의 normalized CSV는 미생성 상태 (후속 전처리 단계에서 일괄 생성 권장)")
    a("- 캐릭터명 표기(예: 게토고죠→주술회전)는 소속 작품 매핑으로 처리 — 캐릭터 사전 분리는 후속 검토 가능")
    a("- 미매핑 잔여 684 고유 값 중 상당수는 굿즈 묶음·결측·장르명으로, 작품 사전과 무관")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"보고서 생성: {OUT_PATH} ({len(L)} lines)")


if __name__ == "__main__":
    main()

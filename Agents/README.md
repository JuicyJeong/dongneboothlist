# 프로젝트 안내 (외부 에이전트용 시작 문서)

> 이 폴더는 다른 플랫폼·다른 에이전트가 이 저장소의 소스코드, 구조, 산출물을 참조할 때
> 최소한의 문서만 읽고 프로젝트를 이해할 수 있도록 만든 요약 문서 모음입니다.
>
> 작성 기준 시점: **2026-10-18 (KST)** · GitHub `master` 최신 상태(JWMI-15/16 폴더 재구조화 반영) 기준.
> 구버전 클론이나 로컬 사본에서는 폴더 구조·수치가 다를 수 있습니다(아래 "주의사항" 7번 참고).
> 원본 문서는 `docs/` 폴더에 있습니다.

## 프로젝트가 하는 일 (한 줄 요약)

동인네트워크(dongne.co) 오프라인 행사(디. 페스타 등)의 **참가 부스 정보를 홈페이지 v2 API에서 크롤링해
월별 CSV 표로 정리**하고, 부가 기능으로 **트위터 계정 정제·팔로워 수 수집**,
그리고 **참가 원작 작품명의 정규화 + 고유 코드 부여(작품 딕셔너리·DB화)** 를 수행합니다.

## 배경

- 동인네트워크는 만화/애니/게임 등 2차 창작의 오프라인 행사이며, 매 행사마다 홈페이지에 참가 부스 정보를 업로드함.
- 홈페이지는 모든 부스 정보를 한 번에 보기 어려운 형태 → 크롤링해서 하나의 표로 정리하고 사용자 편의성을 제공하는 것이 목적.
- 현재 프로젝트 단계는 **"작품 딕셔너리화"**: 부스 데이터의 `대표 작품(원작)` 컬럼의 자유 텍스트를
  정식 한국명 기준으로 통일하고 각 작품에 고유 코드(W0001~)를 부여해, 정규화 CSV·SQLite(`works.db`)로
  데이터베이스 관리가 가능한 형태까지 완료한 상태.

## 핵심 팩트 (빠른 참조)

| 항목 | 값 |
|---|---|
| 대상 데이터 | 24년 1월 ~ 26년 10월, **12개월 / 총 16,187개 부스** |
| 데이터 소스 | dongne.co **v2 API** (`/api/v2/events/{slug}/circles`) |
| 최종 산출물 | `data/processed/normalized/{YY년_M월}_부스정보_normalized.csv` **12개** (UTF-8, 한글 컬럼명, 원작 옆 `_코드`·`_정규화` 컬럼) |
| RAW 최종 산출물 | `{YY년_M월}_부스정보.csv` (19컬럼, 루트·`data/processed/` 병존 / 26년 7월·10월은 +팔로워수·미확보수 21컬럼) |
| 작품 딕셔너리 | `WORK_DICTIONARY.json` (루트, **v1.2**) — 446종(W0001~W0459), `review_needed` 31종 |
| 정규화 매칭률 | 셀 단위 **86.38%** (13,982/16,187 · 빈 셀 제외 97.02% · 2026-10-18 실측) |
| 작품 DB | `works.db` (SQLite) — works 446종 / booth_work 15,650행 / booth_work_raw 16,187행 |
| 재생성 | `python3 pipeline.py --all` (같은 사전 버전이면 md5까지 동일한 결정적 재생성) |
| 문서 원본 | `docs/` 폴더 — Structure.md, HISTORY.md, Work_History.md, pipeline_usage.md, work_dictionary_v1.2_report.md 등 |

## 저장소 지도 (어디에 무엇이 있는가)

```
dongneboothlist/
├── Agents/                             # 이 폴더 — 외부 에이전트용 요약 문서 3종
│   ├── README.md                       # 본 파일 (개요 + 네비게이션)
│   ├── HISTORY.md                      # 지금까지의 진행 기록 (타임라인)
│   └── FEATURES.md                     # 기능·스크립트·데이터 스키마 상세
│
├── src/                                # 실행 소스 코드
│   ├── crawl/booth_search_total.py     # [핵심] v2 API 부스 크롤러
│   ├── pipeline/                       # batch_crawl.py(월별 배치) · preprocess_twitter.py(트위터 정제)
│   ├── normalization/                  # build_work_dictionary.py(사전 빌드) · normalize_works.py(정규화)
│   ├── social/                         # fetch_followers.py · verify_twitter.py · account_info/(파생 프로젝트)
│   └── analytics/                      # vis.py(빈도 시각화) · generate_booth_map.py(부스 배치도)
├── data/
│   ├── raw/                            # {YY년_M월}.csv 수집 원본 (원본 보존 — 수정 금지)
│   ├── processed/                      # {YY년_M월}_clean.csv · _부스정보.csv
│   │   └── normalized/                 # [최종 산출물] {YY년_M월}_부스정보_normalized.csv 12개 (단일 폴더에서만 관리)
│   ├── reference/                      # EVENT_INFORMATION.JSON · 부스명 유사도 사전.csv 등
│   └── cache/                          # twitter_followers_cache.json (팔로워 크롤링 캐시)
├── artifacts/                          # 재생성 가능한 산출물
│   ├── maps/ · visualizations/         # 부스 배치도·시각화 이미지
│   ├── social/                         # 팔로워 로그·top20·유효성 샘플 · account_info/
│   └── legacy/results/                 # 과거(구 API) 시절 결과물 보관
├── scripts/                            # build_db.py · analyze_works.py · llm_batch_map.py 등 도구
├── analysis/                           # 매칭 통계·미매핑 검토 목록 (unmapped_review_{월}.csv 등)
├── docs/                               # 원본 문서 + 변경 이력 (Work_History.md, Structure.md …)
├── pipeline.py                         # [핵심] 정규화 → 미매핑 리포트 → works.db 반영 단일 진입점
├── WORK_DICTIONARY.json                # 작품 마스터 딕셔너리 — 정본은 루트 파일 (v1.2, 446종)
├── works.db                            # SQLite (works / booth_work / booth_work_raw / meta)
└── 루트의 {YY년_M월}*.csv 등           # data/ 내 파일과 병존되는 RAW·clean·부스정보 사본 + 스크립트 사본
```

> 루트에 `normalize_works.py` 등 스크립트 사본과 RAW CSV 사본이 남아 있지만, **정규화 산출물(normalized)은
> `data/processed/normalized/` 단일 폴더에서만** 관리합니다. `data/reference/WORK_DICTIONARY.json`은
> 구버전(v1.0)이므로 사전 정본은 루트 `WORK_DICTIONARY.json`(v1.2)을 사용하세요.

## Agents 폴더 문서 안내

| 문서 | 내용 | 언제 읽나 |
|---|---|---|
| `Agents/README.md` | 프로젝트 개요, 저장소 지도 | 항상 먼저 |
| `Agents/HISTORY.md` | 2024년 초기 버전부터 지금까지의 작업 타임라인과 현재 상태 | "지금까지 뭘 했는지"가 필요할 때 |
| `Agents/FEATURES.md` | 각 기능의 실행 방법, 입출력, CSV/JSON/DB 데이터 스키마 | 코드를 실행·수정·확장할 때 |

더 깊은 내용이 필요하면 원본 문서를 참고하세요:
- 구조·구현 상세: `docs/Structure.md`
- 파이프라인·DB 사용법: `docs/pipeline_usage.md`, `docs/preprocessing_pipeline_design.md`
- 전체 작업 내역: `docs/HISTORY.md` · 변경 단위 이력: `docs/Work_History.md`
- 정규화 분석·사전 리포트: `docs/work_normalization_report.md`, `docs/work_dictionary_v1.1_report.md`, `docs/work_dictionary_v1.2_report.md`, `docs/원작명_정규화.md`
- 계정 수집 파생 프로젝트: `docs/account_info.md`

## 외부 에이전트 주의사항

1. **모든 CSV/JSON은 UTF-8**이며, 컬럼명·값이 한글입니다 (`대표 작품(원작)`, `트위터`, `행사명` 등).
2. **원본 보존 원칙**: `data/raw/`는 수정 금지. 기존 컬럼을 덮어쓰지 말고 새 컬럼을 추가하는 방식이 관례입니다.
   normalized 산출물은 `data/processed/normalized/` 단일 폴더에서만 관리하고, 재생성은 `python3 pipeline.py --all`로 수행합니다
   (루트 등 다른 위치에 normalized 파일을 새로 만들지 않습니다).
3. **코드 불변 원칙**: 기존 `W####` 코드를 다른 작품에 재사용·재매핑 금지. 신규 작품은 사전 최대 번호 +1부터 자동 순차 부여됩니다.
   정체가 불확실한 값은 추측으로 채우지 말고 `판단 불가`(uncertain)로 남깁니다 (루프 절차: `docs/pipeline_usage.md` §4).
4. `WORK_DICTIONARY.json`의 `review_needed: true` 31종과 사전 `metadata.llm_decisions`의 확정 결정(noise 72·uncertain 130)은
   사람이 확정한 값입니다. 확정 전에는 임의 변경 금지.
5. 위치(`seatLabels`) 데이터는 **26년 4월·7월·10월** 3개 회차만 존재합니다 (과거 행사는 API가 미제공).
   팔로워수·미확보수 컬럼은 **26년 7월·10월**에만 있습니다.
6. Selenium 기반 스크립트(`src/social/` 하위)는 Chrome 등 브라우저·드라이버가 필요합니다.
7. 이 저장소의 작업 관례(한글 문서, `docs/` 저장, `docs/Work_History.md` 변경 이력 기록)는 루트 `AGENTS.md`를 따릅니다.
   오래된 클론·로컬 사본은 2026-10-18 이전 구조(평면 구조, 11개월 데이터, v1.0 사전 211종)일 수 있으니
   `git pull` 후 최신 master 기준으로 작업하세요.

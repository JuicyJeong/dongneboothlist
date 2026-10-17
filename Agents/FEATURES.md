# 기능 정리 (스크립트 · 데이터 스키마 · 실행 방법)

> 외부 에이전트용 요약입니다. 코드 상세 분석은 `docs/Structure.md`, 파이프라인 사용법은 `docs/pipeline_usage.md`를 참고하세요.
> 실행 경로는 GitHub `master`(2026-10-18, JWMI-15/16 재구조화 후) 기준입니다.

## 전체 파이프라인

```
EVENT_INFORMATION.JSON (data/reference/ — 행사 설정)
        │
        ▼
[1] src/crawl/booth_search_total.py ──dongne.co v2 API──▶ {YY년_M월}.csv (raw → data/raw/)
        │
        ▼
[2] src/pipeline/preprocess_twitter.py ──────────────────▶ {YY년_M월}_clean.csv (data/processed/)
        │
        ▼
[3] 복제(정산본) ────────────────────────────────────────▶ {YY년_M월}_부스정보.csv (루트·data/processed/ 병존)
        │
        ▼
[4] pipeline.py  (단일 진입점: 정규화 → 미매핑 리포트 → DB 반영)
    ├─ normalize_works.py ──▶ data/processed/normalized/{YY년_M월}_부스정보_normalized.csv  [최종 산출물]
    ├─ 미매핑 리포트 ───────▶ analysis/unmapped_review_{YY년_M월}.csv (사람 확인용)
    └─ scripts/build_db.py ─▶ works.db (SQLite: works / booth_work / booth_work_raw)
```

- 일괄 실행: `src/pipeline/batch_crawl.py`가 [1]→[2]→[3]을 `MONTHS` 리스트(12개월) 순회.
- 사전 갱신 루프: `scripts/llm_batch_map.py`로 미매핑을 내보내 결정을 반영한 뒤 `pipeline.py --all`로 전체 재생성 (§F9).
- 부가 기능: `src/social/fetch_followers.py`(팔로워수) · `verify_twitter.py`(계정 검증) · `src/analytics/vis.py`·`generate_booth_map.py`(시각화·배치도).

## 기능 목록

### F1. 부스 크롤링 — `src/crawl/booth_search_total.py` (핵심)

- dongne.co **v2 API**에서 행사별 부스 데이터를 페이지네이션(limit=100)으로 수집해 월별 CSV 생성.
- 실행: `python3 src/crawl/booth_search_total.py --date 26년_7월` (기본값은 스크립트 내 상수)
- 흐름: `data/reference/EVENT_INFORMATION.JSON`에서 `--date` 월의 행사 목록 → 각 행사 slug로 `GET /api/v2/events/{slug}/circles` 호출 → `fields[]`를 systemKey 기준으로 컬럼 매핑 → `seatLabels[]`에서 위치/열/번호/반부스 파싱 → 저장.
- API 엔드포인트:
  - 부스 목록: `GET https://dongne.co/api/v2/events/{slug}/circles?page={page}&limit=100`
  - 쁘띠존: `GET https://dongne.co/api/v2/events/{slug}/petit-zones`
  - 행사 메타: `GET https://dongne.co/api/v2/events/{slug}` (schedules에서 개최일)
  - 행사 목록: `GET https://dongne.co/api/v2/events?status=past&page={page}&limit=100`
- systemKey → 컬럼 매핑: `mainWork`→대표 작품(원작), `otherWorks`→그 외 다루는 작품, `character`→캐릭터, `coupleDouble`→커플링(joinChar="X"), `coupleInclination`→커플링 성향, `coupleOther`→그 외 커플링, `medium`→매체, `twitter`→트위터, `petit_zone`→쁘띠존.

### F2. 트위터 컬럼 정제 — `src/pipeline/preprocess_twitter.py`

- 실행: `python3 src/pipeline/preprocess_twitter.py --input data/raw/26년_7월.csv --output data/processed/26년_7월_clean.csv`
- 처리: `@` 접두사 제거 → 순수 핸들 / URL(x.com/...)→핸들 추출 / `,`·`/`·공백으로 다중 계정 분리 보존 / 제어문자·한글 노이즈 제거 / `.bsky.social` → `bsky:핸들` 명시.
- 목적: `src/social/account_info/selenium_run.py`의 URL 생성 호환 확보 + 데이터 품질.

### F3. 팔로워 수 수집 — `src/social/fetch_followers.py`

- 비로그인 **Selenium**으로 계정별 팔로워 수를 크롤링해 행별로 합산.
- 실행: `python3 src/social/fetch_followers.py --input data/processed/26년_10월_clean.csv --output data/processed/26년_10월_clean.csv` (전체) / `--limit 50` (샘플). 그 외 `--delay-min/--delay-max/--rest-every/--merge-only` 등 지원.
- 특징: 고유 계정 캐싱(`data/cache/twitter_followers_cache.json`, 키 소문자 정규화)으로 재개·중복 제거, 다중 계정 sum, 미확보(restricted/not_found/bsky)는 `미확보수` 컬럼에 표시, 연속 실패 감지 시 자동 중단.
- 실적:
  - 26년 7월: 고유 계정 1,183개 중 1,150개(97.2%) 확보, 팔로워 합계 3,812,119 (약 92분).
  - 26년 10월: 신규 929계정 중 908 성공(97.7%) + 7월 캐시 161계정 재사용, 트위터 보유 994행 중 완전확보 972행 (약 4시간 40분).

### F4. 계정 유효성 검증 — `src/social/verify_twitter.py`

- 비로그인 Selenium으로 계정 존재 여부를 5가지 상태로 분류: `valid` / `protected` / `restricted` / `suspended` / `not_found`.

### F5. 배치 크롤링 — `src/pipeline/batch_crawl.py`

- 스크립트 내 `MONTHS` 리스트(24년_1월 ~ 26년_10월 12개월)의 각 월에 대해 F1(`--date`) → F2 → `_부스정보.csv` 복제를 순회 실행.

### F6. 시각화·배치도 — `src/analytics/vis.py` · `src/analytics/generate_booth_map.py`

- `vis.py`: `대표 작품(원작)` 빈도를 집계·차트화 (구 시절 스크립트, 내부에 소규모 원작명 매핑 사전 포함). 예전 산출물은 `artifacts/legacy/results/`에 보관.
- `generate_booth_map.py`: 행사 부스 배치도 PNG 생성 → `artifacts/maps/` (예: `booth_map_df2607_일.png`).

### F7. 작품 마스터 딕셔너리 — `src/normalization/build_work_dictionary.py` + `WORK_DICTIONARY.json`

- `build_work_dictionary.py`에 작품 마스터 데이터를 코드로 정의하고 실행하면 `WORK_DICTIONARY.json`을 빌드. **작품 추가/수정은 이 파일의 WORKS 리스트를 편집 후 재빌드**하는 방식 (LLM 배치 결정 반영은 `scripts/llm_batch_map.py --apply` 사용, §F9).
- 네이밍 원칙: 한국 정발명 우선(없으면 한국에서 많이 쓰는 풀네임), 약칭은 `abbreviations`에만, 띄어쓰기/특수문자 변형은 `aliases`에 등록.
- JSON 구조:

```json
{
  "metadata": { "version", "naming_rule", "total_works", "origin_legend", "category_legend", "llm_decisions" },
  "works": {
    "W0001": {
      "code": "W0001",
      "canonical_name": "슬램덩크",
      "origin": "kr|jp|cn|en|multi|meta",
      "category": "manga|anime|game|webtoon|webnovel|novel|movie|drama|vtuber|trpg|...",
      "aliases": ["띄어쓰기/특수문자 변형"],
      "abbreviations": ["약칭/줄임말"],
      "review_needed": false,
      "notes": "비고"
    }
  },
  "reverse_index": { "모든 표기(소문자)": "코드" }
}
```

- 현재 규모(**v1.2**, 정본은 루트 `WORK_DICTIONARY.json`): 446종(W0001~W0459), `review_needed: true` 31종, `metadata.llm_decisions`에 noise 72·uncertain 130 결정 영속화.
- 주의: `data/reference/WORK_DICTIONARY.json`은 구버전(v1.0, 211종)이므로 사용하지 말 것.

### F8. 작품명 정규화 — `pipeline.py` + `src/normalization/normalize_works.py`

- 실행(권장): `python3 pipeline.py --input <부스정보.csv>` / 전체 재생성 `python3 pipeline.py --all` / 저장 위치 변경 `--outdir <폴더>` / DB 생략 `--skip-db`.
- 엔진 단독 실행: `python3 src/normalization/normalize_works.py --all` / `--input <csv>` / `--dry-run` / `--columns ...` / `--fuzzy-threshold 0.85`
- **4단계 매칭**:
  1. `exact` — reverse_index 직접 조회
  2. `normalized` — 공백/특수문자 제거 후 매칭
  3. 괄호 병기 — `정식명(약칭)` → 괄호 앞 텍스트 / 괄호 안 약칭 각각 매칭
  4. `fuzzy` — Levenshtein 거리(임계값 0.85)
- 다중 작품(콤마 구분)은 전체 매칭 실패 시 분리 후 각각 적용.
- 출력 방식: 기존 컬럼을 덮어쓰지 않고 `대표 작품(원작)_코드`(W코드, `;` 구분)·`대표 작품(원작)_정규화`(정식명, `;` 구분) 컬럼을 **원문 칼럼 바로 옆**에 추가 (JWMI-7부터 전 회차 공통 배치).
- 성능(12회차 전체 16,187셀, 2026-10-18 실측): matched 13,982 (**86.38%**), unmatched 214셀/103종(1.32%), uncertain 139(0.86%), noise 77(0.48%), empty 1,775(10.97%). 빈 셀 제외 유효 매칭률 **97.02%**, 등장 작품 444종.

### F9. 정규화 → DB 파이프라인·사전 갱신 루프 — `pipeline.py` · `scripts/` · `works.db`

- `pipeline.py`: 정규화 → 미매핑 리포트(`analysis/unmapped_review_{월}.csv`) → `works.db` 반영을 한 번에 수행. 회차 단위 DELETE→적재라 재실행 멱등.
- `works.db` 스키마:
  - `works` — 작품 마스터 (사전 기반, 446종)
  - `booth_work` — 부스 링크 ↔ 작품 코드 매핑 (15,650행)
  - `booth_work_raw` — 원문 보존 + 상태 분류 (16,187행, matched/unmatched/uncertain/noise/empty)
  - `meta` — dict_version, built_at
- 사전 갱신 루프 (미매핑 개선 절차, 상세: `docs/pipeline_usage.md` §4):
  ```bash
  python3 scripts/llm_batch_map.py --export --tag v1.3          # 미매핑 고유 값 내보내기
  #   → analysis/llm_batch_input_v1.3.csv 에 decision 기입 (alias/new/noise/uncertain)
  python3 scripts/llm_batch_map.py --apply --mapping analysis/llm_mapping_v1.3.csv --new-version 1.3
  python3 pipeline.py --all                                     # 전체 재생성 (결정적 — md5 동일)
  python3 scripts/analyze_works.py --tag v1.3                   # 커버리지 측정
  ```
- 원칙: 기존 `W####` 코드 재사용·재매핑 금지, 신규 코드는 최대 번호 +1부터 자동 순차 부여, 불확실 값은 추측 금지(`판단 불가` 표기).

## 데이터 스키마

### `{YY년_M월}_부스정보.csv` (RAW 정산본, UTF-8, 한글 컬럼명)

19컬럼 (기본) — 26년 7월·10월은 `팔로워수`·`미확보수`가 추가되어 21컬럼:

```
부스명, 대표자, 위치, 위치(열), 위치(번호), 반부스, 부스(=sp 수), 대표 작품(원작),
그 외 다루는 작품, 쁘띠존, 캐릭터, 커플링, 커플링 성향, 그 외 커플링, 매체, 트위터,
[팔로워수], [미확보수], 링크(=dongne.co 부스 상세 URL), 행사명, 개최일(Day1/Day2/...)
```

### `{YY년_M월}_부스정보_normalized.csv` (최종 산출물, `data/processed/normalized/`)

RAW 부스정보 + 정규화 2컬럼 (원문 칼럼 바로 옆 배치) = 기본 21컬럼, 26년 7월·10월은 23컬럼:

```
..., 부스, 대표 작품(원작), 대표 작품(원작)_코드, 대표 작품(원작)_정규화, 그 외 다루는 작품, ...,
트위터, [팔로워수], [미확보수], 링크, 행사명, 개최일
```

- `대표 작품(원작)_코드`: `W####` (`;` 로 복수 구분) · `_정규화`: 정식 한국명 (`;` 구분) · 판단 불가 값은 `판단 불가` 표기.
- `링크` 형식: `https://dongne.co/events/{slug}/circles/{applicationId}`
- 컬럼 순서는 월별 파일마다 다를 수 있음. **컬럼명 기준으로 접근 권장.**

### 데이터 보유 현황 (12개월 / 16,187 부스)

| 월 | 부스 수 | 트위터 | 위치 | 팔로워수 |
|---|---:|---:|---:|---:|
| 24년_1월 | 1,254 | 1,016 | — | — |
| 24년_4월 | 1,250 | 951 | — | — |
| 24년_7월 | 1,246 | 996 | — | — |
| 24년_9월 | 1,118 | 800 | — | — |
| 25년_1월 | 1,394 | 1,068 | — | — |
| 25년_4월 | 1,360 | 991 | — | — |
| 25년_7월 | 1,409 | 1,027 | — | — |
| 25년_10월 | 1,301 | 949 | — | — |
| 26년_1월 | 1,411 | 1,056 | — | — |
| 26년_4월 | 1,483 | 1,135 | O | — |
| 26년_7월 | 1,539 | 1,108 | O | O |
| 26년_10월 | 1,422 | 997 | O | O |
| **합계** | **16,187** | | | |

- 위치(`seatLabels`)는 26년 4월·7월·10월만 보유 — 과거 행사는 API가 빈 배열 반환(사이트 측 미제공).
- 팔로워수·미확보수는 26년 7월·10월만 보유.

### 기타 데이터 파일

| 파일 | 설명 |
|---|---|
| `data/reference/EVENT_INFORMATION.JSON` | 월별 행사 설정: key=`{YY년_M월}`, 값=행사 목록(slug/이름/개최일) |
| `WORK_DICTIONARY.json` (루트) | 작품 마스터 딕셔너리 v1.2 (446종) — **정본** |
| `works.db` (루트) | 작품·부스 매핑 SQLite (§F9) |
| `data/cache/twitter_followers_cache.json` | 계정별 팔로워 수 캐시 (키 소문자 정규화) |
| `data/reference/부스명 유사도 사전.csv` | 부스명 유사도 매핑 사전 (원작명 정규화와는 무관한 별개 자산) |
| `artifacts/social/` | `top20_팔로워수.csv` · `twitter_validity_sample.csv` · `fetch_followers.log` |
| `analysis/` | `matching_stats_v1.2.json` · `unmatched_v1.2.csv` · `unmapped_review_{월}.csv` · LLM 배치 입출력 |
| `data/reference/WORK_DICTIONARY.json` | 구버전 사전(v1.0, 211종) — 사용 금지, 참고용 |

## 실행 요구 사항

- Python 3 (표준 라이브러리 + pandas/matplotlib 정도, 요구사항 파일은 별도 없음)
- Selenium 기반 스크립트(F3, F4, `src/social/account_info/selenium_run.py`)는 Chrome 등 브라우저·드라이버 필요
- 네트워크 접근: dongne.co v2 API / x.com(트위터)

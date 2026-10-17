# Structure

## 프로젝트 개요

동인네트워크(dongne.co) 행사 부스 정보를 크롤링·정제하여 CSV로 정리하는 프로젝트.
동인네트워크 v2 API를 통한 부스 데이터 수집, 트위터 계정 정제, 팔로워 수 집계, 유효성 검증 기능 수행.

## 폴더 구조

```
dongneboothlist/
├── AGENTS.md                      # 에이전트 작업 규칙
├── Agents/                        # 외부 에이전트용 요약 문서 (README·HISTORY·FEATURES, JWMI-17)
├── README.md                      # 프로젝트 시작 안내
├── .gitignore                     # 로컬 캐시·런타임 파일 제외 규칙
├── src/                           # 실행 소스 코드
│   ├── crawl/                     # v2 API 부스 수집기
│   ├── pipeline/                  # 배치 수집·트위터 전처리
│   ├── normalization/             # 작품 사전 생성·정규화
│   ├── social/                    # X 계정 수집·검증, 파생 노트북
│   └── analytics/                 # 배치도·빈도 시각화
├── data/                          # 입력·중간·참조 데이터
│   ├── raw/                       # {YY년_M월}.csv 수집 원본
│   ├── processed/                 # clean/부스정보 중간 산출물
│   │   └── normalized/            # 최종 정규화 산출물 단일 폴더 ({YY년_M월}_부스정보_normalized.csv 12개, JWMI-15/16)
│   ├── reference/                 # 행사 설정·작품/부스 매핑 사전
│   └── cache/                     # 재실행용 팔로워 캐시
├── artifacts/                     # 재생성 가능한 산출물
│   ├── maps/                      # 행사 부스 배치도 PNG
│   ├── visualizations/            # 분석 시각화 이미지
│   ├── social/                    # 계정 검증·팔로워 결과 및 로그
│   └── legacy/results/            # 이전 API 기반 결과 보관
└── docs/                          # 구조·변경 이력·분석·파생 프로젝트 문서
```

## 스크립트별 역할 및 프로세스 흐름

### 1. booth_search_total.py (핵심 크롤러)

v2 API에서 부스 데이터를 수집하여 월별 CSV 생성.

**흐름**:
1. `EVENT_INFORMATION.json`에서 `--date`로 지정된 월의 행사 목록 읽기
2. 각 행사 CODE(slug)로 `dongne.co/api/v2/events/{slug}/circles` 호출 (limit=100, 페이지네이션)
3. 응답의 `fields[]`를 systemKey 기반으로 컬럼 매핑
4. `seatLabels[]`에서 위치/열/번호/반부스 파싱
5. `{date}.csv` 저장

**실행**: `python3 src/crawl/booth_search_total.py --date 26년_7월`

### 2. preprocess_twitter.py (트위터 정제)

트위터 컬럼 정규화. `--input`/`--output` 인자로 월별 재사용.

**처리**:
- `@` 접두사 제거 → 순수 핸들 (selenium_run.py URL 호환)
- URL(`x.com/...`) → 핸들 추출
- 구분자(`,` `/` 공백) → 다중 계정 분리 보존
- 제어문자/한글 노이즈 제거
- `.bsky.social` → `bsky:핸들` 명시

**실행**: `python3 src/pipeline/preprocess_twitter.py --input data/raw/26년_7월.csv --output data/processed/26년_7월_clean.csv`

### 3. fetch_followers.py (팔로워 수 수집)

비로그인 Selenium으로 팔로워 수 크롤링 + 행별 합산.

**특징**:
- 고유 계정 캐싱(`twitter_followers_cache.json`)으로 중복 제거/재개
- 다중 계정 팔로워 수 합산 → `팔로워수`
- 미확보 계정(restricted/not_found/bsky) → `미확보수`
- 20개마다 자동 저장, `--limit` 테스트 옵션

**실행**: `python3 fetch_followers.py` (전체) / `--limit 50` (샘플)

### 4. verify_twitter.py (유효성 검증)

비로그인 Selenium으로 계정 존재 여부 분류.
상태: `valid` / `protected` / `restricted` / `suspended` / `not_found`

### 5. batch_crawl.py (배치)

`MONTHS` 리스트의 월별로 booth_search_total.py + preprocess_twitter.py 순회 실행 + `_부스정보.csv` 복사.

## v2 API 구조 (핵심)

### 엔드포인트
- 부스 목록: `GET https://dongne.co/api/v2/events/{slug}/circles?page={page}&limit=100`
- 쁘띠존: `GET https://dongne.co/api/v2/events/{slug}/petit-zones`
- 행사 메타: `GET https://dongne.co/api/v2/events/{slug}` (schedules에서 개최일)
- 행사 목록: `GET https://dongne.co/api/v2/events?status=past&page={page}&limit=100`

### 부스 아이템 → CSV 컬럼 매핑
- `circleName` → 부스명
- `ownerName` → 대표자
- `boothCount` → 부스 (숫자 + "sp")
- `seatLabels[]` → 위치 / 위치(열) / 위치(번호) / 반부스
- `applicationId` → 링크 (`https://dongne.co/events/{slug}/circles/{applicationId}`)
- `fields[].systemKey`:
  - `mainWork` → 대표 작품(원작)
  - `otherWorks` → 그 외 다루는 작품
  - `character` → 캐릭터
  - `coupleDouble` → 커플링 (joinChar="X")
  - `coupleInclination` → 커플링 성향
  - `coupleOther` → 그 외 커플링
  - `medium` → 매체
  - `twitter` → 트위터
  - `petit_zone` → 쁘띠존 (직접 제목 문자열)

## 데이터 현황

### 월별 부스 데이터 (24년~26년, 12개월)
| 월 | 부스 수 | 트위터 | 위치 |
|---|---:|---:|---:|
| 24년_1월 | 1,254 | 1,016 | 0 |
| 24년_4월 | 1,250 | 951 | 0 |
| 24년_7월 | 1,246 | 996 | 0 |
| 24년_9월 | 1,118 | 800 | 0 |
| 25년_1월 | 1,394 | 1,068 | 0 |
| 25년_4월 | 1,360 | 991 | 0 |
| 25년_7월 | 1,409 | 1,027 | 0 |
| 25년_10월 | 1,301 | 949 | 0 |
| 26년_1월 | 1,411 | 1,056 | 0 |
| 26년_4월 | 1,483 | 1,135 | 1,483 |
| 26년_7월 | 1,539 | 1,108 | 1,539 |
| 26년_10월 | 1,422 | 997 | 1,422 |
| **합계** | **16,187** | | |

> 위치 데이터는 26년_4월·7월·10월만 보유 (과거 행사는 dongne.co API에서 seatLabels 미제공)
> 팔로워수는 26년_7월·26년_10월 보유 (`팔로워수`·`미확보수` 컬럼)
> RAW 부스정보 CSV는 루트와 data/processed 양쪽에 병존, 정규화 산출물(normalized)은
> **data/processed/normalized/ 단일 폴더**에서만 관리 (JWMI-15/16, pipeline.py --all 재생성)

## 원작 작품명 정규화 시스템

### 개요

`대표 작품(원작)` 컬럼의 2,262개 고유값을 정식 한국명 기준으로 정규화.
마스터 딕셔너리(`WORK_DICTIONARY.json`)와 정규화 스크립트(`normalize_works.py`)로 구성.

### 파일 구조 (추가)

```
├── WORK_DICTIONARY.json                       # 작품 마스터 딕셔너리 (v1.2, 446종)
├── pipeline.py                                # 정규화 → 미매핑 리포트 → DB 반영 단일 진입점
├── normalize_works.py                         # 정규화 엔진
├── scripts/build_db.py                        # normalized CSV → works.db 구축
├── scripts/analyze_works.py                   # 셀 단위 매칭 통계 측정
└── data/processed/normalized/{YY년_M월}_부스정보_normalized.csv  # 정규화 결과 (단일 폴더)
```

### WORK_DICTIONARY.json 구조

```json
{
  "metadata": { "version", "naming_rule", "total_works", "origin_legend", "category_legend" },
  "works": {
    "W0001": {
      "code": "W0001",
      "canonical_name": "정식 한국명",
      "origin": "kr|jp|cn|en|meta",
      "category": "manga|anime|game|webtoon|webnovel|...",
      "aliases": ["띄어쓰기/특수문자 변형"],
      "abbreviations": ["약칭/줄임말"],
      "review_needed": true/false,
      "notes": "비고"
    }
  },
  "reverse_index": { "모든 표기 소문자": "코드" }
}
```

### normalize_works.py 매칭 프로세스 (4단계)

1. **exact**: 정확 매칭 (사전 인덱스 직접 조회)
2. **normalized**: 공백/특수문자 제거 후 매칭
3. **괄호 병기**: `정식명(약칭)` → 괄호 앞 텍스트 / 괄호 안 약칭 각각 매칭
4. **fuzzy**: Levenshtein 거리 기반 유사도 매칭 (임계값 0.85)

다중 작품(콤마 구분)은 전체 매칭 실패 시 분리 후 각각 적용.

### 매칭 통계 (v1.2 사전 기준 전체 12회차 16,187셀, 2026-10-18 실측)

셀 단위 분류 (analyze_works.py 기준):

| 셀 분류 | 건수 | 비율 |
|---|---:|---:|
| **matched** (코드 부여) | **13,982** | **86.38%** |
| unmatched (사람 확인) | 214 | 1.32% |
| uncertain (판단 불가) | 139 | 0.86% |
| noise (작품 외 표기 확정) | 77 | 0.48% |
| empty (빈 셀) | 1,775 | 10.97% |

- 빈 셀 제외 유효 매칭률: **97.02%**, 사용 작품 444종
- 방식별(토큰 단위, 참고): exact 14,572 / exact_fallback 453 / exact_paren_stripped 276 / normalized 167 / fuzzy 99 외 소수
- works.db: booth_work 15,650행 / booth_work_raw 16,187행 / works 446종

## 비고

- 과거 행사는 `past events` API에 누락이 잦음 → 명명 패턴(df+YYMM, novel+NN, 25d+NN) 추정 검증 필요
- 팔로워 수는 캐시 재사용으로 효율화, 과거 행사 신규 계정은 별도 크롤링 필요
- Account_info/ 파생 프로젝트는 본 크롤링 결과를 입력으로 Selenium 계정 수집 수행
- 원작 작품 딕셔너리는 빈도 5 이상 기준 211개 작품 등록. 미매칭(unmatched)은 딕셔너리 확장으로 지속 개선 가능
- 28개 작품은 `review_needed: true` (정식 한국명 확인 필요)


## 정규화 산출물 관리 (JWMI-15/16)

`*_부스정보_normalized.csv` 12개(24년_1월~26년_10월)는 `data/processed/normalized/`
단일 폴더에서만 관리한다. 루트·data/processed 직하위의 normalized 파일은 제거되었으며,
재생성은 `python3 pipeline.py --all` 로 수행한다(같은 폴더에 결정적 재생성 — 사전 버전이
같으면 md5까지 동일). `pipeline.py --outdir <폴더>` 로 저장 위치를 바꿀 수 있다.
26년_10월 파일은 `대표 작품(원작)` 바로 뒤에 `대표 작품(원작)_코드`, `대표 작품(원작)_정규화`
칼럼을 두며(JWMI-7 방식), 전체 회차 재실행으로 전 회차가 동일 배치를 따른다.
26년_7월·26년_10월은 `팔로워수`·`미확보수` 칼럼을 입력 부스정보에서 그대로 상속 보존한다.

`works.db`에는 `works`, `booth_work`, `booth_work_raw`, `meta` 테이블을 저장하며,
pipeline.py는 회차 단위로 기존 행을 삭제 후 적재하므로 재실행이 멱등하다.
`analysis/`에는 v1.2 통계·미매핑 검토 목록(unmapped_review_*.csv)·변경 세트,
`scripts/`에는 분석·DB 구축·보고서 생성 도구를 둔다. 기존 `src/`, `data/`, `artifacts/`
디렉터리 구조와 RAW 부스정보의 루트·processed 병존은 유지한다.

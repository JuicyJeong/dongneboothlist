# Structure

## 프로젝트 개요

동인네트워크(dongne.co) 행사 부스 정보를 크롤링·정제하여 CSV로 정리하는 프로젝트.
동인네트워크 v2 API를 통한 부스 데이터 수집, 트위터 계정 정제, 팔로워 수 집계, 유효성 검증 기능 수행.

## 폴더 구조

```
dongneboothlist/
├── AGENTS.md                      # 에이전트 기본 동작 규칙
├── README.md                      # 프로젝트 소개
├── EVENT_INFORMATION.json         # 행사 정보 설정 (13개월, slug/이름/개최일)
├── 부스명 유사도 사전.csv          # 부스명 유사도 매핑 사전 (기존)
│
├── booth_search_total.py          # [핵심] v2 API 부스 크롤링
├── preprocess_twitter.py          # 트위터 컬럼 정제
├── fetch_followers.py             # 팔로워 수 크롤링 + 합산 (캐시/재개)
├── verify_twitter.py              # 트위터 계정 유효성 검증
├── batch_crawl.py                 # 월별 순회 배치 크롤링
├── vis.py                         # 부스 빈도 시각화 (기존)
├── pipeline.py                    # [JWMI-5] 단일 진입점: 정규화 → 미매핑 리포트 → DB 반영
├── normalize_works.py             # 작품명 정규화 엔진 (사전 기반 매칭 + 폴백 분리 + 판단 불가)
├── build_work_dictionary.py       # 작품 사전 빌드 (기존)
├── works.db                       # [JWMI-5] SQLite 매핑 DB (works/booth_work/booth_work_raw/meta)
│
├── scripts/                       # 작품 사전 분석·빌드·DB 스크립트 (JWMI-4/5)
│   ├── analyze_works.py           # 11개 회차 전수 분석 → analysis/ 산출물 저장
│   ├── extract_unmatched_parts.py # 미매핑 셀의 작품 단위 실패 토큰 추출
│   ├── build_v1_1.py              # WORK_DICTIONARY v1.0→v1.1 변경 세트 빌드
│   ├── generate_v1_1_report.py    # docs 보고서 생성기 (v1.1)
│   ├── llm_batch_map.py           # [JWMI-5] LLM 배치 2차: --export(미매핑 내보내기)/--apply(사전 반영)
│   ├── build_db.py                # [JWMI-5] normalized CSV → SQLite(works.db) 구축
│   └── generate_v1_2_report.py    # [JWMI-5] docs 보고서 생성기 (v1.2)
│
├── analysis/                      # 작품 사전 분석 산출물 (영속화)
│   ├── matching_stats_{1.0,v1.1,v1.2}.json  # 회차별/전체 매칭 통계
│   ├── frequency_all_{1.0,v1.1,v1.2}.csv    # 대표 작품 칼럼 전체 빈도
│   ├── unmatched_{1.0,v1.1,v1.2}.csv        # 미매핑 셀 값 + 빈도
│   ├── unmatched_parts_{1.0,v1.1}.csv       # 실패 토큰 단위 추출
│   ├── matched_works_{1.0,v1.1,v1.2}.csv    # 매칭된 작품 코드 빈도
│   ├── llm_batch_input_v1.2.csv             # [JWMI-5] LLM 배치 입력 (미매핑 고유 값)
│   ├── llm_mapping_v1.2.csv                 # [JWMI-5] LLM 매핑 결정 (value,decision,target,reason)
│   ├── v1.{1,2}_changeset.json              # 사전 변경 세트 요약
│   ├── unmapped_review_<회차>.csv           # [JWMI-5] 회차별 사람 확인용 리포트 (pipeline 생성)
│   └── WORK_DICTIONARY_v1.0_backup.json     # 백업 (재빌드 기준점)
│
├── WORK_DICTIONARY.json           # 작품 사전 v1.2 (446종, W0001~W0459, noise_terms·llm_decisions 포함)
│
├── docs/                          # 문서 폴더
│   ├── HISTORY.md                 # 전체 작업 히스토리
│   ├── Work_History.md            # 변경 이력 (날짜/시간 KST)
│   ├── Structure.md               # 본 파일 (폴더 구조/코드 분석)
│   ├── 원작명_정규화.md            # 정규화 규칙 문서 (기존)
│   ├── work_normalization_report.md # 정규화 리포트 (기존)
│   ├── work_dictionary_v1.1_report.md # 11개 회차 전수 분석 + 사전 v1.1 보고서
│   ├── work_dictionary_v1.2_report.md # [JWMI-5] 사전 v1.2 + 파이프라인 보고서 (자동 생성)
│   ├── preprocessing_pipeline_design.md # [JWMI-5] 전처리 방식 설계 문서 (대안 비교·선택 근거)
│   └── pipeline_usage.md          # [JWMI-5] 파이프라인 사용법
│
├── Account_info/                  # 트위터 계정 수집 파생 프로젝트
│   ├── README.md
│   ├── selenium_run.py            # Selenium 트위터 계정 정보 수집
│   ├── preprocess.ipynb           # 부스 정보 전처리 노트북
│   ├── User_Booth_match.ipynb     # 부스-계정 매칭/분석 노트북
│   ├── acc_format.csv             # 계정 정보 포맷
│   └── asset/
│
├── Results/                       # 과거 결과물 보관 (구 API 결과)
│   ├── 24년_4월.csv
│   ├── 24년_7월.csv
│   ├── 24년_9월.csv
│   └── 25년_1월.csv
│
├── {YY년_M월}.csv                 # 크롤링 raw 데이터 (월별)
├── {YY년_M월}_clean.csv           # 트위터 정제 후 데이터
├── {YY년_M월}_부스정보.csv        # 최종 산출물 (clean 복사본)
├── {YY년_M월}_부스정보_normalized.csv # [JWMI-5] 정규화 결과 (_코드/_정규화 컬럼 — 26년_10월부터 원문 칼럼 바로 옆 배치, 기존 회차는 맨 끝)
│
├── twitter_followers_cache.json   # 팔로워 수 캐시 (고유 계정 1,183개)
├── twitter_validity_sample.csv    # 유효성 검증 샘플 (40개)
├── top20_팔로워수.csv             # 팔로워수 Top 20
└── fetch_followers.log            # 팔로워 크롤링 로그
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

**실행**: `python3 booth_search_total.py --date 26년_7월`

### 2. preprocess_twitter.py (트위터 정제)

트위터 컬럼 정규화. `--input`/`--output` 인자로 월별 재사용.

**처리**:
- `@` 접두사 제거 → 순수 핸들 (selenium_run.py URL 호환)
- URL(`x.com/...`) → 핸들 추출
- 구분자(`,` `/` 공백) → 다중 계정 분리 보존
- 제어문자/한글 노이즈 제거
- `.bsky.social` → `bsky:핸들` 명시

**실행**: `python3 preprocess_twitter.py --input 26년_7월.csv --output 26년_7월_clean.csv`

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
| 26년_10월 | 1,430 | 997 | 1,430 |
| **합계** | **16,195** | | |

> 위치 데이터는 26년_4월·7월·10월만 보유 (과거 행사는 dongne.co API에서 seatLabels 미제공)
> 팔로워수는 26년_7월만 보유 (`팔로워수`·`미확보수` 컬럼)
> 26년_10월은 2026-09-21 신규 수집분(JWMI-7)으로 v1.2 전체 매칭 통계(11개월 14,765셀) 분모에는 미포함

## 원작 작품명 정규화·DB화 시스템

### 개요

`대표 작품(원작)` 컬럼의 비정형 표기를 정식 한국명 기준으로 정규화하고 작품 코드(W####)에
대응시킨 뒤 SQLite(`works.db`)로 부스-작품 매핑을 관리한다.
하이브리드 방식: 규칙 기반 1차 매칭(결정적·재현 가능) → 미매핑 고유 값만 LLM 배치 2차
(4분류 결정 → 사전 반영 → 재정규화). 설계 근거는 `docs/preprocessing_pipeline_design.md`.

### 파일 구조

```
├── pipeline.py                       # 단일 진입점 (정규화 → 리포트 → DB)
├── WORK_DICTIONARY.json              # 작품 사전 v1.2 (446종)
├── normalize_works.py                # 정규화 엔진
├── works.db                          # SQLite 매핑 DB
├── scripts/llm_batch_map.py          # LLM 배치 2차 (export/apply)
├── scripts/build_db.py               # DB 구축
├── {YY년_M월}_부스정보_normalized.csv # 정규화 결과
└── analysis/unmapped_review_<회차>.csv # 사람 확인용 미매핑 리포트
```

### WORK_DICTIONARY.json 구조

```json
{
  "metadata": { "version", "naming_rule", "total_works", "origin_legend", "category_legend",
                "noise_terms": ["작품 외 표기(굿즈·장르 등)"],
                "split_stopwords": ["폴백 분리 시 버리는 연결어(등, 위주, 드림 ...)"],
                "llm_decisions": { "value": { "decision", "target", "reason" } } },
  "works": {
    "W0001": {
      "code": "W0001",
      "canonical_name": "정식 한국명",
      "origin": "kr|jp|cn|en|multi|meta",
      "category": "manga|anime|game|webtoon|webnovel|trpg|...",
      "aliases": ["띄어쓰기/오타/변형 표기"],
      "abbreviations": ["약칭/줄임말"],
      "review_needed": true/false,
      "notes": "비고"
    }
  },
  "reverse_index": { "코드": ["모든 표기 키 목록"] }
}
```

### normalize_works.py 매칭 프로세스

셀 단위 순서 (첫 성공 시 반환, 실패 시 다음 단계):

1. **noise 필터**: 사전 `metadata.noise_terms` 및 하드코딩 결측 표기
2. **exact**: 사전 등록 표기와 정확 매칭
3. **normalized**: 공백/특수문자/꺾쇠 괄호 제거 후 매칭
4. **괄호 병기**: `정식명(약칭)` → 괄호 앞 텍스트 / 괄호 안 약칭 각각 매칭
5. **fuzzy**: Levenshtein 유사도 매칭 (임계값 0.85)
6. **콤마 분리**: 다중 작품 병기 셀을 파트별 2~5 재적용
7. **폴백 분리** (v1.2 신설): 파트 전체 매칭 실패 시 기호 경계(`.` `/` `&` `+` `·`)
   세그먼트 분리 → 공백 토큰 최장 우선(greedy longest) exact/normalized 재매칭.
   fuzzy는 오탐 방지 위해 미적용. 연결어(등/위주/드림 등)는 `split_stopwords`로 제거.
   하나도 매칭 없으면 원본 유지 (미지 작품명 붕괴 방지)
8. **판단 불가**: 모든 매칭 실패 + 사전 `metadata.llm_decisions`의 uncertain 결정이면
   `판단 불가` 표기 (추측 매핑 없음)

### DB 스키마 (works.db)

```sql
works(code PK, canonical_name, origin, category, aliases, abbreviations,
      review_needed, notes, dict_version)   -- 사전 기반 마스터 (재구축 시 전체 교체)
booth_work(event, booth_link, work_code, position, match_method, confidence,
      PRIMARY KEY(event, booth_link, work_code, position))  -- 부스 링크 키 매핑
booth_work_raw(event, booth_link, row_index, raw_value, normalized, codes, status)
      -- 원문 보존 + 상태(matched/unmatched/uncertain/noise/empty)
meta(key, value)                            -- dict_version, built_at
```

### pipeline.py 흐름

```
pipeline.py --input <신규회차_부스정보.csv> [--skip-db] [--all]
  ① normalize_works.process_file → <회차>_부스정보_normalized.csv
  ② analysis/unmapped_review_<회차>.csv (미매핑·판단 불가 고유 값 + decision 빈 양식)
  ③ scripts/build_db: works 마스터 교체 + booth_work/booth_work_raw 적재(멱등)
사전 갱신 루프: scripts/llm_batch_map.py --export → decision 기입 → --apply → ①~③ 재실행
```

### 매칭 통계 (v1.2 사전, 전체 14,765셀 — 셀 단위 산식)

| 항목 | v1.2 (셀 단위) |
|---|---:|
| 매칭 성공 셀 (코드 1개 이상) | **12,816** |
| 매칭률 (전체 셀 분모, 빈 셀 포함) | **86.80%** |
| 매칭률 (유효 셀 분모, 빈 셀 1,614 제외) | 97.45% |
| 판단 불가 셀 | 130 |
| 노이즈 셀 | 76 |
| 잔여 미매핑 | 129셀 / 고유 55종 |
| 처리율 (코드 부여 또는 명시 분류) | 88.20% (유효 셀 분모 99.02%) |
| 등장 작품 수 | 444 |
| 사전 등재 | **446** |

> 사전 버전별 추이(구 토큰 단위 산식, 참고): v1.0 77.58% → v1.1 82.57% → v1.2 셀 단위 86.80%.
> v1.2 통계는 셀 단위 상호배타 분류(matched/unmatched/uncertain/noise/empty)이며,
> 노이즈 셀 = 셀 전체 원본 값이 `metadata.llm_decisions` noise 결정값(72종)과 정확히 일치하는 셀.
> 산식 정의 상세: `docs/work_dictionary_v1.2_report.md` §1.1, 측정: `scripts/analyze_works.py --tag v1.2`
> DB 실측: works 446종 / booth_work 14,139행(중복 부스 링크 dedup 반영) / booth_work_raw 14,765행.
> 잔여 미매핑 129셀(고유 55종)은 `analysis/unmatched_v1.2.csv` 및 `analysis/unmapped_review_*.csv` 사람 확인 대상

## 비고

- 과거 행사는 `past events` API에 누락이 잦음 → 명명 패턴(df+YYMM, novel+NN, 25d+NN) 추정 검증 필요
- 팔로워 수는 캐시 재사용으로 효율화, 과거 행사 신규 계정은 별도 크롤링 필요
- Account_info/ 파생 프로젝트는 본 크롤링 결과를 입력으로 Selenium 계정 수집 수행
- 작품 코드는 불변 원칙: 기존 W#### 재사용·재매핑 금지, 신규 작품은 사전 최대 번호 +1부터 부여
  (llm_batch_map.py --apply 검증에서 차단)
- 불확실한 작품 정체는 추측 금지 — uncertain 결정으로 `판단 불가` 표기되며,
  결정 이력은 사전 `metadata.llm_decisions`와 `analysis/llm_mapping_*.csv`에 근거와 함께 영속화
- 31개 작품은 `review_needed: true` (정식 한국명 확인 필요 — v1.0 승계 28건 + v1.1 신규 3건)
- pipeline 재실행 멱등성 검증 완료 (normalized CSV SHA-256·DB 레코드 수 일치, 2026-09-21)

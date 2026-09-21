# Structure

## 프로젝트 개요

동인네트워크(dongne.co) 행사 부스 정보를 크롤링·정제하여 CSV로 정리하는 프로젝트.
동인네트워크 v2 API를 통한 부스 데이터 수집, 트위터 계정 정제, 팔로워 수 집계, 유효성 검증 기능 수행.

## 폴더 구조

```
dongneboothlist/
├── AGENTS.md                      # 에이전트 기본 동작 규칙
├── README.md                      # 프로젝트 소개
├── EVENT_INFORMATION.json         # 행사 정보 설정 (12개월, slug/이름/개최일)
├── 부스명 유사도 사전.csv          # 부스명 유사도 매핑 사전 (기존)
│
├── booth_search_total.py          # [핵심] v2 API 부스 크롤링
├── preprocess_twitter.py          # 트위터 컬럼 정제
├── fetch_followers.py             # 팔로워 수 크롤링 + 합산 (캐시/재개)
├── verify_twitter.py              # 트위터 계정 유효성 검증
├── batch_crawl.py                 # 월별 순회 배치 크롤링
├── vis.py                         # 부스 빈도 시각화 (기존)
│
├── docs/                          # 문서 폴더
│   ├── HISTORY.md                 # 전체 작업 히스토리
│   ├── Work_History.md            # 변경 이력 (날짜/시간 KST)
│   └── Structure.md               # 본 파일 (폴더 구조/코드 분석)
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

### 월별 부스 데이터 (24년~26년, 11개월)
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
| **합계** | **14,765** | | |

> 위치 데이터는 26년_4월·7월만 보유 (과거 행사는 dongne.co API에서 seatLabels 미제공)
> 팔로워수는 26년_7월만 보유 (`팔로워수`·`미확보수` 컬럼)

## 원작 작품명 정규화 시스템

### 개요

`대표 작품(원작)` 컬럼의 2,262개 고유값을 정식 한국명 기준으로 정규화.
마스터 딕셔너리(`WORK_DICTIONARY.json`)와 정규화 스크립트(`normalize_works.py`)로 구성.

### 파일 구조 (추가)

```
├── WORK_DICTIONARY.json            # 작품 마스터 딕셔너리 (211개 작품)
├── build_work_dictionary.py        # 딕셔너리 빌드 스크립트
├── normalize_works.py              # 정규화 스크립트 (4단계 매칭)
├── {YY년_M월}_부스정보_normalized.csv # 정규화 결과 (원본 + 정규화/코드 컬럼 추가)
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

1. **exact**: 정확 매칭 (reverse_index 직접 조회)
2. **normalized**: 공백/특수문자 제거 후 매칭
3. **괄호 병기**: `정식명(약칭)` → 괄호 앞 텍스트 / 괄호 안 약칭 각각 매칭
4. **fuzzy**: Levenshtein 거리 기반 유사도 매칭 (임계값 0.85)

다중 작품(콤마 구분)은 전체 매칭 실패 시 분리 후 각각 적용.

### 매칭 통계 (전체 14,765셀)

| 매칭 방식 | 건수 | 비율 |
|---|---:|---:|
| exact | 12,417 | 84.1% |
| exact_paren_stripped | 191 | 1.3% |
| normalized | 120 | 0.8% |
| fuzzy | 68 | 0.5% |
| exact_paren_inner | 23 | 0.2% |
| **매칭 성공** | **11,461** | **77.6%** |
| unmatched | 1,633 | 11.1% |
| empty | 1,636 | 11.1% |

> 빈 값 제외 매칭률: **87.3%**

## 비고

- 과거 행사는 `past events` API에 누락이 잦음 → 명명 패턴(df+YYMM, novel+NN, 25d+NN) 추정 검증 필요
- 팔로워 수는 캐시 재사용으로 효율화, 과거 행사 신규 계정은 별도 크롤링 필요
- Account_info/ 파생 프로젝트는 본 크롤링 결과를 입력으로 Selenium 계정 수집 수행
- 원작 작품 딕셔너리는 빈도 5 이상 기준 211개 작품 등록. 미매칭(unmatched)은 딕셔너리 확장으로 지속 개선 가능
- 28개 작품은 `review_needed: true` (정식 한국명 확인 필요)

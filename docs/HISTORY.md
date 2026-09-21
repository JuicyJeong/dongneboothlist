# 동인네트워크 부스 정보 정리 - 작업 히스토리

> 최종 업데이트: 2026-07-10

## 개요

동인네트워크(dongne.co) 행사 부스 정보를 크롤링·정제하여 CSV로 정리하는 작업 히스토리.
2024년 1월 ~ 2026년 7월까지 총 **11개월·14,765개 부스** 데이터를 취합.

---

## 작업 히스토리

### 1. 프로젝트 분석 및 API 마이그레이션 (핵심)

동인네트워크 사이트가 리뉴얼되어 기존 API(`api.dongne.co`)가 폐지됨을 확인.
새로운 v2 API(`dongne.co/api/v2/`)로 전환.

**변경 전후 비교**

| 구분 | 기존(폐지) | 신규(v2) |
|---|---|---|
| 엔드포인트 | `api.dongne.co/circles?event_id=` | `dongne.co/api/v2/events/{slug}/circles` |
| 부스 데이터 키 | `circle_name`, `owner_name`, `extra_vars{}` | `circleName`, `ownerName`, `fields[]` |
| 쁘띠존 | 부스에 ID → 별도 조회 | 부스에 직접 제목 문자열 |
| 페이지네이션 | `per_page=1000` | `limit` 최대 100 → 반복 호출 |
| 위치 | `seat`(문자열) | `seatLabels[]`(배열, `E-11` 하이픈 형식) |

`booth_search_total.py`를 v2 API에 맞게 재작성. CSV 컬럼(19개)은 기존 호환성 유지.

### 2. 26년 7월 부스 크롤링

- `EVENT_INFORMATION.JSON`에 `26년_7월` 행사 3개 추가 (df2607, sports11, df260702)
- 총 1,539개 부스 (df2607: 781 / sports11: 315 / df260702: 443)

### 3. 트위터 컬럼 전처리

`26년_7월_clean.csv` 생성 (raw 보존). 5가지 데이터 품질 이슈 해결:

| 이슈 | 처리 |
|---|---|
| `@` 접두사 불일치 (782건) | 제거 → 순수 핸들 |
| 전체 URL (4건) | 핸들 추출 |
| 다중 계정 (97건) | 구분자(`,` `/` 공백) 분리 보존 |
| 제어문자/한글 노이즈 | 제거 |
| Bluesky 계정 (3건) | `bsky:핸들` 명시 |

`preprocess_twitter.py`로 자동화. `selenium_run.py:31` URL 생성 호환성 확보.
최종 1,119개 중 1,119개(100%) 유효 핸들.

### 4. 트위터 계정 유효성 검증 (샘플링)

`verify_twitter.py` - 비로그인 Selenium 기반 계정 존재 여부 분류.
5가지 상태: `valid` / `protected` / `restricted` / `suspended` / `not_found`.
샘플 40개 기준 valid 90%.

### 5. 팔로워 수 크롤링

`fetch_followers.py` - 비로그인 Selenium, 다중 계정 합산.
- 고유 계정 1,183개, ok 1,150개 (97.2%)
- 크롤링 소요: 약 92분 (백그라운드 실행)
- 캐시(`twitter_followers_cache.json`)로 재실행 시 이어서/즉시 복원
- 다중 계정 sum, 미확보 계정 제외 + `미확보수` 표시
- 26년 7월 팔로워 합계: 3,812,119

### 6. 부스 위치 업데이트

행사 직전 배치도 공개 후 위치 데이터 갱신.
- `seatLabels` 파싱 버그 수정: `E-11` 하이픈 형식 지원 (기존 `A23` 구형 호환)
- `parse_seat()`에서 열/번호/반부스 분리 (`L-17a` → 열=L, 번호=17, 반부스=a)
- 26년 7월 위치 100% 채워짐

### 7. 과거 행사 배치 크롤링 (24년~26년)

`EVENT_INFORMATION.JSON`을 12개월로 확장:
- `idol06` → `vidol06` (어나더 스테이지 명명 변경 반영)
- 누락 월 추가: 25년 1/7/10월, 26년 1/4월

`booth_search_total.py`·`preprocess_twitter.py`에 인자 지원(`--date`/`--input`/`--output`) 추가.
`batch_crawl.py`로 10개월 순회 자동화.

### 8. 누락 행사 복구

`past events` API의 누락 발견 (이전에도 df240902 등 누락 사례 있었음).
행사 명명 패턴(df+YYMM, novel+NN, 25d+NN) 추정으로 직접 검증하여 누락 4개 복구:

| 월 | 복구 전 | 복구 후 | 추가 행사 |
|---|---|---|---|
| 25년_10월 | 83부스 (wt02) | 1,301부스 | df2510(691), df251002(397), 25d08(130) |
| 26년_1월 | 724부스 (df2601) | 1,411부스 | novel06(687) |

행사 시리즈 무결성 점검 완료 (디페스타·소설·쩜오·대운동회·오락관·어나더·다이스·스크롤바다).

---

## 산출물

### 데이터 파일 (`*_부스정보.csv`)

| 파일 | 부스 수 | 트위터 | 위치 |
|---|---:|---:|---:|
| 24년_1월_부스정보.csv | 1,254 | 1,016 | 0 |
| 24년_4월_부스정보.csv | 1,250 | 951 | 0 |
| 24년_7월_부스정보.csv | 1,246 | 996 | 0 |
| 24년_9월_부스정보.csv | 1,118 | 800 | 0 |
| 25년_1월_부스정보.csv | 1,394 | 1,068 | 0 |
| 25년_4월_부스정보.csv | 1,360 | 991 | 0 |
| 25년_7월_부스정보.csv | 1,409 | 1,027 | 0 |
| 25년_10월_부스정보.csv | 1,301 | 949 | 0 |
| 26년_1월_부스정보.csv | 1,411 | 1,056 | 0 |
| 26년_4월_부스정보.csv | 1,483 | 1,135 | 1,483 |
| 26년_7월_부스정보.csv | 1,539 | 1,108 | 1,539 |
| **합계** | **14,765** | | |

> 위치 데이터는 26년_4월·7월만 보유. 과거 행사는 dongne.co API에서 `seatLabels`를 빈 배열로 반환 (사이트 측 미제공).
> 팔로워수는 26년_7월만 보유 (`팔로워수`·`미확보수` 컬럼).

### 스크립트

| 스크립트 | 역할 |
|---|---|
| `booth_search_total.py` | v2 API 부스 크롤링 (`--date` 인자) |
| `preprocess_twitter.py` | 트위터 컬럼 정제 (`--input`/`--output` 인자) |
| `fetch_followers.py` | 팔로워 수 크롤링 + 합산 (캐시/재개/`--limit`) |
| `verify_twitter.py` | 계정 유효성 검증 (비로그인 Selenium) |
| `batch_crawl.py` | 월별 순회 배치 크롤링 |

### 설정/캐시

- `EVENT_INFORMATION.json` - 12개월 행사 정보 (slug/이름/개최일)
- `twitter_followers_cache.json` - 계정별 팔로워 수 캐시 (1,183개)

---

## 주요 기술 노트

### v2 API 엔드포인트
- 부스 목록: `GET https://dongne.co/api/v2/events/{slug}/circles?page={page}&limit=100`
- 쁘띠존: `GET https://dongne.co/api/v2/events/{slug}/petit-zones`
- 행사 메타: `GET https://dongne.co/api/v2/events/{slug}` (schedules에서 개최일)

### fields[].systemKey → 컬럼 매핑
- `mainWork` → 대표 작품(원작)
- `otherWorks` → 그 외 다루는 작품
- `character` → 캐릭터
- `coupleDouble` → 커플링 (joinChar="X")
- `coupleInclination` → 커플링 성향
- `coupleOther` → 그 외 커플링
- `medium` → 매체
- `twitter` → 트위터
- `petit_zone` → 쁘띠존 (직접 제목 문자열)

### 비고
- 과거 행사는 `past events` API에 누락이 잦음 → 명명 패턴 추정 검증 필요
- 트위터 계정 검증은 비로그인 Selenium으로 `restricted`까지 분류 가능 (확정 불가)
- 팔로워 수는 캐시 재사용으로 효율화, 과거 행사 신규 계정은 별도 크롤링 필요

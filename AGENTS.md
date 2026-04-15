# DongneBoothList - AGENTS.md

## 프로젝트 개요
동인네트워크(dongne.co) 부스 정보 수집 및 분석 도구. 아마추어 창작 문화 이벤트(디페, 오락관, 어나더 스테이지, 다이스 페스타 등)의 부스 데이터를 API로 수집하고 정규화/분석합니다.

## 기술 스택
- Python 3.9+, uv (패키지 매니저)
- hatchling 빌드 시스템
- 주요 라이브러리: requests, pandas, pyyaml

## 프로젝트 구조
```
├── src/
│   ├── config/
│   │   ├── settings.yaml          # API 설정 (base_url, endpoints, 크롤링 설정)
│   │   ├── field_mapping.yaml     # API 필드 → 출력 컬럼 매핑
│   │   └── works_dictionary.yaml  # 작품명 정규화 사전 (canonical → variants)
│   ├── crawler/
│   │   ├── api_client.py          # 동인네트워크 API 클라이언트 (v2 API + 페이지네이션)
│   │   └── raw_exporter.py        # raw CSV 내보내기
│   ├── preprocessor/
│   │   ├── field_cleaner.py       # 트위터 아이디 등 필드 정제
│   │   └── work_normalizer.py     # 대표작품 정규화 (works_dictionary.yaml 기반)
│   ├── analyzer/                  # 분석 모듈 (미구현)
│   └── twitter/                   # 트위터 관련 모듈
├── scripts/
│   ├── 00_fetch_events.py         # EVENT_INFORMATION.json 업데이트
│   ├── 01_crawl.py                # 크롤링 실행
│   ├── 02_preprocess.py           # 트위터 전처리
│   ├── 02_preprocess_all.py       # 전체 전처리
│   ├── 02a_preprocess_twitter.py  # 트위터 전처리
│   ├── 02b_preprocess_works.py    # 작품 전처리
│   ├── build_similarity_dict.py   # 유사도 사전 빌드
│   └── llm_normalize_works.py     # LLM 기반 작품 정규화
├── EVENT_INFORMATION.JSON         # 행사 정보 (2020~2026년, 68개 행사, 22개월)
├── data/
│   ├── dict/
│   │   └── works_dictionary.json  # 작품명 정규화 사전 (JSON 형식)
│   └── raw/                       # 크롤링 결과 CSV (22개월, 26,722개 부스)
```

## API 정보
- **v2 API** (2026년 4월 변경됨):
  - Base URL: `https://dongne.co/api/v2`
  - 부스 목록: `/events/{slug}/circles` (페이지네이션: limit=100, page 파라미터)
  - 쁘띠존: `/events/{slug}/petit-zones`
  - 행사 목록: `https://dongne.co/api/events` (?past=true 로 과거 행사 조회)
- **구 API** (폐기): `https://api.dongne.co` (DNS 해석 불가)

## 데이터 파이프라인
1. `scripts/01_crawl.py --date "26년_4월"` → `data/raw/raw_26년_4월.csv`
2. `scripts/02_preprocess.py` → 트위터 정제
3. 작품명 정규화 (works_dictionary.yaml 사용)

## works_dictionary 구조
```yaml
canonical 작품명:
  - variant1
  - variant2

미분류:
  - 아직 매핑 안 된 작품들
```
- 68개 canonical, 206개 variant 등록 완료
- 미분류 208개 항목은 사용자가 직접 분류 필요
- yaml: `src/config/works_dictionary.yaml`, json: `data/dict/works_dictionary.json`

## 최근 변경 이력 (2026-04-15)
1. `pyproject.toml` - hatch build targets wheel packages 설정 추가
2. `settings.yaml` - API를 v2로 마이그레이션
3. `field_mapping.yaml` - 숫자 코드(10229 등) → systemKey(mainWork 등)로 교체
4. `api_client.py` - v2 API 응답 구조에 맞게 전면 재작성 (페이지네이션, fields 배열 파싱)
5. `EVENT_INFORMATION.JSON` - 2020~2026년 행사 68개로 업데이트 (API에서 자동 수집)
6. `works_dictionary.yaml` - 작품명 정규화 사전 신규 생성

## 실행 명령어
```bash
# 크롤링
uv run python scripts/01_crawl.py --date "26년_4월"

# 전처리
uv run python scripts/02_preprocess.py --date "26년_4월"

# 전체 전처리
uv run python scripts/02_preprocess_all.py --date "26년_4월"
```

## TODO / 해야할 일
- [ ] **works_dictionary.yaml 미분류 정리** - 208개 미분류 항목을 적절한 canonical로 이동하거나 새 canonical 생성 필요. 사용자가 직접 확인하며 분류해야 함
- [x] **work_normalizer.py 업데이트** - `works_dictionary.yaml`을 사용하도록 마이그레이션 완료
- [x] **다이스 페스타 "대표 룰" 필드 처리** - ruleMain/ruleSub을 대표 작품(원작)/그 외 다루는 작품에 통합 완료
- [ ] **analyzer 모듈 구현** - `src/analyzer/`가 비어있음. 작품별/매체별/행사별 통계 분석 기능 구현 필요
- [ ] **EVENT_INFORMATION.JSON Day 분류 개선** - 현재 같은 날짜끼리 Day1/Day2로 나눔. 실제로는 같은 주말의 토/일이 Day1/Day2여야 하는데, 일부 행사는 토요일에만 열릴 수도 있어 로직 검토 필요
- [ ] **EVENT_INFORMATION.JSON 자동 업데이트 스크립트** - `scripts/00_fetch_events.py`와 실제 API 연동하여 자동으로 최신화하는 기능
- [x] **과거 행사 크롤링** - 2020~2026년 22개월, 68개 행사, 26,722개 부스 크롤링 완료
- [ ] **Lint/Typecheck** - `ruff` 설정이 있으나 실행 확인 필요: `uv run ruff check src/`

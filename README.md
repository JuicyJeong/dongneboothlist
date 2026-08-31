# 동인 네트워크 행사 부스 정보 정리

동인네트워크(dongne.co) 행사 부스 정보를 수집·정제하고 작품명을 코드화하는 데이터 프로젝트입니다. 수집 원본, 정제 데이터, 참조 사전, 분석 결과를 분리하여 재현 가능한 작업 흐름을 제공합니다.

## 디렉터리 역할

```text
src/          실행 소스 코드
  crawl/      동인네트워크 v2 API 수집기
  pipeline/   월별 배치 실행 및 트위터 전처리
  normalization/ 작품 마스터 사전 생성·정규화
  social/     X(트위터) 계정 검증 및 팔로워 집계
  analytics/  부스 배치도·빈도 분석
data/         버전 관리 대상 데이터
  raw/        API 수집 원본 CSV
  processed/  정제·부스정보·정규화 CSV
  reference/  행사 설정·작품 사전·매핑 사전
  cache/      재실행에 사용하는 팔로워 캐시
artifacts/    재생성 가능한 결과물
  maps/, visualizations/, social/, legacy/
docs/         구조, 변경 이력, 분석 문서
```

자세한 구조와 데이터 흐름은 `docs/Structure.md`를 참조하세요.

## 주요 실행 방법

```sh
# 행사 부스 원본 수집 → data/raw/
python3 src/crawl/booth_search_total.py --date 26년_7월

# 트위터 핸들 정제 → data/processed/
python3 src/pipeline/preprocess_twitter.py

# 전체 월 수집·정제·최종 부스정보 생성
python3 src/pipeline/batch_crawl.py

# 작품명 정규화 통계(파일 미생성)
python3 src/normalization/normalize_works.py --dry-run

# 26년 7월 부스 배치도 생성 → artifacts/maps/
python3 src/analytics/generate_booth_map.py
```

## 유의 사항

- `data/raw/`는 원본 보존용이며 직접 수정하지 않습니다.
- `data/processed/`는 원본에서 재생성 가능한 가공 데이터입니다.
- `artifacts/`는 결과물 보관 위치입니다. 새 결과 생성 전에는 기존 파일을 보존하거나 별도 이름으로 저장하세요.
- X(트위터) 수집기는 Selenium 및 ChromeDriver가 필요하며, 서비스 정책·요청 제한을 준수해야 합니다.

## 배경

행사 홈페이지의 개별 부스 정보를 하나의 테이블로 정리해 방문 계획과 데이터 분석에 활용하는 것이 목적입니다. 작품명 정규화 사전은 동일 작품의 여러 표기를 고유 코드로 연결해 데이터 품질을 높입니다.

자세히 보기: https://swift-aries-692.notion.site/e4396146350d485591e086f2afa3651e?pvs=74
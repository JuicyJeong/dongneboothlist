# Work History

## 2026-09-21 17:10 (KST)

변경 파일: WORK_DICTIONARY.json
변경 내용: v1.0 → v1.1 갱신. 신규 작품 158종 추가(W0212~W0369, 기존 코드 미변경), 기존 55개 작품에 별칭 98개 병합, W0117 살파랑 origin 정정(kr→cn, priest의 杀破狼), W0027·W0208·W0177 교차 중복/오귀속 별칭 제거, metadata.noise_terms 신설(60종), reverse_index 재생성(1,221키). 총 작품 211→369종
사유: 11개 회차 대표 작품 칼럼 전수 분석 기반 사전 보강. 웹 검증(나무위키·공식 사이트)으로 미확인 작품의 원작명·origin·category 확정

---

변경 파일: normalize_works.py
변경 내용: 사전 metadata.noise_terms를 로드해 작품 외 표기(공예·굿즈·장르명)를 noise로 분류하도록 노이즈 필터 보강. 기존 하드코딩 노이즈 목록은 유지
사유: 노이즈 기준을 사전 데이터로 이관해 재분석 시 동일 기준 적용

---

변경 파일: scripts/analyze_works.py (신규)
변경 내용: 11개 회차 `대표 작품(원작)` 전수 분석 스크립트. 회차별/전체 매칭 통계, 전체 빈도, 미매핑·매칭 목록을 analysis/ 하위 파일로 저장
사유: 분석 재현성 확보 및 세션 유실 대비 중간 산출물 영속화

---

변경 파일: scripts/extract_unmatched_parts.py (신규)
변경 내용: 미매핑 셀을 콤마 분리·괄호 처리 후 작품 단위 실패 토큰 추출. 토큰 빈도+예시 셀을 analysis/unmatched_parts_*.csv 로 저장
사유: 다중 작품 병기 셀 속 실제 실패 토큰 식별용

---

변경 파일: scripts/build_v1_1.py (신규)
변경 내용: v1.0→v1.1 변경 세트(별칭·정정·신규 작품·noise_terms)를 코드화한 사전 빌드 스크립트. --dry-run 지원, 변경 요약을 analysis/v1.1_changeset.json 저장
사유: 사전 갱신 내역의 재현성·추적성 확보

---

변경 파일: scripts/generate_v1_1_report.py (신규)
변경 내용: analysis 산출물과 갱신된 사전을 읽어 docs/work_dictionary_v1.1_report.md 생성
사유: 보고서 수치가 산출물에서 자동 산출되도록 하여 수치 불일치 방지

---

변경 파일: docs/work_dictionary_v1.1_report.md (신규)
변경 내용: 11개 회차 전수 분석 보고서. 매칭 통계(77.58%→82.57%, 미매핑 고유 1,189→684), 웹 검증 내역, 신규 코드 목록(W0212~W0369), 별칭 추가 내역, 잔여 미매핑 상위 60건, 판단 불가·review_needed 항목, 재현 방법
사유: 이슈 JWMI-4 완료 기준 중 분석 보고서 산출

---

변경 파일: analysis/ (신규 폴더)
변경 내용: matching_stats_1.0.json, matching_stats_v1.1.json, frequency_all_1.0.csv, frequency_all_v1.1.csv, unmatched_1.0.csv, unmatched_v1.1.csv, matched_works_1.0.csv, matched_works_v1.1.csv, unmatched_parts_v1.0.csv, unmatched_parts_v1.1.csv, v1.1_changeset.json, WORK_DICTIONARY_v1.0_backup.json 저장
사유: 분석 산출물 영속화 (v1.0 백업 포함 — build_v1_1.py 재실행 기준점)

사유(전체 작업): 이슈 JWMI-4 "[Stage 1] 11개 회차 대표 작품 칼럼 전수 분석 및 작품 사전(WORK_DICTIONARY.json) v1.1 보강" 완료

---

## 2026-07-16 23:14 (KST)

변경 파일: 26년_7월_부스정보.csv (및 26년_7월.csv, 26년_7월_clean.csv)
변경 내용: 26년_7월 부스 위치 최종 업데이트. 최종 배치도 공개에 따른 좌석 변경 22건 반영 (예: M-03→M-01, R-20→S-03, E-12a→E-09b 등). 부스 수는 1,539 동일, 위치 100% 채워짐 유지. 팔로워수·미확보수는 기존 캐시값 병합으로 보존 (1,107행)
사유: 행사 임박 최종 배치도 업데이트. booth_search_total.py 재크롤링 후 이전 백업에서 팔로워수 컬럼을 링크 기준 매핑하여 병합 (fetch_followers 재크롤링 타임아웃 회피)

---

## 2026-07-10 11:52 (KST)

변경 파일: EVENT_INFORMATION.json
변경 내용: 24년~26년 행사 정보 12개월로 확장. `26년_7월`(df2607, sports11, df260702) 추가, `idol06`→`vidol06` 명명 변경 반영, 누락 월 추가(25년 1/7/10월, 26년 1/4월), 25년10월·26년1월 누락 행사 복구(df2510, df251002, 25d08, novel06)
사유: 과거 행사 데이터 정리를 위한 행사 정보 보완. past events API 누락분은 명명 패턴 추정으로 직접 검증하여 추가

---

변경 파일: booth_search_total.py
변경 내용: 구 API(api.dongne.co) 폐지에 따라 신규 v2 API(dongne.co/api/v2)로 전면 재작성. CSV 컬럼 19개 기존 호환성 유지. `--date` 인자 추가, `parse_seat()` 하이픈 형식(`E-11`) 지원으로 위치 파싱 버그 수정
사유: 사이트 리뉴얼로 구 API 응답 불가, 새 API 구조(fields[], seatLabels[]) 대응

---

변경 파일: preprocess_twitter.py (신규)
변경 내용: 트위터 컬럼 정제 스크립트 작성. @ 제거, URL→핸들 추출, 다중 계정 분리(, / 공백 구분자), 제어문자/한글 노이즈 제거, Bluesky 계정 `bsky:` 명시. `--input`/`--output` 인자 지원
사유: selenium_run.py URL 생성 호환성 확보 및 데이터 품질 개선

---

변경 파일: fetch_followers.py (신규)
변경 내용: 비로그인 Selenium 기반 팔로워 수 크롤링 스크립트. 고유 계정 캐싱(twitter_followers_cache.json)으로 재개/중복 제거, 다중 계정 합산, 미확보 계정 `미확보수` 표시. `--limit` 옵션 지원
사유: 부스별 팔로워 수 집계 요청. 캐시로 효율화

---

변경 파일: verify_twitter.py (신규)
변경 내용: 비로그인 Selenium 기반 계정 유효성 검증 스크립트. valid/protected/restricted/suspended/not_found 5가지 상태 분류
사유: 트위터 계정 존재 여부 확인 요청

---

변경 파일: batch_crawl.py (신규)
변경 내용: 월별 순회 배치 크롤링 스크립트. booth_search_total.py + preprocess_twitter.py + _부스정보.csv 복사 자동화
사유: 24년~26년 다수 월 일괄 처리

---

변경 파일: AGENTS.md (신규)
변경 내용: 에이전트 기본 동작 규칙 문서 작성. Context7/Sequential Thinking 기본 적용, 한글 응답, md 파일 docs 저장, Work_History.md/Structure.md 관리, temp 폴더 사용 규칙
사유: 에이전트 작업 일관성 확보

---

변경 파일: docs/HISTORY.md (신규)
변경 내용: 이 세션의 전체 작업 히스토리 문서. API 마이그레이션, 트위터 정제, 팔로워 수, 위치 업데이트, 과거 배치, 누락 복구 작업 내역 및 산출물 정리
사유: 작업 내역 문서화

---

데이터 산출물 (신규 생성)
- 24년_1월~26년_7월 `*_부스정보.csv` 11개 (총 14,765 부스)
- `26년_7월_부스정보.csv`에 팔로워수/미확보수 컬럼 포함 (고유 계정 1,183개, ok 1,150)
- twitter_followers_cache.json (팔로워 수 캐시)
- twitter_validity_sample.csv (유효성 검증 샘플 40개)
- top20_팔로워수.csv (팔로워수 Top 20)

---

## 2026-07-10 14:50 (KST)

변경 파일: docs/work_normalization_report.md (신규)
변경 내용: 원작 작품 스트링 정규화 분석 리포트. 2,262개 고유값에 대해 9가지 정규화 카테고리(띄어쓰기, 특수문자, 대소문자, 약칭, 괄호 병기, 다중 작품, 시리즈, 노이즈, 비창작물) 분석
사유: 원작 작품명 정규화 프로세스 설계를 위한 사전 분석

---

변경 파일: WORK_DICTIONARY.json (신규)
변경 내용: 원작 작품 정규화 마스터 딕셔너리. 211개 작품, 670개 exact 인덱스, 각 작품에 고유 코드(W0001~) + 정식 한국명 + origin + category + aliases(띄어쓰기/특수문자 변형) + abbreviations(약칭) 등록. reverse_index 포함
사유: 모든 작품명을 정식 한국명 기준으로 통일하고, unseen data 대응을 위한 매핑 기반 구축

---

변경 파일: build_work_dictionary.py (신규)
변경 내용: WORK_DICTIONARY.json 생성 스크립트. WORKS 리스트(정식명/origin/category/aliases/abbreviations 정의) → JSON 빌드
사유: 딕셔너리 유지보수 및 확장 자동화

---

변경 파일: normalize_works.py (신규)
변경 내용: 원작 작품명 정규화 스크립트. 4단계 매칭: exact → normalized → 괄호 병기(paren_stripped/paren_inner) → fuzzy(Levenshtein). 다중 작품(콤마 분리) 대응. 코드값 자동 할당. `--all`/`--input`/`--dry-run`/`--columns`/`--fuzzy-threshold` 인자 지원
사유: WORK_DICTIONARY.json 기반 CSV 정규화 자동화

---

데이터 산출물 (신규)
- WORK_DICTIONARY.json: 211개 작품 (검토 필요 28개), 670 exact / 495 norm 인덱스
- normalize_works.py 매칭 결과: 전체 14,765셀 중 매칭 성공 11,461 (77.6%), 빈 값 제외 87.3%
- 매칭 방식: exact 84.1%, exact_paren_stripped 1.3%, normalized 0.8%, fuzzy 0.5%

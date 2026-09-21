# Work History

## 2026-09-21 22:12 (KST)

변경 파일: EVENT_INFORMATION.JSON, booth_search_total.py, normalize_works.py, pipeline.py, 26년_10월.csv, 26년_10월_clean.csv, 26년_10월_부스정보.csv, 26년_10월_부스정보_normalized.csv (신규), analysis/unmapped_review_26년_10월.csv (신규), works.db, docs/Work_History.md, docs/Structure.md, docs/pipeline_usage.md
변경 내용: 26년 10월 회차 신규 수집·정규화. ① EVENT_INFORMATION.JSON에 26년_10월 4행사 등록(dongne.co API 실측 확인: df2610 제35회 디. 페스타(토) 10/3, df261002 제35회 디. 페스타(일)·25d09 제9회 쩜오 어워드·wt03 스크롤의 바다 3화 10/4, 추정 슬러그 미사용). ② booth_search_total.py로 4행사 1,430부스 크롤링(페이지 요청 간 time.sleep 0.5초 추가) → _clean → _부스정보 생성. ③ normalize_works.py process_file이 _코드/_정규화 칼럼을 원문 칼럼 바로 옆에 삽입하도록 변경(사용자 요구: 원문 옆에 작품코드·작품명 병기) 및 pipeline.py update_db가 built_at을 갱신하도록 보완. ④ pipeline.py 실행: 26년_10월_부스정보_normalized.csv(코드 부여 셀 1,168/1,430=81.7%, 유효 셀 분모 92.2%), 미매핑 리포트 170 고유 값, works.db booth_work 1,500행 반영. 참고: pipeline 콘솔 통계(952/66.6%)는 기존 세그먼트 혼재 산식 출력이며 셀 단위 실측과 상이(향후 정렬 과제), 사전(v1.2) 미확장·신규 작품은 리포트로만 남김
사유: 이슈 JWMI-7 — 26년 10월 회차 CSV 생성 및 원작 칼럼 전처리(작품코드·작품명 병기)

---

## 2026-09-21 18:32 (KST)

변경 파일: scripts/analyze_works.py (수정), analysis/matching_stats_v1.2.json, analysis/unmatched_v1.2.csv, analysis/frequency_all_v1.2.csv, analysis/matched_works_v1.2.csv (재생성), scripts/generate_v1_2_report.py (수정), docs/work_dictionary_v1.2_report.md (재생성), docs/Structure.md (갱신)
변경 내용: 보고 레이어를 최종 산출물 기준으로 재수집. analyze_works.py를 셀 단위 상호배타 분류(matched/unmatched/uncertain/noise/empty, matched=코드 1개 이상 부여 셀, noise=셀 전체 값이 llm_decisions noise 결정값과 정확히 일치) 기준으로 개편하고 산식 정의를 stats JSON `metric_definitions`에 함께 기록. 재측정 결과: 매칭 12,816셀/86.80%(전체 14,765셀 분모, 빈 셀 1,614 포함), 유효 셀 분모 97.45%, 판단 불가 130셀, 노이즈 76셀, 잔여 미매핑 129셀/고유 55종, 처리율 88.20%(유효 셀 99.02%), 등장 작품 444종. unmatched_v1.2.csv는 이미 해소된 226셀분을 제외한 실제 사람 확인 목록(55종)으로 재생성. 리포트에 지표 산식 정의 섹션 신설 및 works.db 실측값(works 446/booth_work 14,139/booth_work_raw 14,765) 기재. 회차별 수치는 커밋된 *_부스정보_normalized.csv 실측과 정합 확인
사유: JWMI-5 재검토 지적 시정 — 기존 통계가 최종 사전으로 측정은 되었으나 matched 계산에서 셀 수에서 토큰 수(unmatched/uncertain/noise/empty 세그먼트)를 차감하는 혼재 산식을 써 매칭률 과소(84.19%→86.80% 실측)·잔여 과대(323→129셀 실측) 계상되고, unmatched 목록에 이미 코드 부여된 값(354종 중 다수)이 남는 문제. 토큰/셀 단위 분리로 시정

---

## 2026-09-21 16:27 (KST)

변경 파일: agent/agent/c8d9fd463f10 브랜치 (병합)
변경 내용: Stage 1(JWMI-4) 산출물 병합 — WORK_DICTIONARY.json v1.1, scripts/ 4종, analysis/ 12종, docs/work_dictionary_v1.1_report.md, normalize_works.py 노이즈 필터 보강. WORK_DICTIONARY.json·docs/Work_History.md·docs/Structure.md·normalize_works.py 4파일 add/add 충돌은 Stage 1(theirs) 버전으로 해결
사유: 이슈 JWMI-5 작업 시작 전 Stage 1 산출물 확보

---

변경 파일: docs/Work_History.md, docs/work_dictionary_v1.1_report.md, docs/Structure.md, .gitignore, scripts/__pycache__/ (삭제)
변경 내용: Stage 1 인수인계 선행 정정. Work_History의 "2026-09-21 17:10 (KST)" 항목 시각을 실제 커밋 시각 15:22로 정정, v1.1 리포트 review_needed 수치 "총 31건(v1.0 승계 28 + 신규 3)" 명기, Structure.md review_needed 28→31건 갱신, scripts/__pycache__/*.pyc 제거 및 .gitignore 신설
사유: Stage 1 검토 승인 시 지적된 선행 정정 3건 수행

---

변경 파일: docs/preprocessing_pipeline_design.md (신규)
변경 내용: 전처리 방식 설계 문서. 순수 규칙/순수 LLM 배치/하이브리드 3안을 비용·정확도·재현성·확장성·감사 가능성 관점에서 비교하고 하이브리드(규칙 1차 + 미매핑 한정 LLM 배치 2차, 확정분은 사전 별칭/신규 코드로 환원) 채택 근거, 파이프라인 아키텍처, SQLite 스키마, 멱등성 보장·검증 계획 기술
사유: 이슈 JWMI-5 완료 기준 중 "전처리 방식 설계 문서"

---

변경 파일: normalize_works.py (확장)
변경 내용: 파트 전체 매칭 실패 시 2차 폴백 분리 추가 — 기호 경계(마침표·`/`·`&`·`+`·`·`·`|`) 세그먼트 분리 후 공백 토큰 최장 우선(greedy longest) exact/normalized 재매칭(fuzzy는 오탐 방지 위해 미적용). 연결어(등·등등·위주·드림 등)는 사전 metadata.split_stopwords로 제거. `판단 불가` 표기(metadata.llm_decisions의 uncertain 결정, 전체 매칭 실패 시 최종 적용), 같은 파트 내 중복 코드 제거, normalize_key에 꺾쇠 괄호 제거 추가. 매칭 방식에 uncertain/fallback 계열 신설
사유: 콤마 외 구분자 병기 셀('데못죽.플레이브', '괴담출근 데못죽' 등) 미매핑 해소 및 추측 금지 원칙의 출력 반영

---

변경 파일: scripts/analyze_works.py (수정)
변경 내용: uncertain(판단 불가) 방식을 매칭 실패와 동일하게 집계하도록 matched_cells 계산 수정
사유: 정규화 엔진의 신규 매칭 방식 통계 반영

---

변경 파일: scripts/llm_batch_map.py (신규)
변경 내용: LLM 병렬 배치 2차 처리 도구. --export로 규칙 1차 미매핑 고유 값(빈도·decision·target·reason 빈 양식)을 analysis/llm_batch_input_<tag>.csv로 내보내고, --apply로 alias(별칭 병합)/new(신규 코드)/noise(noise_terms 추가)/uncertain(판단 불가 영속화) 4분류 매핑을 검증 후 WORK_DICTIONARY.json에 반영. new의 canonical 지정·자동 코드 할당(W#### 순차), 기존 코드 재사용·재매핑·canonical 충돌 검증, reverse_index 재생성, 백업 및 analysis/v1.2_changeset.json 변경 세트 저장, --dry-run 지원
사유: 하이브리드 파이프라인의 LLM 2차 단계 구현 및 재현 가능한 사전 갱신

---

변경 파일: WORK_DICTIONARY.json (v1.1 → v1.2)
변경 내용: LLM 배치 매핑 360행 반영 — 신규 작품 77종(W0370~W0459, 기존 코드 미변경), 기존 76개 작품에 별칭 병합(예: 귀멸→W0212, 진격거→W0138, TFP→W0038, CoC7th_TRPG→W0115), noise_terms 72종 추가(굿즈·장르·창작 표기), metadata.llm_decisions 130건(판단 불가)·split_stopwords 8종 신설, reverse_index 재생성. 총 작품 369→446종
사유: 규칙 1차 미매핑 336 고유 값에 대한 LLM 2차 처리 확정분 반영

---

변경 파일: scripts/build_db.py (신규), works.db (신규)
변경 내용: SQLite 매핑 DB 구축 스크립트 및 DB. works(작품 마스터, 사전 기반 교체)/booth_work(부스 링크를 키로 작품 코드 연결, position으로 복수 작품 분해)/booth_work_raw(원문·정규화·코드·상태 보존)/meta 테이블. utf-8-sig 읽기로 BOM 컬럼 처리, INSERT OR REPLACE로 재실행 멱등. 적재 결과: 매핑 14,140행 / 원문 14,765행(matched 12,816 / unmatched 205 / uncertain 130 / empty 1,614)
사유: 이슈 JWMI-5 완료 기준 중 "부스-작품 매핑 DB화"

---

변경 파일: pipeline.py (신규)
변경 내용: 단일 진입점 CLI. --input(반복 지정)/--all 대상으로 ①정규화(normalized CSV 산출) ②미매핑 리포트(analysis/unmapped_review_<회차>.csv, 사람 확인용 decision 빈 양식 포함) ③DB 반영까지 자동 실행. --skip-db 옵션
사유: 이슈 JWMI-5 완료 기준 중 "신규 회차 재실행 가능한 파이프라인 CLI"

---

변경 파일: scripts/generate_v1_2_report.py (신규), docs/work_dictionary_v1.2_report.md (신규)
변경 내용: v1.2 갱신 보고서 자동 생성기 및 산출 보고서. 수치는 analysis 산출물에서 자동 산출 (매칭률 82.57%→84.19%, 등장 작품 367→444종, 처리율 97.81%, LLM 2차 분류 내역, 회차별 통계, 잔여 미매핑 상위 30건, 재현 방법)
사유: 결과 요약 문서화 및 수치 불일치 방지

---

변경 파일: docs/pipeline_usage.md (신규)
변경 내용: 파이프라인 사용법 문서. 신규 회차 처리 흐름, DB 스키마·조회 예시, 미매핑 사전 갱신 루프(배치 export → decision 기입 → apply → 재실행), 주의사항(코드 불변·판단 불가·부스 링크·멱등성)
사유: 이슈 JWMI-5 완료 기준 중 "사용법 문서"

---

변경 파일: *_부스정보_normalized.csv 11개 (신규), analysis/ 산출물 갱신
변경 내용: 전체 11개 회차 대표 작품(원작) 칼럼 v1.2 사전 정규화 결과. 26년_7월 기존 파일은 v1.2 기준으로 재생성. analysis에 matching_stats_v1.2.json, unmatched_v1.2.csv, llm_batch_input_v1.2.csv, llm_mapping_v1.2.csv, v1.2_changeset.json, WORK_DICTIONARY_v1.1_backup.json, unmapped_review_<회차>.csv 11개 저장
사유: 이슈 JWMI-5 완료 기준 중 "전체 회차 *_normalized.csv"

---

검증 (2026-09-21): ① 멱등성 — pipeline --all 2회 실행, normalized CSV 11개 SHA-256 및 DB 레코드 수 일치 ② 샘플 정확도 — 26년_7월 무작위 50셀 검토, 오매핑 0건, 불확실 값은 판단 불가로 올바르게 표기 ③ 사전 검증 — --apply 단계에서 기존 코드 충돌·canonical 중복 전수 차단 확인

사유(전체 작업): 이슈 JWMI-5 "[Stage 2] 하이브리드 전처리 파이프라인 구현 및 전체 회차 정규화·DB화" 완료

---

## 2026-09-21 15:22 (KST)

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

## 2026-08-31 15:44 (KST)

변경 파일: `src/`, `data/`, `artifacts/`, `README.md`, `docs/Structure.md`, `.gitignore`
변경 내용: 루트에 혼재되어 있던 실행 코드, 행사 원본·정제 데이터, 참조 사전, 캐시, 이미지·로그·과거 결과를 역할별 디렉터리로 이동하고 기본 입출력 경로를 새 구조에 맞게 갱신했다.
사유: 소스 코드와 산출물을 분리해 재실행·검토·버전 관리의 일관성을 확보했다.
롤백: 해당 리팩터링 커밋을 되돌리면 Git 이동 이력과 기존 루트 경로를 함께 복원할 수 있다.

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

# 작품 정규화·매핑 DB 파이프라인 사용법

> 이슈: JWMI-5 · 설계 배경은 `docs/preprocessing_pipeline_design.md` 참조
> 대상: `대표 작품(원작)` 칼럼이 포함된 `*_부스정보.csv`

## 1. 구성 요소

| 파일 | 역할 |
|---|---|
| `pipeline.py` | **단일 진입점** — 정규화 → 미매핑 리포트 → DB 반영 |
| `normalize_works.py` | 규칙 기반 정규화 엔진 (exact → normalized → 괄호 → fuzzy → 폴백 분리) |
| `WORK_DICTIONARY.json` | 작품 사전 (v1.2, 446종). 별칭·약칭·노이즈·판단 불가 결정 포함 |
| `scripts/llm_batch_map.py` | 미매핑 LLM 배치 2차: 내보내기/사전 반영 |
| `scripts/build_db.py` | normalized CSV → SQLite(`works.db`) 구축 |
| `scripts/analyze_works.py` | 전체 회차 매칭 통계 측정 (`analysis/` 산출) |
| `scripts/generate_v1_2_report.py` | v1.2 보고서 자동 생성 (`docs/work_dictionary_v1.2_report.md`) |

## 2. 신규 회차 처리 (기본 흐름)

새 회차 CSV(예: `26년_10월_부스정보.csv`)가 들어오면:

```bash
python3 pipeline.py --input 26년_10월_부스정보.csv
```

수행되는 단계:

1. **① 정규화** — `26년_10월_부스정보_normalized.csv` 생성
   - `대표 작품(원작)_정규화` 컬럼: 정규화된 작품명 (`;` 로 복수 작품 구분)
   - `대표 작품(원작)_코드` 컬럼: `W####` 코드 (`;` 구분)
   - 정체 불확실 값은 `판단 불가`로 표기 (추측 매핑 없음)
2. **② 미매핑 리포트** — `analysis/unmapped_review_26년_10월.csv`
   - 미매핑·판단 불가 고유 값 + 빈도. 사람 확인용 (decision 컬럼 비워둠)
3. **③ DB 반영** — `works.db`에 부스-작품 매핑 적재 (재실행 멱등)

옵션:

```bash
python3 pipeline.py --input a.csv --input b.csv   # 여러 파일 동시 처리
python3 pipeline.py --all                          # 전체 회차 재구축
python3 pipeline.py --input a.csv --skip-db        # DB 반영 생략
python3 pipeline.py --input a.csv --db other.db --dict WORK_DICTIONARY.json
```

## 3. DB 스키마 (`works.db`)

```sql
works(code PK, canonical_name, origin, category, aliases, abbreviations,
      review_needed, notes, dict_version)          -- 작품 마스터 (사전 기반)
booth_work(event, booth_link, work_code, position, match_method, confidence)
      -- 부스 링크를 키로 작품 코드 연결, PRIMARY KEY(event, booth_link, work_code, position)
booth_work_raw(event, booth_link, row_index, raw_value, normalized, codes, status)
      -- 원문 보존 + 상태(matched/unmatched/uncertain/noise/empty)
meta(key, value)                                   -- dict_version, built_at
```

조회 예시:

```sql
-- 작품별 부스 수 (최근 회차)
SELECT w.canonical_name, COUNT(DISTINCT b.booth_link) AS booths
FROM booth_work b JOIN works w ON w.code = b.work_code
WHERE b.event = '26년_7월'
GROUP BY 1 ORDER BY booths DESC LIMIT 20;

-- 미매핑·판단 불가 셀 확인
SELECT booth_link, raw_value FROM booth_work_raw
WHERE event = '26년_10월' AND status IN ('unmatched','uncertain');
```

## 4. 미매핑이 남았을 때 (사전 갱신 루프)

파이프라인은 코드를 부여할 수 없는 값을 지어내지 않고 리포트로 넘긴다.
사전을 갱신해 커버리지를 올리는 절차:

```bash
# 1. 현재 사전 기준 미매핑 고유 값을 배치 입력으로 내보내기
python3 scripts/llm_batch_map.py --export --tag v1.3
#    → analysis/llm_batch_input_v1.3.csv

# 2. LLM/사람이 각 행에 decision 기입
#    value,decision,target,reason[,origin,category,canonical]
#    - alias   : 확실한 기존 작품 표기 → target=기존 W#### 코드
#    - new     : 사전에 없는 별개 작품 → target=신규 코드(비우면 자동 순차 부여)
#    - noise   : 작품 외 표기(굿즈·장르·창작·결측)
#    - uncertain: 정체 불확실 → 판단 불가 표기 (추측 금지)
#    저장: analysis/llm_mapping_v1.3.csv

# 3. 검증 후 사전 반영 (기존 W#### 코드 재사용·재매핑은 검증에서 차단됨)
python3 scripts/llm_batch_map.py --apply --mapping analysis/llm_mapping_v1.3.csv \
    --new-version 1.3

# 4. 전체 재실행 (사전 버전 기준 정규화 결과 재생성 — 결정적)
python3 pipeline.py --all
python3 scripts/analyze_works.py --tag v1.3   # 커버리지 측정
```

## 5. 주의사항

- **코드 불변**: 기존 `W####` 코드를 다른 작품에 재사용·재매핑 금지. 신규 작품은
  사전 최대 번호 +1부터 자동 순차 부여 (`--apply` 검증)
- **판단 불가**: 불확실한 작품 정체는 추측으로 채우지 말고 `uncertain`으로 남긴다.
  정규화 결과에는 `판단 불가`로 표기되며 코드는 부여되지 않는다
- **부스 링크**: DB 매핑의 키는 부스 링크(행사별 고유). 링크가 없는 행은
  `booth_work_raw`에만 기록되고 매핑 테이블에서 제외된다
- **멱등성**: 같은 입력 + 같은 사전 버전이면 결과(정규화 CSV·DB)가 동일하다
  (검증: `docs/preprocessing_pipeline_design.md` §6)
- `판단 불가` 결정은 사전 `metadata.llm_decisions`에 영속화되므로, 사전을 되돌리려면
  `analysis/WORK_DICTIONARY_v<이전버전>_backup.json`을 복원하면 된다

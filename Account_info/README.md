# selenium_run.py

이 스크립트는 Selenium을 사용하여 Twitter 계정 정보를 수집하고, 수집된 데이터를 CSV 파일로 저장하는 프로그램입니다.

## 요구 사항

- Python 3.x
- Selenium
- pandas

## 설치

필요한 라이브러리를 설치하려면 다음 명령어를 사용하세요:

```sh
pip install selenium pandas
```

## 사용법

1. 크롬 드라이버를 다운로드하고, 시스템 경로에 추가하거나 `webdriver.Chrome()`에 경로를 지정합니다.
2. `final_2501.csv` 파일을 준비합니다. 이 파일은 계정아이디 열을 포함해야 합니다.
3. 스크립트를 실행합니다:

```sh
python selenium_run.py
```

## 주요 기능

- `sleep_random_sec(min, max)`: 주어진 범위 내에서 랜덤한 시간 동안 대기합니다.
- `get_twitter_user_data(driver, input_ID)`: 주어진 Twitter 사용자 ID에 대한 데이터를 수집합니다.
  - 계정 이름
  - 팔로워 수
  - 최상단 트윗 내용
  - 최상단 트윗의 리트윗 수
  - 최상단 트윗의 마음 수
  - 최상단 트윗의 노출 수

## 파일 설명

- `final_2501.csv`: 입력 파일로, 계정아이디 열을 포함해야 합니다.
- `final2501.csv`: 출력 파일로, 수집된 Twitter 계정 정보가 저장됩니다.

## 주의 사항

- Twitter 계정이 비공개이거나 존재하지 않는 경우, 해당 계정의 정보를 수집할 수 없습니다.
- 스크립트 실행 중 크롬 브라우저가 자동으로 열리고 닫힙니다.

## 예제

다음은 `final_2501.csv` 파일의 예제입니다:

```
계정아이디
user1
user2
user3
```

스크립트 실행 후, `final2501.csv` 파일에 수집된 데이터가 저장됩니다.

## 문의

궁금한 사항이 있으면 @Juicy_Wave로 문의하세요.


import time
import requests
import json
import argparse
import pandas as pd

print("*****************동인네트워크 부스 정리 프로그램 실행합니다*****************")
print("****************MADE BY PPJ(Twitter: @Juicy_Wave)****************")


# JSON 파일 경로 설정
json_file_path = 'EVENT_INFORMATION.json'

# JSON 파일 읽기
with open(json_file_path, 'r', encoding='utf-8') as json_file:
    json_data = json.load(json_file)


# 특정 날짜를 선택 (예: "24년_1월")
ap = argparse.ArgumentParser()
ap.add_argument('--date', default='26년_7월', help='처리할 월 (예: 24년_4월)')
args = ap.parse_args()
selected_date = args.date

# 선택된 날짜에 해당하는 데이터 추출
selected_events = [event for event in json_data if event['DATE'] == selected_date][0]['INFO']

# event_list, event_dict, day_dict 생성
event_list = [event['CODE'] for event in selected_events]
event_dict = {event['CODE']: event['NAME'] for event in selected_events}
day_dict = {event['NAME']: event['DAY'] for event in selected_events}


twitter_acc_list = []

API_BASE = "https://dongne.co/api/v2"
HEADERS = {"User-Agent": "Mozilla/5.0"}

FIELD_MAP = {
    'mainWork': '대표 작품(원작)',
    'otherWorks': '그 외 다루는 작품',
    'character': '캐릭터',
    'coupleDouble': '커플링',
    'coupleInclination': '커플링 성향',
    'coupleOther': '그 외 커플링',
    'medium': '매체',
    'twitter': '트위터',
    'petit_zone': '쁘띠존',
}


def parse_field_value(field):
    value = field.get('value', '')
    if value is None or value == '':
        return ''
    if isinstance(value, list):
        join_char = field.get('joinChar', ',')
        return join_char.join(str(v) for v in value)
    return str(value)


def parse_seat(seat_labels):
    seat = ''
    col, num, half = '', '', ''
    if seat_labels:
        seat = ', '.join(str(s) for s in seat_labels)
        first = str(seat_labels[0])
        if first:
            if '-' in first:
                parts = first.split('-', 1)
                col = parts[0]
                rest = parts[1] if len(parts) > 1 else ''
            else:
                col = first[0]
                rest = first[1:]
            if rest:
                if not rest[-1].isdigit():
                    num = rest[:-1]
                    half = rest[-1]
                else:
                    num = rest
                    half = ''
    return seat, col, num, half


time_now = time.strftime('%Y-%m-%d-%H:%M', time.localtime(time.time()))
count = 1
print("**********************오늘의 날짜는", time_now, "**********************")


COLUMNS = ['부스명', '대표자', '위치', '위치(열)', '위치(번호)', '반부스', '부스', '대표 작품(원작)', '그 외 다루는 작품', '쁘띠존', '캐릭터', '커플링', '커플링 성향', '그 외 커플링', '매체',
           "트위터", "링크", "행사명", "개최일"]

save_df = pd.DataFrame(columns=COLUMNS)

for currunt_event in event_list:
    init_df = pd.DataFrame(columns=COLUMNS)

    try:
        all_items = []
        page = 1
        while True:
            url = f"{API_BASE}/events/{currunt_event}/circles?page={page}&limit=100"
            req = requests.get(url, headers=HEADERS, timeout=30)
            j_data = req.json()
            data = j_data['data']
            all_items.extend(data['items'])
            pagination = data.get('pagination', {})
            total_pages = pagination.get('totalPages', 1)
            if page >= total_pages:
                break
            page += 1

        print(event_dict[currunt_event], "- 총 부스 수:", len(all_items))
    except Exception as e:
        print("url에러 발생. 주소를 다시 확인해주세요.", e)
        continue

    for item in all_items:
        info_dict = {}

        info_dict["부스명"] = str(item.get("circleName", "") or "")
        info_dict["대표자"] = str(item.get("ownerName", "") or "")

        seat, col, num, half = parse_seat(item.get("seatLabels", []))
        info_dict["위치"] = seat
        info_dict["위치(열)"] = col
        info_dict["위치(번호)"] = num
        info_dict["반부스"] = half

        booth_count = item.get("boothCount", "")
        info_dict["부스"] = str(booth_count) + "sp" if booth_count != "" else ""

        for field in item.get("fields", []):
            system_key = field.get("systemKey")
            if system_key in FIELD_MAP:
                info_dict[FIELD_MAP[system_key]] = parse_field_value(field)

        if "트위터" in info_dict and info_dict["트위터"]:
            twitter_acc_list.append(info_dict["트위터"])

        info_dict["링크"] = f"https://dongne.co/events/{currunt_event}/circles/{item.get('applicationId', '')}"
        info_dict["행사명"] = event_dict[currunt_event]
        info_dict["개최일"] = day_dict[event_dict[currunt_event]]

        init_df.loc[len(init_df)] = info_dict

    save_df = pd.concat([save_df, init_df], ignore_index=True)

    print(count, "번째 행사 작성 완료. 다음 행사로 넘어갑니다...")
    count = count + 1


save_df.to_csv(selected_date + ".csv", index=False, encoding="utf-8-sig")


print("*****************실행 완료. 다음 실행은 다음 이 시간에...*****************")



"""
== v2 API 응답 필드 매핑 (2026 리뉴얼 이후) ==
엔드포인트: https://dongne.co/api/v2/events/{EVENT_SLUG}/circles?page={page}&limit=100 (limit 최대 100)
쁘띠존:      https://dongne.co/api/v2/events/{EVENT_SLUG}/petit-zones

circleName     -> 부스명
ownerName      -> 대표자
boothCount     -> 부스 (숫자 + "sp")
seatLabels[]   -> 위치 / 위치(열) / 위치(번호) / 반부스 (배치도 공개 후 입력됨)
applicationId  -> 링크 (https://dongne.co/events/{slug}/circles/{applicationId})

fields[].systemKey:
  mainWork            -> 대표 작품(원작)
  otherWorks          -> 그 외 다루는 작품
  character           -> 캐릭터
  coupleDouble        -> 커플링       (joinChar="X" 로 조인)
  coupleInclination   -> 커플링 성향
  coupleOther         -> 그 외 커플링
  medium              -> 매체
  twitter             -> 트위터
  petit_zone          -> 쁘띠존        (직접 제목 문자열)
"""

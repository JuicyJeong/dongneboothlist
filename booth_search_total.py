import time
import requests
import json
import pandas as pd

print("*****************동인네트워크 부스 정리 프로그램 실행합니다*****************")
print("****************MADE BY PPJ(Twitter: @Juicy_Wave)****************")


# JSON 파일 경로 설정
json_file_path = 'aaa.json'

# JSON 파일 읽기
with open(json_file_path, 'r', encoding='utf-8') as json_file:
    json_data = json.load(json_file)


# 특정 날짜를 선택 (예: "24년_1월")
selected_date = "24년_1월"

# 선택된 날짜에 해당하는 데이터 추출
selected_events = [event for event in json_data if event['DATE'] == selected_date][0]['INFO']

# event_list, event_dict, day_dict 생성
event_list = [event['CODE'] for event in selected_events]
event_dict = {event['CODE']: event['NAME'] for event in selected_events}
day_dict = {event['NAME']: event['DAY'] for event in selected_events}
# event_list = ["df2301","novel03"] ###URL에 들어갈 행사 주소 문자열들을 리스트로 먼저 선언. #23년 1월

# event_dict = {event_list[0]:"7월 토 디페",event_list[1]:"7월 일 디페",event_list[2]:"제 5회 쩜오 어워드",event_list[3]:"제 6회 대운동회"}
# event_dict = {event_list[0]:"제 20회 디페스타",event_list[1]:"아아─, 이것이 『소설』이라는 것이다. Chapter 3"}#23년 1월
# day_dict = {"제 20회 디페스타":'day1',"아아─, 이것이 『소설』이라는 것이다. Chapter 3":"day2"}
#event_list = ["df2304","df230402","dice02","game04","vidol05"] ###URL에 들어갈 행사 주소 문자열들을 리스트로 먼저 선언.

# ################################# 23년 10월##############################################
# event_list = ["df2310","sports08"] ###URL에 들어갈 행사 주소 문자열들을 리스트로 먼저 선언.
# event_dict = {event_list[0]:"제23회 디. 페스타",event_list[1]:"제 8회 대운동회"}
# day_dict = {"제23회 디. 페스타":'day1',"제 8회 대운동회":'day2'}
# ################################# 23년 10월##############################################

################################# 24년 01월##############################################
# event_list = ["df2401","novel04"] ###URL에 들어갈 행사 주소 문자열들을 리스트로 먼저 선언.
# event_dict = {event_list[0]:"제24회 디. 페스타",event_list[1]:"아아─, 이것이 『소설』이라는 것이다. Chapter 4"}
# day_dict = {"제24회 디. 페스타":'Day1',"아아─, 이것이 『소설』이라는 것이다. Chapter 4":'Day2'}
################################# 23년 10월##############################################


time_now = time.strftime('%Y-%m-%d-%H:%M', time.localtime(time.time()))
count = 1
print("**********************오늘의 날짜는",time_now,"**********************")




save_df = pd.DataFrame(
        columns=['부스명', '대표자', '위치', '부스', '대표 작품(원작)', '그 외 다루는 작품', '쁘띠존', '캐릭터', '커플링', '커플링 성향', '그 외 커플링', '매체',
                 "링크","행사명","개최일"])

for currunt_event in event_list:
    init_df = pd.DataFrame(
        columns=['부스명', '대표자', '위치', '부스', '대표 작품(원작)', '그 외 다루는 작품', '쁘띠존', '캐릭터', '커플링', '커플링 성향', '그 외 커플링', '매체',
                 "링크","행사명","개최일"])

    try:
        #쁘띠존 리스트 딕셔너리로 먼저 긁어오기
        petit_dict = {}
        petitzone_url = "https://api.dongne.co/events/petits?event_id="+ str(currunt_event) + \
                        "&page=1&per_page=50&keyword=&desc=DESC&last=false" #50개 이상 되는 적이 없음
        req = requests.get(petitzone_url)
        j_text = req.text
        j_data = json.loads(j_text)

        for i in range(0,len(j_data["list"])):

            # print(str(j_data["list"][i]["petit_id"]))
            # print(str(j_data["list"][i]["title"]))
            petit_dict[str(j_data["list"][i]["petit_id"])] = str(j_data["list"][i]["title"])

        petit_dict[""] =""
        # print(event_dict[currunt_event],"에서 개최되는 쁘띠존들은?",petit_dict)
    except:
        print("로딩에러가 발생. 주소를 다시한번 확인해주세요.")
        pass

    #부스 데이터 긁어서 딕셔너리로 반환하기

    try:
        srl_get = "https://api.dongne.co/circles?event_id="+ str(currunt_event) +\
                  "&form=owner_name,twitter,seat,booth,petit_promotion_booth,10155,10199,10229,rule_main,rule_sub,10200," \
                  "petitzone,10202,10225,10204,10233,10226,10232,10208,10209&page=1&per_page=1000" \
                  "&original=&petitzone=&fav=&color=&target=&keyword=&orderby=&sort=&sorting=false&last=false"


        req = requests.get(srl_get)
        j_text = req.text
        j_data = json.loads(j_text)
    except:
        print("url에러 발생. 주소를 다시 확인해주세요.")
        pass

    #부스 주소를 json에서 갖고와서 리스트에 저장하고 칼럼에 집어넣기.
    for i in range(0,len(j_data["list"])):
        info_dict = {}
        # print(j_data["list"][i])
        info_dict["부스명"]= str(j_data["list"][i]["circle_name"])
        info_dict["대표자"] = str(j_data["list"][i]["owner_name"])
        info_dict["위치"] = str(j_data["list"][i]["seat"])
        info_dict["부스"] = str(j_data["list"][i]["booth"])+"sp"



        extra_values = j_data["list"][i]["extra_vars"] #딕셔너리 형태
        new_extra_values = dict(extra_values) #json 스트링을 딕셔너리로 변환하는데 작은 따옴표를 큰 따옴표로 바꿔야함.
        # print(new_extra_values)

    #선택 값 입력 필드 있으면 딕셔너리에 추가, 없으면 넘어가기.

        if "rule_main" in new_extra_values: # 다이스페스타 한정
            info_dict['대표 작품(원작)']= new_extra_values["rule_main"]
            # print(info_dict)
        if "rule_sub" in new_extra_values: # 다이스페스타 한정
            rule_sub = new_extra_values["rule_sub"]
            info_dict['그 외 다루는 작품'] = rule_sub
            # print(info_dict)
        if "10229" in new_extra_values: #대표작품(원작)
            wonjac = new_extra_values['10229']
            info_dict['대표 작품(원작)']= wonjac

        if "10200" in new_extra_values: #10200: 그 외 다루는 작품
            otherjac = new_extra_values['10200']
            info_dict["그 외 다루는 작품"] = otherjac

        if "petitzone" in new_extra_values: #쁘띠존
            petit_number =  new_extra_values["petitzone"]
            petit_str = petit_dict[str(petit_number)]
            info_dict["쁘띠존"] = str(petit_str)

        if "10225" in new_extra_values: #10225: 캐릭터
            character = new_extra_values["10225"]
            info_dict["캐릭터"] = character


        if "10233" in new_extra_values: #10233: 커플링
            couple = new_extra_values["10233"].replace(",","X")
            info_dict["커플링"] = couple

        if "10226" in new_extra_values:  # 10226: 커플링 성향
            couple_s = new_extra_values["10226"]
            info_dict["커플링 성향"] = couple_s

        if "10232" in new_extra_values: #그 외 커플링
            other_couple = new_extra_values["10232"]
            info_dict["그 외 커플링"] = other_couple

        if "10209" in new_extra_values: # 매체
            media = new_extra_values["10209"]
            info_dict["매체"] = media

        info_dict["링크"] ="https://dongne.co/event/"+ str(currunt_event)+"/circles/" +str(j_data["list"][i]["application_srl"])
        info_dict["행사명"] = event_dict[currunt_event]
        info_dict["개최일"] = day_dict[event_dict[currunt_event]]

        # print(info_dict)
        init_df.loc[len(init_df)] = info_dict
        rule_main = rule_sub = wonjac = otherjac = petit_str = character = couple = couple_s = other_couple = media = " "

    # print(init_df.head())

    save_df = pd.concat([save_df,init_df],ignore_index=True)
    # init_df.to_csv("event_booth/"+str(time_now)+"_"+str(currunt_event)+"_booth_data.csv",encoding="utf-8-sig")

    print(count,"번째 행사 작성 완료. 다음 행사로 넘어갑니다...")
    count = count + 1

# save_df.to_csv("total_booth/"+str(time_now)+"_booth_data.csv",index=False,encoding="utf-8-sig")
# save_df.to_csv("total_booth_data.csv",index=False,encoding="utf-8-sig")
# save_df.to_csv("23년7월.csv",index=False,encoding="utf-8-sig")
save_df.to_csv("24년1월.csv",index=False,encoding="utf-8-sig")



print("*****************실행 완료. 다음 실행은 다음 이 시간에...*****************")


"""
application_srl: 주소 넘버
circle_name: 부스명
owner_name: 대표자
seat: 위치
booth: 부스 사이즈
10299: 대표 작품(원작)그 외 다루는 작품
10200: 그 외 다루는 작품
petitzone: 쁘띠존(주소값으로 되어있음)
10225: 캐릭터
10233: 커플링
10226: 커플링 성향
10232: 그외 커플링
10209: 매체
application_srl: 주소 넘버(링크)
"""
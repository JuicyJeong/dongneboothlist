import requests
import json
import pandas as pd

event_list = ["dice01","df2204","game03","vidol04"] ###URL에 들어갈 행사 주소 문자열들을 리스트로 먼저 선언.
event_dict = {"다이스 페스타":event_list[0],"제 18회 디페스타":event_list[1],"제 3회 오락관":event_list[2],"제 4회 어나더 스테이지":event_list[3]}

### 부스 주소를 따로 api를 통해 갖고 오기
for currunt_event in event_list:

    srl_get = "https://api.dongne.co/circles?event_id=" + str(currunt_event) + "&form=owner_name,twitter,seat,booth,petit_promotion_booth,10155,10199," \
    "10229,rule_main,rule_sub,10200,petitzone,10202,10225,10204,10233,10226,10232,10208,10209&page=1&per_page=1000&original" \
    "=&petitzone=&fav=&color=&target=&keyword=&orderby=&sort=&sorting=false&last=false"


    req = requests.get(srl_get)
    j_text = req.text
    j_data =json.loads(j_text)

    srl_list = []

    #부스 주소를 json에서 갖고와서 리스트에 저장하고 칼럼에 집어넣기.
    for i in range(0,len(j_data["list"])):

        # print(j_data["list"][i]["application_srl"])
        booth_url ="https://dongne.co/event/" +str(currunt_event)+ "/circles/" +str(j_data["list"][i]["application_srl"])
        srl_list.append(booth_url)
        #부스명과 부스주소를 딕셔너리로 생성
    print(srl_list)

    new_df = pd.read_csv(str(currunt_event) + "_booth_data.csv")
    print(new_df.info())
    new_df["링크"] = srl_list
    print(new_df.head())

    if "Unnamed: 0" in new_df.columns:
        new_df = new_df.drop(columns=["Unnamed: 0"])

    new_df.to_csv(str(currunt_event) + "_booth_data.csv",index=False,encoding="utf-8-sig")


'''
임시 데이터프레임을 선언. 파일을 하나씩 읽어오도록 합니다. 파일명을 딕셔너리 형태로 변경해서 행사명으로 바꾸도록 합시다.
그 후에 임시 데이터프레임에 한 파일씩 집어넣은 다음에 새로운 엑셀파일로 저장합니다.
 저장하기 전에 어디서 행사명을 새로운 칼럼으로 추가합니다. 이걸 반복문으로 돌려서 실행.
 최종 통합 파일도 하나 만들어줍시다.
'''

def get_key(val): #value 값으로 key값을 리턴하는 함수
    for key, value in event_dict.items():
        if val == value:
            return key

    return "There is no such Key"


total_df = pd.DataFrame()
for i in range(0,len(event_list)):

    save_df= pd.read_csv(str(event_list[i])+"_booth_data.csv")
    save_df["행사명"] = str(get_key(event_list[i]))
    total_df = total_df.append(save_df)
    if "Unnamed: 0" in total_df.columns:
        total_df = total_df.drop(columns=["Unnamed: 0"])
    print(total_df.head())

total_df.to_csv("행사 부스 통합본.csv",index=False,encoding="utf-8-sig")

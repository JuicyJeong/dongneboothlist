from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd


#크롬드라이버로 원하는 url로 접속

url = 'https://dongne.co/event/df2204/circles?page=1&per_page=1000'
driver = webdriver.Chrome('/Users/jinwoojeong/Desktop/Study/DF/chromedriver')
driver.get(url)
time.sleep(5)

'''
부스 내용 파싱하는 부분, sm8,col12랑 sm12,col12파트가 두개로 나뉘어져 있어서 두개로 분기를 해야함
판다스에서 정렬하거나, 엑셀에서 장르별 정렬로 나중에 세팅하면 되니까 우선은 순차적으로 하나씩 긁어오는거에 집중하기.
'''
div_list = ["div > div > div.col-sm-8.col-12","div > div > div.col-sm-12.col-12"]
save_df = pd.DataFrame(columns=['부스명','대표자','부스',"대표 작품(원작)","그 외 다루는 작품",'쁘띠존','캐릭터','커플링','커플링 성향','그 외 커플링','매체'])

for div_element in div_list:
    booth_titles = driver.find_elements_by_css_selector(div_element) #12-12짜리도 있으니 리스트로 놓고 돌려야함


    #리스트 초기화, 앞에 리스트 추가하기
    temp_list = []
    string_list = ["부스명"]


    for i in booth_titles: #한 부스마다 기준으로 돌아가는 반복문.
        raw_text = i.text
        # print(raw_text)

        temp_list = raw_text.split("\n") #줄바꿈을 기준으로 리스트에 한 element 부여.
        # print(temp_list)

        #리스트에 element 쭉 돌면서 : 있으면 나눠서 새 리스트에 입력, 없으면 구분자로 나눈후에 append.
        first_list = [] #새로 입력할 리스트. 여기에는 구분자가 나뉘어져 있는걸 한번만 슬라이스한 것과 원래 있던것들을 집어넣습니다.
        list_len = len(temp_list)
        list_range = range(0,list_len)



        for current_list_number in list_range: #리스트 쭉 돌면서 : 있으면 한번만 자르기
            if ":" in temp_list[current_list_number]:
                divide_list = temp_list[current_list_number].split(":",1)
                for i in range(0,2): #어차피 두개니까 둘로 나눠도 될듯???
                    first_list.append(divide_list[i]) #두개로 나뉘어져 있는데 리스트로 긁으면 안되니까 반복문으로 요소 추가하기
            else:
                first_list.append(temp_list[current_list_number]) # :가 없는건 그냥 추가하기


        #필요없는 내용 딕셔너리로 만들기 전에 삭제하기
        first_list.remove('공유')
        if '신작' in first_list:
            first_list.remove('신작')
        if '오리지널(1차창작)' in first_list:
            first_list.remove('오리지널(1차창작)')


        second_list = string_list + first_list #맨 앞에 "부스명" 추가.
        final_list = [] #마지막에 들어갈 리스트 선언
        for i in range(0,len(second_list)):
            temp_string = second_list[i].strip()
            final_list.append(temp_string)
        # print(final_list) #전체 리스트 확인

    # 딕셔너리로 가기 전에 zip 쓰려고 나누기
        key_index = final_list[0::2]
        value_index = final_list[1::2]
        # print("key:",key_index)
        # print("value:",value_index)

        dict_list= dict(zip(key_index,value_index))
        # print(dict_list)
        save_df.loc[len(save_df)] = dict_list

print(save_df.head(10))
save_df.to_csv("booth_data.csv")






from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

#크롬드라이버로 원하는 url로 접속
event_list = ["dice01","df2204","game03","vidol04"] ###URL에 들어갈 행사 주소 문자열들을 리스트로 먼저 선언.
driver = webdriver.Chrome('/Users/jinwoojeong/Desktop/Study/DF/chromedriver')  ##크롬드라이버 실행해서 창을 띄움.

for currunt_event in event_list:
    url = 'https://dongne.co/event/'+str(currunt_event)+'/circles?page=1&per_page=1000'
    driver.get(url)
    time.sleep(5) #로딩시간을 위해 지연.

    '''
    부스 페이지에는 부스컷(이미지)가 삽입되어있는지 아닌지에 따라서 따와야 하는 css셀렉터가 다릅니다.(가로열, 세로열 길이 값이 다르므로)
    따라서 가져와야할 css셀렉터를 리스트로 입력해두고 반복문 처리를 통해 갖고 오기로 합니다.
    필요한 것은 부스의 정보이며, 가져오는 순서는 크게 중요하지 않기 때문에(뷰어에서 따로 볼 것이므로) 갖고오는 순서대로 append합니다.
    '''

    #가져올 css셀렉터를 리스트로 선언하고 빈 데이터프레임을 생성.
    div_list = ["div > div > div.col-sm-8.col-12","div > div > div.col-sm-12.col-12"]
    save_df = pd.DataFrame(columns=['부스명','대표자','부스',"대표 작품(원작)","그 외 다루는 작품",'쁘띠존','캐릭터','커플링','커플링 성향','그 외 커플링','매체'])

    '''
    반복문으로 부스데이터들을 리스트로 1차로 변환. 출력되는 형태 중,  key: value 형식으로 표형해야 하는 string값이 있으므로 리스트에서 
    딕셔너리 형태로 변환합니다.
    그 후 딕셔너리의 key값과 데이터프레임의 열 값을 매치하여 한 행 씩 빈 데이터프레임에 추가합니다. 
    '''
    for div_element in div_list:
        booth_titles = driver.find_elements_by_css_selector(div_element) #div_element는 line22에 있는 리스트의 원소들.


        #리스트 초기화, 앞에 리스트 추가하기
        temp_list = []
        string_list = ["부스명"]


        for i in booth_titles: #한 부스마다 기준으로 돌아가는 반복문.
            raw_text = i.text
            # print(raw_text)

            temp_list = raw_text.split("\n") #줄바꿈을 기준으로 리스트에 한 element씩 부여.
            # print(temp_list)

            #리스트에 element 쭉 돌면서 : 있으면 나눠서 새 리스트에 입력, 없으면 구분자로 나눈 추가 작업을 거친 후  새 리스트에append.
            first_list = [] #새로 입력할 리스트. 여기에는 구분자가 나뉘어져 있는걸 한번만 슬라이스한 것과 원래 있던것들을 집어넣습니다.


            list_len = len(temp_list)
            list_range = range(0,list_len)



            for current_list_number in list_range: #리스트 반복문으로 돌면서 : 이 있으면 구분자로 슬라이싱후(1회만) 새 리스트에 추가하기.
                if ":" in temp_list[current_list_number]:
                    divide_list = temp_list[current_list_number].split(":",1)
                    for i in range(0,2): #구분자로 2개로 나뉘어졌으므로 반복문으로 하나씩 추가.
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

            # 리스트의 element들의 앞뒤 공백을 제거하기 위해 반복문으로 element를 돌면서 공백 삭제후, 새로운 리스트에 하나씩 추가합니다.
            for i in range(0,len(second_list)):
                temp_string = second_list[i].strip()
                final_list.append(temp_string)
            # print(final_list) #전체 리스트 확인


            # 딕셔너리로 만들기 위해 홀수번째 element는 key값으로, 짝수번째 element는 value값으로 나눠서 리스트를 만든 후 zip을 통해 딕셔너리를 생성
            key_index = final_list[0::2]
            value_index = final_list[1::2]
            # print("key:",key_index)
            # print("value:",value_index)

            dict_list= dict(zip(key_index,value_index))
            # print(dict_list)

            #딕셔너리의 key값과 데이터프레임의 열 값을 매치하면서 한 행씩 데이터프레임에 값을 추가합니다.
            save_df.loc[len(save_df)] = dict_list


    print(save_df.head(10))
    save_df.to_csv(str(currunt_event)+"_booth_data.csv",encoding="utf-8-sig")






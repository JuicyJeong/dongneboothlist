from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import random
import time

import pandas as pd
import math



def sleep_random_sec(min, max):
    randfloat = random.uniform(min,max)
    time.sleep(randfloat)



def get_twitter_user_data(driver, input_ID):
    #####init#####
    account_name = ""
    num_of_follower=0
    tweet_content = ""
    num_of_retweeted =0
    num_of_liked = 0
    num_of_exposed = 0
    user_twitter_ID = input_ID
    #####init#####

    driver.get(url='https://twitter.com/'+user_twitter_ID)
    sleep_random_sec(6,15)
    try:
        a = driver.find_elements(By.CLASS_NAME,'css-1qaijid.r-bcqeeo.r-qvutc0.r-poiln3')
        num_of_follower = driver.find_element(By.CSS_SELECTOR,PAGE_Account_info_Num_of_follower).text
        # if '만' in num_of_follower:
        #     print("계정 단위가 만이 넘어서... 숫자로 변환합니다.")
        #     num_of_follower = float(num_of_follower[:-1]) * 10000

        # first_tweet_text = driver.find_element(By.CSS_SELECTOR, turtle_selectors['articles'])
        # print('turtle test: ', first_tweet_text.text)
        # first_tweet_text = first_tweet_text.find_element(By.CSS_SELECTOR, turtle_selectors['tweet_div'])
        # print('turtle test: ', first_tweet_text.text)
        # first_tweet_text = first_tweet_text.find_elements(By.CSS_SELECTOR, turtle_selectors['spans'])
        # print('turtle test: ', first_tweet_text.text)
        # first_tweet_text = ''.join(list(map(lambda x: x.text, list(first_tweet_text))))
        # print('turtle test: ', first_tweet_text.text)

        first_tweet_info = driver.find_element(By.CSS_SELECTOR,PAGE_Account_info_First_tweet_info)
        raw_tweet_data = first_tweet_info.text
        sliced_data = raw_tweet_data.split('\n') #%%%%%%%%%%%%%%%%%%%%%%% 여기 트윗이 있고 없고에 따라 다른 열에 값이 들어가는 버그가 발생. 이거 나중에 보수해야함. 급하니깐 일단 돌려
        # print(len(sliced_data))

        if(sliced_data[0] == '메인에 올림'):
            del sliced_data[0]
        # 앞의 정보 4개는 날릴것들. 그 다음 트윗 내용은 슬라이스가 가변적으로 되기 때문에 뒤의 접근을 

        account_name =  sliced_data[0]

        tweet_content = ""
        for i in range(4,len(sliced_data)-4):
            tweet_content =  tweet_content + sliced_data[i]

        num_of_retweeted = sliced_data[-3]
        # if "천" in num_of_retweeted:
        #     num_of_retweeted = float(num_of_retweeted[:-1])*1000
        # elif "만" in num_of_retweeted:
        #     num_of_retweeted = float(num_of_retweeted[:-1])*10000

        num_of_liked = sliced_data[-2]
        num_of_exposed = sliced_data[-1]
    except Exception as e:
        print("SYSTEM: 에러가 발생했습니다. 해당 계정의 정보를 로드할 수 없습니다. 계정이 플텍이거나 다른 이유로 계정을 확인할 수 없습니다. 다음으로 넘어갑니다.")
        pass

    else:
        # print(first_tweet_info.text)
        print(f'이 계정의 계정명은 {account_name}')
        print(user_twitter_ID, "의 계정 팔로워수는: " , num_of_follower)
        print(f'해당 트윗의 내용:\n{tweet_content}')
        print(f'해당 트윗의 리트윗 수:{num_of_retweeted},\n해당 트윗의 마음 수:{num_of_liked},\n해당트윗의 노출 수: {num_of_exposed}')
        '''
        \n으로 나눈다고 치면, 
        '''
        sleep_random_sec(6,13)
    
    return account_name, num_of_follower, tweet_content, num_of_retweeted, num_of_liked, num_of_exposed





'''
# const string
로그인 페이지1 아이디 입력 필드: r-30o5oe.r-1dz5y72.r-13qz1uu.r-1niwhzg.r-17gur6a.r-1yadl64.r-deolkf.r-homxoj.r-poiln3.r-7cikom.r-1ny4l3l.r-t60dpp.r-fdjqy7
로그인 페이지2 - 비밀번호 입력:  r-30o5oe.r-1dz5y72.r-13qz1uu.r-1niwhzg.r-17gur6a.r-1yadl64.r-deolkf.r-homxoj.r-poiln3.r-7cikom.r-1ny4l3l.r-t60dpp.r-fdjqy7
계정 페이지 - 팔로워(CSS셀렉터):#react-root > div > div > div.css-175oi2r.r-13qz1uu.r-417010.r-18u37iz > main > div > div > div > div > div > div:nth-child(3) > div > div > div > div > div.css-175oi2r.r-13awgt0.r-18u37iz.r-1w6e6rj > div:nth-child(2) > a > span.css-1qaijid.r-bcqeeo.r-qvutc0.r-poiln3.r-1b43r93.r-1cwl3u0.r-b88u0q > span
계정 페이지 - 첫번째 트윗: #react-root > div > div > div.css-175oi2r.r-13qz1uu.r-417010.r-18u37iz > main > div > div > div > div > div > div:nth-child(3) > div > div > section > div > div > div:nth-child(1)

첫번째 트윗 내용: main > div > div > div > div > div > section > div > div > div:nth-child(1) > div > div > article > div > div > div:nth-child(3) > div:nth-child(1)



엄휘용
---

driver.find_element(By.CSS_SELECTOR, ???)

article들 (article하나는 트윗 하나를 가짐):
'article'

An article 중 트윗 내용을 담은 div를 select (div는 text span과 img span을 가짐)
'& > .css-175oi2r.r-eqz5dr.r-16y2uox.r-1wbh5a2 > .css-175oi2r.r-16y2uox.r-1wbh5a2.r-1ny4l3l > .css-175oi2r.r-18u37iz > .css-185oi2r.r-1iusvr4.r-16y2uox.r-1777fci.r-kzbkwu > .css-175oi2r:not(.r-zl2h9q) > .css-1rynq56.r-8akbws.r-krxsd3.r-dnmrzs.r-1udh08x.r-bcqeeo.r-qvutc0.r-37j5jr.r-a023e6.r-rjixqe.r-16dba41.r-bnwqim'

find_elements(By.CSS_SELECTOR, 'span')
'''
PAGE_login_field = 'r-30o5oe.r-1dz5y72.r-13qz1uu.r-1niwhzg.r-17gur6a.r-1yadl64.r-deolkf.r-homxoj.r-poiln3.r-7cikom.r-1ny4l3l.r-t60dpp.r-fdjqy7'
PAGE_Account_info_Num_of_follower = '#react-root > div > div > div.css-175oi2r.r-13qz1uu.r-417010.r-18u37iz > main > div > div > div > div > div > div:nth-child(3) > div > div > div > div > div.css-175oi2r.r-13awgt0.r-18u37iz.r-1w6e6rj > div:nth-child(2) > a > span.css-1qaijid.r-bcqeeo.r-qvutc0.r-poiln3.r-1b43r93.r-1cwl3u0.r-b88u0q > span'
PAGE_Account_info_First_tweet_info = '#react-root > div > div > div.css-175oi2r.r-13qz1uu.r-417010.r-18u37iz > main > div > div > div > div > div > div:nth-child(3) > div > div > section > div > div > div:nth-child(1)'
turtle_selectors = {
    'articles': 'article',
    'tweet_div': '& > .css-175oi2r.r-eqz5dr.r-16y2uox.r-1wbh5a2 > .css-175oi2r.r-16y2uox.r-1wbh5a2.r-1ny4l3l > .css-175oi2r.r-18u37iz > .css-185oi2r.r-1iusvr4.r-16y2uox.r-1777fci.r-kzbkwu > .css-175oi2r:not(.r-zl2h9q) > .css-1rynq56.r-8akbws.r-krxsd3.r-dnmrzs.r-1udh08x.r-bcqeeo.r-qvutc0.r-37j5jr.r-a023e6.r-rjixqe.r-16dba41.r-bnwqim',
    'spans': 'span',
}


if __name__== '__main__':

    ##############################START##############################
    # 브라우저 꺼짐 방지 옵션
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    # 크롬 드라이버 생성
    driver = webdriver.Chrome(options=chrome_options)

    # 페이지 로딩이 완료될 때 까지 기다리는 코드
    driver.implicitly_wait(3)

    # 사이트 접속하기
    driver.get(url='https://twitter.com/i/flow/login')
    sleep_random_sec(3,5)
    driver.find_element(By.CLASS_NAME,PAGE_login_field).click()

    ##########################################################계정정보 다른곳에 넣기################################################################
    ##########################################################계정정보 다른곳에 넣기################################################################
    driver.find_element(By.CLASS_NAME,PAGE_login_field).send_keys("YOUR_ACCOUNT")
    ##########################################################계정정보 다른곳에 넣기################################################################
    ##########################################################계정정보 다른곳에 넣기################################################################

    driver.find_element(By.CLASS_NAME,PAGE_login_field).send_keys(Keys.ENTER)
    driver.implicitly_wait(3)
    sleep_random_sec(3,5)

    driver.find_element(By.CLASS_NAME,PAGE_login_field).click()

    ##########################################################계정정보 다른곳에 넣기################################################################
    ##########################################################계정정보 다른곳에 넣기################################################################
    driver.find_element(By.CLASS_NAME,PAGE_login_field).send_keys("YOUR_PASSWORD")
    ##########################################################계정정보 다른곳에 넣기################################################################
    ##########################################################계정정보 다른곳에 넣기################################################################

    driver.find_element(By.CLASS_NAME,PAGE_login_field).send_keys(Keys.ENTER)
    driver.implicitly_wait(2)
    sleep_random_sec(3,6)

    ##############################LOGIN_PHASE_DONE##############################

    data = pd.read_csv('final202404.csv') 
    id_list = data["계정아이디"] #비어있는 값들도 있음


    for i, item in enumerate(id_list[0:],0):
        
        if i > 850:
            print("목표 달성 종료. 루프를 중지합니다.")
            break
        if isinstance(item, float) and math.isnan(item):
            print(f"{i}번째 셀에는 기록된 아이디가 없습니다.")
        else:
            #여기에 값 채워넣으세요.
            ADD_account_name, ADD_num_of_follower, ADD_tweet_content, ADD_num_of_retweeted, ADD_num_of_liked, ADD_num_of_exposed=  get_twitter_user_data(driver,item)
            print(i,'번째 루프...')
            data.loc[i,'계정명'] = ADD_account_name
            data.loc[i,"팔로워수"] = ADD_num_of_follower
            data.loc[i,"최상단트윗_알티"] = ADD_num_of_retweeted
            data.loc[i,"최상단트윗_마음"] = ADD_num_of_liked
            data.loc[i,"최상단트윗_노출수"] = ADD_num_of_exposed
            data.loc[i,"최상단트윗_내용"] = ADD_tweet_content
            # print(data.iloc[i])


    data.to_csv("final202404.csv",index=False,encoding="utf-8-sig")
    print("파일 저장 완료!")



    driver.quit()
    print("프로그램을 종료합니다.")
`



# driver.find_element(By.XPATH,'//*[@id="APjFqb"]').send_keys("tistory")
# driver.find_element(By.XPATH,'//*[@id="APjFqb"]').send_keys(Keys.ENTER)
`
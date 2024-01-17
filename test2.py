import pandas as pd
import math


data = pd.read_csv('get_user_data.csv')

# print(data.head())
# print(data.iloc[0]['계정아이디'])

# account_name, num_of_follower, tweet_content, num_of_retweeted, num_of_liked, num_of_exposed
i = 0
account_name = '랩터14'
num_of_follower = 300
tweet_content = '안녕 나 오늘 밥 이상한거 먹었다.'
num_of_retweeted = 1
num_of_liked = 10
num_of_exposed = 4000


data.loc[i,'계정명'] = account_name
data.loc[i,"팔로워수"] = num_of_follower
data.loc[i,"최상단트윗_알티"] = num_of_retweeted
data.loc[i,"최상단트윗_마음"] = num_of_liked
data.loc[i,"최상단트윗_노출수"] = num_of_exposed
data.loc[i,"최상단트윗_내용"] = tweet_content
print(data.iloc[i])

# print(data.head())

# print(data["계정아이디"])


id_list = data["계정아이디"]
# print(len(id_list))
# print(id_list[0])
print(type(math.isnan(id_list[1052])))



# print(i,",",id_list[i])

for i, item in enumerate(id_list):
    if i > 100:
        break

    if isinstance(item, float) and math.isnan(item):
        print(f"{i}번째 셀에는 값이 없습니다.")
    else:
        print(type(item))





# data.to_csv("final.csv",index=False,encoding="utf-8-sig")
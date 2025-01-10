import pandas as pd
import matplotlib.pyplot as plt
import re
import matplotlib.font_manager as fm


# 폰트 경로 설정 (예: 나눔고딕)
font_path = '/Users/juicy/Library/Fonts/NanumSquareNeoOTF-Rg.otf'
fontprop = fm.FontProperties(fname=font_path)

# CSV 파일 경로 설정
csv_file_path = '24년_9월.csv'  # 여기서 your_file_path_here 부분을 실제 파일 경로로 바꿔주세요.

# CSV 파일 읽기
data = pd.read_csv(csv_file_path)

# 전처리 함수 정의
def preprocess_data(df):
    # 소문자 변환 및 공백 제거
    df['대표 작품(원작)'] = df['대표 작품(원작)'].str.lower().str.strip()

    # 여러 공백을 하나로 줄이기
    df['대표 작품(원작)'] = df['대표 작품(원작)'].replace('\s+', ' ', regex=True)

    # 구분자로 나누기 (쉼표, 슬래시 등)
    split_delimiters = [',', '/', '&', ' and ', ' 및 ']
    pattern = '|'.join(map(re.escape, split_delimiters))
    df['대표 작품(원작)'] = df['대표 작품(원작)'].str.split(pattern)
    df = df.explode('대표 작품(원작)').reset_index(drop=True)

    # 앞뒤 공백 제거
    df['대표 작품(원작)'] = df['대표 작품(원작)'].str.strip()

    # 유사 항목 그룹화 (필요 시 확장 가능)
    df['대표 작품(원작)'] = df['대표 작품(원작)'].replace({
        'jujutsu kaisen': 'jujutsu kaisen', 
        'jujutsukaisen': 'jujutsu kaisen', 
        'jujutsu kaisen ': 'jujutsu kaisen',
        'attack on titan': 'attack on titan',
        'shingeki no kyojin': 'attack on titan',
        'demon slayer': 'demon slayer',
        'kimetsu no yaiba': 'demon slayer'
        # 추가 그룹화를 원한다면 여기에 추가하세요
    })

    return df

# 전처리 실행
data = preprocess_data(data)

# # Day1 데이터 필터링
# day1_data = data[data['개최일'] == 'Day1']

# # 빈도수가 높은 상위 10개 항목 추출
# top_10_works = day1_data['대표 작품(원작)'].value_counts().head(10)

# # 그래프 그리기
# plt.figure(figsize=(10, 6))
# top_10_works.sort_values(ascending=False).plot(kind='bar', color='skyblue')
# plt.title('Top 10 Most Frequent 대표 작품(원작) on Day1 (Sorted by Frequency)')
# plt.xlabel('대표 작품(원작)')
# plt.ylabel('Frequency')
# plt.xticks(rotation=45, ha='right')
# plt.tight_layout()
# plt.show()

# 데이터와 그래프 설정
def plot_top_10_for_day(day):
    day_data = data[data['개최일'] == day]
    top_10_works = day_data['대표 작품(원작)'].value_counts().head(10)
    
    plt.figure(figsize=(10, 6))
    top_10_works.sort_values(ascending=False).plot(kind='bar', color='skyblue')
    plt.title(f'Top 10 Most Frequent 대표 작품(원작) on {day} (Sorted by Frequency)', fontproperties=fontprop)
    plt.xlabel('대표 작품(원작)', fontproperties=fontprop)
    plt.ylabel('Frequency', fontproperties=fontprop)
    plt.xticks(rotation=45, ha='right', fontproperties=fontprop)
    plt.yticks(fontproperties=fontprop)
    plt.tight_layout()
    plt.show()

# Day2 그래프 생성
plot_top_10_for_day('Day2')

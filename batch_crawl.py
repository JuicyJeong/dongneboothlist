import shutil
import subprocess
import pandas as pd

MONTHS = ['24년_1월','24년_4월','24년_7월','24년_9월',
          '25년_1월','25년_4월','25년_7월','25년_10월',
          '26년_1월','26년_4월']

print(f'=== {len(MONTHS)}개월 배치 크롤링 시작 ===\n')

summary = []
for i, m in enumerate(MONTHS, 1):
    print(f'[{i}/{len(MONTHS)}] {m}')
    r1 = subprocess.run(['python3', 'booth_search_total.py', '--date', m],
                        capture_output=True, text=True)
    if r1.returncode != 0:
        print(f'  크롤링 실패: {r1.stderr[-200:]}')
        continue
    r2 = subprocess.run(['python3', 'preprocess_twitter.py',
                        '--input', f'{m}.csv', '--output', f'{m}_clean.csv'],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        print(f'  전처리 실패: {r2.stderr[-200:]}')
        continue
    shutil.copy(f'{m}_clean.csv', f'{m}_부스정보.csv')
    df = pd.read_csv(f'{m}_부스정보.csv', dtype=str).fillna('')
    tw = (df['트위터'] != '').sum()
    seat = (df['위치'] != '').sum()
    summary.append((m, len(df), tw, seat))
    print(f'  부스 {len(df)} | 트위터 {tw} | 위치 {seat}')

print('\n=== 전체 요약 ===')
print(f'{"월":12} {"부스":>5} {"트위터":>6} {"위치":>5}')
print('-' * 35)
total_b = 0
for m, b, t, s in summary:
    print(f'{m:12} {b:>5} {t:>6} {s:>5}')
    total_b += b
print('-' * 35)
print(f'{"합계":12} {total_b:>5}')

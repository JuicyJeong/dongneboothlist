import shutil
import subprocess
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
CRAWLER = ROOT_DIR / "src" / "crawl" / "booth_search_total.py"
PREPROCESSOR = ROOT_DIR / "src" / "pipeline" / "preprocess_twitter.py"
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

MONTHS = ['24년_1월','24년_4월','24년_7월','24년_9월',
          '25년_1월','25년_4월','25년_7월','25년_10월',
          '26년_1월','26년_4월']

print(f'=== {len(MONTHS)}개월 배치 크롤링 시작 ===\n')

summary = []
for i, m in enumerate(MONTHS, 1):
    print(f'[{i}/{len(MONTHS)}] {m}')
    r1 = subprocess.run(['python3', str(CRAWLER), '--date', m],
                        capture_output=True, text=True)
    if r1.returncode != 0:
        print(f'  크롤링 실패: {r1.stderr[-200:]}')
        continue
    raw_path = RAW_DIR / f'{m}.csv'
    clean_path = PROCESSED_DIR / f'{m}_clean.csv'
    booth_path = PROCESSED_DIR / f'{m}_부스정보.csv'
    r2 = subprocess.run(['python3', str(PREPROCESSOR),
                        '--input', str(raw_path), '--output', str(clean_path)],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        print(f'  전처리 실패: {r2.stderr[-200:]}')
        continue
    shutil.copy(clean_path, booth_path)
    df = pd.read_csv(booth_path, dtype=str).fillna('')
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

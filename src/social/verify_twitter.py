import random
import time
from pathlib import Path

import pandas as pd
from collections import Counter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ROOT_DIR = Path(__file__).resolve().parents[2]
INPUT = ROOT_DIR / 'data' / 'processed' / '26년_7월_clean.csv'
OUTPUT = ROOT_DIR / 'artifacts' / 'social' / 'twitter_validity_sample.csv'
SAMPLE_N = 40
SEED = 42

df = pd.read_csv(INPUT, dtype=str).fillna('')

handles = []
for v in df['트위터']:
    for h in v.split(','):
        h = h.strip()
        if h and not h.startswith('bsky:'):
            handles.append(h)
unique = sorted(set(handles))
print(f'고유 트위터 핸들 수: {len(unique)}')
print(f'샘플링: {SAMPLE_N}개 (seed={SEED})')

random.seed(SEED)
sample = random.sample(unique, min(SAMPLE_N, len(unique)))

opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')
opts.add_argument('--disable-blink-features=AutomationControlled')

driver = webdriver.Chrome(options=opts)


def classify(handle):
    try:
        driver.get(f'https://twitter.com/{handle}')
        title = ''
        for _ in range(8):
            time.sleep(1.5)
            title = driver.title or ''
            tl = title.lower()
            if title and '프로필' not in title and 'log in' not in tl and 'x -' not in tl:
                break
        body_el = driver.find_element(By.TAG_NAME, 'body')
        body = body_el.text
        body_low = body.lower()
        title_low = title.lower()
        if f'@{handle}'.lower() in title_low:
            if '비공개' in body or 'protected' in body_low or 'only approved followers' in body_low:
                return 'protected', title
            return 'valid', title
        if 'unable to show this account' in body_low or 'may be private, deleted' in body_low:
            return 'restricted', title
        if 'suspended' in body_low or '일시적으로' in body or 'x rules' in body_low:
            return 'suspended', title
        if "doesn't exist" in body_low or '존재하지 않' in body or 'try searching' in body_low:
            return 'not_found', title
        return 'unknown', title
    except Exception as e:
        return f'error:{type(e).__name__}', ''


results = []
for i, h in enumerate(sample, 1):
    status, title = classify(h)
    print(f'[{i:2d}/{len(sample)}] {h:25s} -> {status}')
    results.append({'handle': h, 'status': status, 'title': title})
    time.sleep(random.uniform(1.5, 3.0))

driver.quit()

out = pd.DataFrame(results)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUTPUT, index=False, encoding='utf-8-sig')

print()
print('=== 요약 ===')
for k, v in Counter(r['status'] for r in results).most_common():
    print(f'  {k}: {v}')
print(f'결과 저장: {OUTPUT}')

import argparse
import json
import os
import random
import re
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT_DIR / 'data' / 'processed'
CACHE_DIR = ROOT_DIR / 'data' / 'cache'

INPUT = PROCESSED_DIR / '26년_7월_clean.csv'
OUTPUT = PROCESSED_DIR / '26년_7월_clean.csv'
CACHE = CACHE_DIR / 'twitter_followers_cache.json'

COUNT_RE = re.compile(r'^([\d.]+)\s*(천|만|K|M|B)?$')
FOLLOWER_TEXT_RE = re.compile(r'([\d,.]+[천만KMB]?)\s*팔로워')


def parse_count(s):
    if not s:
        return None
    s = s.strip().replace(',', '').replace(' ', '')
    m = COUNT_RE.match(s)
    if not m:
        return None
    try:
        n = float(m.group(1))
    except ValueError:
        return None
    mult = {'천': 1e3, '만': 1e4, 'K': 1e3, 'M': 1e6, 'B': 1e9}.get(m.group(2), 1)
    return int(n * mult)


def get_followers(driver, handle):
    try:
        driver.get(f'https://twitter.com/{handle}')
        title = ''
        for _ in range(8):
            time.sleep(1.5)
            title = driver.title or ''
            tl = title.lower()
            if title and '프로필' not in title and 'log in' not in tl and 'x -' not in tl:
                break
        body = driver.find_element(By.TAG_NAME, 'body').text
        body_low = body.lower()
        if f'@{handle}'.lower() not in title.lower():
            if 'unable to show this account' in body_low or 'may be private, deleted' in body_low:
                return None, 'restricted'
            if 'suspended' in body_low or 'x rules' in body_low:
                return None, 'suspended'
            if "doesn't exist" in body_low or '존재하지 않' in body or 'try searching' in body_low:
                return None, 'not_found'
            return None, 'unknown'
        try:
            el = driver.find_element(By.CSS_SELECTOR, '[data-testid="followers"]')
            cnt = parse_count(el.text)
            if cnt is not None:
                return cnt, 'ok'
        except Exception:
            pass
        m = FOLLOWER_TEXT_RE.search(body)
        if m:
            cnt = parse_count(m.group(1))
            if cnt is not None:
                return cnt, 'ok'
        return None, 'no_count'
    except Exception as e:
        return None, f'error:{type(e).__name__}'


def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='고유 계정 중 상위 N개만 처리(테스트용). 0=전체')
    ap.add_argument('--no-headless', action='store_true', help='브라우저 창 표시')
    args = ap.parse_args()

    df = pd.read_csv(INPUT, dtype=str).fillna('')

    handles = []
    for v in df['트위터']:
        for h in v.split(','):
            h = h.strip()
            if h and not h.startswith('bsky:'):
                handles.append(h)
    unique = sorted(set(handles))
    if args.limit > 0:
        unique = unique[:args.limit]
    print(f'고유 트위터 핸들: {len(unique)}개 (bsky 제외)')

    cache = load_cache()
    todo = [h for h in unique if h not in cache]
    print(f'캐시 확보: {len(unique) - len(todo)} / 미처리: {len(todo)}')

    opts = Options()
    if not args.no_headless:
        opts.add_argument('--headless=new')
    opts.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')
    opts.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=opts)
    start = time.time()
    for i, h in enumerate(todo, 1):
        cnt, status = get_followers(driver, h)
        cache[h] = {'followers': cnt, 'status': status}
        elapsed = int(time.time() - start)
        rate = elapsed / i if i else 0
        eta = int(rate * (len(todo) - i))
        disp = cnt if cnt is not None else '-'
        print(f'[{i:4d}/{len(todo)}] {h:25s} fol={disp!s:>8} ({status}) elapsed={elapsed}s eta={eta}s')
        if i % 20 == 0:
            save_cache(cache)
        time.sleep(random.uniform(1.0, 2.5))
    save_cache(cache)
    driver.quit()

    ok = sum(1 for v in cache.values() if v.get('status') == 'ok')
    print(f'\n크롤링 완료: 확보 {ok} / {len(cache)}')

    fol_col, miss_col = [], []
    for v in df['트위터']:
        parts = [p.strip() for p in v.split(',') if p.strip()]
        tw = [p for p in parts if not p.startswith('bsky:')]
        total = 0
        miss = 0
        for h in tw:
            rec = cache.get(h)
            if rec and rec.get('followers') is not None:
                total += rec['followers']
            else:
                miss += 1
        fol_col.append(total if tw else '')
        miss_col.append(miss if tw else 0)

    if '팔로워수' in df.columns:
        df = df.drop(columns=['팔로워수'])
    if '미확보수' in df.columns:
        df = df.drop(columns=['미확보수'])
    insert_at = df.columns.get_loc('트위터') + 1
    df.insert(insert_at, '팔로워수', fol_col)
    df.insert(insert_at + 1, '미확보수', miss_col)
    df.to_csv(OUTPUT, index=False, encoding='utf-8-sig')

    print(f'\n저장 완료: {OUTPUT}')
    print(f"  팔로워수 합(확보 행): {sum(x for x in fol_col if x != '')}")
    print(f'  미확보 계정 포함 행: {sum(1 for x in miss_col if x)}')


if __name__ == '__main__':
    main()

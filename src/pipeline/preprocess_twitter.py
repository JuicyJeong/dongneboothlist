import argparse
import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / 'data' / 'raw'
PROCESSED_DIR = ROOT_DIR / 'data' / 'processed'

ap = argparse.ArgumentParser()
ap.add_argument('--input', default=RAW_DIR / '26년_7월.csv', type=Path)
ap.add_argument('--output', default=PROCESSED_DIR / '26년_7월_clean.csv', type=Path)
args = ap.parse_args()
INPUT = args.input
OUTPUT = args.output

CONTROL_RE = re.compile(r'[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]')
TWITTER_HANDLE_RE = re.compile(r'^[A-Za-z0-9_]+$')
TWITTER_URL_RE = re.compile(r'(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)')
BSKY_DOMAIN_RE = re.compile(r'([A-Za-z0-9._-]+)\.bsky\.social', re.IGNORECASE)
BSKY_PATH_RE = re.compile(r'bsky\.social/profile/([A-Za-z0-9._-]+)', re.IGNORECASE)


def normalize_token(s):
    s = s.strip().lstrip('@').strip()
    if not s:
        return ''
    m = BSKY_PATH_RE.search(s) or BSKY_DOMAIN_RE.search(s)
    if m:
        return 'bsky:' + m.group(1)
    m = TWITTER_URL_RE.search(s)
    if m:
        return m.group(1)
    return s


def is_valid(token):
    if token.startswith('bsky:'):
        return bool(re.fullmatch(r'bsky:[A-Za-z0-9._-]+', token))
    return bool(TWITTER_HANDLE_RE.fullmatch(token))


def clean_handle(raw):
    if raw is None:
        return ''
    s = str(raw).strip()
    if not s or s.lower() == 'nan':
        return ''
    s = CONTROL_RE.sub('', s)
    s = re.sub(r'[,/]', ' ', s)
    tokens = [normalize_token(t) for t in s.split()]
    tokens = [t for t in tokens if is_valid(t)]
    return ', '.join(tokens)


df = pd.read_csv(INPUT, dtype=str).fillna('')

before = df['트위터'].copy()
df['트위터'] = before.apply(clean_handle)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False, encoding='utf-8-sig')

total = len(df)
filled_after = (df['트위터'] != '').sum()
multi = df['트위터'].str.contains(',').sum()
bsky = df['트위터'].str.contains('bsky:').sum()

first = df['트위터'][df['트위터'] != ''].str.split(',').str[0].str.strip()
valid = first.apply(lambda x: is_valid(x))
at_remaining = df['트위터'].str.startswith('@').sum()
url_remaining = df['트위터'].str.contains('http', case=False).sum()
non_ascii = df['트위터'].apply(lambda x: any(ord(c) > 127 for c in x)).sum()

print(f"입력: {INPUT}")
print(f"출력: {OUTPUT}")
print(f"총 행수: {total}")
print(f"값 있음(before 1128): {filled_after}")
print(f"@ 로 시작: 782 -> {at_remaining}")
print(f"URL 포함: 4 -> {url_remaining}")
print(f"비ASCII(한글 등) 포함: {non_ascii}")
print(f"첫 계정 유효: {valid.sum()} / {len(first)}")
print(f"다중 계정(쉼표): {multi}행")
print(f"Bluesky 계정(bsky:): {bsky}행")
print()
print("=== 정제 후 다중 계정 샘플 ===")
for _, r in df[df['트위터'].str.contains(',')].head(5).iterrows():
    print(f"{r['부스명'][:18]:18s} -> {r['트위터']}")
print()
print("=== Bluesky 계정 샘플 ===")
for _, r in df[df['트위터'].str.contains('bsky:')].head(5).iterrows():
    print(f"{r['부스명'][:18]:18s} -> {r['트위터']}")

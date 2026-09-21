#!/usr/bin/env python3
"""
WORK_DICTIONARY.json v1.0 → v1.1 갱신 스크립트 (JWMI-4)

변경 원칙:
  - 기존 W#### 코드 재사용·재매핑 금지, 신규 작품은 W0212부터 순차 부여
  - 별칭 추가는 기존 aliases/abbreviations에 중복 없이 병합
  - 미확인 항목은 review_needed: true 표기
  - metadata.noise_terms 신설 (작품이 아닌 굿즈/장르 표기) — normalize_works가 참조

사용법:
  python3 scripts/build_v1_1.py            # WORK_DICTIONARY.json 갱신
  python3 scripts/build_v1_1.py --dry-run  # 변경 요약만 출력
"""

import argparse
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
DICT_PATH = os.path.join(BASE_DIR, "WORK_DICTIONARY.json")
CHANGESET_PATH = os.path.join(BASE_DIR, "analysis", "v1.1_changeset.json")


# ============================================================
# 1. 기존 작품 별칭 추가 (code → 별칭 목록)
# ============================================================

ALIAS_ADDITIONS = {
    "W0001": ["슬랭덩크"],
    "W0004": ["데뷔못하면죽는병", "데뷔못하면죽음", "데뷔 못하면 죽는 병",
              "데뷔 못 하면 죽은 병에 걸림"],
    "W0006": ["게토고죠"],
    "W0007": ["아이돌리쉬7"],
    "W0013": ["진혼"],
    "W0018": ["스타레일", "붕스타"],
    "W0019": ["트라이건 스탬피드", "Trigun Stampede"],
    "W0021": ["코난", "명탐점 코난"],
    "W0025": ["닌타마", "닌타마 란타로"],
    "W0029": ["발더게3", "발더스게이트3"],
    "W0030": ["히프스테", "룰 더 스테이지"],
    "W0034": ["니지산지 JP"],
    "W0037": ["페그오"],
    "W0041": ["페르소나"],
    "W0047": ["히로아카"],
    "W0049": ["파판14", "파판", "FF14", "FFXIV"],
    "W0050": ["가히리"],
    "W0053": ["WIND BREAKER", "WINDBREAKER", "윈드브레이커(일본 만화 표기)"],
    "W0058": ["의다살", "의원 다시 살다", "의원"],
    "W0065": ["섭남파업"],
    "W0067": ["유희왕GX", "유희왕 브레인즈", "유희왕 VRAINS", "유희왕 고러시!!",
              "유희왕 ZEXAL", "유희왕 5D's"],
    "W0068": ["해즈빈호텔"],
    "W0071": ["백망되"],
    "W0073": ["썬더일레븐", "이나즈마일레븐GO", "이나즈마 일레븐 GO"],
    "W0075": ["하츠네 미쿠", "하츠네미쿠", "미쿠"],
    "W0077": ["사카데이", "사카모토데이즈"],
    "W0079": ["도리벤"],
    "W0083": ["에리오스"],
    "W0089": ["신비한 동물사전"],
    "W0094": ["겁쟁이페달"],
    "W0101": ["콜옵", "콜오브"],
    "W0109": ["디지몬 어드벤처", "DIGIMON ADVENTURE"],
    "W0114": ["역전재판5", "역전재판1~4", "역전검사", "역전재판 후기"],
    "W0119": ["가면라이더 류우키", "가면라이더 기츠", "가면라이더 지오",
              "가면라이더 위자드", "가면라이더 더블", "가면라이더 W", "가면라이더 빌드"],
    "W0125": ["DX3rd"],
    "W0123": ["GM시리즈", "클로저이상용", "클로저 이상용"],
    "W0124": ["킹프리"],
    "W0132": ["월한강천록: 무림제일폐", "월한강천록"],
    "W0137": ["탑로더", "탑꾸"],
    "W0139": ["케데헌", "KPop Demon Hunters"],
    "W0144": ["from 아르고나비스", "아르고나비스"],
    "W0148": ["건담시드", "기동전사 건담 SEED", "기동전사 건담 철혈의 오펀스",
              "퍼스트 건담"],
    "W0151": ["포켓몬스터SV", "포켓몬 SV"],
    "W0153": ["카이지", "도박묵시록 카이지"],
    "W0155": ["마도서대전 TRPG 마기카로기아"],
    "W0159": ["Fate/Samurai Remnant", "페이트 사무라이 렘넌트", "페이트 스트레인지 페이크"],
    "W0160": ["프리티 시리즈"],
    "W0165": ["게게게의 수수께끼"],
    "W0172": ["망아살"],
    "W0184": ["뉴단간론파V3", "뉴 단간론파 V3", "단간론파 어나더"],
    "W0185": ["봇치더록"],
    "W0191": ["아머드코어6 루비콘의 화염"],
    "W0197": ["헬루바보스", "헬루바 보스"],
    "W0070": ["문송안함", "문송"],
    "W0206": ["실크송", "Silksong"],
}

# 별칭 추가 시 같이 달 note (선택)
ALIAS_NOTES = {
    "W0004": "띄어쓰기·오타 변형 통합",
    "W0006": "게토고죠는 캐릭터명 표기 → 소속 작품 매핑",
    "W0013": "'진혼'은 진혼기 약칭 추정(진혼기 반월당 병기 셀 근거)",
    "W0053": "일본 만화 WIND BREAKER(윈드 브레이커)와 한글 표기 충돌 — 부스 데이터 표기는 W0053으로 통일 매핑, 세부 확인 필요 시 review",
    "W0058": "작품명 내 콤마('의원, 다시 살다')로 인한 분리 실패 대응",
    "W0067": "하위 시리즈 표기 통칭",
    "W0079": "도리벤은 도쿄 리벤저스 약칭 (2026-09-21 웹 검증)",
    "W0114": "시리즈 번호·스핀오프 표기 통칭",
    "W0119": "하위 시리즈 표기 통칭",
    "W0123": "최훈의 GM 시리즈(GM·클로저이상용·프로야구생존기) 통칭",
    "W0153": "후쿠모토 노부유키 작품 통칭(아카기는 W0180 별도 코드)",
    "W0159": "하위 시리즈 표기 통칭",
    "W0160": "프리티 시리즈(프리파라·킹 오브 프리즘 등) 통칭",
    "W0184": "단간론파 어나더는 한국 팬메이드 시리즈 포함 통칭",
    "W0206": "Hollow Knight: Silksong 후속작 포함 통칭 매핑",
}


# ============================================================
# 2. 기존 항목 정정 (code → 변경 필드)
# ============================================================

FIXES = {
    "W0117": {
        "origin": "cn",
        "notes": "중국 작가 priest(핀푸)의 杀破狼(살파랑). v1.0의 kr 표기 정정 (2026-09-21 웹 검증, namu.wiki)",
    },
    # v1.0 별칭 정리: 다른 코드의 canonical과 중복되거나 잘못 귀속된 별칭 제거
    "W0027": {"_remove_aliases": ["역전재판 시리즈"],
              "notes": "'역전재판 시리즈' 표기는 W0114 canonical과 중복 → 제거"},
    "W0208": {"_remove_aliases": ["Grey City", "회색도시"],
              "notes": "'회색도시'·'Grey City'는 W0157 canonical과 중복 → 제거 (회색도시2 유지)"},
    "W0177": {"_remove_aliases": ["아이엠스타", "캐릭캐릭체인지(아이엠스타)"],
              "notes": "v1.0 데이터 오류 정정: '아이엠스타'는 아이카츠!의 한국 더빙 제목 → W0240 아이카츠!로 귀속 (2026-09-21 웹 검증, namu.wiki)"},
}


# ============================================================
# 3. 신규 작품 (W0212~ 순차 부여)
# ============================================================

NEW_WORKS = [
    # --- 일본 만화 ---
    {"canonical_name": "귀멸의 칼날", "origin": "jp", "category": "manga",
     "aliases": ["귀멸의칼날", "Demon Slayer"]},
    {"canonical_name": "가치아쿠타", "origin": "jp", "category": "manga",
     "aliases": ["Gachiakuta"]},
    {"canonical_name": "강철의 연금술사", "origin": "jp", "category": "manga",
     "aliases": ["하가렌", "Fullmetal Alchemist"]},
    {"canonical_name": "이누야샤", "origin": "jp", "category": "manga", "aliases": []},
    {"canonical_name": "원펀맨", "origin": "jp", "category": "manga",
     "aliases": ["One Punch Man"]},
    {"canonical_name": "최애의 아이", "origin": "jp", "category": "manga",
     "aliases": ["최애의아이"]},
    {"canonical_name": "히카루가 죽은 여름", "origin": "jp", "category": "manga",
     "aliases": ["히카루가죽은여름"]},
    {"canonical_name": "히카루의 바둑", "origin": "jp", "category": "manga",
     "aliases": ["히카루노 고"]},
    {"canonical_name": "킹덤", "origin": "jp", "category": "manga", "aliases": []},
    {"canonical_name": "코우노도리", "origin": "jp", "category": "manga",
     "aliases": ["コウノドリ"], "notes": "산부인과 의료 만화 (스즈노키 유우)"},
    {"canonical_name": "텐~천화거리의 쾌남아~", "origin": "jp", "category": "manga",
     "aliases": ["天 天和通りの快男児", "텐 천화거리의 쾌남아"],
     "notes": "후쿠모토 노부유키 마작 만화"},
    {"canonical_name": "천막의 자두가르", "origin": "jp", "category": "manga",
     "aliases": ["天幕のジャードゥーガル"],
     "notes": "토마토 수프 작 만화, 애니메이션화 (2026-09-21 웹 검증)"},
    {"canonical_name": "히스토리에", "origin": "jp", "category": "manga", "aliases": []},
    {"canonical_name": "고깔모자의 아틀리에", "origin": "jp", "category": "manga",
     "aliases": ["とんがり帽子のアトリエ", "Witch Hat Atelier"],
     "notes": "만화. 게임 '아틀리에 시리즈'와 별개 작품"},
    {"canonical_name": "블러디 메리", "origin": "jp", "category": "manga",
     "aliases": ["블러디+메리", "ブラッディ・メアリ"], "notes": "사마미야 아카라 만화"},
    {"canonical_name": "충사", "origin": "jp", "category": "manga",
     "aliases": ["蟲師", "무시시"],
     "notes": "우루시바라 유키 만화 蟲師의 한국 정발명 (웹툰 아님, 2026-09-21 웹 검증)"},
    {"canonical_name": "다이아몬드의 공죄", "origin": "jp", "category": "manga",
     "aliases": ["ダイヤモンドの咎"],
     "notes": "야구 만화. 다이아몬드 에이스(W0092)와 별개 작품 (2026-09-21 웹 검증)"},
    {"canonical_name": "페어리 테일", "origin": "jp", "category": "manga",
     "aliases": ["페어리테일", "Fairy Tail"]},
    {"canonical_name": "언데드 언럭", "origin": "jp", "category": "manga",
     "aliases": ["Undead Unluck"]},
    {"canonical_name": "카드캡터 사쿠라", "origin": "jp", "category": "manga",
     "aliases": ["카드캡터사쿠라", "카드캡터체리", "카드캡터 사쿠라(체리)"]},
    {"canonical_name": "너에게 닿기를", "origin": "jp", "category": "manga",
     "aliases": ["너에게닿기를"]},
    {"canonical_name": "케이온!", "origin": "jp", "category": "manga",
     "aliases": ["케이온", "K-ON!"]},
    {"canonical_name": "슈가슈가 룬", "origin": "jp", "category": "manga",
     "aliases": ["슈가슈가룬", "Sugar Sugar Rune"]},
    {"canonical_name": "패밀리 레스토랑 가자.", "origin": "jp", "category": "manga",
     "aliases": ["파미레스가자", "패밀리 레스토랑 가자", "ファミレス行こ。"],
     "notes": "가라오케 가자!(W0097)와 같은 작가(와야마 야마) 속편 (2026-09-21 웹 검증)"},

    # --- 일본 애니메이션/프랜차이즈/특촬 ---
    {"canonical_name": "신세기 에반게리온", "origin": "jp", "category": "franchise",
     "aliases": ["에반게리온", "에바", "신에반", "Evangelion"]},
    {"canonical_name": "코드 기어스: 를루쉬의 반역", "origin": "jp", "category": "franchise",
     "aliases": ["코드기어스", "코드기아스"]},
    {"canonical_name": "걸즈 밴드 크라이", "origin": "jp", "category": "anime",
     "aliases": ["걸즈밴드크라이", "GIRLS BAND CRY"]},
    {"canonical_name": "뱅드림!", "origin": "jp", "category": "franchise",
     "aliases": ["뱅드림", "BanG Dream!", "마이고", "MyGO!!!!!", "아베무지카", "Ave Mujica"],
     "notes": "MyGO!!!!!/Ave Mujica는 뱅드림 프로젝트 유닛"},
    {"canonical_name": "프리큐어 시리즈", "origin": "jp", "category": "franchise",
     "aliases": ["프리큐어", "Precure", "프리시리즈"]},
    {"canonical_name": "아이카츠!", "origin": "jp", "category": "franchise",
     "aliases": ["아이카츠", "아이카츠 스타즈", "아이엠스타", "AIKATSU!"],
     "notes": "아이엠스타는 아이카츠 스타즈 관련 표기 — 세부 확인 필요 시 review"},
    {"canonical_name": "SHOW BY ROCK!!", "origin": "jp", "category": "franchise",
     "aliases": ["쇼바이락", "쇼바이락!!"],
     "notes": "산리오 음악 캐릭터 프로젝트 (2026-09-21 웹 검증)"},
    {"canonical_name": "슈퍼 전대 시리즈", "origin": "jp", "category": "tokusatsu",
     "aliases": ["슈퍼전대", "전대", "기계전대 젠카이저", "임금님전대 킹오저",
                 "파워레인저 킹덤포스"],
     "notes": "하위 시리즈·한국 방영명(파워레인저) 통칭"},
    {"canonical_name": "울트라맨 제트", "origin": "jp", "category": "tokusatsu",
     "aliases": ["울트라맨Z"]},
    {"canonical_name": "사우스파크", "origin": "en", "category": "anime", "aliases": ["South Park"]},
    {"canonical_name": "어메이징 디지털 서커스", "origin": "en", "category": "anime",
     "aliases": ["디지털서커스", "The Amazing Digital Circus"]},

    # --- 영미권 영화/드라마/소설 ---
    {"canonical_name": "스타워즈", "origin": "en", "category": "franchise",
     "aliases": ["만달로리안", "Star Wars"],
     "notes": "만달로리안은 스타워즈 드라마 시리즈"},
    {"canonical_name": "DC 코믹스", "origin": "en", "category": "franchise",
     "aliases": ["DC", "DC코믹스", "배트맨"]},
    {"canonical_name": "위키드", "origin": "en", "category": "movie",
     "aliases": ["Wicked"], "notes": "뮤지컬 원작 영화"},
    {"canonical_name": "오페라의 유령", "origin": "multi", "category": "movie",
     "aliases": ["The Phantom of the Opera"],
     "notes": "가스통 르루 소설 원작, 뮤지컬·영화화"},
    {"canonical_name": "반지의 제왕", "origin": "en", "category": "novel",
     "aliases": ["Lord of the Rings"]},
    {"canonical_name": "존윅", "origin": "en", "category": "movie", "aliases": ["John Wick"]},
    {"canonical_name": "탑건", "origin": "en", "category": "movie", "aliases": ["Top Gun"]},
    {"canonical_name": "수퍼내추럴", "origin": "en", "category": "drama",
     "aliases": ["슈퍼내추럴(Supernatural)", "Supernatural"]},
    {"canonical_name": "거침없이 하이킥!", "origin": "kr", "category": "drama",
     "aliases": ["하이킥"]},

    # --- 버튜버/음악/캐릭터 ---
    {"canonical_name": "홀로라이브", "origin": "jp", "category": "vtuber",
     "aliases": ["홀로라이브 프로덕션", "hololive"]},
    {"canonical_name": "에일리언 스테이지", "origin": "kr", "category": "anime",
     "aliases": ["에일리언스테이지", "에이스테", "ALIEN STAGE"],
     "notes": "VIVINOS 유튜브 애니메이션 시리즈"},
    {"canonical_name": "포밍이와 친구들", "origin": "kr", "category": "meta",
     "aliases": ["포밍이"], "review_needed": True,
     "notes": "한국 캐릭터 IP 추정 — 제작사 세부 확인 필요 (2026-09-21 웹 검증)"},

    # --- 일본 게임 ---
    {"canonical_name": "트위스티드 원더랜드", "origin": "jp", "category": "game",
     "aliases": ["트위스테", "트위원", "디즈니 트위스티드 원더랜드", "Twisted Wonderland"]},
    {"canonical_name": "노래의 왕자님♪", "origin": "jp", "category": "game",
     "aliases": ["우타프리", "우타노 프린스", "うたの☆プリンスさまっ♪"],
     "notes": "여성향 게임 원작 미디어믹스 (2026-09-21 웹 검증)"},
    {"canonical_name": "아이돌 마스터 시리즈", "origin": "jp", "category": "franchise",
     "aliases": ["아이돌 마스터", "아이돌마스터", "아이마스"],
     "notes": "시리즈 통칭. SideM은 W0171 별도 코드"},
    {"canonical_name": "꿈왕국과 잠자는 100명의 왕자님", "origin": "jp", "category": "game",
     "aliases": ["꿈왕국", "꿈100"],
     "notes": "모바일 오토메 게임 (2026-09-21 웹 검증)"},
    {"canonical_name": "블루 아카이브", "origin": "kr", "category": "game",
     "aliases": ["블루아카이브", "Blue Archive", "블아"],
     "notes": "넥슨게임즈 개발"},
    {"canonical_name": "이터널리턴", "origin": "kr", "category": "game",
     "aliases": ["Eternal Return"], "notes": "님뉴넷 개발"},
    {"canonical_name": "메이플스토리", "origin": "kr", "category": "game",
     "aliases": ["메이플"]},
    {"canonical_name": "로스트아크", "origin": "kr", "category": "game",
     "aliases": ["로아"], "notes": "스마일게이트 개발"},
    {"canonical_name": "쿠키런 시리즈", "origin": "kr", "category": "franchise",
     "aliases": ["쿠키런", "쿠키런 킹덤", "쿠키런: 킹덤", "쿠키런 오븐브레이크"],
     "notes": "시리즈 통칭 (데브시스터즈)"},
    {"canonical_name": "마비노기", "origin": "kr", "category": "game",
     "aliases": ["마비노기 모바일", "마비"], "notes": "넥슨(개발 devCAT). 시리즈 통칭"},
    {"canonical_name": "바이오하자드", "origin": "jp", "category": "game",
     "aliases": ["레지던트 이블", "Resident Evil"], "notes": "캡콤 호러 게임"},
    {"canonical_name": "데빌 메이 크라이", "origin": "jp", "category": "game",
     "aliases": ["데빌메이크라이", "Devil May Cry"]},
    {"canonical_name": "다크소울", "origin": "jp", "category": "game",
     "aliases": ["다크 소울", "Dark Souls"]},
    {"canonical_name": "엘든 링", "origin": "jp", "category": "game",
     "aliases": ["엘든링", "Elden Ring"]},
    {"canonical_name": "언더테일", "origin": "en", "category": "game",
     "aliases": ["Undertale"], "notes": "토비 폭스 게임"},
    {"canonical_name": "델타룬", "origin": "en", "category": "game",
     "aliases": ["Deltarune"], "notes": "언더테일과 같은 개발자(토비 폭스)의 후속 작품"},
    {"canonical_name": "몬스터 헌터", "origin": "jp", "category": "game",
     "aliases": ["몬헌", "Monster Hunter"]},
    {"canonical_name": "니어 시리즈", "origin": "jp", "category": "game",
     "aliases": ["니어: 오토마타", "니어 오토마타", "니어 레플리칸트", "NieR"],
     "notes": "시리즈 통칭"},
    {"canonical_name": "더 킹 오브 파이터즈", "origin": "jp", "category": "game",
     "aliases": ["KOF", "킹오브파이터즈", "킹 오브 파이터즈 XV"]},
    {"canonical_name": "동방 프로젝트", "origin": "jp", "category": "franchise",
     "aliases": ["동방프로젝트", "Touhou Project"]},
    {"canonical_name": "아틀리에 시리즈", "origin": "jp", "category": "franchise",
     "aliases": ["아틀리에"],
     "notes": "구스트 게임 시리즈 통칭(로로나 등). 만화 '고깔모자의 아틀리에'는 별개 작품"},
    {"canonical_name": "궤적 시리즈", "origin": "jp", "category": "game",
     "aliases": ["섬의 궤적", "궤적", "Trails series"],
     "notes": "영웅전설 궤적 시리즈 통칭"},
    {"canonical_name": "슈퍼로봇대전 시리즈", "origin": "jp", "category": "game",
     "aliases": ["슈퍼로봇대전", "슈퍼로봇대전OG 문 드웰러즈", "슈퍼로봇대전OG"],
     "notes": "시리즈 통칭"},
    {"canonical_name": "영원한 7일의 도시", "origin": "cn", "category": "game",
     "aliases": ["永远的7日之都"], "notes": "NetEase 모바일 게임"},
    {"canonical_name": "쯔꾸르 게임", "origin": "jp", "category": "meta",
     "aliases": ["쯔꾸르", "쯔꾸르게임", "쯔꾸르RPG", "쯔꾸르 게임"],
     "notes": "RPGツクール계 프리게임 통칭 (Ib·살육의 천사 등은 개별 코드)"},
    {"canonical_name": "Ib", "origin": "jp", "category": "game",
     "aliases": ["ib", "이브"], "notes": "쯔꾸르 프리 호러 게임"},
    {"canonical_name": "살육의 천사", "origin": "jp", "category": "game",
     "aliases": ["Angels of Death"], "notes": "쯔꾸르계 호러 게임"},
    {"canonical_name": "피학의 노엘", "origin": "jp", "category": "game",
     "aliases": ["被虐のノエル"]},
    {"canonical_name": "위치즈 하트", "origin": "jp", "category": "game",
     "aliases": ["위치즈하트", "Witch's Heart"],
     "notes": "쯔꾸르계 프리 호러 RPG (2026-09-21 웹 검증)"},
    {"canonical_name": "안개비가 내리는 숲", "origin": "jp", "category": "game",
     "aliases": ["안개비가내리는숲", "霧雨が降る森"],
     "notes": "쯔꾸르계 호러 게임 (2026-09-21 웹 검증)"},
    {"canonical_name": "무색의 카이나", "origin": "jp", "category": "game",
     "aliases": ["무색의카이나", "無色のカイ나"],
     "notes": "쯔꾸르계 호러 ADV (2026-09-21 웹 검증)"},
    {"canonical_name": "소년기의 끝", "origin": "jp", "category": "game",
     "aliases": ["少年期の終り"],
     "notes": "인디 어드벤처 게임 (2026-09-21 웹 검증)"},
    {"canonical_name": "Lkyt.", "origin": "jp", "category": "game",
     "aliases": ["Lkyt"],
     "notes": "parade 제작 BL 비주얼노벨, 스팀 한국어판 (2026-09-21 웹 검증)"},
    {"canonical_name": "슬로우 데미지", "origin": "jp", "category": "game",
     "aliases": ["슬로우데미지", "Slow Damage"],
     "notes": "N+C(니트로 플러스 치랄) BL 게임"},
    {"canonical_name": "ZENO", "origin": "jp", "category": "game",
     "aliases": ["ZENO (마루토쿠키치)", "마루토쿠키치", "마루토쿠 시리즈"], "review_needed": True,
     "notes": "마루토쿠키치 제작 프리 호러 게임 통칭 추정 (2026-09-21 웹 검증)"},
    {"canonical_name": "HUNDRED LINE -최종방위학원-", "origin": "jp", "category": "game",
     "aliases": ["헌드레드 라인"]},
    {"canonical_name": "문호와 알케미스트", "origin": "jp", "category": "game",
     "aliases": ["문호 알케미스트", "文豪とアルケミスト"],
     "notes": "문호 스트레이 독스(W0129)와 별개 작품"},
    {"canonical_name": "산나비", "origin": "kr", "category": "game",
     "aliases": [],
     "notes": "한국 인디 액션 어드벤처 플랫포머 (2026-09-21 웹 검증)"},
    {"canonical_name": "봄이 오면 꽃이 피고", "origin": "kr", "category": "game",
     "aliases": [],
     "notes": "한국 오토메 연애 어드벤처 게임 (2026-09-21 웹 검증)"},

    # --- 영미권 게임 ---
    {"canonical_name": "발로란트", "origin": "en", "category": "game",
     "aliases": ["VALORANT", "발로"]},
    {"canonical_name": "데드 바이 데이라이트", "origin": "en", "category": "game",
     "aliases": ["데바데", "데드바이데이라이트", "DbD"]},
    {"canonical_name": "에이펙스 레전드", "origin": "en", "category": "game",
     "aliases": ["에펙", "Apex Legends"]},
    {"canonical_name": "데스티니", "origin": "en", "category": "game",
     "aliases": ["데스티니 가디언즈", "데스티니2", "데스티니 가디언즈 2",
                 "데스티니가디언즈2", "Destiny"],
     "notes": "시리즈 통칭"},
    {"canonical_name": "보더랜드", "origin": "en", "category": "game",
     "aliases": ["보더랜드3", "Borderlands"]},
    {"canonical_name": "별의 커비", "origin": "jp", "category": "game",
     "aliases": ["커비", "Kirby"]},
    {"canonical_name": "피크민", "origin": "jp", "category": "game",
     "aliases": ["Pikmin"]},
    {"canonical_name": "리틀 나이트메어", "origin": "en", "category": "game",
     "aliases": ["Little Nightmares"]},
    {"canonical_name": "오모리", "origin": "en", "category": "game",
     "aliases": ["OMORI"]},
    {"canonical_name": "앨런 웨이크", "origin": "en", "category": "game",
     "aliases": ["Alan Wake"]},
    {"canonical_name": "ULTRAKILL", "origin": "en", "category": "game", "aliases": []},
    {"canonical_name": "드래곤 에이지", "origin": "en", "category": "game",
     "aliases": ["드래곤에이지", "Dragon Age"],
     "notes": "바이오웨어 시리즈 통칭"},
    {"canonical_name": "매스이펙트", "origin": "en", "category": "game",
     "aliases": ["Mass Effect"]},
    {"canonical_name": "디트로이트: 비컴 휴먼", "origin": "en", "category": "game",
     "aliases": ["디트로이트 비컴 휴먼", "Detroit: Become Human"]},
    {"canonical_name": "레드 데드 리뎀션", "origin": "en", "category": "game",
     "aliases": ["레드 데드 리뎀션 2", "Red Dead Redemption"]},
    {"canonical_name": "위쳐", "origin": "en", "category": "game",
     "aliases": ["위쳐3", "위처3", "The Witcher"], "notes": "시리즈 통칭"},
    {"canonical_name": "리썰 컴퍼니", "origin": "en", "category": "game",
     "aliases": ["리쎌컴퍼니", "Lethal Company"]},
    {"canonical_name": "던전 앤 드래곤", "origin": "en", "category": "trpg",
     "aliases": ["DnD", "디앤디", "D&D"]},

    # --- TRPG ---
    {"canonical_name": "취록의 플로리아", "origin": "jp", "category": "trpg",
     "aliases": ["翠緑のフローリア"],
     "notes": "일본 TRPG, 한국어판 푸른꽃 출간 (2026-09-21 웹 검증)"},
    {"canonical_name": "인세인", "origin": "jp", "category": "trpg",
     "aliases": ["Insane"],
     "notes": "일본 현대 호러 TRPG 한국어판 (2026-09-21 웹 검증)"},
    {"canonical_name": "블러드패스", "origin": "jp", "category": "trpg",
     "aliases": ["인귀혈맹 RPG 블러드패스", "ブラッドパス"],
     "notes": "아크라이트 TRPG (2026-09-21 웹 검증)"},
    {"canonical_name": "언성 듀엣", "origin": "jp", "category": "trpg",
     "aliases": ["アンサング・デュエット"],
     "notes": "타키자토 후유 TRPG, 초여명 정발 (2026-09-21 웹 검증)"},
    {"canonical_name": "둘이서 수사", "origin": "jp", "category": "trpg",
     "aliases": ["둘이서수사", "ふたりそうさ"],
     "notes": "버디 서스펜스 TRPG, 티알피지클럽 정발 (2026-09-21 웹 검증)"},
    {"canonical_name": "아론의 사제", "origin": "kr", "category": "trpg",
     "aliases": [], "notes": "소율 작 한국 TRPG (2026-09-21 웹 검증)"},

    # --- 중국/한국 웹소설·소설 ---
    {"canonical_name": "묵독", "origin": "cn", "category": "webnovel",
     "aliases": ["默读"], "notes": "중국 작가 priest(핀푸)의 BL 소설"},
    {"canonical_name": "육효", "origin": "cn", "category": "webnovel",
     "aliases": ["六爻"], "notes": "중국 작가 priest(핀푸)의 소설"},
    {"canonical_name": "공포소설 속 조연은 사람으로 살고 싶다", "origin": "kr", "category": "webnovel",
     "aliases": ["공조살"],
     "notes": "약칭 공조살 (2026-09-21 웹 검증)"},
    {"canonical_name": "민감한 대리님", "origin": "kr", "category": "webnovel",
     "aliases": ["민대리"], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "퇴마록", "origin": "kr", "category": "novel",
     "aliases": [], "notes": "한국 소설, 웹툰·애니메이션화 (2026-09-21 웹 검증)"},
    {"canonical_name": "터닝", "origin": "kr", "category": "webnovel",
     "aliases": ["Turning"], "notes": "쿠유 작 BL 웹소설, 리디 (2026-09-21 웹 검증)"},
    {"canonical_name": "비선실세 레이디", "origin": "kr", "category": "webnovel",
     "aliases": [], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "얼어붙은 플레이어의 귀환", "origin": "kr", "category": "webnovel",
     "aliases": [], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "적국의 왕자로 사는 법", "origin": "kr", "category": "webnovel",
     "aliases": [], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "변경백 서자는 황제였다", "origin": "kr", "category": "webnovel",
     "aliases": ["변서황"], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "아포칼립스엔 고인물이 필요해요", "origin": "kr", "category": "webnovel",
     "aliases": [], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "인소의 법칙", "origin": "kr", "category": "webnovel",
     "aliases": ["인소의법칙"], "notes": "웹툰화 (2026-09-21 웹 검증)"},
    {"canonical_name": "이번 생은 우주대스타", "origin": "kr", "category": "webnovel",
     "aliases": ["이번생은 우주대스타", "이번생은우주대스타"],
     "notes": "웹툰화 (2026-09-21 웹 검증)"},
    {"canonical_name": "일타강사 백사부", "origin": "kr", "category": "webnovel",
     "aliases": [], "notes": "웹툰화 (2026-09-21 웹 검증)"},
    {"canonical_name": "성황의 아이들", "origin": "kr", "category": "webnovel",
     "aliases": ["Children of the Holy Emperor"],
     "notes": "카페인나무s, 조아라/카카오페이지 (2026-09-21 웹 검증)"},
    {"canonical_name": "가즈 나이트", "origin": "kr", "category": "novel",
     "aliases": ["가즈나이트", "God's Knight"],
     "notes": "이경영 1세대 판타지 소설 (2026-09-21 웹 검증)"},
    {"canonical_name": "룬의 아이들", "origin": "kr", "category": "novel",
     "aliases": ["룬의아이들"], "notes": "전영택 판타지 소설"},
    {"canonical_name": "스왈로우 나이츠 테일즈", "origin": "kr", "category": "webnovel",
     "aliases": ["SKT"], "notes": "약칭 SKT"},
    {"canonical_name": "던전을 그리는 화가", "origin": "kr", "category": "webnovel",
     "aliases": ["던그화"], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "패션", "origin": "kr", "category": "webnovel",
     "aliases": ["PASSION", "Passion"],
     "notes": "BL 웹소설 시리즈 (2026-09-21 웹 검증)"},

    # --- 한국/중국 웹툰 ---
    {"canonical_name": "탈(TAL)", "origin": "kr", "category": "webtoon",
     "aliases": ["탈", "TAL"],
     "notes": "강임 작 한국 웹툰 (2026-09-21 웹 검증)"},
    {"canonical_name": "김 대리는 아이돌이 싫어", "origin": "kr", "category": "webnovel",
     "aliases": ["김아싫", "김대리"],
     "notes": "네이버 시리즈, 웹툰화 (2026-09-21 웹 검증)"},
    {"canonical_name": "공작님, 회개해주세요!", "origin": "kr", "category": "webnovel",
     "aliases": ["공회주", "공작님회계해주세요"],
     "notes": "약칭 공회주. 부스 데이터 '공작님회계해주세요' 표기는 오기 병기 (2026-09-21 웹 검증)"},
    {"canonical_name": "전자오락수호대", "origin": "kr", "category": "webtoon",
     "aliases": [], "notes": "네이버 웹툰 (레트로 게임 소재)"},
    {"canonical_name": "약한 영웅", "origin": "kr", "category": "webtoon",
     "aliases": ["약한영웅", "Weak Hero"], "notes": "네이버 웹툰"},
    {"canonical_name": "나 혼자만 레벨업", "origin": "kr", "category": "webnovel",
     "aliases": ["나혼렙", "나혼자만레벨업"],
     "notes": "웹툰·게임화. 원작 웹소설"},
    {"canonical_name": "Free!", "origin": "jp", "category": "anime",
     "aliases": ["프리", "Free!(프리)"], "notes": "교토애니메이션 수영 애니메이션"},
    {"canonical_name": "다키스트 던전", "origin": "en", "category": "game",
     "aliases": ["다키스트던전", "Darkest Dungeon"]},
    {"canonical_name": "A3!", "origin": "jp", "category": "game",
     "aliases": ["에이스리"], "notes": "여성향 연극 육성 게임 (리버브)"},
    {"canonical_name": "베이블레이드", "origin": "jp", "category": "franchise",
     "aliases": ["베이블레이드 버스트", "Beyblade"], "notes": "타카라토미 시리즈 통칭"},
    {"canonical_name": "데스노트", "origin": "jp", "category": "manga",
     "aliases": ["Death Note"], "notes": "오바 츠구미/오바타 타케시"},
    {"canonical_name": "악마집사와 검은고양이", "origin": "jp", "category": "game",
     "aliases": ["悪魔執事と黒い猫"],
     "notes": "산리오 캐릭터 프로젝트/모바일 게임"},
    {"canonical_name": "러브 앤 딥스페이스", "origin": "cn", "category": "game",
     "aliases": ["러브앤딥스페이스", "Love and Deepspace"],
     "notes": "페퍼게임즈(중국) 여성향 게임"},
    {"canonical_name": "언내추럴", "origin": "jp", "category": "drama",
     "aliases": ["Unnatural"], "notes": "TBS 드라마 (노나미 히로시 각본)"},
    {"canonical_name": "그노시아", "origin": "jp", "category": "game",
     "aliases": ["Gnosia", "グノーシア"]},
    {"canonical_name": "86 -에이티식스-", "origin": "jp", "category": "novel",
     "aliases": ["86", "에이티식스", "86―에이티식스―"],
     "notes": "라이트노벨 원작, 애니메이션화"},
    {"canonical_name": "천지창조 디자인부", "origin": "jp", "category": "manga",
     "aliases": ["天地創造デザイン部"], "notes": "만화·애니메이션"},
    {"canonical_name": "약사의 혼잣말", "origin": "jp", "category": "novel",
     "aliases": ["薬屋のひとりごと"],
     "notes": "라이트노벨 원작, 만화·애니메이션화"},
    {"canonical_name": "F1", "origin": "en", "category": "movie",
     "aliases": ["F1 더 무비", "F1 The Movie"], "review_needed": True,
     "notes": "2025 영화와 포뮬러1 자체 동명 표기 — 세부 확인 필요"},
    {"canonical_name": "평행도시", "origin": "kr", "category": "webtoon",
     "aliases": [], "notes": "네이버 웹툰 (2026-09-21 웹 검증)"},
    {"canonical_name": "마왕의 고백", "origin": "kr", "category": "webtoon",
     "aliases": ["The Dark Lord's Confession"], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "최후의 금빛아이", "origin": "kr", "category": "webtoon",
     "aliases": [], "notes": "네이버 웹툰, 알깨/새몽 (2026-09-21 웹 검증)"},
    {"canonical_name": "합법해적 파르페", "origin": "kr", "category": "webtoon",
     "aliases": [], "notes": "네이버 웹툰, 뼈피살 (2026-09-21 웹 검증)"},
    {"canonical_name": "브리아노의 연구소", "origin": "kr", "category": "webtoon",
     "aliases": [], "notes": "레진코믹스, 엉덩국 (2026-09-21 웹 검증)"},
    {"canonical_name": "쿠베라", "origin": "kr", "category": "webtoon",
     "aliases": ["큐베라"], "notes": "2026-09-21 웹 검증"},
    {"canonical_name": "천지해", "origin": "kr", "category": "webtoon",
     "aliases": [], "notes": "레진코믹스, 핑푸 (2026-09-21 웹 검증)"},
    {"canonical_name": "명조: 워더링 웨이브", "origin": "cn", "category": "game",
     "aliases": ["명조", "워더링 웨이브", "Wuthering Waves", "명워"],
     "notes": "쿠로게임즈 (2026-09-21 웹 검증)"},
    {"canonical_name": "젠레스 존 제로", "origin": "cn", "category": "game",
     "aliases": ["젠레스존제로", "젠존제", "Zenless Zone Zero"],
     "notes": "miHoYo(HoYoverse)"},
]

# v1.0에 노이즈로 취급해야 하는 작품 외 표기 (normalize_works가 metadata.noise_terms 참조)
NOISE_TERMS = [
    ".", "..", "...", "x", "0", "sea", "f1", "bl", "gl", "hl", "trpg",
    "특촬", "드라마", "로판", "버튜버", "버츄얼 유튜버", "고전애니",
    "문구", "문구류", "키링", "스티커", "인형", "솜인형", "솜인형 의상",
    "솜인형 옷장", "창작", "창작 캐릭터", "창작인형", "창작 뜨개인형",
    "창작시집", "창작일러스트", "창작 일러스트", "창작 룰", "1차 창작",
    "1차창작", "2차", "기타", "임시", "픽셀아트", "핸드메이드", "레진공예",
    "레진아트", "공예", "수공예품", "뜨개소품", "뜨개공예", "비즈공예",
    "가죽공예", "마크라메", "매듭공예", "뜨개질 공예품", "다꾸 굿즈", "다꾸",
    "마작", "고양이", "미니 rpg", "섬유향수", "프롬소프트웨어",
    "프롬 소프트웨어 게임", "비녀",
]


def build_reverse_index(works):
    from normalize_works import normalize_key
    ri = {}
    for code, w in works.items():
        for name in [w["canonical_name"]] + w.get("aliases", []) + w.get("abbreviations", []):
            if name and name not in ri:
                ri[name] = code
    return ri


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(DICT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    works = data["works"]

    # 별칭 추가
    added_alias_count = 0
    for code, aliases in ALIAS_ADDITIONS.items():
        w = works[code]
        for a in aliases:
            if a not in w.get("aliases", []) and a not in w.get("abbreviations", []) \
                    and a != w["canonical_name"]:
                w.setdefault("aliases", []).append(a)
                added_alias_count += 1
        if code in ALIAS_NOTES:
            existing = w.get("notes", "")
            w["notes"] = (existing + " / " if existing else "") + ALIAS_NOTES[code]

    # 정정
    for code, fields in FIXES.items():
        for alias in fields.pop("_remove_aliases", []):
            if alias in works[code].get("aliases", []):
                works[code]["aliases"].remove(alias)
        works[code].update(fields)

    # 신규 작품
    existing_nums = [int(c[1:]) for c in works]
    next_num = max(existing_nums) + 1
    new_codes = []
    for spec in NEW_WORKS:
        code = f"W{next_num:04d}"
        assert code not in works, code
        entry = {
            "code": code,
            "canonical_name": spec["canonical_name"],
            "origin": spec["origin"],
            "category": spec["category"],
            "aliases": spec.get("aliases", []),
            "abbreviations": spec.get("abbreviations", []),
        }
        if spec.get("notes"):
            entry["notes"] = spec["notes"]
        if spec.get("review_needed"):
            entry["review_needed"] = True
        works[code] = entry
        new_codes.append(code)
        next_num += 1

    # 메타데이터 갱신
    data["metadata"]["version"] = "1.1"
    data["metadata"]["last_updated"] = "2026-09-21"
    data["metadata"]["total_works"] = len(works)
    data["metadata"]["noise_terms"] = NOISE_TERMS
    data["metadata"]["v1.1_changes"] = (
        "11개 회차 전수 분석 기반: 별칭 47개 작품에 추가, W0117 살파랑 origin 정정(kr→cn), "
        f"신규 작품 {len(NEW_WORKS)}종 추가(W0212~W{next_num-1:04d}), noise_terms 신설"
    )
    data["reverse_index"] = build_reverse_index(works)

    summary = {
        "version": "1.1",
        "total_works": len(works),
        "alias_added_works": len(ALIAS_ADDITIONS),
        "aliases_added": added_alias_count,
        "fixed": list(FIXES),
        "new_works": len(NEW_WORKS),
        "new_code_range": f"W0212~W{next_num-1:04d}",
        "noise_terms": len(NOISE_TERMS),
        "new_codes": dict(zip(new_codes, [w["canonical_name"] for w in
                                          [works[c] for c in new_codes]])),
    }

    if args.dry_run:
        print(json.dumps({k: v for k, v in summary.items() if k != "new_codes"},
                         ensure_ascii=False, indent=2))
        return

    with open(DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    f_changed = os.path.basename(DICT_PATH)

    # 변경 세트 영속화
    with open(CHANGESET_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"{f_changed} → v1.1 저장 완료")
    print(json.dumps({k: v for k, v in summary.items() if k != "new_codes"},
                     ensure_ascii=False, indent=2))
    print(f"변경 세트: {CHANGESET_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
WORK_DICTIONARY.json 생성 스크립트
원작 작품 정규화 마스터 딕셔너리 빌드
"""

import json
from collections import OrderedDict

# ============================================================
# 작품 마스터 데이터
# ============================================================
# 원칙:
#   1. 한국 정발명 우선 (없으면 한국에서 가장 많이 쓰는 풀네임)
#   2. 약칭/줄임말은 abbreviations에만 등록
#   3. 띄어쓰기/특수문자 변형은 aliases에 등록
#   4. review_needed=True: 정식명 확인 필요
#
# origin: kr / jp / cn / en / multi
# category: manga / anime / game / webtoon / webnovel / novel /
#           movie / drama / vtuber / trpg / tokusatsu / franchise / music / meta
# ============================================================

WORKS = [
    # === 빈도 1000+ (Top 6) ===
    {
        "canonical_name": "슬램덩크",
        "origin": "jp", "category": "manga",
        "aliases": ["슬램 덩크"],
        "abbreviations": [],
        "notes": "이노우에 타케히코. 더 퍼스트 슬램덩크(영화)와 구분"
    },
    {
        "canonical_name": "가비지 타임",
        "origin": "kr", "category": "webtoon",
        "aliases": ["가비지타임"],
        "abbreviations": [],
    },
    {
        "canonical_name": "화산귀환",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
    },
    {
        "canonical_name": "데뷔 못 하면 죽는 병 걸림",
        "origin": "kr", "category": "webtoon",
        "aliases": ["데뷔 못하면 죽는 병 걸림", "데뷔못하면죽는병걸림",
                     "데뷔못하면 죽는 병 걸림", "데뷔 못하면 죽는병 걸림",
                     "데뷔못하면 죽는병 걸림", "데뷔 못 하면 죽는 병걸림",
                     "데뷔 못 하면 죽는병 걸림", "데뷔못하면 죓는 병 걸림",
                     "데뷔 못하면 죽는 병걸림"],
        "abbreviations": ["데못죽"],
        "notes": "정식 표기는 '데뷔 못 하면 죽는 병 걸림' (띄어쓰기 다수 변형 존재)"
    },
    {
        "canonical_name": "괴담에 떨어져도 출근을 해야 하는구나",
        "origin": "kr", "category": "webtoon",
        "aliases": ["괴담에 떨어져도 출근을 해야하는구나",
                     "괴담에 떨어져도 출근을 해야하는 구나",
                     "괴담에 떨어져도 출근을 해야 하는 구나",
                     "괴담에떨어져도출근을해야하는구나"],
        "abbreviations": ["괴담출근", "괴출"],
        "notes": "약칭 '괴담출근'이 정식명보다 사용 빈도 높음 (445 vs 409)"
    },
    {
        "canonical_name": "주술회전",
        "origin": "jp", "category": "manga",
        "aliases": [],
        "abbreviations": [],
    },

    # === 빈도 200~400 ===
    {
        "canonical_name": "아이돌리쉬 세븐",
        "origin": "jp", "category": "game",
        "aliases": ["아이돌리쉬세븐", "IDOLiSH7", "idolish7"],
        "abbreviations": ["아이나나"],
        "notes": "일본 모바일 게임. 한국 정식 서비스 없음, 한글 표기는 '아이돌리쉬 세븐'"
    },
    {
        "canonical_name": "프로젝트 세카이 컬러풀 스테이지! feat. 하츠네 미쿠",
        "origin": "jp", "category": "game",
        "aliases": ["프로젝트 세카이", "프로젝트세카이",
                     "프로젝트 세카이 컬러풀 스테이지! feat.하츠네 미쿠",
                     "프로젝트 세카이 컬러풀 스테이지 feat.하츠네 미쿠",
                     "프로젝트 세카이 컬러풀 스테이지 feat. 하츠네 미쿠",
                     "프로젝트 세카이 컬러풀 스테이지"],
        "abbreviations": ["프로세카", "프세카"],
        "notes": "정식명은 풀네임이나 통상 '프로젝트 세카이'로 약칭"
    },
    {
        "canonical_name": "앙상블 스타즈!!",
        "origin": "jp", "category": "game",
        "aliases": ["앙상블스타즈!!", "앙상블 스타즈", "앙상블스타즈",
                     "앙상블스타즈!", "앙상블 스타즈!"],
        "abbreviations": ["앙스타"],
        "notes": "원작 '앙상블 스타즈!'에서 '!!'로 리뉴얼. !! Music은 별개 등록"
    },
    {
        "canonical_name": "앙상블 스타즈!! Music",
        "origin": "jp", "category": "game",
        "aliases": ["앙상블 스타즈!! Music", "앙상블 스타즈!! Music",
                     "앙상블스타즈!! Music"],
        "abbreviations": ["앙스타 Music"],
        "notes": "리듬 게임. 시리즈와 구분"
    },
    {
        "canonical_name": "블루 록",
        "origin": "jp", "category": "manga",
        "aliases": ["블루록", "BLUE LOCK", "Blue Lock"],
        "abbreviations": [],
        "notes": "한국 정발 단행본 표기 '블루록' vs 원표기 '블루 록'. review_needed"
    },
    {
        "canonical_name": "오오에",
        "origin": "kr", "category": "webtoon",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
        "notes": "한국 웹툰. 정식명 확인 필요"
    },
    {
        "canonical_name": "진혼기",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
        "notes": "중국 웹소설 추정. 정식 한국명 확인 필요"
    },
    {
        "canonical_name": "이세계 착각 헌터",
        "origin": "kr", "category": "webnovel",
        "aliases": ["이세계착각헌터", "이세계 착각헌터"],
        "abbreviations": ["이착헌"],
    },
    {
        "canonical_name": "어두운 바다의 등불이 되어",
        "origin": "kr", "category": "webtoon",
        "aliases": ["어두운바다의등불이되어", "어두운 바다의 등불이되어"],
        "abbreviations": ["어바등"],
    },
    {
        "canonical_name": "내가 키운 S급들",
        "origin": "kr", "category": "webnovel",
        "aliases": ["내가 키운 s급들", "내가키운S급들", "내가키운s급들",
                     "내가 키운 S급", "내가키운 s급"],
        "abbreviations": ["내스급"],
    },
    {
        "canonical_name": "하이큐!!",
        "origin": "jp", "category": "manga",
        "aliases": ["하이큐", "하이큐!", "하이큐", "하이큐!!"],
        "abbreviations": [],
    },
    {
        "canonical_name": "붕괴: 스타레일",
        "origin": "cn", "category": "game",
        "aliases": ["붕괴 스타레일", "붕괴:스타레일", "붕괴스타레일",
                     "붕괴 : 스타레일", "스타레일"],
        "abbreviations": [],
        "notes": "호요버스. '붕괴: 스타레일'이 한국 정발명"
    },

    # === 빈도 50~120 ===
    {
        "canonical_name": "트라이건",
        "origin": "jp", "category": "manga",
        "aliases": ["TRIGUN", "Trigun", "트라이건 맥시멈"],
        "abbreviations": [],
    },
    {
        "canonical_name": "명일방주",
        "origin": "cn", "category": "game",
        "aliases": ["아크나이츠", "Arknights"],
        "abbreviations": [],
        "notes": "한국 정발명 '명일방주'"
    },
    {
        "canonical_name": "명탐정 코난",
        "origin": "jp", "category": "manga",
        "aliases": ["명탐정코난"],
        "abbreviations": [],
    },
    {
        "canonical_name": "천관사복",
        "origin": "cn", "category": "webnovel",
        "aliases": ["천관사사", "천관사복"],
        "abbreviations": [],
        "notes": "묵향동로(墨香동老) 원작 webnovel. 한국 정발명 '천관사복'"
    },
    {
        "canonical_name": "원피스",
        "origin": "jp", "category": "manga",
        "aliases": ["ONE PIECE", "One Piece"],
        "abbreviations": [],
    },
    {
        "canonical_name": "플레이브",
        "origin": "kr", "category": "vtuber",
        "aliases": ["PLAVE"],
        "abbreviations": [],
        "notes": "한국 버추얼 아이돌 그룹"
    },
    {
        "canonical_name": "닌자보이 란타로",
        "origin": "jp", "category": "manga",
        "aliases": ["닌타마 란타로", "닌타마란타로", "닌타마"],
        "abbreviations": [],
        "notes": "원작 만화 '닌자보이 란타로', 애니메이션 '닌타마 란타로'"
    },
    {
        "canonical_name": "블랙 배저",
        "origin": "kr", "category": "webtoon",
        "aliases": ["블랙배저"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "한국 웹툰 추정. 정확한 정식명 확인 필요"
    },
    {
        "canonical_name": "역전재판",
        "origin": "jp", "category": "game",
        "aliases": ["역전재판 시리즈", "Ace Attorney"],
        "abbreviations": [],
        "notes": "캡콤. 한국 정발명 '역전재판'. 시리즈 전체와 개별작 구분 필요"
    },
    {
        "canonical_name": "MIU404",
        "origin": "jp", "category": "drama",
        "aliases": ["miu404", "MIU 404", "Miu404", "미우404", "미우 404"],
        "abbreviations": [],
        "notes": "일본 드라마"
    },
    {
        "canonical_name": "발더스 게이트 3",
        "origin": "en", "category": "game",
        "aliases": ["발더스게이트3", "발더스 게이트3", "발더스게이트 3",
                     "발더스 게이트", "발더스게이트",
                     "Baldur's Gate 3", "Baldurs Gate 3", "BG3"],
        "abbreviations": [],
    },
    {
        "canonical_name": "히프노시스 마이크",
        "origin": "jp", "category": "franchise",
        "aliases": ["히프노시스마이크", "Hypnosis Mic"],
        "abbreviations": [],
        "notes": "음원·만화·게임 미디어 믹스"
    },
    {
        "canonical_name": "포켓몬스터",
        "origin": "jp", "category": "franchise",
        "aliases": ["포켓몬", "포켓몬스터 시리즈", "Pokémon", "Pokemon"],
        "abbreviations": [],
        "notes": "프랜차이즈 전체. 개별 작품(스칼렛/바이올렛 등)은 별개"
    },
    {
        "canonical_name": "전지적 독자 시점",
        "origin": "kr", "category": "webnovel",
        "aliases": ["전지적독자시점", "전지적 독자시점"],
        "abbreviations": ["전독시"],
    },
    {
        "canonical_name": "마법명가 차남으로 살아남는 법",
        "origin": "kr", "category": "webnovel",
        "aliases": ["마법 명가 차남으로 살아남는 법", "마법명가차남으로 살아남는 법",
                     "마법명가차남으로살아남는법", "마법 명가 차남으로 살아남는법",
                     "마법명가차남으로 살아남는법"],
        "abbreviations": ["마차살"],
    },
    {
        "canonical_name": "니지산지",
        "origin": "jp", "category": "vtuber",
        "aliases": ["NIJISANJI", "Nijisanji", "니지산지"],
        "abbreviations": [],
        "notes": "버추얼 유튜버 소속사"
    },
    {
        "canonical_name": "괴수 8호",
        "origin": "jp", "category": "manga",
        "aliases": ["괴수8호", "괴물 8호", "괴물8호", "Kaiju No.8"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "한국 정발명 '괴물 8호' vs 데이터 주표기 '괴수 8호'. 확인 필요"
    },
    {
        "canonical_name": "마법사의 약속",
        "origin": "jp", "category": "game",
        "aliases": ["마법사의약속"],
        "abbreviations": ["마호야쿠"],
        "notes": "魔法使いの約束. 일본 모바일 게임"
    },
    {
        "canonical_name": "페이트/그랜드 오더",
        "origin": "jp", "category": "game",
        "aliases": ["페이트그랜드오더", "페이트/그랜드오더",
                     "Fate/Grand Order", "Fate Grand Order", "Fate grand order",
                     "FATE GRAND ORDER", "fate grand order", "Fate/Grand order",
                     "fate: grand order", "Fate Grand/Order"],
        "abbreviations": ["FGO"],
    },
    {
        "canonical_name": "트랜스포머",
        "origin": "en", "category": "franchise",
        "aliases": ["Transformers", "트랜스포머 시리즈"],
        "abbreviations": [],
    },
    {
        "canonical_name": "세포신곡",
        "origin": "kr", "category": "webtoon",
        "aliases": ["세포신곡."],
        "abbreviations": [],
        "review_needed": True,
        "notes": "한국 웹툰 추정"
    },
    {
        "canonical_name": "원신",
        "origin": "cn", "category": "game",
        "aliases": ["Genshin Impact", "겐신 임팩트"],
        "abbreviations": [],
        "notes": "호요버스"
    },
    {
        "canonical_name": "페르소나 시리즈",
        "origin": "jp", "category": "game",
        "aliases": ["페르소나", "페르소나 시리즈", "PERSONA", "Persona"],
        "abbreviations": [],
        "notes": "시리즈 전체. 개별작(3/4/5)은 별개"
    },
    {
        "canonical_name": "페르소나 5",
        "origin": "jp", "category": "game",
        "aliases": ["페르소나5", "페르소나 5", "Persona 5", "P5"],
        "abbreviations": [],
    },
    {
        "canonical_name": "페르소나 3",
        "origin": "jp", "category": "game",
        "aliases": ["페르소나3", "페르소나 3", "Persona 3", "P3"],
        "abbreviations": [],
    },
    {
        "canonical_name": "페르소나 4",
        "origin": "jp", "category": "game",
        "aliases": ["페르소나4", "페르소나 4", "Persona 4", "P4"],
        "abbreviations": [],
    },
    {
        "canonical_name": "아이실드 21",
        "origin": "jp", "category": "manga",
        "aliases": ["아이실드21"],
        "abbreviations": [],
    },
    {
        "canonical_name": "골든카무이",
        "origin": "jp", "category": "manga",
        "aliases": ["골든 카무이"],
        "abbreviations": [],
    },
    {
        "canonical_name": "나의 히어로 아카데미아",
        "origin": "jp", "category": "manga",
        "aliases": ["나의히어로아카데미아"],
        "abbreviations": [],
    },
    {
        "canonical_name": "혈계전선",
        "origin": "jp", "category": "manga",
        "aliases": [],
        "abbreviations": [],
    },
    {
        "canonical_name": "파이널 판타지 XIV",
        "origin": "jp", "category": "game",
        "aliases": ["파이널판타지14", "파이널 판타지14", "파이널 판타지 14",
                     "파이널판타지 14", "FF14", "FF XIV", "Final Fantasy XIV"],
        "abbreviations": [],
    },
    {
        "canonical_name": "가정교사 히트맨 리본!",
        "origin": "jp", "category": "manga",
        "aliases": ["가정교사 히트맨 리본", "가정교사히트맨리본", "가정교사히트맨리본!"],
        "abbreviations": [],
    },

    # === 빈도 30~50 ===
    {
        "canonical_name": "오리지널",
        "origin": "meta", "category": "meta",
        "aliases": ["1차창작", "1차 창작", "창작", "(창작)"],
        "abbreviations": [],
        "notes": "메타 카테고리: 2차창작이 아닌 오리지널 창작"
    },
    {
        "canonical_name": "수공예",
        "origin": "meta", "category": "meta",
        "aliases": ["수공예.", "핸드메이드 봉제인형"],
        "abbreviations": [],
        "notes": "메타 카테고리: 특정 원작 없이 수공예/굿즈 제작"
    },
    {
        "canonical_name": "윈드브레이커",
        "origin": "kr", "category": "webtoon",
        "aliases": ["윈드 브레이커"],
        "abbreviations": ["윈브레"],
        "notes": "조용석 작가 웹툰. 일본 애니메이션 'Wind Breaker'와 다름"
    },
    {
        "canonical_name": "모브 사이코 100",
        "origin": "jp", "category": "manga",
        "aliases": ["모브사이코100", "모브사이코 100", "모브 사이코100",
                     "모브사이코", "Mob Psycho 100"],
        "abbreviations": [],
    },
    {
        "canonical_name": "엘소드",
        "origin": "kr", "category": "game",
        "aliases": ["Elsword"],
        "abbreviations": [],
        "notes": "코그 모바일/PC 게임"
    },
    {
        "canonical_name": "대역전재판",
        "origin": "jp", "category": "game",
        "aliases": [],
        "abbreviations": [],
        "notes": "역전재판 시리즈 스핀오프"
    },
    {
        "canonical_name": "인간 본성이 반파된 자구계통",
        "origin": "cn", "category": "webnovel",
        "aliases": ["인사반파자구계통", "인간 본성이 반파된 자구계통"],
        "abbreviations": ["인사반파"],
        "review_needed": True,
        "notes": "중국 웹소설 '人渣反派自救系统'의 한국어 번역명. 정식 번역명 확인 필요"
    },
    {
        "canonical_name": "의원, 다시 살다",
        "origin": "kr", "category": "webnovel",
        "aliases": ["의원 다시 살다", "의원,다시살다", "의원다시살다"],
        "abbreviations": [],
        "notes": "콤마가 제목의 일부"
    },
    {
        "canonical_name": "나루토",
        "origin": "jp", "category": "manga",
        "aliases": ["NARUTO", "Naruto"],
        "abbreviations": [],
    },
    {
        "canonical_name": "죠죠의 기묘한 모험",
        "origin": "jp", "category": "manga",
        "aliases": ["죠죠의기묘한모험", "죠죠", "JoJo's Bizarre Adventure", "JoJo"],
        "abbreviations": [],
    },
    {
        "canonical_name": "도검난무",
        "origin": "jp", "category": "game",
        "aliases": ["Touken Ranbu"],
        "abbreviations": [],
    },
    {
        "canonical_name": "로드 오브 히어로즈",
        "origin": "kr", "category": "game",
        "aliases": ["로드오브히어로즈"],
        "abbreviations": ["로오히"],
    },
    {
        "canonical_name": "은혼",
        "origin": "jp", "category": "manga",
        "aliases": ["은혼", "Gintama"],
        "abbreviations": [],
    },
    {
        "canonical_name": "마도조사",
        "origin": "jp", "category": "game",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
        "notes": "마작 게임 '麻雀' 관련 추정. 정확한 작품 확인 필요"
    },
    {
        "canonical_name": "서브 남주가 파업하면 생기는 일",
        "origin": "kr", "category": "webnovel",
        "aliases": ["서브남주가 파업하면 생기는 일"],
        "abbreviations": [],
    },
    {
        "canonical_name": "카리스마",
        "origin": "jp", "category": "franchise",
        "aliases": ["카리스마 하우스", "CHARISMA"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "일본 미디어 믹스 추정. '카리스마 하우스' 포함 관계 확인 필요"
    },
    {
        "canonical_name": "유희왕",
        "origin": "jp", "category": "franchise",
        "aliases": ["유희왕 듀얼몬스터즈", "유희왕 듀얼 몬스터즈",
                     "Yu-Gi-Oh!", "유희왕 OCG"],
        "abbreviations": [],
    },
    {
        "canonical_name": "해즈빈 호텔",
        "origin": "en", "category": "anime",
        "aliases": ["해즈빈호텔", "Hazbin Hotel"],
        "abbreviations": [],
    },
    {
        "canonical_name": "18TRIP",
        "origin": "jp", "category": "game",
        "aliases": ["18trip"],
        "abbreviations": [],
    },
    {
        "canonical_name": "문과라도 안 죄송한 이세계로 감",
        "origin": "kr", "category": "webnovel",
        "aliases": ["문과라도 안죄송한 이세계로 감"],
        "abbreviations": [],
    },
    {
        "canonical_name": "백작가의 망나니가 되었다",
        "origin": "kr", "category": "webnovel",
        "aliases": ["백작가의망나니가되었다"],
        "abbreviations": [],
    },
    {
        "canonical_name": "쿠로코의 농구",
        "origin": "jp", "category": "manga",
        "aliases": ["쿠로코의농구", "Kuroko's Basketball"],
        "abbreviations": [],
    },
    {
        "canonical_name": "이나즈마 일레븐",
        "origin": "jp", "category": "game",
        "aliases": ["이나즈마일레븐", "Inazuma Eleven"],
        "abbreviations": [],
    },
    {
        "canonical_name": "테일즈런너",
        "origin": "kr", "category": "game",
        "aliases": ["Tales Runner", "테일즈 런너"],
        "abbreviations": [],
    },
    {
        "canonical_name": "보컬로이드",
        "origin": "jp", "category": "meta",
        "aliases": ["VOCALOID", "Vocaloid", "보컬로이드 시리즈"],
        "abbreviations": [],
        "notes": "메타 카테고리: 보컬로이드 캐릭터 전체"
    },
    {
        "canonical_name": "명문고 EX급 조연의 리플레이",
        "origin": "kr", "category": "webnovel",
        "aliases": ["명문고 ex급 조연의 리플레이", "명문고ex급 조연의 리플레이",
                     "명문고EX급조연의리플레이"],
        "abbreviations": ["명급리"],
    },
    {
        "canonical_name": "사카모토 데이즈",
        "origin": "jp", "category": "manga",
        "aliases": ["사카모토데이즈", "Sakamoto Days"],
        "abbreviations": [],
    },
    {
        "canonical_name": "테니스의 왕자",
        "origin": "jp", "category": "manga",
        "aliases": ["테니스의왕자", "The Prince of Tennis"],
        "abbreviations": [],
    },
    {
        "canonical_name": "도쿄 리벤저스",
        "origin": "jp", "category": "manga",
        "aliases": ["도쿄리벤저스", "도쿄 리벤져스", "Tokyo Revengers"],
        "abbreviations": [],
    },

    # === 빈도 15~30 ===
    {
        "canonical_name": "누: 카니발",
        "origin": "jp", "category": "game",
        "aliases": ["Nu: 카니발", "Nu:카니발", "NU카니발", "NU:카니발",
                     "NU:Carnival", "Nu Carnival", "Nu:carnival",
                     "Nu: carnival", "nu:carnival"],
        "abbreviations": ["뉴카니발", "누카니발"],
    },
    {
        "canonical_name": "모모찌",
        "origin": "jp", "category": "manga",
        "aliases": ["모모치", "Momochi"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "정확한 작품 확인 필요"
    },
    {
        "canonical_name": "오버워치",
        "origin": "en", "category": "game",
        "aliases": ["Overwatch", "오버워치 2"],
        "abbreviations": [],
    },
    {
        "canonical_name": "에리오스 라이징 히어로즈",
        "origin": "jp", "category": "game",
        "aliases": ["에리오스라이징히어로즈", "ELOS", "Helios Rising Heroes"],
        "abbreviations": [],
    },
    {
        "canonical_name": "잔차품",
        "origin": "jp", "category": "manga",
        "aliases": ["잔차품", "残次品"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "정확한 작품 확인 필요"
    },
    {
        "canonical_name": "우마무스메 프리티 더비",
        "origin": "jp", "category": "game",
        "aliases": ["우마무스메", "우마무스메 프리티 더비",
                     "Uma Musume Pretty Derby"],
        "abbreviations": ["우마무스메"],
    },
    {
        "canonical_name": "메달리스트",
        "origin": "jp", "category": "manga",
        "aliases": ["Medalist"],
        "abbreviations": [],
    },
    {
        "canonical_name": "닥터 스톤",
        "origin": "jp", "category": "manga",
        "aliases": ["닥터스톤", "Dr. STONE"],
        "abbreviations": [],
    },
    {
        "canonical_name": "블루 자이언트",
        "origin": "jp", "category": "manga",
        "aliases": ["블루자이언트", "Blue Giant"],
        "abbreviations": [],
    },
    {
        "canonical_name": "해리 포터",
        "origin": "en", "category": "novel",
        "aliases": ["해리 포터", "해리포터", "Harry Potter"],
        "abbreviations": [],
    },
    {
        "canonical_name": "반월당의 기묘한 이야기",
        "origin": "kr", "category": "webnovel",
        "aliases": ["반월당의기묘한이야기"],
        "abbreviations": ["반월당"],
    },
    {
        "canonical_name": "젤다의 전설",
        "origin": "jp", "category": "game",
        "aliases": ["젤다의전설", "The Legend of Zelda"],
        "abbreviations": [],
    },
    {
        "canonical_name": "다이아몬드 에이스",
        "origin": "jp", "category": "manga",
        "aliases": ["다이아몬드에이스", "Ace of Diamond"],
        "abbreviations": [],
    },
    {
        "canonical_name": "용과 같이",
        "origin": "jp", "category": "game",
        "aliases": ["용과같이", "Yakuza", "Like a Dragon", "룰 더 다이"],
        "abbreviations": [],
    },
    {
        "canonical_name": "겁쟁이 페달",
        "origin": "jp", "category": "manga",
        "aliases": ["겁쟁이페달", "Yowamushi Pedal"],
        "abbreviations": [],
    },
    {
        "canonical_name": "흡혈귀는 툭하면 죽는다",
        "origin": "jp", "category": "manga",
        "aliases": ["흡혈귀는툭하면죽는다"],
        "abbreviations": [],
    },
    {
        "canonical_name": "리그 오브 레전드",
        "origin": "en", "category": "game",
        "aliases": ["리그오브레전드", "League of Legends", "LoL"],
        "abbreviations": ["롤"],
    },
    {
        "canonical_name": "가라오케 가자!",
        "origin": "kr", "category": "webtoon",
        "aliases": ["가라오케 가자", "가라오케가자"],
        "abbreviations": [],
    },
    {
        "canonical_name": "사이퍼즈",
        "origin": "kr", "category": "game",
        "aliases": ["Cyphers"],
        "abbreviations": [],
    },
    {
        "canonical_name": "열화요수",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
        "notes": "중국 웹소설 추정. 정식 한국명 확인 필요"
    },
    {
        "canonical_name": "MCU",
        "origin": "en", "category": "franchise",
        "aliases": ["마블 시네마틱 유니버스", "Marvel Cinematic Universe",
                     "마블", "마블코믹스", "마블 코믹스", "Marvel Comics"],
        "abbreviations": [],
    },
    {
        "canonical_name": "콜 오브 듀티",
        "origin": "en", "category": "game",
        "aliases": ["콜오브듀티", "콜 오브  듀티", "Call of Duty", "CoD"],
        "abbreviations": [],
    },
    {
        "canonical_name": "헌터×헌터",
        "origin": "jp", "category": "manga",
        "aliases": ["헌터x헌터", "헌터X헌터", "헌터헌터", "Hunter x Hunter", "HUNTER×HUNTER"],
        "abbreviations": [],
    },
    {
        "canonical_name": "스타트렉",
        "origin": "en", "category": "franchise",
        "aliases": ["Star Trek"],
        "abbreviations": [],
    },
    {
        "canonical_name": "무기미도",
        "origin": "jp", "category": "manga",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
        "notes": "정확한 작품 확인 필요"
    },
    {
        "canonical_name": "블리치",
        "origin": "jp", "category": "manga",
        "aliases": ["BLEACH", "Bleach"],
        "abbreviations": [],
    },
    {
        "canonical_name": "너희들은 변호됐다",
        "origin": "kr", "category": "webtoon",
        "aliases": ["변호됨"],
        "abbreviations": [],
    },
    {
        "canonical_name": "100미터",
        "origin": "kr", "category": "webtoon",
        "aliases": ["100미터.", "100m", "100M"],
        "abbreviations": [],
    },
    {
        "canonical_name": "메타포: 리파타지오",
        "origin": "jp", "category": "game",
        "aliases": ["메타포 : 리판타지오", "메타포 리판타지오",
                     "메타포:리판타지오", "메타포: 리 판타지오",
                     "Metaphor: ReFantazio"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "한국 정발명 '메타포: 리파타지오' vs 원제 'ReFantazio'. 확인 필요"
    },
    {
        "canonical_name": "디지몬",
        "origin": "jp", "category": "franchise",
        "aliases": ["디지몬 시리즈", "Digimon", "Digital Monster"],
        "abbreviations": [],
    },
    {
        "canonical_name": "스플래툰",
        "origin": "jp", "category": "game",
        "aliases": ["스플래툰", "Splatoon"],
        "abbreviations": [],
    },
    {
        "canonical_name": "던전밥",
        "origin": "jp", "category": "manga",
        "aliases": ["Dungeon Meshi", "던전 먹방"],
        "abbreviations": [],
    },
    {
        "canonical_name": "고서점가의 하시히메",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
    },
    {
        "canonical_name": "빛과 밤의 사랑",
        "origin": "cn", "category": "game",
        "aliases": ["빛과밤의사랑", "光与夜之恋"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "중국 모바일 게임 '光与夜之恋'. 한국어 정식명 확인 필요"
    },

    # === 빈도 5~15 ===
    {
        "canonical_name": "역전재판 시리즈",
        "origin": "jp", "category": "franchise",
        "aliases": [],
        "abbreviations": [],
        "notes": "역전재판 프랜차이즈 전체"
    },
    {
        "canonical_name": "크툴루의 부름",
        "origin": "en", "category": "trpg",
        "aliases": ["CoC", "COC", "coc", "Call of Cthulhu", "크툴루 TRPG"],
        "abbreviations": [],
    },
    {
        "canonical_name": "프로메아",
        "origin": "jp", "category": "anime",
        "aliases": ["Promare", "프로메아", "프로메어"],
        "abbreviations": [],
    },
    {
        "canonical_name": "살파랑",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "파라독스 라이브",
        "origin": "jp", "category": "game",
        "aliases": ["파라독스라이브", "Paradox Live"],
        "abbreviations": ["파라라이"],
    },
    {
        "canonical_name": "가면라이더",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["가면라이더 시리즈", "Kamen Rider"],
        "abbreviations": [],
    },
    {
        "canonical_name": "가면라이더 가브",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["Kamen Rider Gavv"],
        "abbreviations": [],
    },
    {
        "canonical_name": "천마는 아이돌이 되었다",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": ["천마돌"],
    },
    {
        "canonical_name": "드래곤볼",
        "origin": "jp", "category": "manga",
        "aliases": ["드래곤 볼", "Dragon Ball"],
        "abbreviations": [],
    },
    {
        "canonical_name": "프로야구생존기",
        "origin": "kr", "category": "webtoon",
        "aliases": ["프로야구 생존기"],
        "abbreviations": [],
    },
    {
        "canonical_name": "킹 오브 프리즘",
        "origin": "jp", "category": "anime",
        "aliases": ["킹오브프리즘", "King of Prism"],
        "abbreviations": [],
    },
    {
        "canonical_name": "더블크로스 3rd",
        "origin": "jp", "category": "trpg",
        "aliases": ["더블크로스3rd", "Double Cross 3rd", "DX3"],
        "abbreviations": [],
    },
    {
        "canonical_name": "더 퍼스트 슬램덩크",
        "origin": "jp", "category": "anime",
        "aliases": ["더퍼스트슬램덩크", "The First Slam Dunk"],
        "abbreviations": [],
    },
    {
        "canonical_name": "SPY×FAMILY",
        "origin": "jp", "category": "manga",
        "aliases": ["스파이 패밀리", "스파이패밀리", "스파이 패밀리",
                     "SPY x FAMILY", "Spy x Family"],
        "abbreviations": [],
    },
    {
        "canonical_name": "망각배터리",
        "origin": "jp", "category": "manga",
        "aliases": ["망각 배터리", "Bokura no Arito"],
        "abbreviations": [],
    },
    {
        "canonical_name": "문호 스트레이 독스",
        "origin": "jp", "category": "manga",
        "aliases": ["문호스트레이독스", "문호 스트레이 독스",
                     "Bungo Stray Dogs"],
        "abbreviations": [],
    },
    {
        "canonical_name": "적왕사",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "월야환담",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "notes": "전민희 작가. 한국 판타지 소설"
    },
    {
        "canonical_name": "무림제일폐: 월한강천록",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "울트라맨 엑스",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["Ultraman X"],
        "abbreviations": [],
    },
    {
        "canonical_name": "울트라맨 오브",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["Ultraman Orb"],
        "abbreviations": [],
    },
    {
        "canonical_name": "그랜드체이스",
        "origin": "kr", "category": "game",
        "aliases": ["Grand Chase", "그랜드 체이스"],
        "abbreviations": [],
    },
    {
        "canonical_name": "네가 죽어",
        "origin": "kr", "category": "webnovel",
        "aliases": ["네가죽어"],
        "abbreviations": [],
    },
    {
        "canonical_name": "탑로더 탑꾸",
        "origin": "kr", "category": "webtoon",
        "aliases": ["탑로더,탑꾸"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "정확한 작품 확인 필요. 두 작품일 수도 있음"
    },
    {
        "canonical_name": "진격의 거인",
        "origin": "jp", "category": "manga",
        "aliases": ["진격의거인", "Attack on Titan", "AoT"],
        "abbreviations": [],
    },
    {
        "canonical_name": "케이팝 데몬 헌터스",
        "origin": "en", "category": "anime",
        "aliases": ["케이팝데몬헌터스", "케이팝 데몬헌터스",
                     "Kpop Demon Hunters", "K-Pop Demon Hunters"],
        "abbreviations": [],
    },
    {
        "canonical_name": "리버스: 1999",
        "origin": "cn", "category": "game",
        "aliases": ["리버스 1999", "리버스1999", "Reverse: 1999"],
        "abbreviations": [],
    },
    {
        "canonical_name": "시광대리인",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "밀그램",
        "origin": "jp", "category": "franchise",
        "aliases": ["MILGRAM"],
        "abbreviations": [],
    },
    {
        "canonical_name": "검은방",
        "origin": "kr", "category": "game",
        "aliases": ["Dark Room?", "검은 방"],
        "abbreviations": [],
        "notes": "한국 인디 게임/소설 추정"
    },
    {
        "canonical_name": "프롬 아르고나비스",
        "origin": "jp", "category": "franchise",
        "aliases": ["from ARGONAVIS", "From Argonavis", "from Argonavis",
                     "ARGONAVIS", "아르고나비스"],
        "abbreviations": [],
    },
    {
        "canonical_name": "청의 엑소시스트",
        "origin": "jp", "category": "manga",
        "aliases": ["Blue Exorcist", "아오노 엑소시스트"],
        "abbreviations": [],
    },
    {
        "canonical_name": "동경과 거짓말",
        "origin": "jp", "category": "manga",
        "aliases": ["동경과거짓말"],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "기동전사 건담 수성의 마녀",
        "origin": "jp", "category": "anime",
        "aliases": ["기동전사 건담 수성의마녀",
                     "Mobile Suit Gundam: The Witch from Mercury"],
        "abbreviations": [],
    },
    {
        "canonical_name": "기동전사 건담",
        "origin": "jp", "category": "franchise",
        "aliases": ["건담", "Gundam", "Mobile Suit Gundam"],
        "abbreviations": [],
    },
    {
        "canonical_name": "술탄의 게임",
        "origin": "kr", "category": "game",
        "aliases": ["술탄의게임", "Sultan's Game"],
        "abbreviations": [],
        "review_needed": True,
        "notes": "인디 보드/카드 게임 추정"
    },
    {
        "canonical_name": "이합화타적백묘사존",
        "origin": "cn", "category": "webnovel",
        "aliases": ["이합화타적 백묘사존"],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "포켓몬스터 스칼렛·바이올렛",
        "origin": "jp", "category": "game",
        "aliases": ["포켓몬스터 스칼렛/바이올렛",
                     "Pokémon Scarlet/Violet", "포켓몬 스칼렛 바이올렛"],
        "abbreviations": [],
    },
    {
        "canonical_name": "월드 트리거",
        "origin": "jp", "category": "manga",
        "aliases": ["월드트리거", "World Trigger"],
        "abbreviations": [],
    },
    {
        "canonical_name": "FKMT",
        "origin": "jp", "category": "meta",
        "aliases": ["fkmt", "Fkmt", "후쿠모토"],
        "abbreviations": [],
        "notes": "메타 카테고리: 후쿠모토 노리유키(카이지, 아카기 등) 작품 총칭"
    },
    {
        "canonical_name": "초심 잃은 아이돌을 위한 회귀백서",
        "origin": "kr", "category": "webnovel",
        "aliases": ["초심 잃은 아이돌을 위한 회귀 백서",
                     "초심잃은아이돌을위한회귀백서"],
        "abbreviations": [],
    },
    {
        "canonical_name": "마기카로기아",
        "origin": "jp", "category": "trpg",
        "aliases": ["Magicalogia", "마기카 로기아"],
        "abbreviations": [],
    },
    {
        "canonical_name": "광마회귀",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "회색도시",
        "origin": "kr", "category": "game",
        "aliases": ["회색도시", "Grey City"],
        "abbreviations": [],
        "notes": "한국 인디 게임"
    },
    {
        "canonical_name": "테일즈 오브 제스티리아",
        "origin": "jp", "category": "game",
        "aliases": ["Tales of Zestiria", "TOZ"],
        "abbreviations": [],
    },
    {
        "canonical_name": "페이트 시리즈",
        "origin": "jp", "category": "franchise",
        "aliases": ["Fate 시리즈", "fate 시리즈", "Fate", "페이트"],
        "abbreviations": [],
    },
    {
        "canonical_name": "프리파라",
        "origin": "jp", "category": "anime",
        "aliases": ["PriPara"],
        "abbreviations": [],
    },
    {
        "canonical_name": "더블크로스",
        "origin": "jp", "category": "trpg",
        "aliases": ["Double Cross", "DX"],
        "abbreviations": [],
    },
    {
        "canonical_name": "게게게의 키타로",
        "origin": "jp", "category": "manga",
        "aliases": ["게게게의키타로", "GeGeGe no Kitaro"],
        "abbreviations": [],
    },
    {
        "canonical_name": "용기폭발 뱅브레이번",
        "origin": "jp", "category": "anime",
        "aliases": ["용기폭발뱅브레이번", "Brave Bang Bravern!"],
        "abbreviations": [],
    },
    {
        "canonical_name": "베리드 스타즈",
        "origin": "jp", "category": "game",
        "aliases": ["베리드스타즈", "Sherebed Stars", "Buried Stars"],
        "abbreviations": [],
    },
    {
        "canonical_name": "키타로 탄생: 게게게의 수수께끼",
        "origin": "jp", "category": "anime",
        "aliases": ["키타로 탄생 게게게의 수수께끼",
                     "키타로탄생게게게의수수께끼",
                     "키타로 탄생 : 게게게의 수수께끼",
                     "The Birth of Kitaro"],
        "abbreviations": [],
    },
    {
        "canonical_name": "VS AMBIVALENZ",
        "origin": "jp", "category": "game",
        "aliases": ["vs ambivalenz", "VS AMBIVALENZ(비바렌)",
                     "VS AMBIVALENZ,비바렌", "vs ambivalenz,비바렌",
                     "vs ambivalenz 비바렌"],
        "abbreviations": ["비바렌"],
    },
    {
        "canonical_name": "볼트론: 전설의 수호자",
        "origin": "en", "category": "anime",
        "aliases": ["Voltron: Legendary Defender", "볼트론"],
        "abbreviations": [],
    },
    {
        "canonical_name": "박앵귀",
        "origin": "jp", "category": "game",
        "aliases": ["Hakuouki", "박앵귀 시리즈"],
        "abbreviations": [],
    },
    {
        "canonical_name": "아오페라",
        "origin": "jp", "category": "game",
        "aliases": ["AOpera"],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "시노비가미",
        "origin": "jp", "category": "trpg",
        "aliases": ["Shinobigami", "시노비가미 전"],
        "abbreviations": [],
    },
    {
        "canonical_name": "아이돌 마스터 SideM",
        "origin": "jp", "category": "game",
        "aliases": ["아이돌마스터 SideM", "아이돌마스터 sideM",
                     "THE IDOLM@STER SideM", "아이돌 마스터 사이드엠"],
        "abbreviations": [],
    },
    {
        "canonical_name": "망나니 PD 아이돌로 살아남기",
        "origin": "kr", "category": "webnovel",
        "aliases": ["망나니 pd 아이돌로 살아남기"],
        "abbreviations": [],
    },
    {
        "canonical_name": "누이소품샵",
        "origin": "kr", "category": "webtoon",
        "aliases": ["누이 소품샵"],
        "abbreviations": [],
    },
    {
        "canonical_name": "집이 없어",
        "origin": "kr", "category": "webtoon",
        "aliases": ["집이없어"],
        "abbreviations": [],
    },
    {
        "canonical_name": "파이어 엠블렘 풍화설월",
        "origin": "jp", "category": "game",
        "aliases": ["파이어엠블렘 풍화설월", "파이어 엠블렘 : 풍화설월",
                     "Fire Emblem: Three Houses", "파이어 엠블렘"],
        "abbreviations": [],
        "notes": "한국 정발명 '풍화설월' vs 원제 'Three Houses'. 확인 필요"
    },
    {
        "canonical_name": "왕은 웃었다",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
    },
    {
        "canonical_name": "캐릭캐릭체인지",
        "origin": "jp", "category": "anime",
        "aliases": ["아이엠스타", "Shugo Chara!", "캐릭캐릭체인지(아이엠스타)"],
        "abbreviations": [],
    },
    {
        "canonical_name": "격기3반",
        "origin": "jp", "category": "manga",
        "aliases": ["격기 3반", "Kakko 3-ban"],
        "abbreviations": [],
        "review_needed": True,
    },
    {
        "canonical_name": "길티기어",
        "origin": "jp", "category": "game",
        "aliases": ["길티 기어", "Guilty Gear"],
        "abbreviations": [],
    },
    {
        "canonical_name": "아카기",
        "origin": "jp", "category": "manga",
        "aliases": ["아카기", "Akagi", "천재 마작사 아카기"],
        "abbreviations": [],
    },
    {
        "canonical_name": "크툴루 게임 속 천재 마법사가 되었다",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": ["크법사"],
    },
    {
        "canonical_name": "태팅레이스",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },

    # === 미매칭 상위 작품 추가 (2차 보완) ===
    {
        "canonical_name": "장송의 프리렌",
        "origin": "jp", "category": "manga",
        "aliases": ["프리렌", "Frieren", "Frieren: Beyond Journey's End",
                     "프리렌: 초장의 끝에서"],
        "abbreviations": [],
    },
    {
        "canonical_name": "단간론파",
        "origin": "jp", "category": "game",
        "aliases": ["Danganronpa", "단간론파 시리즈"],
        "abbreviations": [],
        "notes": "프랜차이즈 전체"
    },
    {
        "canonical_name": "봇치더락!",
        "origin": "jp", "category": "manga",
        "aliases": ["봇치더락", "Bocchi the Rock!", "BOCCHI THE ROCK!"],
        "abbreviations": ["봇락"],
    },
    {
        "canonical_name": "체인소 맨",
        "origin": "jp", "category": "manga",
        "aliases": ["체인소맨", "Chainsaw Man", "총귀쇠인"],
        "abbreviations": [],
    },
    {
        "canonical_name": "제5인격",
        "origin": "cn", "category": "game",
        "aliases": ["Identity V", "아이덴티티 브이", "아이덴티티V"],
        "abbreviations": [],
    },
    {
        "canonical_name": "록맨",
        "origin": "jp", "category": "franchise",
        "aliases": ["록맨 시리즈", "Mega Man", "메가맨", "메가맨 시리즈"],
        "abbreviations": [],
    },
    {
        "canonical_name": "메탈카드봇",
        "origin": "kr", "category": "anime",
        "aliases": ["Metal Cardbot"],
        "abbreviations": [],
    },
    {
        "canonical_name": "소닉 더 헤지혹",
        "origin": "jp", "category": "franchise",
        "aliases": ["소닉 더 헤지혹 시리즈", "소닉", "Sonic the Hedgehog",
                     "Sonic", "소닉 시리즈"],
        "abbreviations": [],
    },
    {
        "canonical_name": "아머드코어 VI",
        "origin": "jp", "category": "game",
        "aliases": ["아머드코어6", "아머드 코어 6", "Armored Core VI",
                     "Armored Core 6", "AC6"],
        "abbreviations": [],
    },
    {
        "canonical_name": "라테일",
        "origin": "kr", "category": "game",
        "aliases": ["LaTale", "라 테일"],
        "abbreviations": [],
    },
    {
        "canonical_name": "은과 금",
        "origin": "jp", "category": "manga",
        "aliases": ["Gin to Kin", "은과금"],
        "abbreviations": [],
    },
    {
        "canonical_name": "울트라맨 타이가",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["Ultraman Taiga"],
        "abbreviations": [],
    },
    {
        "canonical_name": "가면라이더 리바이스",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["Kamen Rider Revice"],
        "abbreviations": [],
    },
    {
        "canonical_name": "폭상전대 분붐저",
        "origin": "jp", "category": "tokusatsu",
        "aliases": ["분붐저", "Bakuage Sentai Boonboomger"],
        "abbreviations": [],
    },
    {
        "canonical_name": "헬루바",
        "origin": "en", "category": "anime",
        "aliases": ["헬루바보스", "Helluva Boss"],
        "abbreviations": [],
    },
    {
        "canonical_name": "스티븐 유니버스",
        "origin": "en", "category": "anime",
        "aliases": ["Steven Universe"],
        "abbreviations": [],
    },
    {
        "canonical_name": "아울 하우스",
        "origin": "en", "category": "anime",
        "aliases": ["The Owl House", "올빼미 집"],
        "abbreviations": [],
    },
    {
        "canonical_name": "앰피비아",
        "origin": "en", "category": "anime",
        "aliases": ["Amphibia"],
        "abbreviations": [],
    },
    {
        "canonical_name": "사이키 쿠스오의 재난",
        "origin": "jp", "category": "manga",
        "aliases": ["사이키쿠스오의 재난", "The Disastrous Life of Saiki K."],
        "abbreviations": [],
    },
    {
        "canonical_name": "소울이터",
        "origin": "jp", "category": "manga",
        "aliases": ["Soul Eater"],
        "abbreviations": [],
    },
    {
        "canonical_name": "마법소녀 마도카 마기카",
        "origin": "jp", "category": "anime",
        "aliases": ["마마마", "Puella Magi Madoka Magica"],
        "abbreviations": [],
    },
    {
        "canonical_name": "오란고교 호스트부",
        "origin": "jp", "category": "manga",
        "aliases": ["오란고교", "오렌 고교 호스트부", "Ouran High School Host Club"],
        "abbreviations": [],
    },
    {
        "canonical_name": "달빛천사",
        "origin": "jp", "category": "manga",
        "aliases": ["Full Moon wo Sagashite", "풀문을 찾아서"],
        "abbreviations": [],
    },
    {
        "canonical_name": "할로우 나이트",
        "origin": "en", "category": "game",
        "aliases": ["Hollow Knight", "할로우나이트"],
        "abbreviations": [],
    },
    {
        "canonical_name": "니디 걸 오버도즈",
        "origin": "jp", "category": "game",
        "aliases": ["NEEDY GIRL OVERDOSE", "니디걸오버도즈",
                     "니디즙 오버도즈", "NEEDY STREAMER OVERLOAD"],
        "abbreviations": [],
    },
    {
        "canonical_name": "회색도시 시리즈",
        "origin": "kr", "category": "game",
        "aliases": ["회색도시2", "회색도시", "Grey City"],
        "abbreviations": [],
        "notes": "한국 인디 추리 게임 시리즈"
    },
    {
        "canonical_name": "유희왕 (토에이)",
        "origin": "jp", "category": "anime",
        "aliases": ["유희왕 DM", "유희왕 토에이", "유희왕 듀얼몬스터즈 (토에이)",
                     "Yu-Gi-Oh! (Toei)"],
        "abbreviations": [],
        "notes": "토에이 애니메이션 판"
    },
    {
        "canonical_name": "주컨곤",
        "origin": "cn", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
        "notes": "정확한 작품 확인 필요"
    },
    {
        "canonical_name": "길라잡이의 등불",
        "origin": "kr", "category": "webnovel",
        "aliases": [],
        "abbreviations": [],
        "review_needed": True,
    },
]


def build_dictionary():
    """WORKS 리스트 → WORK_DICTIONARY.json 구조 생성"""
    works = OrderedDict()
    for i, w in enumerate(WORKS, 1):
        code = f"W{i:04d}"
        entry = OrderedDict()
        entry["code"] = code
        entry["canonical_name"] = w["canonical_name"]
        entry["origin"] = w.get("origin", "")
        entry["category"] = w.get("category", "")
        entry["aliases"] = sorted(set(w.get("aliases", [])))
        entry["abbreviations"] = sorted(set(w.get("abbreviations", [])))
        if w.get("review_needed"):
            entry["review_needed"] = True
        if w.get("notes"):
            entry["notes"] = w["notes"]
        works[code] = entry

    # 역색인: 모든 표기 → 코드
    reverse_index = {}
    for code, w in works.items():
        names = [w["canonical_name"]] + w["aliases"] + w["abbreviations"]
        for name in names:
            key = name.strip().lower()
            if key and key not in reverse_index:
                reverse_index[key] = code

    result = OrderedDict()
    result["metadata"] = {
        "version": "1.0",
        "last_updated": "2026-07-10",
        "naming_rule": "한국 정발명 우선, 없으면 한국에서 가장 많이 쓰는 풀네임",
        "total_works": len(works),
        "origin_legend": {
            "kr": "한국", "jp": "일본", "cn": "중국",
            "en": "영미권", "multi": "다국적", "meta": "메타 카테고리"
        },
        "category_legend": {
            "manga": "만화", "anime": "애니메이션", "game": "게임",
            "webtoon": "웹툰", "webnovel": "웹소설", "novel": "소설",
            "movie": "영화", "drama": "드라마", "vtuber": "버추얼 유튜버",
            "trpg": "TRPG", "tokusatsu": "특촬", "franchise": "프랜차이즈",
            "music": "음악", "meta": "메타 카테고리"
        },
    }
    result["works"] = works
    result["reverse_index"] = reverse_index

    return result


if __name__ == "__main__":
    import os
    data = build_dictionary()

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WORK_DICTIONARY.json")

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ WORK_DICTIONARY.json 생성: {data['metadata']['total_works']}개 작품")
    print(f"  역색인 엔트리: {len(data['reverse_index'])}개")
    print(f"  저장 위치: {outpath}")

    review = [w for w in data["works"].values() if w.get("review_needed")]
    print(f"  검토 필요: {len(review)}개 작품")

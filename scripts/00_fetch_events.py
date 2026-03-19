#!/usr/bin/env python3
"""
모듈 0: 행사 정보 자동 수집

동인네트워크 API에서 행사 목록을 가져와 EVENT_INFORMATION.json을 생성합니다.

Usage:
    python scripts/00_fetch_events.py --month "2026-04"
    python scripts/00_fetch_events.py --month "2026-04" --output "custom_events.json"
    python scripts/00_fetch_events.py --all
"""

import argparse
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import requests

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EventFetcher:
    """동인네트워크 행사 정보 수집기"""
    
    API_URL = "https://api.dongne.co/events"
    
    def __init__(self):
        self.events = []
    
    def fetch_all_events(self, per_page: int = 500) -> List[Dict]:
        """
        전체 행사 목록 가져오기
        
        Args:
            per_page: 페이지당 행사 수
            
        Returns:
            행사 목록
        """
        logger.info("행사 목록 수집 중...")
        
        params = {
            "page": 1,
            "per_page": per_page
        }
        
        try:
            response = requests.get(self.API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("list", [])
            logger.info(f"총 {len(events)}개 행사 수집 완료")
            
            return events
            
        except requests.RequestException as e:
            logger.error(f"API 요청 실패: {e}")
            return []
    
    def filter_by_month(self, events: List[Dict], year_month: str) -> List[Dict]:
        """
        특정 월 행사만 필터링
        
        Args:
            events: 전체 행사 목록
            year_month: 연월 (예: "2026-04")
            
        Returns:
            필터링된 행사 목록
        """
        filtered = []
        
        for event in events:
            start_date = event.get("start_date", "")
            
            if not start_date:
                continue
            
            # ISO 형식 날짜 파싱 (예: "2026-04-25T15:00:00.000Z")
            try:
                # UTC 시간이므로 한국 시간으로 변환 필요 (UTC+9)
                dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                
                # 한국 시간으로 변환 (단순화: +9시간)
                from datetime import timedelta
                kst_dt = dt + timedelta(hours=9)
                
                event_year_month = kst_dt.strftime("%Y-%m")
                
                if event_year_month == year_month:
                    filtered.append(event)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"날짜 파싱 실패: {start_date} - {e}")
                continue
        
        logger.info(f"{year_month} 행사: {len(filtered)}개")
        return filtered
    
    def convert_to_event_format(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """
        API 응답을 EVENT_INFORMATION.json 형식으로 변환
        
        Args:
            events: API 응답 행사 목록
            
        Returns:
            {DATE: [행사목록]} 형식의 딕셔너리
        """
        result = {}
        
        for event in events:
            event_id = event.get("event_id", "")
            title = event.get("title", "")
            start_date = event.get("start_date", "")
            
            if not event_id or not start_date:
                continue
            
            try:
                # 날짜 파싱
                dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                from datetime import timedelta
                kst_dt = dt + timedelta(hours=9)
                
                # DATE 형식 생성 (예: "25년_4월")
                year_suffix = str(kst_dt.year)[-2:]  # 뒤 2자리
                month = kst_dt.month
                date_key = f"{year_suffix}년_{month}월"
                
                # DAY 계산 (토=Day1, 일=Day2, 그 외는 요일명)
                weekday = kst_dt.weekday()  # 0=월, 5=토, 6=일
                if weekday == 5:  # 토요일
                    day = "Day1"
                elif weekday == 6:  # 일요일
                    day = "Day2"
                else:
                    # 평일인 경우 요일명 사용
                    day_names = ["월", "화", "수", "목", "금", "토", "일"]
                    day = day_names[weekday]
                
                # 행사 정보 생성
                event_info = {
                    "CODE": event_id,
                    "NAME": title,
                    "DAY": day
                }
                
                # 결과에 추가
                if date_key not in result:
                    result[date_key] = []
                
                result[date_key].append(event_info)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"행사 변환 실패: {event_id} - {e}")
                continue
        
        return result
    
    def save_event_information(
        self, 
        events_by_date: Dict[str, List[Dict]], 
        output_path: str = "EVENT_INFORMATION.json",
        mode: str = "merge"
    ) -> str:
        """
        EVENT_INFORMATION.json 저장
        
        Args:
            events_by_date: {DATE: [행사목록]} 형식의 데이터
            output_path: 출력 파일 경로
            mode: 저장 모드 ("merge" | "overwrite")
            
        Returns:
            저장된 파일 경로
        """
        output_file = Path(output_path)
        
        # 기존 데이터 로드 (merge 모드인 경우)
        existing_data = []
        if mode == "merge" and output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # 기존 데이터를 DATE 기준으로 딕셔너리화
        existing_by_date = {}
        for item in existing_data:
            date = item.get("DATE", "")
            if date:
                existing_by_date[date] = item.get("INFO", [])
        
        # 새 데이터 병합
        for date, info_list in events_by_date.items():
            if date in existing_by_date:
                # 기존 데이터와 병합 (중복 제거)
                existing_codes = {e["CODE"] for e in existing_by_date[date]}
                for info in info_list:
                    if info["CODE"] not in existing_codes:
                        existing_by_date[date].append(info)
            else:
                existing_by_date[date] = info_list
        
        # 최종 데이터 구성
        final_data = []
        for date, info in sorted(existing_by_date.items()):
            final_data.append({
                "DATE": date,
                "INFO": info
            })
        
        # 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"저장 완료: {output_file}")
        
        return str(output_file)


def fetch_events_by_month(year_month: str, output_path: str = "EVENT_INFORMATION.json") -> str:
    """
    특정 월 행사 수집 편의 함수
    
    Args:
        year_month: 연월 (예: "2026-04")
        output_path: 출력 파일 경로
        
    Returns:
        저장된 파일 경로
    """
    fetcher = EventFetcher()
    
    # 전체 행사 수집
    all_events = fetcher.fetch_all_events()
    
    # 해당 월 필터링
    filtered = fetcher.filter_by_month(all_events, year_month)
    
    if not filtered:
        logger.warning(f"{year_month}에 해당하는 행사가 없습니다.")
        return ""
    
    # 형식 변환
    events_by_date = fetcher.convert_to_event_format(filtered)
    
    # 저장 (merge 모드)
    return fetcher.save_event_information(events_by_date, output_path, mode="merge")


def fetch_all_events(output_path: str = "EVENT_INFORMATION.json") -> str:
    """
    전체 행사 수집 편의 함수
    
    Args:
        output_path: 출력 파일 경로
        
    Returns:
        저장된 파일 경로
    """
    fetcher = EventFetcher()
    
    # 전체 행사 수집
    all_events = fetcher.fetch_all_events()
    
    # 형식 변환
    events_by_date = fetcher.convert_to_event_format(all_events)
    
    # 저장 (overwrite 모드)
    return fetcher.save_event_information(events_by_date, output_path, mode="overwrite")


def main():
    parser = argparse.ArgumentParser(
        description="동인네트워크 행사 정보 자동 수집"
    )
    parser.add_argument(
        "--month",
        help="수집할 연월 (예: '2026-04')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="전체 행사 수집"
    )
    parser.add_argument(
        "--output",
        default="EVENT_INFORMATION.json",
        help="출력 파일 경로 (기본값: EVENT_INFORMATION.json)"
    )
    
    args = parser.parse_args()
    
    if not args.month and not args.all:
        parser.error("--month 또는 --all 중 하나를 지정해야 합니다.")
    
    print("=" * 60)
    print("동인네트워크 행사 정보 수집기")
    print("=" * 60)
    
    if args.all:
        print("전체 행사 수집 모드")
        output_path = fetch_all_events(args.output)
    else:
        print(f"수집 대상: {args.month}")
        output_path = fetch_events_by_month(args.month, args.output)
    
    if output_path:
        print()
        print("=" * 60)
        print(f"✅ 수집 완료!")
        print(f"📁 저장 위치: {output_path}")
        print("=" * 60)
    else:
        print()
        print("❌ 수집된 행사가 없습니다.")


if __name__ == "__main__":
    main()

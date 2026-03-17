"""
Raw 데이터 내보내기

API에서 수집한 데이터를 CSV로 내보내는 모듈입니다.
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

import pandas as pd

from .api_client import DongneAPIClient

logger = logging.getLogger(__name__)


class RawExporter:
    """Raw 데이터 내보내기 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.client = DongneAPIClient(config_path)
        
        # 설정에서 경로 로드
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.event_info_path = Path(config['crawling']['event_info_path'])
        self.output_dir = Path(config['crawling']['output_dir'])
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_events(self, date: str) -> List[Dict]:
        """
        행사 정보 로드
        
        Args:
            date: 날짜 문자열 (예: "25년_4월")
            
        Returns:
            해당 날짜의 행사 리스트
        """
        if not self.event_info_path.exists():
            raise FileNotFoundError(
                f"행사 정보 파일을 찾을 수 없습니다: {self.event_info_path}\n"
                "EVENT_INFORMATION.json 파일을 프로젝트 루트에 배치해주세요."
            )
        
        with open(self.event_info_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # 해당 날짜의 이벤트 필터링
        date_events = [e for e in events if e.get('DATE') == date]
        
        if not date_events:
            raise ValueError(f"해당 날짜의 행사 정보가 없습니다: {date}")
        
        return date_events[0].get('INFO', [])
    
    def crawl_and_export(self, date: str, output_filename: Optional[str] = None) -> str:
        """
        크롤링 후 CSV로 내보내기
        
        Args:
            date: 날짜 문자열 (예: "25년_4월")
            output_filename: 출력 파일명 (기본값: raw_{date}.csv)
            
        Returns:
            저장된 파일 경로
        """
        logger.info(f"크롤링 시작: {date}")
        
        # 행사 정보 로드
        events = self.load_events(date)
        
        # 이벤트 리스트 생성
        event_list = [e['CODE'] for e in events]
        event_dict = {e['CODE']: e['NAME'] for e in events}
        day_dict = {e['NAME']: e['DAY'] for e in events}
        
        logger.info(f"총 {len(event_list)}개 행사 크롤링 예정")
        
        # 전체 부스 데이터 수집
        all_circles = []
        
        for i, event_code in enumerate(event_list, 1):
            event_name = event_dict.get(event_code, "")
            event_day = day_dict.get(event_name, "")
            
            circles = self.client.crawl_event(event_code, event_name, event_day)
            all_circles.extend(circles)
            
            logger.info(f"진행: {i}/{len(event_list)} - {event_name} ({len(circles)}개 부스)")
        
        # DataFrame 생성
        df = pd.DataFrame(all_circles)
        
        # 컬럼 순서 정렬 (field_mapping.yaml의 output_columns 기준)
        df = self._reorder_columns(df)
        
        # CSV 저장
        if output_filename is None:
            output_filename = f"raw_{date}.csv"
        
        output_path = self.output_dir / output_filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"크롤링 완료: 총 {len(df)}개 부스 → {output_path}")
        
        return str(output_path)
    
    def _reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼 순서 정렬"""
        import yaml
        
        mapping_path = Path(__file__).parent.parent / "config" / "field_mapping.yaml"
        with open(mapping_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        output_columns = config.get('output_columns', [])
        
        # 실제 존재하는 컬럼만 필터링
        existing_columns = [col for col in output_columns if col in df.columns]
        
        # 나머지 컬럼은 뒤에 추가
        remaining_columns = [col for col in df.columns if col not in existing_columns]
        
        return df[existing_columns + remaining_columns]


def crawl_raw_data(date: str, config_path: Optional[str] = None) -> str:
    """
    Raw 데이터 크롤링 편의 함수
    
    Args:
        date: 날짜 문자열 (예: "25년_4월")
        config_path: 설정 파일 경로
        
    Returns:
        저장된 파일 경로
    """
    exporter = RawExporter(config_path)
    return exporter.crawl_and_export(date)

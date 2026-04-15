"""
동인네트워크 API 클라이언트

동인네트워크의 부스 정보를 API를 통해 수집하는 모듈입니다.
"""

import json
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path

import requests
import yaml

logger = logging.getLogger(__name__)


class DongneAPIClient:
    """동인네트워크 API 클라이언트"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.base_url = self.config['api']['base_url']
        self.endpoints = self.config['api']['endpoints']
        self.default_params = self.config['api']['default_params']
        self.request_delay = self.config['crawling']['request_delay']
    
    def get_petitzone_list(self, event_id: str) -> Dict[str, str]:
        """
        쁘띠존 목록 조회
        
        Args:
            event_id: 행사 slug
            
        Returns:
            {petit_id: petit_title} 딕셔너리
        """
        endpoint = self.endpoints['petits'].format(event_id=event_id)
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            petit_dict = {}
            for item in data.get("petitZones", []):
                petit_id = str(item.get("id", ""))
                petit_title = str(item.get("title", ""))
                if petit_id:
                    petit_dict[petit_id] = petit_title
            
            logger.info(f"쁘띠존 {len(petit_dict)}개 로드 완료 (event_id: {event_id})")
            return petit_dict
            
        except requests.RequestException as e:
            logger.error(f"쁘띠존 로드 실패 (event_id: {event_id}): {e}")
            return {}
    
    def get_circles(self, event_id: str) -> List[Dict]:
        """
        부스(서클) 목록 조회 (페이지네이션 지원)
        
        Args:
            event_id: 행사 slug
            
        Returns:
            부스 정보 리스트
        """
        endpoint = self.endpoints['circles'].format(event_id=event_id)
        url = f"{self.base_url}{endpoint}"
        limit = self.default_params.get('limit', 100)
        
        all_items = []
        page = 1
        
        try:
            while True:
                params = {"limit": limit, "page": page}
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("data", {}).get("items", [])
                all_items.extend(items)
                
                pagination = data.get("data", {}).get("pagination", {})
                total_pages = pagination.get("totalPages", 1)
                
                logger.info(f"부스 페이지 {page}/{total_pages} 로드 완료 ({len(items)}개)")
                
                if page >= total_pages:
                    break
                
                page += 1
                time.sleep(self.request_delay)
            
            logger.info(f"부스 총 {len(all_items)}개 로드 완료 (event_id: {event_id})")
            return all_items
            
        except requests.RequestException as e:
            logger.error(f"부스 로드 실패 (event_id: {event_id}): {e}")
            return []
    
    def crawl_event(self, event_id: str, event_name: str, event_day: str) -> List[Dict]:
        """
        단일 행사 크롤링
        """
        logger.info(f"행사 크롤링 시작: {event_name} (ID: {event_id})")
        
        circles = self.get_circles(event_id)
        
        if not circles:
            logger.warning(f"부스 데이터가 없습니다: {event_name}")
            return []
        
        parsed_circles = []
        for circle in circles:
            parsed = self._parse_circle(circle, event_id, event_name, event_day)
            parsed_circles.append(parsed)
        
        logger.info(f"행사 크롤링 완료: {event_name} - {len(parsed_circles)}개 부스")
        return parsed_circles
    
    def _parse_circle(
        self, 
        circle: Dict,
        event_id: str,
        event_name: str,
        event_day: str
    ) -> Dict:
        """
        단일 부스 정보 파싱
        """
        circle_name = str(circle.get("circleName", ""))
        owner_name = str(circle.get("ownerName", ""))
        seat_labels = circle.get("seatLabels", [])
        booth_count = circle.get("boothCount", "")
        application_id = circle.get("applicationId", "")
        
        seat = seat_labels[0] if seat_labels else ""
        
        location_col, location_num, half_booth = self._parse_seat(seat)
        
        booth_size = f"{booth_count}sp" if booth_count else ""
        
        fields = circle.get("fields", [])
        fields_dict = {}
        for field in fields:
            system_key = field.get("systemKey", "")
            value = field.get("value", "")
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            fields_dict[system_key] = value
        
        field_mapping = self._load_field_mapping()
        
        parsed = {
            "부스명": circle_name,
            "대표자": owner_name,
            "위치": seat,
            "위치(열)": location_col,
            "위치(번호)": location_num,
            "반부스": half_booth,
            "부스": booth_size,
            "링크": f"https://dongne.co/events/{event_id}/circles/{application_id}",
            "행사명": event_name,
            "개최일": event_day
        }
        
        for system_key, field_name in field_mapping.items():
            if system_key == "twitter":
                parsed[field_name] = str(fields_dict.get(system_key, ""))
            else:
                value = str(fields_dict.get(system_key, ""))
                parsed[field_name] = value
        
        return parsed
    
    def _parse_seat(self, seat: str) -> tuple:
        if not seat:
            return ("", "", "")
        
        parts = seat.split("-")
        if len(parts) >= 2:
            col = parts[0]
            num = parts[1]
            last_char = num[-1] if num else ""
            if last_char.isdigit():
                return (col, num, "")
            else:
                return (col, num[:-1], last_char)
        
        return (seat, "", "")
    
    def _load_field_mapping(self) -> Dict[str, str]:
        """필드 매핑 로드"""
        mapping_path = Path(__file__).parent.parent / "config" / "field_mapping.yaml"
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config.get('field_mapping', {})

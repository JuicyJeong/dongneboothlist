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
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로 (기본값: src/config/settings.yaml)
        """
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
            event_id: 행사 ID
            
        Returns:
            {petit_id: petit_title} 딕셔너리
        """
        url = f"{self.base_url}{self.endpoints['petits']}"
        params = {
            "event_id": event_id,
            "page": 1,
            "per_page": 50,
            "keyword": "",
            "desc": "DESC",
            "last": "false"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            petit_dict = {}
            for item in data.get("list", []):
                petit_id = str(item.get("petit_id", ""))
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
        부스(서클) 목록 조회
        
        Args:
            event_id: 행사 ID
            
        Returns:
            부스 정보 리스트
        """
        url = f"{self.base_url}{self.endpoints['circles']}"
        params = {
            "event_id": event_id,
            "form": "owner_name,twitter,seat,booth,petit_promotion_booth,10155,10199,10229,rule_main,rule_sub,10200,"
                    "petitzone,10202,10225,10204,10233,10226,10232,10208,10209",
            "page": 1,
            "per_page": 1000,
            "original": "",
            "petitzone": "",
            "fav": "",
            "color": "",
            "target": "",
            "keyword": "",
            "orderby": "",
            "sort": "",
            "sorting": "false",
            "last": "false"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            circles = data.get("list", [])
            logger.info(f"부스 {len(circles)}개 로드 완료 (event_id: {event_id})")
            return circles
            
        except requests.RequestException as e:
            logger.error(f"부스 로드 실패 (event_id: {event_id}): {e}")
            return []
    
    def crawl_event(self, event_id: str, event_name: str, event_day: str) -> List[Dict]:
        """
        단일 행사 크롤링
        
        Args:
            event_id: 행사 ID
            event_name: 행사명
            event_day: 개최일
            
        Returns:
            부스 정보 리스트 (파싱된 형태)
        """
        logger.info(f"행사 크롤링 시작: {event_name} (ID: {event_id})")
        
        # 쁘띠존 목록 로드
        petit_dict = self.get_petitzone_list(event_id)
        petit_dict[""] = ""  # 빈 값 처리
        
        # 부스 목록 로드
        circles = self.get_circles(event_id)
        
        if not circles:
            logger.warning(f"부스 데이터가 없습니다: {event_name}")
            return []
        
        # 각 부스 정보 파싱
        parsed_circles = []
        for circle in circles:
            parsed = self._parse_circle(circle, petit_dict, event_id, event_name, event_day)
            parsed_circles.append(parsed)
        
        time.sleep(self.request_delay)
        
        logger.info(f"행사 크롤링 완료: {event_name} - {len(parsed_circles)}개 부스")
        return parsed_circles
    
    def _parse_circle(
        self, 
        circle: Dict, 
        petit_dict: Dict[str, str],
        event_id: str,
        event_name: str,
        event_day: str
    ) -> Dict:
        """
        단일 부스 정보 파싱
        
        Args:
            circle: 원시 부스 데이터
            petit_dict: 쁘띠존 매핑
            event_id: 행사 ID
            event_name: 행사명
            event_day: 개최일
            
        Returns:
            파싱된 부스 정보
        """
        # 기본 정보
        circle_name = str(circle.get("circle_name", ""))
        owner_name = str(circle.get("owner_name", ""))
        seat = str(circle.get("seat", ""))
        booth = str(circle.get("booth", ""))
        application_srl = circle.get("application_srl", "")
        
        # 위치 파싱 (열, 번호, 반부스)
        location_col, location_num, half_booth = self._parse_seat(seat)
        
        # 부스 사이즈
        booth_size = f"{booth}sp" if booth else ""
        
        # extra_vars 파싱
        extra_vars = circle.get("extra_vars", {})
        
        # 필드 매핑 로드
        field_mapping = self._load_field_mapping()
        
        # 파싱된 데이터 구성
        parsed = {
            "부스명": circle_name,
            "대표자": owner_name,
            "위치": seat,
            "위치(열)": location_col,
            "위치(번호)": location_num,
            "반부스": half_booth,
            "부스": booth_size,
            "링크": f"https://dongne.co/event/{event_id}/circles/{application_srl}",
            "행사명": event_name,
            "개최일": event_day
        }
        
        # extra_vars 필드 매핑
        for api_code, field_name in field_mapping.items():
            if api_code == "petitzone":
                # 쁘띠존은 ID→이름 변환
                petit_id = str(extra_vars.get(api_code, ""))
                parsed[field_name] = petit_dict.get(petit_id, "")
            elif api_code == "twitter":
                # 트위터는 그대로
                parsed[field_name] = str(extra_vars.get(api_code, ""))
            elif api_code in ["rule_main", "rule_sub"]:
                # 다이스페스타 전용 필드
                parsed[field_name] = str(extra_vars.get(api_code, ""))
            else:
                # 코드 기반 필드
                value = str(extra_vars.get(api_code, ""))
                # 커플링은 쉼표를 X로 변환
                if api_code == "10233":
                    value = value.replace(",", "X")
                parsed[field_name] = value
        
        return parsed
    
    def _parse_seat(self, seat: str) -> tuple:
        """
        위치 문자열 파싱
        
        Args:
            seat: 위치 문자열 (예: "A23", "B15c")
            
        Returns:
            (열, 번호, 반부스) 튜플
        """
        if not seat:
            return ("", "", "")
        
        # 첫 문자 = 열
        location_col = seat[0]
        
        # 마지막 문자 확인
        last_char = seat[-1]
        
        if last_char.isdigit():
            # 마지막이 숫자 → 반부스 없음 (예: A23)
            location_num = seat[1:]
            half_booth = ""
        else:
            # 마지막이 문자 → 반부스 (예: A23b)
            location_num = seat[1:-1]
            half_booth = last_char
        
        return (location_col, location_num, half_booth)
    
    def _load_field_mapping(self) -> Dict[str, str]:
        """필드 매핑 로드"""
        mapping_path = Path(__file__).parent.parent / "config" / "field_mapping.yaml"
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config.get('field_mapping', {})

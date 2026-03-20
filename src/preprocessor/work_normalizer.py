"""
대표작품 정규화기

유사도 사전을 사용하여 대표작품명을 정규화합니다.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WorkNormalizer:
    """대표작품 정규화기"""
    
    def __init__(self, dict_path: str = "work_similarity_dict.json"):
        """
        초기화
        
        Args:
            dict_path: 유사도 사전 파일 경로
        """
        self.dict_path = Path(dict_path)
        self.similarity_dict = self._load_dict()
    
    def _load_dict(self) -> Dict[str, str]:
        """유사도 사전 로드"""
        if not self.dict_path.exists():
            logger.warning(f"유사도 사전을 찾을 수 없습니다: {self.dict_path}")
            return {}
        
        with open(self.dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"유사도 사전 로드: {len(data)}개 항목")
        return data
    
    def normalize(self, work_name: str) -> str:
        """
        작품명 정규화
        
        Args:
            work_name: 원본 작품명
            
        Returns:
            정규화된 작품명 (사전에 없으면 원본 그대로)
        """
        if not work_name or work_name == "nan":
            return ""
        
        # 사전에서 찾기
        normalized = self.similarity_dict.get(work_name)
        
        if normalized:
            # SKIP이면 빈 문자열 반환
            if normalized == "SKIP":
                return ""
            return normalized
        
        # 사전에 없으면 원본 그대로
        return work_name
    
    def normalize_with_original(self, work_name: str) -> tuple:
        """
        작품명 정규화 (원본도 함께 반환)
        
        Args:
            work_name: 원본 작품명
            
        Returns:
            (정규화된 작품명, 원본 작품명) 튜플
        """
        normalized = self.normalize(work_name)
        original = work_name if work_name and work_name != "nan" else ""
        
        return (normalized, original)

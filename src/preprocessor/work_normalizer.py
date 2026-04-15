"""
대표작품 정규화기

works_dictionary.yaml을 사용하여 작품명을 정규화합니다.
"""

import logging
from pathlib import Path
from typing import Dict

import yaml

logger = logging.getLogger(__name__)


class WorkNormalizer:
    """대표작품 정규화기"""
    
    def __init__(self, dict_path: str = None):
        if dict_path is None:
            dict_path = Path(__file__).parent.parent / "config" / "works_dictionary.yaml"
        self.dict_path = Path(dict_path)
        self.normalize_map = self._build_map()
    
    def _build_map(self) -> Dict[str, str]:
        """works_dictionary.yaml에서 variant→canonical 매핑 생성"""
        if not self.dict_path.exists():
            logger.warning(f"작품 사전을 찾을 수 없습니다: {self.dict_path}")
            return {}
        
        with open(self.dict_path, 'r', encoding='utf-8') as f:
            dictionary = yaml.safe_load(f)
        
        mapping = {}
        for canonical, variants in dictionary.items():
            if canonical == '미분류' or variants is None:
                continue
            mapping[str(canonical)] = str(canonical)
            if isinstance(variants, list):
                for v in variants:
                    mapping[str(v)] = str(canonical)
        
        logger.info(f"작품 사전 로드: {len(dictionary) - 1}개 canonical, {len(mapping)}개 매핑")
        return mapping
    
    def normalize(self, work_name: str) -> str:
        if not work_name or work_name == "nan":
            return ""
        
        stripped = work_name.strip()
        if stripped in self.normalize_map:
            return self.normalize_map[stripped]
        
        return stripped
    
    def normalize_with_original(self, work_name: str) -> tuple:
        normalized = self.normalize(work_name)
        original = work_name if work_name and work_name != "nan" else ""
        return (normalized, original)

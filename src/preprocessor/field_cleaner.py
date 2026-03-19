"""
필드 정제 모듈

트위터 아이디 등의 필드를 정제하는 모듈입니다.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TwitterCleaner:
    """트위터 아이디 정제기"""
    
    # URL에서 아이디 추출 패턴
    URL_PATTERN = r'https?://(?:twitter|x)\.com/([a-zA-Z0-9_]{1,15})'
    
    # @로 시작하는 아이디 패턴
    AT_ID_PATTERN = r'@([a-zA-Z0-9_]{1,15})'
    
    def clean(self, value: str) -> str:
        """
        트위터 아이디/아이디들 정제
        
        Args:
            value: 원시 트위터 필드 값
            
        Returns:
            정제된 트위터 아이디 (여러 개면 쉼표로 구분)
        """
        if not value or not isinstance(value, str):
            return ""
        
        original = value
        value = value.strip()
        
        # 빈 값 체크
        if not value or value in ['.', '-', '없음']:
            return ""
        
        ids = []
        
        # 1. URL에서 아이디 추출
        url_ids = re.findall(self.URL_PATTERN, value)
        ids.extend(url_ids)
        
        # URL 제거
        value = re.sub(self.URL_PATTERN, '', value)
        
        # 2. @로 시작하는 아이디 추출
        at_ids = re.findall(self.AT_ID_PATTERN, value)
        ids.extend(at_ids)
        
        # @ 아이디 제거
        value = re.sub(self.AT_ID_PATTERN, '', value)
        
        # 3. 남은 텍스트에서 유효한 아이디 추출
        # 괄호, 설명 텍스트 등 제거 후 단어 단위로 분리
        remaining = re.sub(r'\([^)]*\)', '', value)  # 괄호 제거
        remaining = re.sub(r'[^\w\s]', ' ', remaining)  # 특수문자 제거
        words = remaining.split()
        
        for word in words:
            word = word.strip().lower()
            if not word:
                continue
            # 유효한 아이디 패턴 (영문/숫자/밑줄)
            if re.match(r'^[a-zA-Z0-9_]{1,15}$', word):
                if word not in ids:  # 중복 방지
                    ids.append(word)
            elif len(word) <= 30:  # 너무 긴 것은 무시하지만 로그 기록
                # 소셜 도메인 제외
                if not any(domain in word for domain in ['bsky', 'instagram', 'insta']):
                    logger.debug(f"처리되지 않은 텍스트: '{word}' (원본: '{original}')")
        
        # 중복 제거 + 소문자화
        ids = [id.lower() for id in ids]
        ids = list(dict.fromkeys(ids))  # 순서 유지하며 중복 제거
        
        return ', '.join(ids)


class FieldCleaner:
    """필드 정제기 (종합)"""
    
    def __init__(self):
        self.twitter_cleaner = TwitterCleaner()
    
    def clean_twitter(self, value: str) -> str:
        """트위터 필드 정제"""
        return self.twitter_cleaner.clean(value)
    
    def clean_all(self, row: dict) -> dict:
        """
        모든 필드 정제
        
        Args:
            row: 원시 데이터 행
            
        Returns:
            정제된 데이터 행
        """
        # 트위터 정제
        if '트위터' in row:
            row['트위터'] = self.clean_twitter(row['트위터'])
        
        return row

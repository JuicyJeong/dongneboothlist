#!/usr/bin/env python3
"""
LLM 기반 작품명 정규화

GLM5 API를 사용하여 작품명을 정규화합니다.

Usage:
    python scripts/llm_normalize_works.py --input data/dict/collected_works.json --output data/dict/normalized_works.json
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GLM5Normalizer:
    """GLM5 API 기반 작품명 정규화기"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.z.ai/api/paas/v4/chat/completions"):
        """
        초기화
        
        Args:
            api_key: z.ai API 키
            api_base: API 엔드포인트
        """
        self.api_key = api_key
        self.api_base = api_base
        self.cache_file = Path("data/dict/llm_cache.json")
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """캐시 로드"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """캐시 저장"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def normalize_batch(self, works: List[str], batch_size: int = 20) -> Dict[str, str]:
        """
        작품명 배치 정규화
        
        Args:
            works: 작품명 리스트
            batch_size: 배치 크기
            
        Returns:
            {원본: 정규화된_이름} 딕셔너리
        """
        results = {}
        total = len(works)
        
        for i in range(0, total, batch_size):
            batch = works[i:i+batch_size]
            logger.info(f"처리 중: {i+1}-{min(i+batch_size, total)}/{total}")
            
            # 캐시 확인
            uncached = [w for w in batch if w not in self.cache]
            
            if uncached:
                # API 호출
                normalized = self._call_api(uncached)
                
                # 캐시 업데이트
                for orig, norm in normalized.items():
                    self.cache[orig] = norm
                
                self._save_cache()
                time.sleep(5)  # Rate limit 방지 (5초)
            
            # 결과 수집
            for work in batch:
                results[work] = self.cache.get(work, work)
        
        return results
    
    def _call_api(self, works: List[str]) -> Dict[str, str]:
        """
        GLM5 API 호출
        
        Args:
            works: 작품명 리스트
            
        Returns:
            {원본: 정규화된_이름} 딕셔너리
        """
        prompt = self._build_prompt(works)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "glm-4.7",  # GLM 4.7 모델
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 동인 행사 부스의 대표 작품명을 정규화하는 전문가입니다. 한국어, 일본어, 영어 작품명을 모두 이해합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_base, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 결과 파싱
            return self._parse_response(content, works)
            
        except Exception as e:
            logger.error(f"API 호출 실패: {e}")
            # 실패 시 원본 반환
            return {w: w for w in works}
    
    def _build_prompt(self, works: List[str]) -> str:
        """프롬프트 생성"""
        works_str = "\n".join([f"{i+1}. {w}" for i, w in enumerate(works)])
        
        return f"""다음 작품명들을 정규화해주세요.

규칙:
1. 공식 명칭으로 변환 (띄어쓰기, 대소문자, 특수문자 정리)
2. 넘버링/부제는 유지 (예: 파이널판타지14, 페르소나5로얄)
3. 줄임말/별칭은 공식 명칭으로 변환
4. 장르/카테이너리면 "SKIP" 표시 (예: BL, 1차창작, 수공예)
5. 시리즈명은 넘버링 없이 표시 (예: 발더스 게이트 → 발더스 게이트 (시리즈))
6. JSON 형식으로 출력

작품명 목록:
{works_str}

출력 형식:
{{
  "원본명": "정규화된명",
  ...
}}"""
    
    def _parse_response(self, content: str, works: List[str]) -> Dict[str, str]:
        """API 응답 파싱"""
        try:
            # JSON 추출
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                logger.warning("JSON 형식을 찾을 수 없음")
                return {w: w for w in works}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return {w: w for w in works}


def main():
    parser = argparse.ArgumentParser(
        description="LLM 기반 작품명 정규화"
    )
    parser.add_argument(
        "--input",
        default="data/dict/collected_works.json",
        help="입력 파일 (수집된 작품명)"
    )
    parser.add_argument(
        "--output",
        default="data/dict/normalized_works.json",
        help="출력 파일 (정규화된 작품명)"
    )
    parser.add_argument(
        "--api-key",
        help="GLM5 API 키 (또는 GLM5_API_KEY 환경변수)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="배치 크기 (기본값: 5)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="처리할 작품 수 제한 (테스트용)"
    )
    
    args = parser.parse_args()
    
    # API 키 확인
    api_key = args.api_key or os.getenv("GLM5_API_KEY")
    if not api_key:
        logger.error("API 키가 필요합니다. --api-key 또는 GLM5_API_KEY 환경변수를 설정하세요.")
        import sys
        sys.exit(1)
    
    # 입력 파일 로드
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"입력 파일을 찾을 수 없습니다: {input_path}")
        import sys
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        works_dict = json.load(f)
    
    works = list(works_dict.keys())
    
    if args.limit:
        works = works[:args.limit]
    
    logger.info(f"작품명 로드 완료: {len(works)}개")
    
    # 정규화 실행
    normalizer = GLM5Normalizer(api_key)
    normalized = normalizer.normalize_batch(works, batch_size=args.batch_size)
    
    # 저장
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    
    logger.info(f"정규화 완료: {output_path}")
    
    # 통계
    skipped = sum(1 for v in normalized.values() if v == "SKIP")
    changed = sum(1 for k, v in normalized.items() if k != v and v != "SKIP")
    
    print()
    print("=" * 60)
    print(f"✅ 정규화 완료!")
    print(f"   - 처리된 작품: {len(normalized)}개")
    print(f"   - 변경됨: {changed}개")
    print(f"   - SKIP (장르): {skipped}개")
    print(f"📁 저장 위치: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

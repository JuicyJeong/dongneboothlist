#!/usr/bin/env python3
"""
모듈 2: 전체 전처리

트위터 아이디 + 대표작품 전처리를 모두 수행합니다.

Usage:
    python scripts/02_preprocess_all.py --date "26년_4월"
"""

import argparse
import logging
import sys
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_all_preprocessing(date: str) -> dict:
    """
    모든 전처리 실행
    
    Args:
        date: 날짜 문자열 (예: "26년_4월")
        
    Returns:
        결과 파일 경로 딕셔너리
    """
    results = {}
    
    # 2a: 트위터 전처리
    logger.info("=" * 60)
    logger.info("모듈 2a: 트위터 아이디 전처리 시작")
    logger.info("=" * 60)
    
    from pyimport import runpy
    import subprocess
    
    result = subprocess.run(
        [sys.executable, "scripts/02a_preprocess_twitter.py", "--date", date],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"트위터 전처리 실패: {result.stderr}")
        raise RuntimeError("트위터 전처리 실패")
    
    results['twitter'] = f"data/preprocessed/preprocessed_twitter_{date}.csv"
    logger.info(f"✅ 트위터 전처리 완료")
    
    # 2b: 대표작품 전처리
    logger.info("=" * 60)
    logger.info("모듈 2b: 대표작품 전처리 시작")
    logger.info("=" * 60)
    
    result = subprocess.run(
        [sys.executable, "scripts/02b_preprocess_works.py", "--date", date],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"대표작품 전처리 실패: {result.stderr}")
        raise RuntimeError("대표작품 전처리 실패")
    
    results['works'] = f"data/preprocessed/preprocessed_{date}.csv"
    logger.info(f"✅ 대표작품 전처리 완료")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="전체 전처리 (트위터 + 대표작품)"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="전처리할 날짜 (예: '26년_4월')"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("모듈 2: 전체 전처리")
    print("=" * 60)
    print(f"전처리 날짜: {args.date}")
    print()
    
    try:
        results = run_all_preprocessing(args.date)
        
        print()
        print("=" * 60)
        print("✅ 전체 전처리 완료!")
        print("=" * 60)
        print("📁 결과물:")
        for name, path in results.items():
            print(f"   - {name}: {path}")
        print("=" * 60)
        
    except Exception as e:
        logger.exception(f"전처리 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

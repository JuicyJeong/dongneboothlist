#!/usr/bin/env python3
"""
모듈 2a: 트위터 아이디 전처리

트위터 아이디만 전처리하여 저장합니다.

Usage:
    python scripts/02a_preprocess_twitter.py --date "26년_4월"
"""

import argparse
import logging
from pathlib import Path
import sys

import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessor.field_cleaner import FieldCleaner

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def preprocess_twitter(date: str, input_dir: str = "data/raw", output_dir: str = "data/preprocessed") -> str:
    """
    트위터 아이디만 전처리
    
    Args:
        date: 날짜 문자열 (예: "26년_4월")
        input_dir: 입력 디렉토리
        output_dir: 출력 디렉토리
        
    Returns:
        저장된 파일 경로
    """
    cleaner = FieldCleaner()
    
    # 경로 설정
    input_path = Path(input_dir) / f"raw_{date}.csv"
    output_path = Path(output_dir) / f"preprocessed_twitter_{date}.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")
    
    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"트위터 전처리 시작: {input_path}")
    
    # 데이터 로드
    df = pd.read_csv(input_path)
    logger.info(f"로드된 데이터: {len(df)}개 행")
    
    # 트위터 필드 정제
    if '트위터' in df.columns:
        logger.info("트위터 아이디 정제 중...")
        original = df['트위터'].copy()
        df['트위터'] = df['트위터'].apply(lambda x: cleaner.clean_twitter(str(x) if pd.notna(x) else ""))
        
        changed = (original != df['트위터']).sum()
        logger.info(f"트위터 필드 변경: {changed}개")
    
    # 저장
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"전처리 완료: {output_path}")
    
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="트위터 아이디 전처리"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="전처리할 날짜 (예: '26년_4월')"
    )
    parser.add_argument(
        "--input",
        default="data/raw",
        help="입력 디렉토리 (기본값: data/raw)"
    )
    parser.add_argument(
        "--output",
        default="data/preprocessed",
        help="출력 디렉토리 (기본값: data/preprocessed)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("모듈 2a: 트위터 아이디 전처리")
    print("=" * 60)
    print(f"전처리 날짜: {args.date}")
    print()
    
    try:
        output_path = preprocess_twitter(
            date=args.date,
            input_dir=args.input,
            output_dir=args.output
        )
        
        print()
        print("=" * 60)
        print(f"✅ 전처리 완료!")
        print(f"📁 저장 위치: {output_path}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"전처리 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

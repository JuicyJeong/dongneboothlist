#!/usr/bin/env python3
"""
모듈 2b: 대표작품 전처리

대표작품(원작) 필드만 전처리하여 저장합니다.
현재는 기본 정제만 수행하며, 유사도 사전 기능은 추후 추가 예정입니다.

Usage:
    python scripts/02b_preprocess_works.py --date "26년_4월"
"""

import argparse
import logging
from pathlib import Path
import sys

import pandas as pd

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def preprocess_works(date: str, input_dir: str = "data/preprocessed", output_dir: str = "data/preprocessed") -> str:
    """
    대표작품 필드 전처리
    
    Args:
        date: 날짜 문자열 (예: "26년_4월")
        input_dir: 입력 디렉토리 (트위터 전처리 결과)
        output_dir: 출력 디렉토리
        
    Returns:
        저장된 파일 경로
    """
    # 경로 설정
    input_path = Path(input_dir) / f"preprocessed_twitter_{date}.csv"
    output_path = Path(output_dir) / f"preprocessed_{date}.csv"
    
    if not input_path.exists():
        # 트위터 전처리 결과가 없으면 raw 데이터 사용
        input_path = Path("data/raw") / f"raw_{date}.csv"
        if not input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")
    
    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"대표작품 전처리 시작: {input_path}")
    
    # 데이터 로드
    df = pd.read_csv(input_path)
    logger.info(f"로드된 데이터: {len(df)}개 행")
    
    # TODO: 유사도 사전 로드 (사전 파일이 있을 경우)
    # TODO: 대표작품 정규화 적용
    
    # 현재는 기본 정제만 수행
    if '대표 작품(원작)' in df.columns:
        logger.info("대표작품 기본 정제 중...")
        
        # 기본 정제 (공백, 소문자 등)
        df['대표 작품(원작)'] = df['대표 작품(원작)'].apply(
            lambda x: str(x).strip() if pd.notna(x) else ""
        )
        
        logger.info("기본 정제 완료 (유사도 사전 미적용)")
    
    # 저장
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"전처리 완료: {output_path}")
    
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="대표작품 전처리"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="전처리할 날짜 (예: '26년_4월')"
    )
    parser.add_argument(
        "--input",
        default="data/preprocessed",
        help="입력 디렉토리 (기본값: data/preprocessed)"
    )
    parser.add_argument(
        "--output",
        default="data/preprocessed",
        help="출력 디렉토리 (기본값: data/preprocessed)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("모듈 2b: 대표작품 전처리")
    print("=" * 60)
    print(f"전처리 날짜: {args.date}")
    print()
    
    print("⚠️ 현재 유사도 사전이 없어 기본 정제만 수행합니다.")
    print("   유사도 사전 구축 후 정식 기능이 활성화됩니다.")
    print()
    
    try:
        output_path = preprocess_works(
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

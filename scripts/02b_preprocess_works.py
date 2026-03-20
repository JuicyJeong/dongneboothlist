#!/usr/bin/env python3
"""
모듈 2b: 대표작품 전처리

대표작품(원작) 필드를 정규화합니다.
원본 데이터를 별도 컬럼에 보존합니다.

Usage:
    python scripts/02b_preprocess_works.py --date "26년_4월"
"""

import argparse
import json
import logging
from pathlib import Path
import sys

import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessor.work_normalizer import WorkNormalizer

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
    
    # 정규화기 초기화
    normalizer = WorkNormalizer()
    logger.info(f"사전 로드 완료: {len(normalizer.similarity_dict)}개 항목")
    
    # 대표작품 컬럼 처리
    if '대표 작품(원작)' in df.columns:
        logger.info("대표작품 정규화 중...")
        
        # 원본 컬럼 보존
        df['대표 작품(원작)_원본'] = df['대표 작품(원작)'].apply(
            lambda x: str(x) if pd.notna(x) else ""
        )
        
        # 정규화 적용
        df['대표 작품(원작)'] = df['대표 작품(원작)_원본'].apply(normalizer.normalize)
        
        # SKIP된 것은 빈 문자열로
        df.loc[df['대표 작품(원작)'] == 'SKIP', '대표 작품(원작)'] = ""
        
        # 통계
        changed = (df['대표 작품(원작)'] != df['대표 작품(원작)_원본']).sum()
        skipped = (df['대표 작품(원작)_원본'] != "") & (df['대표 작품(원작)'] == "").sum()
        
        logger.info(f"변경됨: {changed}개")
        logger.info(f"SKIP (장르): {skipped}개")
    
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
        print()
        print("원본 데이터가 '대표 작품(원작)_원본' 컬럼에 보존되었습니다.")
        print("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"전처리 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

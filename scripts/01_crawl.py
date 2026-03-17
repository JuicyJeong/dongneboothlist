#!/usr/bin/env python3
"""
모듈 1: 동인네트워크 부스 크롤러

동인네트워크 API를 통해 부스 정보를 수집하고 raw CSV로 저장합니다.

Usage:
    python scripts/01_crawl.py --date "25년_4월"
    python scripts/01_crawl.py --date "25년_4월" --output "custom_name.csv"
"""

import argparse
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.raw_exporter import crawl_raw_data

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="동인네트워크 부스 크롤러 - Raw 데이터 수집"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="크롤링할 날짜 (예: '25년_4월')"
    )
    parser.add_argument(
        "--output",
        help="출력 파일명 (기본값: raw_{date}.csv)"
    )
    parser.add_argument(
        "--config",
        help="설정 파일 경로"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("동인네트워크 부스 크롤러 (모듈 1)")
    print("MADE BY PPJ (Twitter: @Juicy_Wave)")
    print("=" * 60)
    print(f"크롤링 날짜: {args.date}")
    print()
    
    try:
        output_path = crawl_raw_data(
            date=args.date,
            config_path=args.config
        )
        
        # output 인자가 있으면 해당 이름으로 리네임
        if args.output:
            import shutil
            new_path = Path(output_path).parent / args.output
            shutil.move(output_path, new_path)
            output_path = str(new_path)
        
        print()
        print("=" * 60)
        print(f"✅ 크롤링 완료!")
        print(f"📁 저장 위치: {output_path}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"크롤링 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

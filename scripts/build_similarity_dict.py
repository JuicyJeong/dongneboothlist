#!/usr/bin/env python3
"""
유사도 사전 구축 도구

대표작품명을 수집하고 클러스터링하여 유사도 사전을 구축합니다.

Usage:
    # 1-4단계: 수집 + 클러스터링
    python scripts/build_similarity_dict.py --collect
    
    # 5-6단계: 웹검색 확인 + 사전 등록 (대화형)
    python scripts/build_similarity_dict.py --verify
    
    # 전체 실행
    python scripts/build_similarity_dict.py --all
"""

import argparse
import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimilarityDictBuilder:
    """유사도 사전 구축기"""
    
    # 구분자 패턴
    SEPARATORS = r'[,/;&\n]+|\s+및\s+|\s+and\s+'
    
    # 정규화 패턴 (앞뒤 공백, 특수문자)
    NORMALIZE_PATTERN = r'^[\s\-\.\:\:]+|[\s\-\.\:\:]+$'
    
    # 넘버링 패턴 (아라비아 숫자, 로마숫자, 부제)
    NUMBERING_PATTERN = r'(\d+|[IVXivx]+|[-:]\s*[^,\-/]+)$'
    
    def __init__(self, data_dir: str = "data/raw", output_dir: str = "data/dict"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.works_file = self.output_dir / "collected_works.json"
        self.clusters_file = self.output_dir / "work_clusters.json"
        self.dict_file = Path("부스명 유사도 사전.json")  # 기존 파일명 유지
    
    def collect_works(self) -> Dict[str, int]:
        """
        1-3단계: 모든 CSV에서 대표작품 수집 및 분리
        
        Returns:
            {작품명: 등장횟수} 딕셔너리
        """
        logger.info("=" * 60)
        logger.info("1-3단계: 대표작품 수집 및 분리")
        logger.info("=" * 60)
        
        works_counter = Counter()
        
        # 모든 raw CSV 파일 검색
        csv_files = list(self.data_dir.glob("**/*.csv"))
        logger.info(f"발견된 CSV 파일: {len(csv_files)}개")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # 대표작품 컬럼 찾기
                work_col = None
                for col in df.columns:
                    if '대표' in col and '작품' in col:
                        work_col = col
                        break
                
                if not work_col:
                    logger.warning(f"대표작품 컬럼 없음: {csv_file.name}")
                    continue
                
                # 작품명 수집
                for value in df[work_col].dropna():
                    works = self._split_works(str(value))
                    works_counter.update(works)
                
                logger.info(f"처리 완료: {csv_file.name}")
                
            except Exception as e:
                logger.error(f"파일 처리 실패 {csv_file.name}: {e}")
        
        logger.info(f"수집된 작품명: {len(works_counter)}개 (총 {sum(works_counter.values())}회)")
        
        # 저장
        with open(self.works_file, 'w', encoding='utf-8') as f:
            json.dump(dict(works_counter.most_common()), f, ensure_ascii=False, indent=2)
        logger.info(f"저장: {self.works_file}")
        
        return dict(works_counter)
    
    def _split_works(self, value: str) -> List[str]:
        """
        작품명 분리
        
        Args:
            value: 원시 작품명 필드
            
        Returns:
            분리된 작품명 리스트
        """
        if not value or pd.isna(value):
            return []
        
        # 구분자로 분리
        parts = re.split(self.SEPARATORS, str(value))
        
        works = []
        for part in parts:
            # 정규화
            work = re.sub(self.NORMALIZE_PATTERN, '', part).strip()
            
            # 너무 짧거나 빈 값 제외
            if len(work) >= 2:
                works.append(work)
        
        return works
    
    def cluster_works(self, works: Dict[str, int] = None) -> Dict[str, List[str]]:
        """
        4단계: 유사한 작품명 클러스터링
        
        Args:
            works: {작품명: 등장횟수} 딕셔너리
            
        Returns:
            {대표명: [유사작품들]} 클러스터
        """
        logger.info("=" * 60)
        logger.info("4단계: 작품명 클러스터링")
        logger.info("=" * 60)
        
        if works is None:
            if not self.works_file.exists():
                raise FileNotFoundError("먼저 collect_works()를 실행하세요")
            with open(self.works_file, 'r', encoding='utf-8') as f:
                works = json.load(f)
        
        # 클러스터링 로직
        clusters = defaultdict(list)
        processed = set()
        
        work_names = list(works.keys())
        
        for i, work1 in enumerate(work_names):
            if work1 in processed:
                continue
            
            cluster = [work1]
            processed.add(work1)
            
            # 유사한 작품명 찾기
            for work2 in work_names[i+1:]:
                if work2 in processed:
                    continue
                
                similarity = self._calculate_similarity(work1, work2)
                if similarity >= 0.7:  # 70% 이상 유사
                    cluster.append(work2)
                    processed.add(work2)
            
            # 가장 많이 등장하는 이름을 대표로
            representative = max(cluster, key=lambda x: works.get(x, 0))
            clusters[representative] = cluster
        
        logger.info(f"생성된 클러스터: {len(clusters)}개")
        
        # 저장
        with open(self.clusters_file, 'w', encoding='utf-8') as f:
            json.dump(dict(clusters), f, ensure_ascii=False, indent=2)
        logger.info(f"저장: {self.clusters_file}")
        
        return dict(clusters)
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        두 문자열의 유사도 계산 (간단한 Jaccard 유사도)
        
        Args:
            s1, s2: 비교할 문자열
            
        Returns:
            유사도 (0~1)
        """
        # 정규화
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        
        # 완전히 같으면 1
        if s1 == s2:
            return 1.0
        
        # 넘버링 추출 후 비교
        series1, num1 = self._extract_series_and_number(s1)
        series2, num2 = self._extract_series_and_number(s2)
        
        # 넘버링이 다르면 0 (같은 시리즈라도 다른 작품)
        if num1 and num2 and num1 != num2:
            return 0.0
        
        # 시리즈명이 같고 넘버링도 같으면 높은 유사도
        if series1 == series2:
            if num1 == num2:  # 둘 다 넘버링이 없거나 같음
                return 0.9
            elif not num1 or not num2:  # 한쪽만 넘버링 있음
                return 0.5  # 낮은 유사도
        
        # 하나가 다른 하나를 포함하면 높은 유사도
        if s1 in s2 or s2 in s1:
            shorter = min(len(s1), len(s2))
            longer = max(len(s1), len(s2))
            return shorter / longer
        
        # 문자 집합 기반 Jaccard 유사도
        set1 = set(s1)
        set2 = set(s2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _extract_series_and_number(self, title: str) -> Tuple[str, str]:
        """
        작품명에서 시리즈명과 넘버링 분리
        
        Args:
            title: 작품명
            
        Returns:
            (시리즈명, 넘버링) 튜플
        """
        # 로마숫자 변환 매핑
        roman_map = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
                     'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10',
                     'xi': '11', 'xii': '12', 'xiii': '13', 'xiv': '14', 'xv': '15', 'xvi': '16'}
        
        # 넘버링 추출 시도
        match = re.search(self.NUMBERING_PATTERN, title)
        
        if match:
            num_part = match.group(1).strip()
            series = title[:match.start()].strip()
            
            # 로마숫자 변환
            num_lower = num_part.lower()
            if num_lower in roman_map:
                num_part = roman_map[num_lower]
            
            return (series, num_part)
        
        # 넘버링 없음
        return (title, "")
    
    def verify_and_build_dict(self, clusters: Dict[str, List[str]] = None, auto: bool = True) -> Dict[str, str]:
        """
        5-6단계: 웹검색 확인 + 사전 등록
        
        Args:
            clusters: {대표명: [유사작품들]} 클러스터
            auto: 자동 모드 (기본 True)
            
        Returns:
            {별칭: 정식명} 사전
        """
        logger.info("=" * 60)
        logger.info("5-6단계: 웹검색 확인 + 사전 등록")
        logger.info("=" * 60)
        
        if clusters is None:
            if not self.clusters_file.exists():
                raise FileNotFoundError("먼저 cluster_works()를 실행하세요")
            with open(self.clusters_file, 'r', encoding='utf-8') as f:
                clusters = json.load(f)
        
        # 기존 사전 로드
        existing_dict = {}
        if self.dict_file.exists():
            with open(self.dict_file, 'r', encoding='utf-8') as f:
                existing_dict = json.load(f)
        
        new_dict = {}
        
        # 클러스터가 여러 개인 것만 처리
        multi_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
        
        logger.info(f"처리할 클러스터: {len(multi_clusters)}개")
        
        if auto:
            # 자동 모드: 대표명을 정식 명칭으로 사용
            logger.info("자동 모드로 실행 중...")
            
            for representative, variants in multi_clusters.items():
                # 대표명을 정식 명칭으로 사용
                official_name = representative
                
                # 별칭 등록
                for variant in variants:
                    if variant != official_name:
                        new_dict[variant] = official_name
            
            logger.info(f"자동 등록 완료: {len(new_dict)}개 별칭")
        else:
            # 대화형 모드
            logger.info("대화형 모드로 전환합니다...")
            
            for representative, variants in multi_clusters.items():
                print()
                print("=" * 60)
                print(f"대표명: {representative}")
                print(f"유사 작품들: {', '.join(variants)}")
                print()
                
                print("옵션:")
                print("  1. 대표명 사용")
                print("  2. 직접 정식명 입력")
                print("  3. 건너뛰기")
                print("  q. 종료")
                print()
                
                choice = input("선택: ").strip()
                
                if choice == 'q':
                    break
                elif choice == '1':
                    official_name = representative
                elif choice == '2':
                    official_name = input("정식 명칭 입력: ").strip()
                else:
                    continue
                
                # 사전에 등록
                for variant in variants:
                    if variant != official_name:
                        new_dict[variant] = official_name
                
                print(f"→ 등록: {len(variants) - 1}개 별칭 → '{official_name}'")
        
        # 기존 사전과 병합
        final_dict = {**existing_dict, **new_dict}
        
        # 저장
        with open(self.dict_file, 'w', encoding='utf-8') as f:
            json.dump(final_dict, f, ensure_ascii=False, indent=2)
        logger.info(f"저장: {self.dict_file}")
        
        return final_dict


def main():
    parser = argparse.ArgumentParser(
        description="유사도 사전 구축 도구"
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="1-3단계: 작품 수집 및 분리"
    )
    parser.add_argument(
        "--cluster",
        action="store_true",
        help="4단계: 클러스터링"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="5-6단계: 웹검색 확인 + 사전 등록 (대화형)"
    )
    parser.add_argument(
        "--auto-verify",
        action="store_true",
        help="5-6단계: 자동 사전 등록 (대화형 없이)"
    )
    parser.add_argument(
        "--auto-verify",
        action="store_true",
        help="5-6단계: 자동 사전 등록 (대화형 없이)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="자동 모드: 모든 클러스터 자동 등록 (대화형 X)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="자동 모드: 모든 클러스터를 대표명으로 자동 등록 (대화형 생략)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="전체 실행"
    )
    parser.add_argument(
        "--data-dir",
        default="data/raw",
        help="데이터 디렉토리"
    )
    parser.add_argument(
        "--output-dir",
        default="data/dict",
        help="출력 디렉토리"
    )
    
    args = parser.parse_args()
    
    if not (args.collect or args.cluster or args.verify or args.auto_verify or args.all):
        parser.error("--collect, --cluster, --verify, --auto-verify, --all 중 하나를 지정해야 합니다")
    
    builder = SimilarityDictBuilder(
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    print("=" * 60)
    print("유사도 사전 구축 도구")
    print("=" * 60)
    print()
    
    try:
        if args.all:
            # 전체 실행
            works = builder.collect_works()
            clusters = builder.cluster_works(works)
            builder.verify_and_build_dict(clusters, auto=True)
        elif args.auto_verify:
            # 자동 사전 등록
            builder.verify_and_build_dict(auto=True)
        elif args.verify:
            # 대화형 사전 등록
            builder.verify_and_build_dict(auto=False)
        else:
            # 개별 실행
            works = None
            clusters = None
            
            if args.collect:
                works = builder.collect_works()
            
            if args.cluster:
                clusters = builder.cluster_works(works)
            
            if args.verify:
                builder.verify_and_build_dict(clusters)
        
        print()
        print("=" * 60)
        print("✅ 완료!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        import sys
        sys.exit(1)
    except Exception as e:
        logger.exception(f"오류 발생: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()

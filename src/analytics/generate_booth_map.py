#!/usr/bin/env python3
"""
동인네트워크 부스 배치도 생성 스크립트
정적 PNG 배치도 생성 (matplotlib 기반)

사용법:
  python3 generate_booth_map.py                          # 26년 7월 df2607 (토/일 각각)
  python3 generate_booth_map.py --event df2607 --day 토   # 토요일만
  python3 generate_booth_map.py --event df2607 --day 일   # 일요일만
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MAPS_DIR = ROOT_DIR / "artifacts" / "maps"

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm

# 한글 폰트 설정
for font_name in ["Apple SD Gothic Neo", "AppleGothic", "Nanum Gothic", "Noto Sans CJK KR"]:
    try:
        fm.findfont(font_name, fallback_to_default=False)
        plt.rcParams["font.family"] = font_name
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 데이터 로드
# ============================================================

def load_booth_data(csv_path, event_slug, day_filter=None):
    """
    CSV에서 특정 행사+요일의 부스 데이터 로드.
    반환: [{부스명, 열, 번호, 반부스, 부스크기, ...}, ...]
    """
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = row.get("링크", "")
            if event_slug not in link:
                continue

            event_name = row.get("행사명", "")
            if day_filter:
                if day_filter == "토" and "토" not in event_name:
                    continue
                if day_filter == "일" and "일" not in event_name:
                    continue

            col = (row.get("위치(열)") or "").strip()
            num = (row.get("위치(번호)") or "").strip()
            if not col or not num or not num.isdigit():
                continue

            rows.append({
                "name": row.get("부스명", "").strip(),
                "col": col,
                "num": int(num),
                "sub": (row.get("반부스") or "").strip(),
                "size": row.get("부스", "").strip(),
                "twitter": row.get("트위터", "").strip(),
                "original": row.get("대표 작품(원작)", "").strip(),
                "link": row.get("링크", "").strip(),
            })
    return rows


# ============================================================
# 구역 정의
# ============================================================

ZONE_COLORS = {
    "zone1": {"name": "제1전시장 (A-M)", "bg": "#6366f1", "bg_alpha": 0.15,
              "border": "#6366f1", "border_alpha": 0.4, "rows": list(range(0, 13))},
    "zone2": {"name": "제2전시장 (N-T)", "bg": "#10b981", "bg_alpha": 0.15,
              "border": "#10b981", "border_alpha": 0.4, "rows": list(range(13, 20))},
    "zone3": {"name": "제3전시장 (U-Z)", "bg": "#f59e0b", "bg_alpha": 0.15,
              "border": "#f59e0b", "border_alpha": 0.4, "rows": list(range(20, 26))},
}

ROW_LABELS = [chr(ord("A") + i) for i in range(26)]


def get_zone(row_idx):
    """행 인덱스(0-base) → 구역 반환"""
    for zkey, z in ZONE_COLORS.items():
        if row_idx in z["rows"]:
            return zkey, z
    return None, None


# ============================================================
# 배치도 그리기
# ============================================================

def draw_booth_map(booths, title, output_path, max_col=26):
    """
    부스 데이터 → 배치도 PNG 생성.

    레이아웃:
      - Y축: 행 (A~Z, 위에서 아래)
      - X축: 번호 (1~max_col, 왼쪽에서 오른쪽)
      - 각 번호 셀: a(상단) + b(하단) 분할
    """
    CELL_W = 1.0       # 번호 셀 너비
    CELL_H = 1.0       # 번호 셀 높이
    SUB_H = CELL_H / 2  # a/b 각 높이
    ROW_GAP = 0.3      # 행 사이 간격
    ZONE_GAP = 0.8     # 구역 사이 간격

    num_rows = 26

    # 그리드 빌드: grid[row_idx][num] = {"a": booth, "b": booth, "full": booth}
    grid = [defaultdict(dict) for _ in range(num_rows)]
    for b in booths:
        ri = ord(b["col"]) - ord("A")
        if ri < 0 or ri >= num_rows:
            continue
        n = b["num"]
        if n < 1 or n > max_col:
            continue
        if b["sub"] == "a":
            grid[ri][n]["a"] = b
        elif b["sub"] == "b":
            grid[ri][n]["b"] = b
        else:
            grid[ri][n]["full"] = b

    # 전체 높이 계산 (구역 간격 포함)
    total_h = num_rows * (CELL_H + ROW_GAP)
    for gi in [13, 20]:
        total_h += ZONE_GAP - ROW_GAP
    total_w = max_col * CELL_W + 2

    fig_w = max_col * 0.5 + 3
    fig_h = num_rows * 0.5 + 3
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h))
    ax.set_xlim(-1.5, max_col * CELL_W + 0.5)
    ax.set_ylim(-total_h - 0.5, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#fafafa")

    # 제목
    ax.text(max_col * CELL_W / 2 - 0.5, 1.0, title,
            ha="center", va="bottom", fontsize=16, fontweight="bold", color="#1a1a1a")

    # 구역 배경
    y_cursor = 0
    for ri in range(num_rows):
        if ri == 13 or ri == 20:
            y_cursor -= ZONE_GAP

        zkey, zone = get_zone(ri)
        if ri == 0 or ri == 13 or ri == 20:
            zone_bottom = y_cursor - CELL_H
            count = 13 if ri == 0 else (7 if ri == 13 else 6)
            zone_top = y_cursor + (count - 1) * (CELL_H + ROW_GAP) + CELL_H
            bg = patches.FancyBboxPatch(
                (-1.2, zone_bottom - 0.1), max_col * CELL_W + 1.4, zone_top - zone_bottom + 0.2,
                boxstyle="round,pad=0.1", linewidth=2,
                edgecolor=zone["border"], facecolor=zone["bg"], alpha=0.08
            )
            ax.add_patch(bg)
            ax.text(-0.9, zone_top - 0.05, zone["name"],
                    ha="left", va="top", fontsize=9, fontweight="bold",
                    color=zone["border"], alpha=0.7)

        # 행 라벨
        ax.text(-0.5, y_cursor - CELL_H / 2, ROW_LABELS[ri],
                ha="center", va="center", fontsize=11, fontweight="bold", color="#666")

        # 번호별 부스 그리기
        for n in range(1, max_col + 1):
            cell = grid[ri].get(n, {})
            x = (n - 1) * CELL_W

            if "full" in cell:
                b = cell["full"]
                _draw_booth_cell(ax, x, y_cursor - CELL_H, CELL_W, CELL_H, b, zone, label_type="full")
            elif "a" in cell or "b" in cell:
                if "a" in cell:
                    _draw_booth_cell(ax, x, y_cursor - SUB_H, CELL_W, SUB_H,
                                     cell["a"], zone, label_type="sub_a")
                else:
                    _draw_booth_cell(ax, x, y_cursor - SUB_H, CELL_W, SUB_H,
                                     None, zone, label_type="empty_sub")
                if "b" in cell:
                    _draw_booth_cell(ax, x, y_cursor - CELL_H, CELL_W, SUB_H,
                                     cell["b"], zone, label_type="sub_b")
                else:
                    _draw_booth_cell(ax, x, y_cursor - CELL_H, CELL_W, SUB_H,
                                     None, zone, label_type="empty_sub")

        y_cursor -= (CELL_H + ROW_GAP)

    # 번호 라벨 (상단)
    for n in range(1, max_col + 1):
        ax.text((n - 1) * CELL_W + CELL_W / 2, 0.3, str(n),
                ha="center", va="bottom", fontsize=6, color="#999")

    # 범례
    legend_items = [
        ("부스 (1sp)", "#ffffff", ZONE_COLORS["zone1"]["border"]),
        ("부스 (2sp, a+b)", "#e8e8ff", ZONE_COLORS["zone1"]["border"]),
        ("부스 (4sp, 더블)", "#c8c8ff", ZONE_COLORS["zone1"]["border"]),
        ("빈 자리", "#f0f0f0", "#ccc"),
    ]
    for i, (label, fc, ec) in enumerate(legend_items):
        lx = max_col * CELL_W - 4 + (i % 2) * 2.5
        ly = -total_h - 0.2 - (i // 2) * 0.5
        rect = patches.FancyBboxPatch((lx, ly), 0.3, 0.3,
                                       boxstyle="round,pad=0.02",
                                       facecolor=fc, edgecolor=ec, linewidth=0.8)
        ax.add_patch(rect)
        ax.text(lx + 0.4, ly + 0.15, label, fontsize=7, va="center", color="#666")

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight",
                facecolor=fig.get_facecolor(), pad_inches=0.3)
    plt.close(fig)
    print(f"  → 저장: {output_path}")


def _draw_booth_cell(ax, x, y, w, h, booth, zone, label_type="full"):
    """개별 부스 셀 그리기"""
    if booth is None:
        rect = patches.FancyBboxPatch(
            (x + 0.02, y + 0.02), w - 0.04, h - 0.04,
            boxstyle="round,pad=0.01",
            facecolor="#f5f5f5", edgecolor="#ddd", linewidth=0.3
        )
        ax.add_patch(rect)
        return

    size = booth.get("size", "")
    is_double = "4" in size

    fc = zone["bg"]
    fc_alpha = zone["bg_alpha"]
    ec = zone["border"]
    ec_alpha = zone["border_alpha"]

    if is_double:
        fc_alpha = min(fc_alpha + 0.15, 0.5)

    rect = patches.FancyBboxPatch(
        (x + 0.02, y + 0.02), w - 0.04, h - 0.04,
        boxstyle="round,pad=0.01",
        facecolor=fc, edgecolor=ec, linewidth=0.5, alpha=1.0
    )
    rect.set_alpha(1.0)

    import matplotlib.colors as mcolors
    rgba_bg = mcolors.to_rgba(fc)
    rgba_bg = (rgba_bg[0], rgba_bg[1], rgba_bg[2], fc_alpha)
    rgba_bd = mcolors.to_rgba(ec)
    rgba_bd = (rgba_bd[0], rgba_bd[1], rgba_bd[2], ec_alpha)

    rect = patches.FancyBboxPatch(
        (x + 0.02, y + 0.02), w - 0.04, h - 0.04,
        boxstyle="round,pad=0.01",
        facecolor=rgba_bg, edgecolor=rgba_bd, linewidth=0.6
    )
    ax.add_patch(rect)

    name = booth.get("name", "")
    num = booth.get("num", "")
    sub = booth.get("sub", "")

    if label_type == "full":
        label = str(num)
        if is_double:
            label = f"{num}"
        ax.text(x + w / 2, y + h / 2, label,
                ha="center", va="center", fontsize=5.5, fontweight="bold",
                color=ec, alpha=0.9)
        if name and h > 0.6:
            short = name[:5] + "…" if len(name) > 5 else name
            ax.text(x + w / 2, y + h / 2 - 0.25, short,
                    ha="center", va="center", fontsize=3.5, color="#555")
    elif label_type in ("sub_a", "sub_b"):
        label = f"{num}{sub}"
        ax.text(x + w / 2, y + h / 2, label,
                ha="center", va="center", fontsize=4.5, fontweight="bold",
                color=ec, alpha=0.9)
        if name and h > 0.3:
            short = name[:4] + "…" if len(name) > 4 else name
            ax.text(x + w / 2, y + h * 0.15, short,
                    ha="center", va="center", fontsize=2.8, color="#666")


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="부스 배치도 PNG 생성")
    parser.add_argument("--input", default=PROCESSED_DIR / "26년_7월_부스정보.csv", type=Path, help="입력 CSV")
    parser.add_argument("--event", default="df2607", help="행사 slug")
    parser.add_argument("--day", choices=["토", "일", "all"], default="all", help="요일 필터")
    parser.add_argument("--output-dir", default=MAPS_DIR, type=Path, help="출력 디렉터리")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(args.input):
        print(f"오류: 파일을 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    days = ["토", "일"] if args.day == "all" else [args.day]

    for day in days:
        print(f"처리 중: {args.event} ({day}요일)")
        booths = load_booth_data(args.input, args.event, day)
        if not booths:
            print(f"  데이터 없음, 건너뜀")
            continue

        print(f"  부스 수: {len(booths)}")

        max_num = max(b["num"] for b in booths)
        title = f"제34회 디. 페스타 ({day}) - 배치도"
        outpath = os.path.join(args.output_dir, f"booth_map_{args.event}_{day}.png")
        draw_booth_map(booths, title, outpath, max_col=max_num)


if __name__ == "__main__":
    main()

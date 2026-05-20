"""帮助首页插件表：叠绘绿/红圆点（pillowmd 表格字体不含 🟢🔴 字形）。"""

from __future__ import annotations

import re
from pathlib import Path

import pillowmd
from PIL import Image, ImageDraw, ImageFont

from .help_constants import HELP_STATUS_OFF, HELP_STATUS_ON

_FORM_LINE = (210, 202, 194)
_FORM_FILL = (255, 252, 249)
_DOT_ON = (36, 110, 62)
_DOT_OFF = (184, 67, 90)
_LINE_MATCH_RATIO = 0.12
_LINE_MERGE_PX = 4
_DOT_R = 7


def should_paint_help_status_dots(markdown: str) -> bool:
    return "## 插件列表" in markdown and "| 状态 |" in markdown


def parse_plugin_table_statuses(markdown: str) -> list[bool] | None:
    if not should_paint_help_status_dots(markdown):
        return None
    section = markdown.split("## 插件列表", 1)[1]
    rows: list[bool] = []
    in_table = False
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if in_table and rows:
                break
            continue
        if re.match(r"^\|\s*[-:]+\s*\|", s):
            in_table = True
            continue
        if not in_table:
            if "序号" in s and "状态" in s:
                in_table = True
            continue
        cells = [c.strip() for c in s.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        if cells[2] == HELP_STATUS_ON:
            rows.append(True)
        elif cells[2] == HELP_STATUS_OFF:
            rows.append(False)
    return rows or None


def _color_near(rgb: tuple[int, ...], target: tuple[int, int, int], tol: int = 10) -> bool:
    return len(rgb) >= 3 and all(abs(int(rgb[i]) - target[i]) <= tol for i in range(3))


def _cluster_coords(coords: list[int], merge: int = _LINE_MERGE_PX) -> list[int]:
    if not coords:
        return []
    coords = sorted(coords)
    groups: list[list[int]] = [[coords[0]]]
    for c in coords[1:]:
        if c - groups[-1][-1] <= merge:
            groups[-1].append(c)
        else:
            groups.append([c])
    return [sum(g) // len(g) for g in groups]


def _scan_line_positions(img: Image.Image, horizontal: bool) -> list[int]:
    rgb = img.convert("RGB")
    w, h = rgb.size
    limit = h if horizontal else w
    cross = w if horizontal else h
    coords: list[int] = []
    for i in range(limit):
        hits = 0
        for j in range(cross):
            px = rgb.getpixel((j, i) if horizontal else (i, j))
            if _color_near(px, _FORM_LINE):
                hits += 1
        if hits >= int(cross * _LINE_MATCH_RATIO):
            coords.append(i)
    return _cluster_coords(coords)


def _find_plugin_table(img: Image.Image, expected_rows: int) -> tuple[list[tuple[int, int]], tuple[int, int]] | None:
    h_lines = _scan_line_positions(img, horizontal=True)
    v_lines = _scan_line_positions(img, horizontal=False)
    if len(h_lines) < expected_rows + 2 or len(v_lines) < 5:
        return None

    best: tuple[list[tuple[int, int]], tuple[int, int]] | None = None
    best_width = -1
    for vi in range(len(v_lines) - 4):
        col_x = v_lines[vi : vi + 5]
        width = col_x[-1] - col_x[0]
        if width < 200:
            continue
        status_col = (col_x[2] + 6, col_x[3] - 6)
        if status_col[1] - status_col[0] < 28:
            continue
        for hi in range(len(h_lines) - 1):
            row_bounds: list[tuple[int, int]] = []
            for r in range(hi + 1, len(h_lines) - 1):
                y0 = h_lines[r] + 2
                y1 = h_lines[r + 1] - 2
                if y1 - y0 < 8:
                    continue
                row_bounds.append((y0, y1))
            if len(row_bounds) < expected_rows:
                continue
            if len(row_bounds) > expected_rows:
                row_bounds = row_bounds[-expected_rows:]
            if len(row_bounds) != expected_rows:
                continue
            if width > best_width:
                best_width = width
                best = (row_bounds, status_col)
    return best


def _load_font(size: int = 22) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = Path(pillowmd.__file__).resolve().parent / "data" / "fonts" / "smSans.ttf"
    if font_path.is_file():
        return ImageFont.truetype(str(font_path), size=size)
    return ImageFont.load_default()


def _paint_status_cell(
    draw: ImageDraw.ImageDraw,
    cell: tuple[int, int, int, int],
    text: str,
    enabled: bool,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    x0, y0, x1, y1 = cell
    draw.rectangle(cell, fill=_FORM_FILL)
    cy = (y0 + y1) // 2
    dot_color = _DOT_ON if enabled else _DOT_OFF
    cx = x0 + 14
    draw.ellipse((cx - _DOT_R, cy - _DOT_R, cx + _DOT_R, cy + _DOT_R), fill=dot_color)
    tx = cx + _DOT_R + 8
    ty = cy - (font.size // 2) - 1
    draw.text((tx, ty), text, fill=(42, 38, 48), font=font)


def apply_help_status_dots(image: Image.Image, markdown: str) -> Image.Image:
    statuses = parse_plugin_table_statuses(markdown)
    if not statuses:
        return image
    layout = _find_plugin_table(image, len(statuses))
    if not layout:
        return image
    row_bounds, status_col = layout
    x0, x1 = status_col
    font = _load_font()
    out = image.convert("RGBA")
    draw = ImageDraw.Draw(out)
    for i, enabled in enumerate(statuses):
        if i >= len(row_bounds):
            break
        y0, y1 = row_bounds[i]
        text = HELP_STATUS_ON if enabled else HELP_STATUS_OFF
        _paint_status_cell(draw, (x0, y0, x1, y1), text, enabled, font)
    return out

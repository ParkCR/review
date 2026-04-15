#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复盘手册索引生成器
扫描 reviews/ 文件夹下的所有 .html 文件，提取元数据，生成 index.html 和 data.js
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from html import escape

# ========== 可配置参数 ==========
REVIEWS_DIR = Path("reviews")          # 存放复盘文件的目录
OUTPUT_HTML = Path("index.html")       # 输出的索引文件名
OUTPUT_DATA = Path("data.js")          # 输出的数据文件名
TEMPLATE_FILE = Path("templates/index_template.html")  # HTML 模板文件路径
DATE_PATTERN = r"(\d{4}-\d{2}-\d{2})[-_]"  # 支持 - 或 _ 作为分隔符
TAG_PATTERN = r"<!--\s*tags:\s*(.+?)\s*-->"          # 标签注释正则
SUMMARY_PATTERN = r"<!--\s*summary:\s*(.+?)\s*-->"   # 摘要注释正则
DEFAULT_SUMMARY = "无摘要"
# ================================

def extract_metadata(html_path):
    """
    从HTML文件中提取元数据（标签、摘要）
    返回: (tags_str, summary_str)
    """
    tags = ""
    summary = DEFAULT_SUMMARY
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ 无法读取文件 {html_path.name}: {e}")
        return tags, summary

    # 提取标签
    tag_match = re.search(TAG_PATTERN, content, re.IGNORECASE)
    if tag_match:
        tags = tag_match.group(1).strip()
    else:
        # 可选：如果希望默认从文件名中提取一些标签，可在此扩展
        pass

    # 提取摘要
    summary_match = re.search(SUMMARY_PATTERN, content, re.IGNORECASE)
    if summary_match:
        summary = summary_match.group(1).strip()
    else:
        # 如果没找到注释，尝试取第一个 <p> 标签内的文本
        p_match = re.search(r'<p>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
        if p_match:
            summary = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()[:150]
            if not summary:
                summary = DEFAULT_SUMMARY
    return tags, summary

def parse_filename(filename):
    """
    从文件名解析日期和标题
    返回: (date_str, title_str)
    """
    stem = filename.stem
    match = re.match(DATE_PATTERN, stem)
    if match:
        date_candidate = match.group(1)
        try:
            # 验证是否为有效日期
            datetime.strptime(date_candidate, "%Y-%m-%d")
            date = date_candidate
            title = stem[len(match.group(0)):].replace('_', ' ').strip()
            if not title:
                title = stem
        except ValueError:
            date = "未知日期"
            title = stem
    else:
        date = "未知日期"
        title = stem
    return date, title

def generate_data_js(items):
    """生成 data.js 文件"""
    data_js_content = f"const reviewData = {json.dumps(items, ensure_ascii=False, indent=2)};"
    with open(OUTPUT_DATA, 'w', encoding='utf-8') as f:
        f.write(data_js_content)
    print(f"✅ 生成 {OUTPUT_DATA} 完成")

def generate_html():
    """读取独立模板文件，生成 index.html"""
    if not TEMPLATE_FILE.exists():
        print(f"❌ 模板文件不存在：{TEMPLATE_FILE}")
        return
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ 生成 {OUTPUT_HTML} 完成（基于独立模板）")

def generate_index():
    """
    主函数：扫描文件，构建数据，生成 index.html 和 data.js
    """
    # 确保 reviews 目录存在
    if not REVIEWS_DIR.exists():
        print(f"⚠️ 目录 {REVIEWS_DIR} 不存在，创建空目录。")
        REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
        items = []
    else:
        items = []
        for html_file in REVIEWS_DIR.glob("*.html"):
            print(f"📄 处理: {html_file.name}")
            date, title = parse_filename(html_file)
            tags, summary = extract_metadata(html_file)

            # 相对路径（假设 index.html 与 reviews 同级）
            link = f"reviews/{html_file.name}"

            items.append({
                "title": title,
                "date": date,
                "tags": tags,
                "summary": summary,
                "link": link
            })

    # 按日期倒序（最新的在前）
    items.sort(key=lambda x: x["date"], reverse=True)

    # 生成 data.js
    generate_data_js(items)

    # 生成 index.html（从模板读取）
    generate_html()

    print(f"✅ 共处理 {len(items)} 条记录")

if __name__ == "__main__":
    generate_index()

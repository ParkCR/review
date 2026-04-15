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
DATE_PATTERN = r"(\d{4}-\d{2}-\d{2})[-_]"  # 支持 - 或 _ 作为分隔符
TAG_PATTERN = r"<!--\s*tags:\s*(.+?)\s*-->"          # 标签注释正则
SUMMARY_PATTERN = r"<!--\s*summary:\s*(.+?)\s*-->"   # 摘要注释正则
DEFAULT_SUMMARY = "无摘要"
# ================================

def extract_metadata(html_path):
    """从HTML文件中提取元数据（标签、摘要）"""
    tags = ""
    summary = DEFAULT_SUMMARY
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ 无法读取文件 {html_path.name}: {e}")
        return tags, summary

    tag_match = re.search(TAG_PATTERN, content, re.IGNORECASE)
    if tag_match:
        tags = tag_match.group(1).strip()

    summary_match = re.search(SUMMARY_PATTERN, content, re.IGNORECASE)
    if summary_match:
        summary = summary_match.group(1).strip()
    else:
        p_match = re.search(r'<p>(.*?)</p>', content, re.DOTALL | re.IGNORECASE)
        if p_match:
            summary = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()[:150]
            if not summary:
                summary = DEFAULT_SUMMARY
    return tags, summary

def parse_filename(filename):
    """从文件名解析日期和标题"""
    stem = filename.stem
    match = re.match(DATE_PATTERN, stem)
    if match:
        date_candidate = match.group(1)
        try:
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

def generate_html(items):
    """生成带搜索框清空按钮和标签点击筛选的 index.html"""
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>复盘手册索引</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', 'Inter', sans-serif;
            background: #f5f7fb;
            padding: 2rem 1.5rem;
            color: #1e293b;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #1e293b, #3b82f6);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
        }}
        .sub {{
            color: #475569;
            margin-bottom: 2rem;
            border-left: 3px solid #3b82f6;
            padding-left: 1rem;
        }}
        .filter-bar {{
            background: white;
            border-radius: 20px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }}
        .search-box {{
            flex: 2;
            min-width: 200px;
            position: relative;
        }}
        .search-box input {{
            width: 100%;
            padding: 0.6rem 2rem 0.6rem 1rem;
            border: 1px solid #cbd5e1;
            border-radius: 40px;
            font-size: 0.9rem;
            outline: none;
            transition: 0.2s;
        }}
        .search-box input:focus {{
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
        }}
        .clear-search {{
            position: absolute;
            right: 0.8rem;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: #94a3b8;
            font-size: 1rem;
            font-weight: bold;
            background: none;
            border: none;
            padding: 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
            background: rgba(0,0,0,0.05);
        }}
        .clear-search:hover {{
            background: #e2e8f0;
            color: #1e293b;
        }}
        .tag-filter-box {{
            flex: 1;
            min-width: 150px;
        }}
        .tag-filter-box input {{
            width: 100%;
            padding: 0.6rem 1rem;
            border: 1px solid #cbd5e1;
            border-radius: 40px;
            font-size: 0.9rem;
        }}
        .sort-box select {{
            padding: 0.6rem 1rem;
            border: 1px solid #cbd5e1;
            border-radius: 40px;
            font-size: 0.9rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        th, td {{ text-align: left; padding: 1rem; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f8fafc; font-weight: 600; color: #1e293b; }}
        tr:hover {{ background: #fefce8; }}
        .tag {{
            display: inline-block;
            background: #eef2ff;
            color: #1e4a76;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-right: 0.4rem;
            margin-bottom: 0.2rem;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .tag:hover {{ background: #cbdffc; }}
        a {{ color: #1e4a76; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .empty-row td {{ text-align: center; padding: 3rem; color: #64748b; }}
        .footer {{ margin-top: 2rem; text-align: center; font-size: 0.75rem; color: #64748b; }}
        @media (max-width: 700px) {{ body {{ padding: 1rem; }} th, td {{ padding: 0.75rem; }} }}
    </style>
</head>
<body>
<div class="container">
    <h1>📚 复盘手册索引</h1>
    <div class="sub">由 GitHub Actions 自动生成 · 支持搜索、标签筛选、排序 · 点击标签快速筛选 · 搜索框右侧✖一键清空</div>

    <div class="filter-bar">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 搜索标题 / 标签 / 摘要" autocomplete="off">
            <span class="clear-search" id="clearSearchBtn" style="display: none;">✖</span>
        </div>
        <div class="tag-filter-box">
            <input type="text" id="tagFilter" placeholder="🏷️ 筛选标签 (多个用空格)" autocomplete="off">
        </div>
        <div class="sort-box">
            <select id="sortSelect">
                <option value="date-desc">📅 日期新 → 旧</option>
                <option value="date-asc">📅 日期旧 → 新</option>
                <option value="title-asc">🔤 标题 A → Z</option>
            </select>
        </div>
    </div>

    <div style="overflow-x: auto;">
        <table id="review-table">
            <thead><tr><th>标题</th><th>日期</th><th>标签</th><th>摘要</th></tr></thead>
            <tbody id="tableBody"><tr class="empty-row"><td colspan="4">加载中... 解决了</tbody>
        </table>
    </div>
    <div class="footer">💡 提示：每条记录对应一个复盘 HTML 文件，文件名格式建议 <code>YYYY-MM-DD_主题.html</code>，可在文件内添加 <code>&lt;!-- tags: 标签1 标签2 --&gt;</code> 和 <code>&lt;!-- summary: 摘要 --&gt;</code> 注释以丰富信息。点击任意标签快速筛选，搜索框右侧 ✖ 可清空搜索内容。</div>
</div>

<script src="data.js"></script>
<script>
    function renderTable(data) {{
        const tbody = document.getElementById('tableBody');
        if (!data || data.length === 0) {{
            tbody.innerHTML = '<tr class="empty-row"><td colspan="4">📭 没有匹配的复盘手册</td></tr>';
            return;
        }}
        let html = '';
        data.forEach(item => {{
            let tagsHtml = '';
            if (item.tags) {{
                const rawTags = item.tags.split(/[ ,]+/);
                rawTags.forEach(tag => {{
                    if (tag.trim()) {{
                        const safeTag = escapeHtml(tag);
                        tagsHtml += `<span class="tag" data-tag="${{escapeHtml(tag)}}">${{safeTag}}</span>`;
                    }}
                }});
            }}
            html += `
                <tr>
                    <td><a href="${{escapeHtml(item.link)}}" target="_blank">${{escapeHtml(item.title)}}</a></td>
                    <td>${{escapeHtml(item.date)}}</td>
                    <td>${{tagsHtml || '—'}}</td>
                    <td>${{escapeHtml(item.summary.substring(0, 120))}}${{item.summary.length > 120 ? '…' : ''}}</td>
                </tr>
            `;
        }});
        tbody.innerHTML = html;
    }}

    function escapeHtml(str) {{
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {{
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        }});
    }}

    function filterAndSort() {{
        let filtered = [...reviewData];
        const keyword = document.getElementById('searchInput').value.trim().toLowerCase();
        const tagQuery = document.getElementById('tagFilter').value.trim().toLowerCase();

        if (keyword) {{
            filtered = filtered.filter(item =>
                item.title.toLowerCase().includes(keyword) ||
                item.tags.toLowerCase().includes(keyword) ||
                item.summary.toLowerCase().includes(keyword)
            );
        }}
        if (tagQuery) {{
            const tagList = tagQuery.split(/[ ,]+/).filter(t => t.length > 0);
            if (tagList.length) {{
                filtered = filtered.filter(item => {{
                    const itemTags = item.tags.toLowerCase();
                    return tagList.some(tag => itemTags.includes(tag));
                }});
            }}
        }}

        const sortBy = document.getElementById('sortSelect').value;
        if (sortBy === 'date-desc') {{
            filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
        }} else if (sortBy === 'date-asc') {{
            filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
        }} else if (sortBy === 'title-asc') {{
            filtered.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'));
        }}
        renderTable(filtered);
    }}

    // 搜索框清空按钮逻辑
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');

    function updateClearBtnVisibility() {{
        if (searchInput.value.length > 0) {{
            clearBtn.style.display = 'flex';
        }} else {{
            clearBtn.style.display = 'none';
        }}
    }}

    searchInput.addEventListener('input', function() {{
        updateClearBtnVisibility();
        filterAndSort();
    }});

    clearBtn.addEventListener('click', function() {{
        searchInput.value = '';
        updateClearBtnVisibility();
        filterAndSort();
        searchInput.focus();
    }});

    // 标签点击筛选（事件委托）
    document.getElementById('tableBody').addEventListener('click', function(e) {{
        let target = e.target;
        while (target && target !== this && !target.classList?.contains('tag')) {{
            target = target.parentElement;
        }}
        if (target && target.classList.contains('tag')) {{
            const tagValue = target.getAttribute('data-tag') || target.innerText;
            if (tagValue) {{
                const tagInput = document.getElementById('tagFilter');
                tagInput.value = tagValue;
                filterAndSort();
            }}
            e.preventDefault();
        }}
    }});

    document.getElementById('tagFilter').addEventListener('input', filterAndSort);
    document.getElementById('sortSelect').addEventListener('change', filterAndSort);

    // 初始化
    updateClearBtnVisibility();
    filterAndSort();
</script>
</body>
</html>
"""
    return html_template

def generate_index():
    """主函数：扫描文件，构建数据，生成 index.html 和 data.js"""
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
            link = f"reviews/{html_file.name}"
            items.append({
                "title": title,
                "date": date,
                "tags": tags,
                "summary": summary,
                "link": link
            })

    items.sort(key=lambda x: x["date"], reverse=True)
    generate_data_js(items)
    html_content = generate_html(items)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ 生成 {OUTPUT_HTML} 完成，共 {len(items)} 条记录")

if __name__ == "__main__":
    generate_index()

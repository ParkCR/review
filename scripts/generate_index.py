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

def generate_html(items):
    """
    根据数据生成完整的 index.html 内容
    """
    # HTML 模板（样式和逻辑）
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>复盘手册索引</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', 'Inter', sans-serif;
            background: #f5f7fb;
            padding: 2rem 1.5rem;
            color: #1e293b;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
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
        .filter-bar input, .filter-bar select {{
            padding: 0.6rem 1rem;
            border: 1px solid #cbd5e1;
            border-radius: 40px;
            font-size: 0.9rem;
            outline: none;
            transition: 0.2s;
        }}
        .filter-bar input:focus, .filter-bar select:focus {{
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
        }}
        .search-box {{
            flex: 2;
            min-width: 200px;
        }}
        .tag-filter-box {{
            flex: 1;
            min-width: 150px;
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}
        .tag-filter-box input {{
            flex: 1;
        }}
        .clear-btn {{
            background: #e2e8f0;
            border: none;
            border-radius: 40px;
            width: 36px;
            height: 36px;
            cursor: pointer;
            font-size: 1.2rem;
            color: #475569;
            transition: 0.2s;
            display: none;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .clear-btn:hover {{
            background: #cbd5e1;
            color: #1e293b;
        }}
        .sort-box {{
            min-width: 130px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        th, td {{
            text-align: left;
            padding: 1rem;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #1e293b;
        }}
        tr:hover {{
            background: #fefce8;
        }}
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
        }}
        .clickable-tag {{
            cursor: pointer;
            transition: background 0.1s;
        }}
        .clickable-tag:hover {{
            background: #d9e2ef;
        }}
        a {{
            color: #1e4a76;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .empty-row td {{
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }}
        .footer {{
            margin-top: 2rem;
            text-align: center;
            font-size: 0.75rem;
            color: #64748b;
        }}
        @media (max-width: 700px) {{
            body {{ padding: 1rem; }}
            th, td {{ padding: 0.75rem; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>📚 复盘手册索引</h1>
    <div class="sub">由 GitHub Actions 自动生成 · 支持搜索、标签筛选、排序</div>

    <div class="filter-bar">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 搜索标题 / 标签 / 摘要" autocomplete="off">
        </div>
        <div class="tag-filter-box">
            <input type="text" id="tagFilter" placeholder="🏷️ 筛选标签 (多个用空格)" autocomplete="off">
            <button id="clearTagBtn" class="clear-btn" title="清空标签筛选">✕</button>
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
            <thead>
                <tr><th>标题</th><th>日期</th><th>标签</th><th>摘要</th></tr>
            </thead>
            <tbody id="tableBody">
                <tr class="empty-row"><td colspan="4">加载中... </tr></tr>
            </tbody>
        </table>
    </div>
    <div class="footer">
        💡 提示：每条记录对应一个复盘 HTML 文件，文件名格式建议 <code>YYYY-MM-DD_主题.html</code>，可在文件内添加 <code>&lt;!-- tags: 标签1 标签2 --&gt;</code> 和 <code>&lt;!-- summary: 摘要 --&gt;</code> 注释以丰富信息。
    </div>
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
                item.tags.split(/[ ,]+/).forEach(tag => {{
                    if (tag.trim()) tagsHtml += `<span class="tag clickable-tag" data-tag="${{escapeHtml(tag)}}">${{escapeHtml(tag)}}</span>`;
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

    // 控制清空按钮显示/隐藏
    const tagFilterInput = document.getElementById('tagFilter');
    const clearTagBtn = document.getElementById('clearTagBtn');

    function toggleClearButton() {{
        if (tagFilterInput.value.trim().length > 0) {{
            clearTagBtn.style.display = 'flex';
        }} else {{
            clearTagBtn.style.display = 'none';
        }}
    }}

    // 监听标签筛选输入框手动输入
    tagFilterInput.addEventListener('input', () => {{
        toggleClearButton();
        filterAndSort();
    }});

    // 清空按钮点击
    clearTagBtn.addEventListener('click', () => {{
        tagFilterInput.value = '';
        toggleClearButton();
        filterAndSort();
    }});

    // 标签点击筛选（事件委托）
    document.getElementById('tableBody').addEventListener('click', (e) => {{
        const tagSpan = e.target.closest('.clickable-tag');
        if (tagSpan) {{
            const tag = tagSpan.getAttribute('data-tag');
            if (tag) {{
                tagFilterInput.value = tag;
                toggleClearButton();
                filterAndSort();
            }}
        }}
    }});

    // 监听搜索和排序
    document.getElementById('searchInput').addEventListener('input', filterAndSort);
    document.getElementById('sortSelect').addEventListener('change', filterAndSort);

    // 初始化：隐藏清空按钮，渲染表格
    toggleClearButton();
    filterAndSort();
</script>
</body>
</html>
"""
    return html_template

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

    # 生成 index.html
    html_content = generate_html(items)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 生成 {OUTPUT_HTML} 完成，共 {len(items)} 条记录")

if __name__ == "__main__":
    generate_index()

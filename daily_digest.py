import os
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict

# --- 配置 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- 1. 数据抓取 ---
def fetch_data() -> List[Dict]:
    items = []
    print("正在搜寻 ComfyUI 动态...")
    
    # 尝试抓取 Reddit (ComfyUI 板块)
    try:
        resp = requests.get("https://www.reddit.com/r/comfyui/new/.rss", headers=HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:8]:
            items.append({
                "source": "Reddit",
                "title": entry.title,
                "link": entry.link,
                "summary": "Reddit 社区新鲜分享，点击链接查看原帖讨论。",
                "is_hardcore": "workflow" in entry.title.lower() or "node" in entry.title.lower()
            })
    except:
        print("Reddit 抓取暂时跳过")

    # 尝试抓取 GitHub (新插件)
    try:
        github_url = "https://api.github.com/search/repositories?q=comfyui+nodes+sort:updated&per_page=5"
        resp = requests.get(github_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            for repo in resp.json().get('items', []):
                items.append({
                    "source": "GitHub",
                    "title": f"新插件: {repo['name']}",
                    "link": repo['html_url'],
                    "summary": repo['description'] or "新发布的 ComfyUI 节点。",
                    "is_hardcore": True
                })
    except:
        print("GitHub 抓取暂时跳过")

    return items

# --- 2. 页面生成 ---
def save_html(items: List[Dict]):
    today = datetime.date.today().strftime('%Y-%m-%d')
    # 你的进化标准
    standards = [
        {"task": "减脂：今日热量缺口 500kcal", "icon": "🥗"},
        {"task": "运动：力量训练 40min / 有氧", "icon": "💪"},
        {"task": "护肤：清洁 + 早C晚A + 补水", "icon": "✨"},
        {"task": "ComfyUI：拆解并运行 1 个新工作流", "icon": "🎨"}
    ]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ComfyUI 进化看板</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #050505; color: #a3a3a3; font-family: sans-serif; }}
            .glass {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px); }}
        </style>
    </head>
    <body class="p-6 md:p-12 max-w-6xl mx-auto">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
            <div class="lg:col-span-1">
                <div class="glass p-8 rounded-3xl border-l-4 border-blue-500 sticky top-10">
                    <h2 class="text-white font-bold text-2xl mb-8">🧔 变帅进化标准</h2>
                    <div class="space-y-6">
                        {"".join([f'<div class="flex items-center gap-4 p-4 bg-white/5 rounded-2xl"><span class="text-2xl">{s["icon"]}</span><span class="text-sm text-gray-200">{s["task"]}</span></div>' for s in standards])}
                    </div>
                </div>
            </div>
            <div class="lg:col-span-2">
                <h1 class="text-5xl font-black text-white italic mb-2 tracking-tighter uppercase">COMFYUI <span class="text-blue-500 font-bold">INTEL</span></h1>
                <p class="mb-10 text-gray-600 font-mono italic text-xs tracking-widest uppercase">AUTO_UPDATE: {today}</p>
                <div class="space-y-4">
    """

    if not items:
        html_content += '<div class="glass p-10 rounded-3xl text-center">今日暂无资讯，专注自我提升！</div>'
    else:
        for item in items:
            b_search = f"ComfyUI {item['title'][:15]}"
            html_content += f"""
                    <div class="glass p-6 rounded-2xl hover:bg-white/5 transition-all">
                        <span class="text-[10px] font-bold text-blue-400 uppercase tracking-widest">{item['source']}</span>
                        <h3 class="text-white font-bold text-lg mt-1 mb-3 hover:text-blue-400 transition">
                            <a href="{item['link']}" target="_blank">{item['title']}</a>
                        </h3>
                        <div class="flex gap-4 items-center">
                            <a href="{item['link']}" target="_blank" class="text-xs text-gray-500 underline">READ MORE</a>
                            <a href="https://search.bilibili.com/all?keyword={b_search}" target="_blank" class="text-[10px] bg-pink-500/10 text-pink-400 px-3 py-1 rounded-full border border-pink-500/10 transition">📺 B站搜教程</a>
                        </div>
                    </div>
            """

    html_content += "</div></div></div></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    news = fetch_data()
    save_html(news)
    print("SUCCESS: index.html generated.")

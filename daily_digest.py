import os
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from typing import List, Dict

# --- 核心配置 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
}
TRANSLATOR = GoogleTranslator(source='auto', target='zh-CN')

def translate_safe(text: str) -> str:
    """安全的翻译函数，防止内容过长或为空"""
    try:
        if not text or len(text.strip()) < 5: return ""
        # 移除 HTML 标签，只留纯文本
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        # 截取前 300 字，保证翻译质量和速度
        return TRANSLATOR.translate(clean_text[:300])
    except:
        return text

def fetch_intel() -> List[Dict]:
    items = []
    print("🚀 正在抓取全球 ComfyUI 核心动态...")
    
    # 1. Reddit r/comfyui (抓取最新的分享)
    try:
        resp = requests.get("https://www.reddit.com/r/comfyui/new/.rss", headers=HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:12]:
            # 获取详细描述
            detail = entry.summary if 'summary' in entry else ""
            print(f"翻译资讯: {entry.title[:15]}...")
            
            items.append({
                "tag": "社区动态",
                "title": translate_safe(entry.title),
                "summary": translate_safe(detail),
                "link": entry.link,
                "date": "刚刚"
            })
    except Exception as e:
        print(f"Reddit 同步失败: {e}")

    # 2. GitHub ComfyUI 插件更新
    try:
        url = "https://api.github.com/search/repositories?q=comfyui+nodes+sort:updated&per_page=8"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            for repo in resp.json().get('items', []):
                items.append({
                    "tag": "新工具",
                    "title": f"节点: {repo['name']}",
                    "summary": translate_safe(repo['description'] or "该开发者未写中文描述，这通常是一个新的功能插件。"),
                    "link": repo['html_url'],
                    "date": repo['updated_at'][:10]
                })
    except:
        pass

    return items

def generate_app(items: List[Dict]):
    today = datetime.date.today().strftime('%m月%d日')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <title>Comfy Intel</title>
        
        <!-- 使网页在添加到主屏幕后看起来像 App -->
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2103/2103633.png">
        
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
            body {{ background: #000; color: #fff; font-family: 'Noto Sans SC', sans-serif; -webkit-font-smoothing: antialiased; }}
            .card {{ background: #111; border: 1px solid #222; }}
            .card:active {{ transform: scale(0.98); opacity: 0.9; }}
            /* 隐藏浏览器滚动条 */
            ::-webkit-scrollbar {{ display: none; }}
        </style>
    </head>
    <body class="safe-area">
        <div class="max-w-md mx-auto min-h-screen relative flex flex-col">
            
            <!-- 沉浸式头部 -->
            <header class="p-6 pt-16 sticky top-0 bg-black/80 backdrop-blur-xl z-50">
                <h1 class="text-4xl font-black italic tracking-tighter uppercase">Intel<span class="text-blue-600">.</span></h1>
                <p class="text-[10px] text-gray-500 font-bold tracking-widest uppercase mt-1">Update: {today}</p>
            </header>

            <!-- 纯净资讯流 -->
            <main class="p-4 space-y-4 pb-32">
    """

    for item in items:
        badge_color = "text-orange-400 bg-orange-400/10" if "社区" in item['tag'] else "text-blue-400 bg-blue-400/10"
        b_url = f"https://search.bilibili.com/all?keyword=ComfyUI {item['title'][:12]}"
        
        html += f"""
                <div class="card p-6 rounded-[2rem] transition-all duration-200">
                    <div class="flex items-center gap-2 mb-3">
                        <span class="{badge_color} text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter">
                            {item['tag']}
                        </span>
                    </div>
                    
                    <h2 class="text-lg font-bold leading-tight mb-3">
                        <a href="{item['link']}" target="_blank">{item['title']}</a>
                    </h2>
                    
                    <div class="text-xs text-gray-400 leading-relaxed mb-6 line-clamp-4 font-medium opacity-80">
                        {item['summary'] if item['summary'] else "这是一个最新的 ComfyUI 分享，点击下方详情查看工作流和效果图。"}
                    </div>

                    <div class="flex gap-2">
                        <a href="{item['link']}" target="_blank" class="flex-1 py-4 bg-white/5 rounded-2xl text-[10px] font-bold text-center border border-white/5">
                            原文详情
                        </a>
                        <a href="{b_url}" target="_blank" class="flex-1 py-4 bg-blue-600 rounded-2xl text-[10px] font-bold text-center text-white shadow-lg shadow-blue-900/40">
                            📺 B站搜教程
                        </a>
                    </div>
                </div>
        """

    html += """
            </main>

            <!-- 模拟 App 底部导航 -->
            <nav class="fixed bottom-0 left-0 right-0 max-w-md mx-auto h-20 bg-black/80 backdrop-blur-xl border-t border-white/5 flex items-center justify-around px-10 z-50">
                <div class="flex flex-col items-center gap-1 text-blue-500">
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
                    <span class="text-[9px] font-bold">情报</span>
                </div>
                <div class="flex flex-col items-center gap-1 text-gray-600 opacity-40">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <span class="text-[9px] font-bold">发现</span>
                </div>
                <div class="flex flex-col items-center gap-1 text-gray-600 opacity-40">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                    <span class="text-[9px] font-bold">设置</span>
                </div>
            </nav>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    data = fetch_intel()
    generate_app(data)

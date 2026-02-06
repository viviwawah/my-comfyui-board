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

def translate_text(text: str) -> str:
    """更稳定的翻译函数，支持更长内容的分段处理或截断"""
    try:
        if not text or len(text.strip()) < 3: return ""
        # 清理 HTML 标签
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        # 限制长度以保证翻译质量和速度
        return TRANSLATOR.translate(clean_text[:400])
    except Exception as e:
        print(f"翻译失败: {e}")
        return text

def fetch_comfy_intel() -> List[Dict]:
    items = []
    print("🚀 正在同步全球 ComfyUI 资讯并进行深度翻译...")
    
    # 1. Reddit r/comfyui (最强的工作流分享地)
    try:
        resp = requests.get("https://www.reddit.com/r/comfyui/new/.rss", headers=HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:15]:
            # 提取 Reddit 帖子的正文内容
            content_summary = ""
            if 'summary' in entry:
                # 尝试从摘要中提取文字
                content_summary = entry.summary
            
            print(f"翻译资讯: {entry.title[:20]}...")
            items.append({
                "type": "Community",
                "source": "Reddit 社区",
                "title": translate_text(entry.title),
                "detail": translate_text(content_summary),
                "link": entry.link,
                "time": "刚刚"
            })
    except Exception as e:
        print(f"Reddit 同步失败: {e}")

    # 2. GitHub Custom Nodes (最新的插件更新)
    try:
        url = "https://api.github.com/search/repositories?q=comfyui+nodes+sort:updated&per_page=10"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            for repo in resp.json().get('items', []):
                items.append({
                    "type": "Code",
                    "source": "GitHub 插件库",
                    "title": f"新工具: {repo['name']}",
                    "detail": translate_text(repo['description'] or "该开发者很懒，没有写描述，但这是一个最新的 ComfyUI 插件。"),
                    "link": repo['html_url'],
                    "time": repo['updated_at'][:10]
                })
    except Exception as e:
        print(f"GitHub 同步失败: {e}")

    return items

def generate_app_ui(items: List[Dict]):
    today = datetime.date.today().strftime('%m月%d日')
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <title>Comfy Intel App</title>
        
        <!-- PWA 设置：使其完全像原生 App -->
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black">
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2103/2103633.png">
        
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
            
            body {{ 
                background: #000; 
                color: #fff; 
                font-family: 'Noto Sans SC', sans-serif;
                -webkit-font-smoothing: antialiased;
            }}
            
            .app-container {{ max-width: 500px; margin: 0 auto; min-height: 100vh; background: #000; }}
            
            /* 隐藏滚动条 */
            ::-webkit-scrollbar {{ display: none; }}
            
            .news-card {{
                background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
                border: 1px solid #222;
                transition: transform 0.1s ease;
            }}
            
            .news-card:active {{ transform: scale(0.97); opacity: 0.8; }}
            
            .bottom-nav {{
                background: rgba(0,0,0,0.8);
                backdrop-filter: blur(20px);
                border-top: 0.5px solid #222;
                padding-bottom: env(safe-area-inset-bottom);
            }}
            
            .badge-community {{ background: rgba(249, 115, 22, 0.15); color: #f97316; }}
            .badge-code {{ background: rgba(59, 130, 246, 0.15); color: #3b82f6; }}
        </style>
    </head>
    <body class="flex justify-center">
        <div class="app-container w-full relative">
            
            <!-- App Header -->
            <header class="p-6 pt-14 sticky top-0 bg-black/90 backdrop-blur-xl z-50">
                <div class="flex justify-between items-end">
                    <div>
                        <h1 class="text-4xl font-black italic tracking-tighter">INTEL<span class="text-blue-600">.</span></h1>
                        <p class="text-gray-500 text-[10px] font-bold mt-1 uppercase tracking-widest">{today} 更新</p>
                    </div>
                    <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center text-xs font-bold border-2 border-white/10">AI</div>
                </div>
            </header>

            <!-- 资讯流 -->
            <main class="p-4 space-y-4 pb-32">
    """

    if not items:
        html_template += """
                <div class="py-20 text-center opacity-30 font-bold">暂时没有搜寻到最新情报</div>
        """
    else:
        for item in items:
            badge_class = "badge-community" if item['type'] == "Community" else "badge-code"
            # B站搜索词优化
            b_query = f"ComfyUI {item['title'][:10]}"
            
            html_template += f"""
                <div class="news-card p-6 rounded-[2.5rem] shadow-2xl">
                    <div class="flex justify-between items-center mb-4">
                        <span class="{badge_class} text-[10px] px-3 py-1 rounded-full font-black uppercase">
                            {item['source']}
                        </span>
                        <span class="text-gray-600 text-[10px] font-bold">{item['time']}</span>
                    </div>
                    
                    <h2 class="text-xl font-extrabold leading-tight mb-3 text-white">
                        <a href="{item['link']}" target="_blank">{item['title']}</a>
                    </h2>
                    
                    <div class="text-xs text-gray-400 leading-relaxed mb-6 line-clamp-4">
                        {item['detail'] if item['detail'] else "点击查看详细内容与工作流图片。"}
                    </div>

                    <div class="flex gap-2">
                        <a href="{item['link']}" target="_blank" class="flex-1 bg-white/5 py-4 rounded-2xl text-[11px] font-bold text-center border border-white/5 active:bg-white/10 transition">
                            阅读详情
                        </a>
                        <a href="https://search.bilibili.com/all?keyword={b_query}" target="_blank" class="flex-1 bg-blue-600 py-4 rounded-2xl text-[11px] font-bold text-center text-white active:bg-blue-700 transition shadow-lg shadow-blue-900/40">
                            B站视频
                        </a>
                    </div>
                </div>
            """

    html_template += """
            </main>

            <!-- App Bottom Nav Bar (模拟 App 效果) -->
            <nav class="bottom-nav fixed bottom-0 left-0 right-0 max-w-[500px] mx-auto h-20 flex items-center justify-around px-10 z-50">
                <div class="flex flex-col items-center gap-1 text-blue-500">
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
                    <span class="text-[9px] font-bold">资讯</span>
                </div>
                <div class="flex flex-col items-center gap-1 text-gray-600 opacity-50">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <span class="text-[9px] font-bold">搜索</span>
                </div>
                <div class="flex flex-col items-center gap-1 text-gray-600 opacity-50">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                    <span class="text-[9px] font-bold">我的</span>
                </div>
            </nav>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    intel = fetch_comfy_intel()
    generate_app_ui(intel)
    print("App 界面更新成功！")

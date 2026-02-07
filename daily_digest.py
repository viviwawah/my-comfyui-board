import os
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from typing import List, Dict

# --- 核心配置 ---
# 模拟手机浏览器 User-Agent，防止被拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
}
TRANSLATOR = GoogleTranslator(source='auto', target='zh-CN')

def translate_safe(text: str) -> str:
    """安全的翻译函数，只翻译摘要，保留技术专有名词的语境"""
    try:
        if not text or len(text.strip()) < 5: return ""
        # 移除 HTML 标签，只留纯文本
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        # 截取前 250 字翻译，太长会影响速度
        return TRANSLATOR.translate(clean_text[:250])
    except:
        return text

def fetch_high_quality_intel() -> List[Dict]:
    items = []
    print("🚀 正在挖掘高质量 ComfyUI 热点...")
    
    # 1. Reddit r/comfyui (改为获取 TOP - 每日高赞)
    # 以前是 new (最新)，现在是 top?t=day (24小时内最热)，确保是高质量讨论
    try:
        resp = requests.get("https://www.reddit.com/r/comfyui/top/.rss?t=day", headers=HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:10]: # 只取前10条精华
            # 获取详细描述
            detail = entry.summary if 'summary' in entry else ""
            print(f"处理社区热帖: {entry.title[:15]}...")
            
            items.append({
                "tag": "社区热点", # 标签改为热点
                "title_zh": translate_safe(entry.title), # 中文标题用于展示
                "title_en": entry.title, # 英文标题用于搜索 (修复B站搜索不准的问题)
                "summary": translate_safe(detail),
                "link": entry.link,
                "score": "🔥 Hot" # 标记为热门
            })
    except Exception as e:
        print(f"Reddit 同步失败: {e}")

    # 2. GitHub Trending (改为搜索最近7天的高星项目)
    # 以前是 sort:updated (更新时间)，容易抓到旧项目的微小改动
    # 现在是 created:>7days sort:stars (本周创建且高星)，只抓新出的黑马
    try:
        date_7_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        # 搜索：Topic是comfyui-nodes，创建时间在7天内，按Star数排序
        url = f"https://api.github.com/search/repositories?q=comfyui+nodes+created:>{date_7_days_ago}&sort=stars&order=desc&per_page=5"
        
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            for repo in resp.json().get('items', []):
                print(f"发现新工具: {repo['name']}")
                items.append({
                    "tag": "新工具",
                    "title_zh": f"黑马节点: {repo['name']}",
                    "title_en": f"ComfyUI {repo['name']}", # 构造英文搜索词
                    "summary": translate_safe(repo['description'] or "本周新发布的高关注度 ComfyUI 节点。"),
                    "link": repo['html_url'],
                    "score": f"⭐ {repo['stargazers_count']}"
                })
    except Exception as e:
        print(f"GitHub 同步失败: {e}")

    return items

def generate_app_html(items: List[Dict]):
    today = datetime.date.today().strftime('%m月%d日')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <title>Comfy 热点</title>
        <!-- PWA 全屏设置 -->
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
            body {{ background: #0a0a0a; color: #fff; font-family: 'Noto Sans SC', sans-serif; -webkit-font-smoothing: antialiased; }}
            .card {{ background: #141414; border: 1px solid #262626; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); }}
            .card:active {{ transform: scale(0.98); opacity: 0.9; }}
            /* 隐藏滚动条 */
            ::-webkit-scrollbar {{ display: none; }}
            .line-clamp-3 {{ display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        </style>
    </head>
    <body class="pb-24">
        <div class="max-w-md mx-auto min-h-screen relative flex flex-col">
            
            <!-- 头部 -->
            <header class="px-6 pt-16 pb-6 sticky top-0 bg-black/90 backdrop-blur-xl z-50 border-b border-white/5">
                <div class="flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-black italic tracking-tighter text-white">DAILY<span class="text-blue-500">.</span></h1>
                        <p class="text-[10px] text-gray-500 font-bold tracking-widest uppercase mt-1">ComfyUI 精选日报 · {today}</p>
                    </div>
                    <div class="bg-blue-600/20 text-blue-500 px-3 py-1 rounded-full text-xs font-bold border border-blue-500/20">
                        {len(items)} 条精选
                    </div>
                </div>
            </header>

            <!-- 列表 -->
            <main class="p-4 space-y-5">
    """

    if not items:
        html += """<div class="py-20 text-center text-gray-600">今日暂无高热度内容，去 B 站搜搜看？</div>"""
    
    for item in items:
        badge_bg = "bg-orange-500" if "社区" in item['tag'] else "bg-blue-600"
        
        # --- 关键修复：使用 title_en (英文原名) 进行搜索 ---
        # 移除 URL 中可能导致问题的特殊字符
        clean_keyword = item['title_en'].replace('"', '').replace("'", "")
        b_url = f"https://search.bilibili.com/all?keyword={clean_keyword}"
        
        html += f"""
                <div class="card p-5 rounded-[1.5rem] relative overflow-hidden group">
                    <!-- 顶部标签行 -->
                    <div class="flex justify-between items-start mb-3">
                        <span class="{badge_bg} text-white text-[10px] font-black px-2 py-1 rounded-md uppercase tracking-wide shadow-lg shadow-{badge_bg}/20">
                            {item['tag']}
                        </span>
                        <span class="text-gray-500 text-[10px] font-bold bg-white/5 px-2 py-1 rounded-md">
                            {item['score']}
                        </span>
                    </div>
                    
                    <!-- 标题 -->
                    <h2 class="text-lg font-bold leading-tight mb-2 text-gray-100">
                        <a href="{item['link']}" target="_blank">{item['title_zh']}</a>
                    </h2>
                    
                    <!-- 摘要 -->
                    <p class="text-[11px] text-gray-400 leading-relaxed mb-5 line-clamp-3">
                        {item['summary']}
                    </p>

                    <!-- 操作按钮 -->
                    <div class="grid grid-cols-2 gap-3">
                        <a href="{item['link']}" target="_blank" class="flex items-center justify-center py-3 bg-white/5 rounded-xl text-[10px] font-bold text-gray-300 border border-white/5 active:bg-white/10">
                            查看原文
                        </a>
                        <a href="{b_url}" target="_blank" class="flex items-center justify-center py-3 bg-[#00aeec]/10 rounded-xl text-[10px] font-bold text-[#00aeec] border border-[#00aeec]/20 active:bg-[#00aeec]/20">
                            📺 B站搜 "{clean_keyword[:15]}..."
                        </a>
                    </div>
                </div>
        """

    html += """
            </main>
            
            <footer class="text-center py-10 text-[10px] text-gray-700 font-mono uppercase">
                Updated at 6:00 AM daily
            </footer>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    intel = fetch_high_quality_intel()
    generate_app_html(intel)

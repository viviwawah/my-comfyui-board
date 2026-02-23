import os
import json
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from typing import List, Dict

# --- 核心配置 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
}
TRANSLATOR = GoogleTranslator(source='auto', target='zh-CN')

def translate_safe(text: str) -> str:
    """安全的翻译函数，只翻译摘要，保留技术专有名词的语境"""
    try:
        if not text or len(text.strip()) < 5: return ""
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        return TRANSLATOR.translate(clean_text[:250])
    except:
        return text

def fetch_high_quality_intel() -> List[Dict]:
    items = []
    print("🚀 正在挖掘高质量 ComfyUI 热点...")
    
    # 1. Reddit r/comfyui (获取 TOP - 每日高赞)
    try:
        resp = requests.get("https://www.reddit.com/r/comfyui/top/.rss?t=day", headers=HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:10]:
            detail = entry.summary if 'summary' in entry else ""
            clean_keyword = entry.title.replace('"', '').replace("'", "")
            print(f"处理社区热帖: {entry.title[:15]}...")
            
            items.append({
                "id": entry.link, # 使用链接作为唯一ID
                "tag": "社区热点",
                "title_zh": translate_safe(entry.title),
                "title_en": entry.title,
                "clean_keyword": clean_keyword,
                "summary": translate_safe(detail),
                "link": entry.link,
                "score": "🔥 Hot"
            })
    except Exception as e:
        print(f"Reddit 同步失败: {e}")

    # 2. GitHub Trending (最近7天高星项目)
    try:
        date_7_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        url = f"https://api.github.com/search/repositories?q=comfyui+nodes+created:>{date_7_days_ago}&sort=stars&order=desc&per_page=5"
        
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            for repo in resp.json().get('items', []):
                clean_keyword = f"ComfyUI {repo['name']}".replace('"', '').replace("'", "")
                print(f"发现新工具: {repo['name']}")
                
                items.append({
                    "id": repo['html_url'], # 使用链接作为唯一ID
                    "tag": "新工具",
                    "title_zh": f"黑马节点: {repo['name']}",
                    "title_en": f"ComfyUI {repo['name']}",
                    "clean_keyword": clean_keyword,
                    "summary": translate_safe(repo['description'] or "本周新发布的高关注度 ComfyUI 节点。"),
                    "link": repo['html_url'],
                    "score": f"⭐ {repo['stargazers_count']}"
                })
    except Exception as e:
        print(f"GitHub 同步失败: {e}")

    return items

def generate_app_html(items: List[Dict]):
    today = datetime.date.today().strftime('%m月%d日')
    
    # 将 Python 数据转为 JSON，传递给前端 JavaScript
    items_json = json.dumps(items, ensure_ascii=False)
    
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
            body {{ background: #0a0a0a; color: #fff; font-family: 'Noto Sans SC', sans-serif; -webkit-font-smoothing: antialiased; padding-bottom: 90px; }}
            .card {{ background: #141414; border: 1px solid #262626; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); transition: transform 0.1s; }}
            .card:active {{ transform: scale(0.98); }}
            ::-webkit-scrollbar {{ display: none; }}
            .line-clamp-3 {{ display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
            
            /* 底部导航激活状态 */
            .nav-item.active {{ color: #3b82f6; opacity: 1; }}
            .nav-item {{ opacity: 0.4; transition: all 0.2s; }}
            
            /* 收藏按钮动画 */
            .fav-btn svg {{ transition: transform 0.2s, fill 0.2s; }}
            .fav-btn:active svg {{ transform: scale(1.3); }}
            .is-fav svg {{ fill: #ef4444; color: #ef4444; }}
        </style>
    </head>
    <body>
        <div class="max-w-md mx-auto min-h-screen relative flex flex-col">
            
            <!-- 头部 -->
            <header class="px-6 pt-16 pb-6 sticky top-0 bg-black/90 backdrop-blur-xl z-50 border-b border-white/5">
                <div class="flex justify-between items-center">
                    <div>
                        <h1 id="header-title" class="text-3xl font-black italic tracking-tighter text-white">DAILY<span class="text-blue-500">.</span></h1>
                        <p class="text-[10px] text-gray-500 font-bold tracking-widest uppercase mt-1">ComfyUI 精选 · {today}</p>
                    </div>
                    <div id="header-badge" class="bg-blue-600/20 text-blue-500 px-3 py-1 rounded-full text-xs font-bold border border-blue-500/20">
                        {len(items)} 条精选
                    </div>
                </div>
            </header>

            <!-- 内容区 (由 JS 渲染) -->
            <main id="app-content" class="p-4 space-y-5">
                <!-- 卡片会注入在这里 -->
            </main>
            
            <footer class="text-center py-10 text-[10px] text-gray-700 font-mono uppercase">
                Data cached locally
            </footer>

            <!-- 底部导航 -->
            <nav class="fixed bottom-0 left-0 right-0 max-w-md mx-auto h-[85px] bg-black/95 backdrop-blur-xl border-t border-white/10 flex items-start pt-3 justify-around px-10 z-50 pb-safe">
                <div onclick="switchTab('feed')" id="nav-feed" class="nav-item active flex flex-col items-center gap-1 cursor-pointer">
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
                    <span class="text-[9px] font-bold">情报</span>
                </div>
                <div onclick="switchTab('favorites')" id="nav-fav" class="nav-item flex flex-col items-center gap-1 cursor-pointer">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
                    <span class="text-[9px] font-bold">收藏</span>
                </div>
            </nav>
        </div>

        <!-- 前端逻辑 -->
        <script>
            // 接收 Python 传过来的今日数据
            const dailyItems = {items_json};
            
            // 从本地存储读取收藏列表
            let favorites = JSON.parse(localStorage.getItem('comfy_favorites')) || [];
            let currentTab = 'feed';

            function saveFavorites() {{
                localStorage.setItem('comfy_favorites', JSON.stringify(favorites));
            }}

            function toggleFavorite(id) {{
                // 在今日列表或收藏列表中找到该项目
                let item = dailyItems.find(i => i.id === id) || favorites.find(i => i.id === id);
                if (!item) return;

                const index = favorites.findIndex(fav => fav.id === id);
                if (index > -1) {{
                    // 已存在则移除
                    favorites.splice(index, 1);
                }} else {{
                    // 不存在则添加
                    favorites.push(item);
                }}
                
                saveFavorites();
                renderCurrentTab(); // 重新渲染刷新图标
            }}

            function generateCardHTML(item) {{
                const isFav = favorites.some(fav => fav.id === item.id);
                const badgeBg = item.tag.includes("社区") ? "bg-orange-500" : "bg-blue-600";
                const bUrl = `https://search.bilibili.com/all?keyword=${{item.clean_keyword}}`;
                const favClass = isFav ? "is-fav" : "text-gray-500";
                const favSvg = isFav 
                    ? `<path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"/>`
                    : `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>`;

                return `
                    <div class="card p-5 rounded-[1.5rem] relative overflow-hidden group">
                        <div class="flex justify-between items-start mb-3">
                            <span class="${{badgeBg}} text-white text-[10px] font-black px-2 py-1 rounded-md uppercase tracking-wide">
                                ${{item.tag}}
                            </span>
                            
                            <div class="flex items-center gap-2">
                                <span class="text-gray-500 text-[10px] font-bold bg-white/5 px-2 py-1 rounded-md">${{item.score}}</span>
                                <button onclick="toggleFavorite('${{item.id}}')" class="fav-btn ${{favClass}} bg-white/5 p-1.5 rounded-full outline-none">
                                    <svg class="w-4 h-4" fill="${{isFav ? 'currentColor' : 'none'}}" stroke="currentColor" viewBox="0 0 24 24">${{favSvg}}</svg>
                                </button>
                            </div>
                        </div>
                        
                        <h2 class="text-lg font-bold leading-tight mb-2 text-gray-100">
                            <a href="${{item.link}}" target="_blank">${{item.title_zh}}</a>
                        </h2>
                        
                        <p class="text-[11px] text-gray-400 leading-relaxed mb-5 line-clamp-3">
                            ${{item.summary}}
                        </p>

                        <div class="grid grid-cols-2 gap-3">
                            <a href="${{item.link}}" target="_blank" class="flex items-center justify-center py-3 bg-white/5 rounded-xl text-[10px] font-bold text-gray-300 border border-white/5">
                                查看原文
                            </a>
                            <a href="${{bUrl}}" target="_blank" class="flex items-center justify-center py-3 bg-[#00aeec]/10 rounded-xl text-[10px] font-bold text-[#00aeec] border border-[#00aeec]/20">
                                📺 B站搜 "${{item.clean_keyword.substring(0, 10)}}..."
                            </a>
                        </div>
                    </div>
                `;
            }}

            function renderCurrentTab() {{
                const container = document.getElementById('app-content');
                const itemsToRender = currentTab === 'feed' ? dailyItems : favorites.reverse();
                
                if (itemsToRender.length === 0) {{
                    const msg = currentTab === 'feed' ? "今日暂无高热度内容" : "你的收藏夹空空如也，快去情报页逛逛吧";
                    container.innerHTML = `<div class="py-20 text-center text-gray-600">${{msg}}</div>`;
                    return;
                }}
                
                container.innerHTML = itemsToRender.map(generateCardHTML).join('');
                
                // 更新顶部标题
                document.getElementById('header-title').innerHTML = currentTab === 'feed' ? 'DAILY<span class="text-blue-500">.</span>' : 'SAVED<span class="text-red-500">.</span>';
                document.getElementById('header-badge').innerText = currentTab === 'feed' ? `${{dailyItems.length}} 条精选` : `${{favorites.length}} 条收藏`;
                
                // 重置翻转数组以防副作用
                if(currentTab === 'favorites') favorites.reverse(); 
            }}

            function switchTab(tab) {{
                currentTab = tab;
                document.getElementById('nav-feed').classList.toggle('active', tab === 'feed');
                document.getElementById('nav-fav').classList.toggle('active', tab === 'favorites');
                window.scrollTo(0, 0); // 切换时回到顶部
                renderCurrentTab();
            }}

            // 初始化渲染
            renderCurrentTab();
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    intel = fetch_high_quality_intel()
    generate_app_html(intel)

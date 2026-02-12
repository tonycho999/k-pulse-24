import os
import sys
import json
import time
import random
import requests
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

supabase: Client = create_client(os.environ.get("NEXT_PUBLIC_SUPABASE_URL"), os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# [요구사항 2] 최신 모델부터 차례로 시도
MODELS_TO_TRY = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]

# [요구사항 1] 보완 전략 키워드 전체 반영
SEARCH_KEYWORDS = [
    "컴백", "빌보드", "데뷔", "월드투어", "독점", "가수", "아이돌",
    "뮤직비디오", "챌린지", "유행", "엠카", "포토카드",
    "시청률", "종영", "넷플릭스", "대본리딩", "배우",
    "드라마", "캐스팅", "OTT", "제작발표회", "반전 결말", "개봉",
    "영화", "관객수", "박스오피스", "시사회", "무대인사",
    "예능", "대상 후보", "유튜브", "개그맨", "개그우먼", "코미디언",
    "푸드", "해외 반응", "뷰티", "팝업스토어", "웹툰", "패션", "음식"
]

def get_naver_api_news(keyword):
    import urllib.parse, urllib.request
    url = f"https://openapi.naver.com/v1/search/news?query={urllib.parse.quote(keyword)}&display=20&sort=sim"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", os.environ.get("NAVER_CLIENT_ID"))
    req.add_header("X-Naver-Client-Secret", os.environ.get("NAVER_CLIENT_SECRET"))
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8')).get('items', [])
    except: return []

def get_article_image(link):
    from bs4 import BeautifulSoup
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(link, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        return og_image['content'] if og_image else None
    except: return None

def ai_chief_editor(news_batch):
    raw_text = "\n".join([f"[{i}] {n['title']}" for i, n in enumerate(news_batch)])
    prompt = f"""
    Task: Analyze these {len(news_batch)} news items. 
    1. Select exactly 30 news items and rank them 1 to 30 based on buzzworthiness.
    2. Categorize into [k-pop, k-drama, k-movie, k-entertain, k-culture].
    3. Generate a ONE-SENTENCE "Global Insight" based on the REAL trends found in these news titles. 
       (e.g., "K-Pop groups are dominating global charts while K-Drama leads OTT rankings.")
    
    Output JSON:
    {{
        "global_insight": "Actual trend summary...",
        "articles": [
            {{ "original_index": 0, "rank": 1, "category": "k-pop", "eng_title": "...", "summary": "3-line English summary", "score": 9.5 }}
        ]
    }}
    """
    for model in MODELS_TO_TRY:
        try:
            print(f"🤖 AI 분석 중... (모델: {model})")
            res = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=model, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)
        except: continue
    return None

def run():
    print("🚀 뉴스 엔진 가동...")
    all_news = []
    for kw in SEARCH_KEYWORDS:
        all_news.extend(get_naver_api_news(kw))
    
    print(f"🔍 {len(all_news)}건 수집 완료. AI 랭킹 분석 시작...")
    result = ai_chief_editor(all_news)
    if not result: return

    global_insight = result.get('global_insight', "Global entertainment is evolving with K-Wave's latest innovations.")
    
    # [요구사항 4] 기존 데이터 삭제 (Fresh Start)
    supabase.table("live_news").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    saved = 0
    for art in result.get('articles', []):
        idx = art['original_index']
        if idx >= len(all_news): continue
        orig = all_news[idx]
        
        img = get_article_image(orig['link'])
        if not img: img = f"https://placehold.co/600x400/111/cyan?text={art['category']}"

        data = {
            "rank": art['rank'],
            "category": art['category'],
            "title": art['eng_title'],
            "summary": art['summary'],
            "link": orig['link'],
            "image_url": img,
            "score": art['score'],
            "insight": global_insight,
            "likes": 0, "dislikes": 0,
            "created_at": datetime.now().isoformat()
        }
        
        # 1. 실시간 뉴스 저장
        supabase.table("live_news").insert(data).execute()
        
        # 2. [추가] Top 10 기사는 검색 아카이브에 영구 저장
        if art['rank'] <= 10:
            archive_data = {
                "original_link": orig['link'],
                "category": art['category'],
                "title": art['eng_title'],
                "summary": art['summary'],
                "image_url": img,
                "score": art['score'],
                "archive_reason": "Top 10 Rank"
            }
            supabase.table("search_archive").upsert(archive_data, on_conflict="original_link").execute()
            
        saved += 1
        print(f"✅ #{art['rank']} 저장 완료")

    print(f"=== 최종 완료: {saved}개 뉴스 업데이트 ===")

if __name__ == "__main__":
    run()

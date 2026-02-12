import os
import sys
import json
import time
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

supabase: Client = create_client(os.environ.get("NEXT_PUBLIC_SUPABASE_URL"), os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODELS_TO_TRY = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile"]

# [키워드 유지] 분할 수집 및 키워드 분석의 기준이 되는 맵입니다.
CATEGORY_MAP = {
    "k-pop": ["컴백", "빌보드", "아이돌", "뮤직", "비디오", "챌린지", "포토카드", "월드투어", "가수"],
    "k-drama": ["드라마", "시청률", "넷플릭스", "OTT", "배우", "캐스팅", "대본리딩", "종영"],
    "k-movie": ["영화", "개봉", "박스오피스", "시사회", "영화제", "관객", "무대인사"],
    "k-entertain": ["예능", "유튜브", "개그맨", "코미디언", "방송", "개그우먼"],
    "k-culture": ["푸드", "뷰티", "웹툰", "팝업스토어", "패션", "음식", "해외반응"]
}

def get_naver_api_news(keyword):
    import urllib.parse, urllib.request
    url = f"https://openapi.naver.com/v1/search/news?query={urllib.parse.quote(keyword)}&display=100&sort=sim"
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

def ai_category_editor(category, news_batch):
    limited_batch = news_batch[:150]
    raw_text = "\n".join([f"[{i}] {n['title']}" for i, n in enumerate(limited_batch)])
    
    prompt = f"""
    Task: Select the TOP 30 news items for the '{category}' category.
    Constraints: Select EXACTLY 30, rank 1-30, translate to English, 3-line summary.
    List: {raw_text}
    Output JSON Format: {{ "articles": [ {{ "original_index": 0, "rank": 1, "category": "{category}", "eng_title": "...", "summary": "...", "score": 9.5 }} ] }}
    """
    
    for model in MODELS_TO_TRY:
        try:
            res = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": "You are a professional K-Enter Editor."},
                          {"role": "user", "content": prompt}], 
                model=model, response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content).get('articles', [])
        except: continue
    return []

def run():
    print("🚀 뉴스 엔진 가동 (슬라이딩 교체 모드)...")

    # 1. 좋아요 Top 10 아카이브 백업
    try:
        top_voted = supabase.table("live_news").select("*").order("likes", desc=True).limit(10).execute()
        for item in top_voted.data:
            archive_data = {
                "original_link": item['link'], "category": item['category'], "title": item['title'],
                "summary": item['summary'], "image_url": item['image_url'], "score": item['score'], "archive_reason": "Top 10 Likes"
            }
            supabase.table("search_archive").upsert(archive_data, on_conflict="original_link").execute()
    except: pass

    pending_inserts = []
    
    # 2. 카테고리별 수집 및 분석 (키워드 기반 수집 유지)
    for category, keywords in CATEGORY_MAP.items():
        print(f"📂 {category.upper()} 부문 분석 시작...")
        cat_news = []
        for kw in keywords:
            cat_news.extend(get_naver_api_news(kw))
        
        cat_news = list({n['link']: n for n in cat_news}.values())
        selected = ai_category_editor(category, cat_news)
        
        for art in selected:
            idx = art['original_index']
            if idx >= len(cat_news): continue
            orig = cat_news[idx]
            img = get_article_image(orig['link'])
            if not img: img = f"https://placehold.co/600x400/111/cyan?text={category}"

            pending_inserts.append({
                "rank": art['rank'], "category": category, "title": art['eng_title'],
                "summary": art['summary'], "link": orig['link'], "image_url": img,
                "score": art['score'], "likes": 0, "dislikes": 0, "created_at": datetime.now().isoformat()
            })

    # 3. 슬라이딩 교체: 새 기사 수만큼 오래된/저점수 기사 삭제
    if pending_inserts:
        num_new = len(pending_inserts)
        try:
            to_delete = supabase.table("live_news").select("id") \
                .order("created_at", desc=False) \
                .order("score", desc=False) \
                .limit(num_new).execute()

            delete_ids = [item['id'] for item in to_delete.data]
            if delete_ids:
                supabase.table("live_news").delete().in_("id", delete_ids).execute()
                print(f"🧹 구형 기사 {len(delete_ids)}개 삭제 완료.")
            
            supabase.table("live_news").insert(pending_inserts).execute()
            print(f"✅ 신규 기사 {num_new}개 삽입 완료.")
        except Exception as e:
            print(f"⚠️ 교체 중 오류: {e}")

if __name__ == "__main__":
    run()

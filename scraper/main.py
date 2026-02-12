import os
import sys
import json
import time
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta
# [수정] 날짜 파싱 오류 해결을 위해 추가
from dateutil.parser import isoparse 
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

supabase: Client = create_client(os.environ.get("NEXT_PUBLIC_SUPABASE_URL"), os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODELS_TO_TRY = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile"]

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
    if not news_batch: return []
    limited_batch = news_batch[:150]
    raw_text = "\n".join([f"[{i}] {n['title']}" for i, n in enumerate(limited_batch)])
    
    prompt = f"""
    Task: Select exactly 30 news items for '{category}'. If not enough, select as many as possible.
    Constraints: Rank 1-30, English translation, 3-line summary, AI Score (0.0-10.0).
    List: {raw_text}
    Output JSON: {{ "articles": [ {{ "original_index": 0, "rank": 1, "category": "{category}", "eng_title": "...", "summary": "...", "score": 9.5 }} ] }}
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
    print("🚀 7단계 마스터 엔진 가동 (안전한 30개 유지 로직)...")
    
    for category, keywords in CATEGORY_MAP.items():
        print(f"📂 {category.upper()} 부문 처리 중...")

        # 1~2. 수집 및 중복 제거
        raw_news = []
        for kw in keywords: raw_news.extend(get_naver_api_news(kw))
        
        db_res = supabase.table("live_news").select("link").eq("category", category).execute()
        db_links = {item['link'] for item in db_res.data}
        new_candidate_news = [n for n in raw_news if n['link'] not in db_links]
        new_candidate_news = list({n['link']: n for n in new_candidate_news}.values())
        
        print(f"   🔎 수집: {len(raw_news)}개 -> 신규 기사: {len(new_candidate_news)}개")

        # 3. 분류 및 평점 (AI Scoring)
        selected = ai_category_editor(category, new_candidate_news)
        num_new = len(selected)
        
        if num_new > 0:
            # 7. 신규 기사 삽입 (Upsert로 중복 에러 방지)
            new_data_list = []
            for art in selected:
                idx = art['original_index']
                if idx >= len(new_candidate_news): continue
                orig = new_candidate_news[idx]
                img = get_article_image(orig['link']) or f"https://placehold.co/600x400/111/cyan?text={category}"

                new_data_list.append({
                    "rank": art['rank'], "category": category, "title": art['eng_title'],
                    "summary": art['summary'], "link": orig['link'], "image_url": img,
                    "score": art['score'], "likes": 0, "dislikes": 0, "created_at": datetime.now().isoformat()
                })
            
            if new_data_list:
                supabase.table("live_news").upsert(new_data_list, on_conflict="link").execute()
                print(f"   ✅ 신규 {len(new_data_list)}개 삽입 완료.")

        # 4~6. 슬롯 체크 및 조건부 삭제 (최소 30개 보장)
        res = supabase.table("live_news").select("id", "created_at", "score").eq("category", category).execute()
        current_articles = res.data
        current_count = len(current_articles)
        
        if current_count > 30:
            now = datetime.now()
            threshold = now - timedelta(hours=24)
            
            # [수정된 파싱 로직] isoparse를 사용하여 마이크로초 자릿수 문제 해결
            old_articles = []
            fresh_articles = []
            for a in current_articles:
                # isoparse는 .79472 같은 5자리 마이크로초도 완벽하게 읽습니다.
                dt_obj = isoparse(a['created_at']).replace(tzinfo=None)
                if dt_obj < threshold: old_articles.append(a)
                else: fresh_articles.append(a)
            
            delete_ids = []
            
            # 5. 24시간 넘은 기사 삭제 (30개 될 때까지만)
            old_articles.sort(key=lambda x: x['created_at'])
            for oa in old_articles:
                if current_count <= 30: break
                delete_ids.append(oa['id'])
                current_count -= 1
            
            # 6. 그래도 30개 넘으면 점수 낮은 순 삭제
            if current_count > 30:
                fresh_articles.sort(key=lambda x: x['score'])
                for fa in fresh_articles:
                    if current_count <= 30: break
                    delete_ids.append(fa['id'])
                    current_count -= 1

            if delete_ids:
                supabase.table("live_news").delete().in_("id", delete_ids).execute()
                print(f"   🧹 슬롯 조정: {len(delete_ids)}개 삭제 완료 (최종 30개 유지)")

    print(f"🎉 작업 완료.")

if __name__ == "__main__":
    run()

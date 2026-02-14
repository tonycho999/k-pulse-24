import os
import json
import time
import requests
import urllib.parse
from supabase import create_client, Client
from dotenv import load_dotenv
from ddgs import DDGS

# 1. 환경변수 로드
load_dotenv()

# 2. Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Gemini API 키
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    print(f"🔑 API Key Loaded: {GOOGLE_API_KEY[:5]}...")
else:
    print("❌ No API Key found!")

# ✅ [핵심 변경 1] 검색어를 '한국어'로 변경해야 최신 뉴스가 잡힘
CATEGORIES = {
    "K-Pop": "K-POP 아이돌 최신 뉴스 컴백",
    "K-Drama": "한국 드라마 시청률 순위 최신 뉴스",
    "K-Movie": "한국 영화 박스오피스 개봉작 반응",
    "K-Entertain": "한국 예능 프로그램 시청률 화제성", 
    "K-Culture": "서울 핫플레이스 유행 팝업스토어 트렌드" 
}

# 모델 자동 탐색 (404 방지)
def get_dynamic_model_url():
    print("🔍 Fetching available Gemini models...")
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
    
    try:
        response = requests.get(list_url)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            valid_models = [
                m['name'] for m in models 
                if 'generateContent' in m.get('supportedGenerationMethods', []) 
                and 'flash' in m['name']
            ]
            if valid_models:
                best_model = valid_models[-1] 
                if not best_model.startswith("models/"):
                    best_model = f"models/{best_model}"
                print(f"✅ Selected Model: {best_model}")
                return f"https://generativelanguage.googleapis.com/v1beta/{best_model}:generateContent"
    except Exception as e:
        print(f"⚠️ Model fetch failed: {e}")

    return "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

CURRENT_MODEL_URL = get_dynamic_model_url()

def get_fallback_image(keyword):
    """뉴스에 이미지가 없을 때 이미지 검색 (한국어 검색)"""
    try:
        with DDGS() as ddgs:
            # 여기도 kr-kr로 검색해야 이미지가 잘 나옴
            imgs = list(ddgs.images(keywords=keyword, region="kr-kr", safesearch="off", max_results=1))
            if imgs and len(imgs) > 0:
                return imgs[0].get('image')
    except Exception:
        return ""
    return ""

def search_web(keyword):
    """
    DuckDuckGo 검색: 
    - 키워드: 한국어
    - 지역: 한국 (kr-kr) -> 이게 핵심!
    - 기간: 지난 24시간 (d)
    """
    print(f"🔍 [Search] Searching for '{keyword}' in Korea (Last 24h)...")
    results = []
    
    try:
        with DDGS() as ddgs:
            # ✅ [핵심 변경 2] region="kr-kr" (한국)
            ddg_results = list(ddgs.news(
                query=keyword, 
                region="kr-kr",   # 한국 뉴스만 검색
                safesearch="off", 
                timelimit="d",    # 지난 24시간 (한국어라 이제 데이터 많음)
                max_results=15
            ))
            
            for r in ddg_results:
                title = r.get('title', '')
                body = r.get('body', r.get('snippet', ''))
                link = r.get('url', r.get('href', ''))
                image = r.get('image', r.get('thumbnail', ''))

                if not title or not body or not link or not link.startswith("https"):
                    continue

                if not image:
                    image = get_fallback_image(title)
                    time.sleep(0.3) 

                if not image:
                    continue

                results.append(f"Title: {title}\nBody: {body}\nLink: {link}\nImage: {image}")
                
    except Exception as e:
        print(f"⚠️ Search error: {e}")
    
    return "\n\n".join(results)

def call_gemini_api(category_name, raw_data):
    print(f"🤖 [Gemini] Translating & Writing '{category_name}' articles...")
    
    headers = {"Content-Type": "application/json"}
    
    # ✅ [핵심 변경 3] 한국어 데이터를 줄 테니 -> 영어로 기사를 써라 (번역+요약)
    prompt = f"""
    [Role]
    You are a veteran K-Entertainment journalist writing for an international audience.
    
    [Input Data (Korean News)]
    {raw_data[:25000]} 

    [Task]
    1. Read the Korean news provided above.
    2. Select the Top 10 most viral/important news items.
    3. **Rewrite/Translate them into PERFECT ENGLISH.**
    
    [Content Requirements - STRICT]
    1. **Language**: Output MUST be in **ENGLISH**.
    2. **Length**: 100~500 characters per summary.
    3. **Style**: Insightful, catchy, and professional.
    4. **Image**: Map the 'image_url' from raw data exactly.

    [Output Format (JSON Only)]
    {{
      "news_updates": [
        {{ 
          "keyword": "Main Subject (English)", 
          "title": "Title (English)", 
          "summary": "Summary (English, 100-500 chars)", 
          "link": "Original Link",
          "image_url": "URL starting with https"
        }}
      ],
      "rankings": [
        {{ "rank": 1, "title": "Name (English)", "meta": "Info (English)", "score": 98 }}
      ]
    }}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    full_url = f"{CURRENT_MODEL_URL}?key={GOOGLE_API_KEY}"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(full_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                try:
                    text = response.json()['candidates'][0]['content']['parts'][0]['text']
                    text = text.replace("```json", "").replace("```", "").strip()
                    return json.loads(text)
                except Exception as e:
                    print(f"   ⚠️ JSON Parse Error: {e}")
                    return None
            
            elif response.status_code in [404]:
                 print(f"   ❌ Model Not Found (404).")
                 return None

            elif response.status_code in [429, 503]:
                wait_time = (attempt + 1) * 10
                print(f"   ❌ Temporary Error ({response.status_code}). Retrying...")
                time.sleep(wait_time)
                continue
            
            else:
                print(f"   ❌ API Error ({response.status_code}): {response.text[:200]}")
                return None

        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            time.sleep(5)
            continue
            
    return None

def update_database(category, data):
    news_list = data.get("news_updates", [])
    if news_list:
        clean_news = []
        for item in news_list:
            if not item.get("image_url"): continue

            summary = item.get("summary", "")
            title = item.get("title", "No Title")
            
            if len(summary) < 50: 
                continue

            # 구글 뉴스 검색 링크 생성
            encoded_query = urllib.parse.quote(f"{title} k-pop news")
            search_link = f"https://www.google.com/search?q={encoded_query}&tbm=nws"

            clean_news.append({
                "category": category,
                "keyword": item.get("keyword", category),
                "title": title,
                "summary": summary,
                "link": search_link,
                "image_url": item.get("image_url"),
                "created_at": "now()",
                "likes": 0,
                "score": 80 + (len(summary) / 10) 
            })
        
        if clean_news:
            try:
                supabase.table("live_news").upsert(clean_news, on_conflict="category,keyword,title").execute()
                supabase.table("search_archive").upsert(clean_news, on_conflict="category,keyword,title").execute()
                print(f"   💾 Saved {len(clean_news)} news items.")
            except Exception as e:
                print(f"   ⚠️ DB Save Error: {e}")

    rank_list = data.get("rankings", [])
    if rank_list:
        clean_ranks = []
        for item in rank_list:
            clean_ranks.append({
                "category": category,
                "rank": item.get("rank"),
                "title": item.get("title"),
                "meta_info": item.get("meta", ""),
                "score": item.get("score", 0),
                "updated_at": "now()"
            })
        try:
            supabase.table("live_rankings").upsert(clean_ranks, on_conflict="category,rank").execute()
            print(f"   🏆 Updated rankings.")
        except Exception as e:
             print(f"   ⚠️ Ranking Save Error: {e}")

def main():
    print(f"🚀 Scraper Started (Korea Region Source -> English Output)")
    for category, search_keyword in CATEGORIES.items():
        raw_text = search_web(search_keyword)
        
        if len(raw_text) < 50: 
            print(f"⚠️ {category} : Not enough data (Surprisingly).")
            continue

        data = call_gemini_api(category, raw_text)
        if data:
            update_database(category, data)
        
        print("⏳ Cooldown (5s)...")
        time.sleep(5) 

    print("✅ All jobs finished.")

if __name__ == "__main__":
    main()

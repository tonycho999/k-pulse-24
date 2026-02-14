import os
import json
import time
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# 1. 환경변수 로드
load_dotenv()

# 2. Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Gemini API 키 설정
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# [설정] 검색어 최적화
CATEGORIES = {
    "K-Pop": "k-pop latest news trends",
    "K-Drama": "k-drama ratings news",
    "K-Movie": "korean movie box office news",
    "K-Variety": "korean variety show news",
    "K-Culture": "seoul travel food trends"
}

def search_web(keyword):
    """DuckDuckGo 검색 (라이브러리 경고 무시 및 안정성 확보)"""
    print(f"🔍 [Search] '{keyword}' 검색 중...")
    results = []
    try:
        with DDGS() as ddgs:
            # 1. 뉴스 검색 시도
            ddg_results = list(ddgs.news(keywords=keyword, region="kr-kr", safesearch="off", max_results=10))
            
            # 2. 뉴스 없으면 일반 텍스트 검색 시도
            if not ddg_results:
                time.sleep(1)
                ddg_results = list(ddgs.text(keywords=keyword, region="kr-kr", max_results=5))

            for r in ddg_results:
                title = r.get('title', '')
                body = r.get('body', r.get('snippet', ''))
                link = r.get('url', r.get('href', ''))
                if title and body:
                    results.append(f"제목: {title}\n내용: {body}\n링크: {link}")
                
    except Exception as e:
        print(f"⚠️ 검색 중 오류 발생 (건너뜀): {e}")
    
    return "\n\n".join(results)

def call_gemini_api(category_name, raw_data):
    """
    [핵심] 라이브러리 없이 직접 REST API 호출 (무적의 방식)
    """
    print(f"🤖 [Gemini] '{category_name}' 분석 요청 중 (REST API)...")
    
    # Gemini 1.5 Flash 엔드포인트 URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are a K-Entertainment news editor.
    Here is the raw search data for '{category_name}':
    {raw_data[:15000]} 

    Task: Extract 10 news items and Top 10 rankings.
    Output must be strict JSON without Markdown formatting.

    Format:
    {{
      "news_updates": [
        {{
          "keyword": "Core Keyword",
          "title": "Korean Title",
          "summary": "Korean Summary (1 sentence)",
          "link": "URL"
        }}
      ],
      "rankings": [
        {{ "rank": 1, "title": "Name", "meta": "Info" }}
      ]
    }}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # 응답 상태 체크
        if response.status_code != 200:
            print(f"❌ API 호출 실패: {response.status_code} - {response.text}")
            return None
            
        result = response.json()
        
        # 텍스트 추출
        try:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # JSON 클리닝 (가끔 ```json 같은게 붙어옴)
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"❌ JSON 파싱 실패: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return None

def update_database(category, data):
    # 1. 뉴스 저장
    news_list = data.get("news_updates", [])
    if news_list:
        clean_news = []
        for item in news_list:
            clean_news.append({
                "category": category,
                "keyword": item.get("keyword", category),
                "title": item.get("title", "제목 없음"),
                "summary": item.get("summary", ""),
                "link": item.get("link", ""),
                "created_at": "now()"
            })
        
        try:
            supabase.table("live_news").upsert(clean_news, on_conflict="category,keyword,title").execute()
            supabase.table("search_archive").upsert(clean_news, on_conflict="category,keyword,title").execute()
            print(f"   💾 뉴스 {len(clean_news)}개 저장 완료")
        except Exception as e:
            print(f"   ⚠️ 뉴스 저장 실패: {e}")

    # 2. 랭킹 저장
    rank_list = data.get("rankings", [])
    if rank_list:
        clean_ranks = []
        for item in rank_list:
            clean_ranks.append({
                "category": category,
                "rank": item.get("rank"),
                "title": item.get("title"),
                "meta_info": item.get("meta", ""),
                "updated_at": "now()"
            })
        try:
            supabase.table("live_rankings").upsert(clean_ranks, on_conflict="category,rank").execute()
            print(f"   🏆 랭킹 갱신 완료")
        except Exception:
            pass

def main():
    print("🚀 스크래퍼 시작 (Direct REST API 방식)")
    
    for category, search_keyword in CATEGORIES.items():
        # 1. 검색
        raw_text = search_web(search_keyword)
        
        if len(raw_text) < 50:
            print(f"⚠️ {category} 정보 부족으로 건너뜀")
            continue

        # 2. AI 요약 (REST API)
        data = call_gemini_api(category, raw_text)
        
        # 3. 저장
        if data:
            update_database(category, data)
        
        time.sleep(3) # 대기

    print("✅ 모든 작업 완료")

if __name__ == "__main__":
    main()

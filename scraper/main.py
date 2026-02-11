import os
import sys
import json
import urllib.request
import urllib.parse
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from urllib.parse import urljoin  # 추가됨: 주소 결합용

# 1. 환경 설정
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")
naver_client_id = os.environ.get("NAVER_CLIENT_ID")
naver_client_secret = os.environ.get("NAVER_CLIENT_SECRET")

if not all([supabase_url, supabase_key, groq_api_key, naver_client_id, naver_client_secret]):
    print("❌ Error: .env 키 확인 필요")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)
groq_client = Groq(api_key=groq_api_key)
AI_MODEL = "llama-3.3-70b-versatile"

SEARCH_KEYWORDS = ["K-POP 아이돌", "한국 인기 드라마", "한국 영화 화제", "한국 예능 레전드"]

def get_real_news_image(link):
    """
    강화된 이미지 추출기: 메타 데이터 및 본문 내 고화질 이미지 탐색
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Referer': 'https://news.naver.com/'
        }
        
        response = requests.get(link, headers=headers, timeout=10)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        img_url = None

        # 1. og:image 우선 탐색
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            
        # 2. og:image가 없거나 네이버 기본 로고일 경우 본문 탐색
        if not img_url or "static.naver.net" in img_url:
            # 네이버 뉴스 및 주요 언론사 본문 이미지 셀렉터
            selectors = ['#dic_area img', '#articleBodyContents img', '.article_kanvas img', '.article_body img', 'article img']
            for selector in selectors:
                img_tag = soup.select_one(selector)
                if img_tag and img_tag.get('src'):
                    img_url = img_tag['src']
                    break
        
        if img_url:
            # 상대 경로를 절대 경로로 변환 (예: /img.jpg -> https://news.com/img.jpg)
            img_url = urljoin(link, img_url)
            return img_url

    except Exception as e:
        print(f"⚠️ 추출 실패: {e}")
    return None

def get_naver_api_news(keyword):
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=15&sort=sim"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", naver_client_id)
    req.add_header("X-Naver-Client-Secret", naver_client_secret)
    
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8')).get('items', [])
    except: return []

def ai_chief_editor(news_batch):
    news_text = ""
    for idx, item in enumerate(news_batch):
        clean_title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        news_text += f"{idx+1}. {clean_title}\n"

    prompt = f"""Role: Chief Editor. Task: Select Top 12. Output JSON strictly. Raw Titles:\n{news_text}"""
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=AI_MODEL,
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except: return None

def run():
    print(f"=== {datetime.now()} 실전 이미지 추출 모드 시작 ===")
    all_news = []
    for keyword in SEARCH_KEYWORDS:
        all_news.extend(get_naver_api_news(keyword))
    
    result = ai_chief_editor(all_news)
    if not result: return

    saved_count = 0
    for article in result.get('articles', []):
        idx = article.get('original_title_index', 1) - 1
        if idx < 0 or idx >= len(all_news): idx = 0
        original = all_news[idx]

        # 📡 실제 이미지 추출 시도
        real_img = get_real_news_image(original['link'])
        
        # ❌ 실패 시에만 placeholder 사용 (이때 로그를 남겨 확인)
        if not real_img:
            print(f"⚠️ 이미지를 못 찾음: {article['title'][:20]}...")
            real_img = f"https://placehold.co/600x400/111/cyan?text={article.get('artist', 'News').replace(' ', '+')}"
        else:
            print(f"📸 이미지 추출 성공: {real_img[:50]}...")

        try:
            if supabase.table("live_news").select("id").eq("title", article['title']).execute().data: continue
            
            data = {
                "category": article.get('category', 'General'),
                "artist": article.get('artist', 'Trend'),
                "title": article['title'],
                "summary": article['summary'],
                "score": article.get('score', 5),
                "link": original['link'],
                "source": "Naver News",
                "image_url": real_img,
                "reactions": article['reactions'],
                "is_published": True,
                "created_at": datetime.now().isoformat()
            }
            supabase.table("live_news").insert(data).execute()
            saved_count += 1
        except Exception as e: print(f"💾 저장 에러: {e}")

    print(f"=== 완료: {saved_count}개 업데이트됨 ===")

if __name__ == "__main__":
    run()

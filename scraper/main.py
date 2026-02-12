import os
import sys
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from urllib.parse import urljoin

# 1. 환경 설정
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")
naver_client_id = os.environ.get("NAVER_CLIENT_ID")
naver_client_secret = os.environ.get("NAVER_CLIENT_SECRET")

supabase: Client = create_client(supabase_url, supabase_key)
groq_client = Groq(api_key=groq_api_key)
AI_MODEL = "llama-3.3-70b-versatile"

# 사람처럼 보이기 위한 고정 헤더
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://news.naver.com/'
}

# 2. [기능 1] 네이버 연예 랭킹 30개 수집 (Selenium 스타일 직접 스크래핑)
def get_naver_ranking_30():
    print("📡 네이버 연예 실시간 랭킹 30 수집 중...")
    ranking_url = "https://entertain.naver.com/ranking"
    try:
        res = requests.get(ranking_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = []
        # 네이버 랭킹 뉴스 리스트 태그 (네이버 페이지 구조에 따라 수시 변경될 수 있음)
        # 보통 .rank_lst 나 .tit_area 안의 a 태그를 찾습니다.
        news_links = soup.select('.rank_lst li a.tit') or soup.select('.tit_area a')
        
        for i, a in enumerate(news_links[:30]):
            items.append({
                'title': a.get_text(strip=True),
                'link': urljoin(ranking_url, a['href']),
                'is_ranking': True,
                'rank': i + 1
            })
        return items
    except Exception as e:
        print(f"⚠️ 랭킹 수집 실패: {e}")
        return []

# 3. [기능 2] 부족한 카테고리용 검색어 기반 수집 (API 방식)
def get_naver_api_news(keyword):
    import urllib.parse
    import urllib.request
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news?query={encText}&display=10&sort=sim"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", naver_client_id)
    req.add_header("X-Naver-Client-Secret", naver_client_secret)
    try:
        res = urllib.request.urlopen(req)
        items = json.loads(res.read().decode('utf-8')).get('items', [])
        return [{'title': i['title'], 'link': i['link'], 'is_ranking': False} for i in items]
    except: return []

# 4. [기능 3] 기사 본문 및 실제 이미지 추출
def get_article_details(link):
    try:
        res = requests.get(link, headers=HEADERS, timeout=7)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 이미지 찾기
        og_image = soup.find('meta', property='og:image')
        img_url = og_image['content'] if og_image else None
        
        # 본문 텍스트 찾기 (요약용)
        content = soup.select_one('#dic_area, #articleBodyContents, .article_body')
        text = content.get_text(strip=True)[:1000] if content else ""
        
        return text, img_url
    except: return "", None

# 5. [기능 4] AI 편집장: 요약 및 카테고리 분류 (홈, 음악, 영화, 드라마, 연예)
def ai_chief_editor(news_list):
    # AI에게 전달할 텍스트 구성
    raw_text = "\n".join([f"[{i}] {n['title']}" for i, n in enumerate(news_list)])
    
    prompt = f"""
    Role: K-ENTER 24 Chief Editor.
    Task: Analyze the news and categorize into [Music, Movie, Drama, Celeb].
    Top 30 ranking news should also be assigned to Home.
    
    Raw News:
    {raw_text}
    
    JSON Output Format:
    {{
        "articles": [
            {{
                "original_index": 0,
                "category": "Music",
                "eng_title": "Headline in English",
                "summary": "1-2 sentence English summary",
                "reactions": {{"excitement": 70, "shock": 30, "sadness": 0}}
            }}
        ]
    }}
    """
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=AI_MODEL,
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except: return None

# 6. 실행 프로세스
def run():
    # 랜덤 휴식 효과 (1분 ~ 10분 사이 무작위 대기 후 시작)
    wait_time = random.randint(60, 600)
    print(f"🕒 보안을 위해 {wait_time}초 대기 후 시작합니다...")
    time.sleep(wait_time)

    print(f"=== {datetime.now()} 하이브리드 수집 모드 가동 ===")
    
    # 1단계: 랭킹 수집
    all_raw_news = get_naver_ranking_30()
    
    # 2단계: 모자란 카테고리 보충 (음악, 영화, 드라마 등)
    keywords = ["K-POP 신곡", "한국 영화 개봉", "한국 드라마 화제"]
    for kw in keywords:
        all_raw_news.extend(get_naver_api_news(kw))
    
    # 3단계: AI 분석
    analysis = ai_chief_editor(all_raw_news)
    if not analysis: return

    # 4단계: 상세 내용 추출 및 DB 저장
    saved = 0
    for art in analysis.get('articles', []):
        idx = art['original_index']
        if idx >= len(all_raw_news): continue
        
        item = all_raw_news[idx]
        
        # 중복 체크
        if supabase.table("live_news").select("id").eq("link", item['link']).execute().data:
            continue
            
        body, img = get_article_details(item['link'])
        if not img: img = f"https://placehold.co/600x400/111/cyan?text={art['category']}"

        try:
            data = {
                "category": art['category'], # 음악, 영화, 드라마, 연예 등
                "title": art['eng_title'],
                "summary": art['summary'],
                "link": item['link'],
                "image_url": img,
                "reactions": art['reactions'],
                "is_ranking": item.get('is_ranking', False),
                "created_at": datetime.now().isoformat()
            }
            supabase.table("live_news").insert(data).execute()
            saved += 1
            print(f"✅ 저장: {art['eng_title'][:30]}...")
        except: pass

    print(f"=== 작업 완료: {saved}개 뉴스 업데이트 ===")

if __name__ == "__main__":
    run()

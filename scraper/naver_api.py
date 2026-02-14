# scraper/naver_api.py
import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def search_news_api(keyword, display=10):
    """네이버 뉴스 검색 API (디버깅 강화)"""
    # 키 확인
    if not CLIENT_ID or not CLIENT_SECRET:
        print(f"   🚨 [Naver API Error] Client ID or Secret is MISSING. (ID={CLIENT_ID})")
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    
    # 공백 제거 (시크릿 키 오류 방지)
    headers = {
        "X-Naver-Client-Id": CLIENT_ID.strip(), 
        "X-Naver-Client-Secret": CLIENT_SECRET.strip()
    }
    params = {"query": keyword, "display": display, "sort": "sim"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            # print(f"   ✅ Naver Search Success: Found {len(items)} items.")
            return items
        else:
            # [중요] 에러 원인 출력
            print(f"   🚨 [Naver API Fail] Status: {resp.status_code}")
            print(f"   🚨 Message: {resp.text}")
            return []
            
    except Exception as e:
        print(f"   🚨 [Naver Connection Error] {e}")
        return []

def crawl_article(url):
    """뉴스 본문 및 이미지 추출"""
    if "news.naver.com" not in url:
        return {"text": "", "image": ""}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        time.sleep(0.3) 
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')

        content = ""
        for selector in ["#dic_area", "#articeBody", "#newsEndContents"]:
            el = soup.select_one(selector)
            if el:
                for tag in el(['script', 'style', 'a', 'iframe', 'span']):
                    tag.decompose()
                content = el.get_text(strip=True)
                break
        
        image_url = ""
        og_img = soup.select_one('meta[property="og:image"]')
        if og_img:
            image_url = og_img.get('content', '')

        return {"text": content[:3000], "image": image_url}

    except Exception:
        return {"text": "", "image": ""}

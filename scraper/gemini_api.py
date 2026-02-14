# scraper/gemini_api.py
import os
import json
import requests
import time
from dotenv import load_dotenv

# .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
API_KEY = os.getenv("GOOGLE_API_KEY")

# [중요] 모델명을 하드코딩으로 고정 (가장 안정적인 버전)
# models/ 접두사를 붙여야 404 에러가 덜 납니다.
MODEL_NAME = "models/gemini-1.5-flash"

def ask_gemini(prompt):
    """AI에게 질문 (Flash 모델 전용)"""
    if not API_KEY:
        print("🚨 Google API Key is missing!")
        return None

    # URL 생성
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        # 요청 전송
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # 성공
        if resp.status_code == 200:
            try:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            except Exception:
                return None

        # 실패 (404가 뜨면 API 설정 문제임)
        else:
            print(f"   ❌ Gemini Error {resp.status_code}: {resp.text[:100]}")
            
            # 404 에러가 떴을 때 사용자에게 힌트 주기
            if resp.status_code == 404:
                print("   👉 [Solution] Please ENABLE 'Generative Language API' in Google Cloud Console.")
            
            return None

    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        return None

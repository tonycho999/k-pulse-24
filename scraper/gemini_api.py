import os
import requests
import time
import re
import random
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
API_KEY = os.getenv("GOOGLE_API_KEY")

def ask_gemini_with_search_debug(prompt):
    if not API_KEY: return None, "API_KEY_MISSING"

    # [진단] 모델 리스트 조회 시에도 타임아웃 설정
    model_name = "models/gemini-1.5-flash-latest" # 가장 안정적인 모델 고정 시도
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={API_KEY.strip()}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search_retrieval": {}}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
    }

    # 최대 2회 시도
    for attempt in range(2):
        try:
            # [핵심] timeout을 30초로 짧게 설정하여 무한 대기 방지
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if resp.status_code == 429:
                print(f"⚠️ 429 감지. 즉시 루프 탈출 후 대기 로직으로 이동.")
                return None, f"HTTP_429: Rate Limit"

            if resp.status_code != 200:
                return None, f"HTTP_{resp.status_code}: {resp.text}"

            res_json = resp.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            
            # (기존 파싱 로직 동일...)
            def get_content(tag, text):
                pattern = rf"(?:\*+|#+)?{tag}(?:\*+|#+)?[:\s-]*(.*?)(?=\s*(?:#+|TARGET|HEADLINE|CONTENT|RANKINGS)|$)"
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                return match.group(1).strip() if match else None

            parsed = {
                'target_kr': get_content("TARGET_KR", raw_text),
                'target_en': get_content("TARGET_EN", raw_text),
                'headline': get_content("HEADLINE", raw_text),
                'content': get_content("CONTENT", raw_text),
                'raw_rankings': get_content("RANKINGS", raw_text)
            }

            if parsed['headline'] and parsed['content']:
                return parsed, raw_text
            return None, f"PARSING_ERROR: {raw_text[:100]}"

        except requests.exceptions.Timeout:
            print(f"⏰ 타임아웃 발생! AI가 너무 느립니다. (시도 {attempt+1})")
            continue 
        except Exception as e:
            return None, f"EXCEPTION: {str(e)}"
            
    return None, "TIMEOUT_OR_UNKNOWN_FAILURE"

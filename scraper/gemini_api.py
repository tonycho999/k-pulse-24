import os
import json
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
API_KEY = os.getenv("GOOGLE_API_KEY")

def ask_gemini_with_search(prompt):
    if not API_KEY:
        print("🚨 Google API Key missing")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY.strip()}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search_retrieval": {}}],
        "generationConfig": {
            "temperature": 0.2 # 약간의 창의성을 위해 0.2로 조정
        }
    }

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                res_json = resp.json()
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                
                # JSON 블록 추출
                match = re.search(r'(\{.*\})', text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    try:
                        # 제어 문자 제거
                        clean_json = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
                        return json.loads(clean_json)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 파싱 에러: {e}")
                        # 에러 파악을 위해 텍스트 끝부분 출력 (잘림 확인용)
                        print(f"📄 응답 끝부분: ...{text[-100:]}")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ 시도 {attempt+1} 실패: {e}")
    return None

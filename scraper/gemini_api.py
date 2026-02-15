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
            "temperature": 0.1 # 최대한 보수적으로 답변 유도
        }
    }

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                res_json = resp.json()
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                
                # [무적 파싱 로직] 텍스트 내에서 가장 바깥쪽 { } 를 찾아 추출
                match = re.search(r'(\{.*\})', text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    # 1. 마크다운 코드 블록 기호 제거
                    json_str = json_str.replace("```json", "").replace("```", "")
                    # 2. 구글 검색 주석([1], [2] 등) 제거
                    json_str = re.sub(r'\[\d+\]', '', json_str)
                    # 3. 제어 문자 및 줄바꿈 정리
                    clean_json = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
                    
                    try:
                        return json.loads(clean_json)
                    except json.JSONDecodeError:
                        # 따옴표 중복 등 미세한 에러 수정 시도
                        try:
                            fixed_json = json_str.replace("'", '"')
                            return json.loads(fixed_json)
                        except:
                            print(f"❌ JSON 최종 파싱 실패. 원문 확인 필요.")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ 시도 {attempt+1} 실패: {e}")
    return None

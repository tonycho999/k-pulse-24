import os
import json
import requests
import time
import re
from dotenv import load_dotenv

# .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
API_KEY = os.getenv("GOOGLE_API_KEY")

def get_best_model_name():
    """사용 가능한 최신 모델 자동 탐색 (공백 제거 안전장치 포함)"""
    if not API_KEY: return "models/gemini-1.5-flash"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY.strip()}"
    
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            chat_models = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            
            # 우선순위: 1.5-flash -> 2.0 -> Pro
            for m in chat_models:
                if 'gemini-1.5-flash' in m: return m
            for m in chat_models:
                if 'gemini-2.0-flash' in m: return m
            if chat_models: return chat_models[0]
    except:
        pass
    return "models/gemini-1.5-flash"

def extract_json_from_text(text):
    """
    AI 답변에서 JSON만 칼같이 추출하는 정규표현식 로직.
    답변에 잡담이 섞여도 가장 바깥쪽의 { }를 찾아내어 파싱합니다.
    """
    try:
        # 1. 가장 바깥쪽의 { ... } 패턴을 찾음 (re.DOTALL로 줄바꿈 포함 검색)
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            json_str = match.group(1)
            
            # 2. 제어문자(줄바꿈, 탭 등) 및 불필요한 공백으로 인한 파싱 에러 방지
            # 특히 유니코드 제어문자 및 이스케이프 문자 정제
            json_str = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
            
            return json.loads(json_str)
        return None
    except Exception as e:
        print(f"    ⚠️ JSON Parsing Error: {e}")
        # 실패 시 텍스트 일부를 로그로 출력하여 디버깅 지원
        # print(f"    Raw Text Snippet: {text[:100]}...") 
        return None

def ask_gemini(prompt):
    """AI에게 질문 (URL 무결성 검사 + 안전 필터 완전 해제 + 강화된 파싱)"""
    if not API_KEY:
        print("🚨 Google API Key is missing!")
        return None

    # 1. 모델명 가져오기 및 URL 조립
    model_name = get_best_model_name()
    clean_model = model_name.replace("models/", "").strip()
    clean_key = API_KEY.strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={clean_key}"

    headers = {"Content-Type": "application/json"}
    
    # 2. 안전 필터 전면 해제 (뉴스 분석 중 차단 방지)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"}
    ]

    # 3. 요청 데이터 구성
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": safety_settings,
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1 # 기계적이고 일관된 JSON 출력을 위해 낮게 설정
        }
    }

    # 4. 최대 3번 재시도 로직
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if resp.status_code == 200:
                res_json = resp.json()
                if 'candidates' not in res_json or not res_json['candidates']:
                    # 안전 필터 등으로 인해 답변이 생성되지 않은 경우
                    continue
                
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                
                # [핵심] 강화된 JSON 추출 함수 호출
                result = extract_json_from_text(text)
                if result:
                    return result
                
            elif resp.status_code == 400 and "generationConfig" in resp.text:
                # 구형 모델이 JSON 모드를 지원하지 않을 경우 일반 모드로 재시도
                del payload["generationConfig"]
                continue

            elif resp.status_code in [429, 500, 502, 503]:
                # 속도 제한 또는 서버 에러 시 대기 후 재시도
                time.sleep(2)
                continue
            
            else:
                # 기타 에러 발생 시 로그 출력
                # print(f"    ❌ API Error {resp.status_code}: {resp.text[:100]}")
                pass

        except Exception as e:
            # print(f"    ⚠️ Connection Error (Attempt {attempt+1}): {e}")
            time.sleep(2)

    return None

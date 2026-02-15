import os
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
API_KEY = os.getenv("GOOGLE_API_KEY")

def get_available_models_text():
    """현재 API 키로 사용 가능한 모델 목록을 문자열로 반환 (디버깅용)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            model_names = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            return "✅ 가용 모델 리스트: " + ", ".join(model_names)
        return f"❌ 모델 조회 실패 (HTTP {resp.status_code})"
    except:
        return "🚨 모델 조회 중 예외 발생"

def ask_gemini_with_search_debug(prompt):
    if not API_KEY: return None, "API_KEY_MISSING"

    # 현재 시도할 모델명 (가장 표준적인 이름)
    model_name = "models/gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={API_KEY.strip()}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search_retrieval": {}}],
        "generationConfig": {"temperature": 0.7}
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # 404나 400 에러 발생 시, 가용 모델 리스트를 긁어와서 반환함
        if resp.status_code != 200:
            diag_info = get_available_models_text()
            error_msg = f"HTTP_{resp.status_code}: {resp.text}\n\n🔍 진단정보: {diag_info}"
            return None, error_msg

        res_json = resp.json()
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        
        # [기존 태그 파싱 로직]
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
        return None, f"PARSING_FAILED\n\nRAW_TEXT: {raw_text}"

    except Exception as e:
        return None, f"EXCEPTION: {str(e)}"

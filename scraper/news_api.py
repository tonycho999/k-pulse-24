import os
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
# GitHub Secrets에 저장한 이름을 가져옵니다.
API_KEY = os.getenv("PERPLEXITY_API_KEY")

def ask_news_ai(prompt):
    """Perplexity API를 사용하여 실시간 뉴스를 검색하고 기사를 작성합니다."""
    if not API_KEY: 
        return None, "API_KEY_MISSING"

    url = "https://api.perplexity.ai/chat/completions"
    
    # Perplexity의 최신 실시간 검색 모델인 sonar-pro를 사용합니다.
    # sonar 모델은 자동으로 웹 검색을 수행하여 최신 정보를 가져옵니다.
    payload = {
        "model": "sonar-pro", 
        "messages": [
            {
                "role": "system", 
                "content": "당신은 한국의 최신 연예/문화 뉴스를 정확하게 전달하는 전문 기자입니다. 항상 실시간 웹 검색 결과를 바탕으로 사실만을 작성하세요."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2, # 뉴스이므로 정확도를 위해 낮게 설정
        "top_p": 0.9,
        "return_citations": True # 출처 정보를 포함하도록 설정
    }

    headers = {
        "Authorization": f"Bearer {API_KEY.strip()}",
        "Content-Type": "application/json"
    }

    try:
        # 타임아웃을 60초로 넉넉히 설정 (검색 시간이 필요함)
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code != 200:
            return None, f"HTTP_{resp.status_code}: {resp.text}"

        res_json = resp.json()
        raw_text = res_json['choices'][0]['message']['content']
        
        # 태그 파싱 로직 (기존과 동일하게 유지하여 다른 코드와 호환)
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
        return None, f"PARSING_FAILED: {raw_text[:200]}"

    except Exception as e:
        return None, f"EXCEPTION: {str(e)}"

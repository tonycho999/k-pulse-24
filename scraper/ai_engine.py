import os
import json
import time
import re
import requests
from groq import Groq
from scraper.config import CATEGORY_SEEDS

# =========================================================
# 1. 지능형 모델 필터링 (기존 코드 유지)
# =========================================================

def get_groq_text_models():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return []
    try:
        client = Groq(api_key=api_key)
        all_models = client.models.list()
        valid_models = []
        for m in all_models.data:
            mid = m.id.lower()
            if 'vision' in mid or 'whisper' in mid or 'audio' in mid:
                continue
            valid_models.append(m.id)
        valid_models.sort(reverse=True)
        return valid_models
    except Exception as e:
        print(f"      ⚠️ Groq 모델 조회 실패: {e}")
        return []

def get_openrouter_text_models():
    try:
        res = requests.get("https://openrouter.ai/api/v1/models", timeout=5)
        if res.status_code != 200: return []
        data = res.json().get('data', [])
        valid_models = []
        for m in data:
            mid = m['id'].lower()
            if ':free' in mid and ('chat' in mid or 'instruct' in mid or 'gpt' in mid):
                if 'diffusion' in mid or 'image' in mid or 'vision' in mid or '3d' in mid:
                    continue
                valid_models.append(m['id'])
        valid_models.sort(reverse=True)
        return valid_models
    except Exception as e:
        return []

def get_hf_text_models():
    try:
        url = "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=downloads&direction=-1&limit=5"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return [m['modelId'] for m in res.json()]
    except: pass
    return ["mistralai/Mistral-7B-Instruct-v0.3"]

# =========================================================
# 2. 마스터 AI 실행 엔진 (기존 코드 유지)
# =========================================================

def ask_ai_master(system_prompt, user_input):
    # 1. Groq 시도
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        models = get_groq_text_models()
        client = Groq(api_key=groq_key)
        for model_id in models:
            try:
                completion = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                    temperature=0.3
                )
                return completion.choices[0].message.content.strip()
            except Exception: continue

    # 2. OpenRouter 시도
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        models = get_openrouter_text_models()
        for model_id in models:
            try:
                res = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key}"},
                    json={
                        "model": model_id,
                        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                        "temperature": 0.3
                    },
                    timeout=20
                )
                if res.status_code == 200:
                    content = res.json()['choices'][0]['message']['content']
                    if content: return content
            except: continue

    return ""

# =========================================================
# 3. JSON 파서 (기존 코드 유지)
# =========================================================

def parse_json_result(text):
    if not text: return []
    try: return json.loads(text)
    except: pass
    try:
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
            if not text.startswith("[") and not text.startswith("{"):
                 text = text.split("```")[-1].split("```")[0].strip()
            return json.loads(text)
    except: pass
    try:
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: pass
    return []

# =========================================================
# 4. 분석 및 요약 로직 (여기만 수정됨!)
# =========================================================

def extract_top_entities(category, news_titles):
    """
    [Updated] 제목 뭉치에서 빈도수 기반 엔티티 추출 (회사명 제외 필터링 적용)
    """
    system_prompt = f"""
    You are a K-Content Trend Analyst for '{category}'. 
    Task: Analyze the news titles and extract the most frequently mentioned entities.
    
    [Rules]
    1. Target Entities:
       - K-Pop: Group Names, Solo Singers, Song Titles (e.g., NewJeans, Ditto, Jungkook).
       - K-Drama/Movie: Actor Names, Drama/Movie Titles.
    2. ⛔ EXCLUDE: 
       - Company names (HYBE, SM, YG, JYP, Ador, etc.).
       - Generic words (Comeback, Debut, Chart, Controversy, Netizen).
    3. Output:
       - Return a JSON LIST of strings ordered by frequency (Most mentioned first).
       - Max 30 items.
       - Translate Korean names to English standard names.
    
    Example Input: "NewJeans comeback confirmed...", "HYBE stock falls...", "NewJeans Hype Boy hits..."
    Example Output: ["NewJeans", "Hype Boy"] (Note: HYBE is excluded)
    """
    
    # 제목들을 하나의 텍스트로 결합 (너무 길면 자름)
    user_input = "\n".join(news_titles)[:12000] # 토큰 제한 살짝 늘림
    
    raw_result = ask_ai_master(system_prompt, user_input)
    parsed = parse_json_result(raw_result)
    
    # 리스트인지 확인하고 중복 제거 (순서 유지)
    if isinstance(parsed, list):
        return list(dict.fromkeys(parsed)) 
    return []

def synthesize_briefing(keyword, news_contents):
    """
    [Maintained] 기존 요약 로직 유지
    """
    system_prompt = f"""
    You are a Professional News Briefing Editor. 
    Topic: {keyword}
    
    Task: Summarize the provided news snippets into a 5-10 line cohesive briefing in English.
    Focus on: What is happening, Why it is trending, and Public reaction.
    
    [Format]
    - Style: Professional, Engaging, Journalistic
    - Length: 5 to 10 lines
    - Output: Plain text only (No Markdown, No JSON)
    """
    
    # 내용 결합
    user_input = "\n\n".join(news_contents)[:4000] 
    briefing = ask_ai_master(system_prompt, user_input)
    return briefing

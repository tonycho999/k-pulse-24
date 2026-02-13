import os
import json
import time
import re
import requests
from groq import Groq
from scraper.config import CATEGORIES, EXCLUDE_KEYWORDS

# ---------------------------------------------------------
# 1. 모델 동적 조회 (Hardcoding 제거)
# ---------------------------------------------------------

def get_groq_models():
    """
    [완전 동적] Groq API에 접속해 현재 사용 가능한 모든 모델을 가져와서 최신순 정렬
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return []
    
    try:
        client = Groq(api_key=api_key)
        all_models = client.models.list()
        
        # 1. 모델 ID만 추출
        model_ids = [m.id for m in all_models.data]
        
        # 2. 'whisper'(음성), 'vision'(이미지) 모델 제외 (텍스트만 남김)
        text_models = [m for m in model_ids if 'whisper' not in m and 'vision' not in m]
        
        # 3. 이름 역순 정렬 (보통 버전 숫자가 높은게 위로 옴. 예: llama-3.3 > llama-3.1)
        text_models.sort(reverse=True)
        
        return text_models
    except Exception as e:
        print(f"      ⚠️ Groq 모델 목록 조회 실패: {e}")
        return []

def get_openrouter_models():
    """
    [완전 동적] OpenRouter API에서 'free' 태그가 붙은 모델 전체 조회 -> 최신순 정렬
    """
    try:
        res = requests.get("https://openrouter.ai/api/v1/models")
        if res.status_code != 200: return []
        
        data = res.json().get('data', [])
        
        # 1. 무료(:free) 모델이면서 텍스트 생성 모델인 것만 필터링
        # (instruct, chat 등이 포함된 모델 선호)
        free_models = [
            m['id'] for m in data 
            if ':free' in m['id'] and ('instruct' in m['id'] or 'chat' in m['id'])
        ]
        
        # 2. 최신순 정렬 (문자열 역순 정렬하면 보통 최신 버전이 먼저 옴)
        free_models.sort(reverse=True)
        
        return free_models
    except Exception as e:
        print(f"      ⚠️ OpenRouter 모델 목록 조회 실패: {e}")
        return []

def get_hf_models():
    """
    [완전 동적] Hugging Face Hub API에서 'text-generation' 상위 모델 조회
    """
    try:
        # 다운로드 수 기준 상위 10개 텍스트 생성 모델 조회
        url = "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=downloads&direction=-1&limit=10"
        res = requests.get(url, timeout=5)
        
        if res.status_code == 200:
            models = [m['modelId'] for m in res.json()]
            return models
    except:
        pass
    return [] # 실패 시 빈 리스트 (루프에서 처리됨)

# ---------------------------------------------------------
# 2. 마스터 AI 엔진 (순차적 재시도 로직)
# ---------------------------------------------------------

def ask_ai_master(system_prompt, user_input):
    """
    [규칙]
    1. Groq 목록 가져옴 -> 1번부터 끝까지 시도 -> 실패하면
    2. OpenRouter 목록 가져옴 -> 1번부터 끝까지 시도 -> 실패하면
    3. HF 목록 가져옴 -> 1번부터 끝까지 시도
    """
    
    # --- 1단계: Groq (동적 목록) ---
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        models = get_groq_models() # 동적 조회
        if models:
            client = Groq(api_key=groq_key)
            for model_id in models:
                try:
                    # print(f"      🤖 Groq 시도: {model_id}")
                    completion = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                        temperature=0.1 # 안전하게 낮춤
                    )
                    return completion.choices[0].message.content.strip()
                except Exception:
                    continue # 안 되면 다음 모델로 (조용히 넘어감)

    # --- 2단계: OpenRouter (동적 목록) ---
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        print("      🚨 Groq 전멸 -> OpenRouter 목록 조회 및 시도")
        models = get_openrouter_models() # 동적 조회
        for model_id in models:
            try:
                # print(f"      🤖 OpenRouter 시도: {model_id}")
                res = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {or_key}"},
                    json={
                        "model": model_id,
                        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                        "temperature": 0.1
                    },
                    timeout=20
                )
                if res.status_code == 200:
                    content = res.json()['choices'][0]['message']['content']
                    if content: return content
            except:
                continue

    # --- 3단계: Hugging Face (동적 목록) ---
    hf_token = os.getenv("HF_API_TOKEN")
    if hf_token:
        print("      💀 OpenRouter 전멸 -> HF 목록 조회 및 시도")
        models = get_hf_models() # 동적 조회
        for model_id in models:
            try:
                # print(f"      🤖 HF 시도: {model_id}")
                API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {"inputs": f"<s>[INST] {system_prompt}\n\n{user_input} [/INST]"}
                res = requests.post(API_URL, headers=headers, json=payload, timeout=20)
                
                if res.status_code == 200:
                    result = res.json()
                    # HF 응답 형식 대응 (리스트거나 딕셔너리거나)
                    if isinstance(result, list) and 'generated_text' in result[0]:
                        return result[0]['generated_text']
                    elif isinstance(result, dict) and 'generated_text' in result:
                        return result['generated_text']
            except:
                continue

    return ""

# ---------------------------------------------------------
# 3. JSON 파싱 유틸리티 (매우 중요)
# ---------------------------------------------------------
def parse_json_result(text):
    """AI 사족 제거 및 JSON 추출"""
    if not text: return []
    try: return json.loads(text)
    except:
        try:
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
                if not text.startswith("[") and not text.startswith("{"):
                     text = text.split("```")[-1].split("```")[0].strip()
                return json.loads(text)
        except: pass
    
    # 정규식으로 [...] 또는 {...} 찾기
    try:
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: pass
    
    # print(f"      ❌ 파싱 실패. 원본: {text[:50]}...")
    return []

# ---------------------------------------------------------
# 4. 외부 호출 함수
# ---------------------------------------------------------
def ai_filter_and_rank_keywords(raw_keywords):
    system_prompt = f"""
    You are the Chief Editor of 'K-Enter24'. 
    Filter keywords for: {json.dumps(CATEGORIES, indent=2)}.
    Exclude: {', '.join(EXCLUDE_KEYWORDS)}.
    Return JSON object ONLY: {{"k-pop": ["keyword1"], ...}}
    """
    raw_result = ask_ai_master(system_prompt, json.dumps(raw_keywords, ensure_ascii=False))
    parsed = parse_json_result(raw_result)
    return parsed if isinstance(parsed, dict) else {}

def ai_category_editor(category, news_list):
    system_prompt = f"""
    You are an expert K-Content News Editor for '{category}'.
    Summarize these articles.
    
    [OUTPUT FORMAT]
    Return a VALID JSON ARRAY strictly like this:
    [
        {{
            "original_index": 0,
            "eng_title": "Translated Title",
            "summary": "Context... Development... Impact...",
            "score": 8.5
        }}
    ]
    """
    
    input_data = []
    for i, n in enumerate(news_list):
        input_data.append({
            "index": i, 
            "title": n['title'], 
            "body": n.get('full_content', '')[:1000]
        })

    raw_result = ask_ai_master(system_prompt, json.dumps(input_data, ensure_ascii=False))
    parsed_list = parse_json_result(raw_result)
    
    # 리스트인지 확인
    if isinstance(parsed_list, list):
        if parsed_list: print(f"      ✅ AI 분석 성공: {len(parsed_list)}개")
        return parsed_list
    return []

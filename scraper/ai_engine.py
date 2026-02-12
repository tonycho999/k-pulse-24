import json
import re
from config import groq_client

def get_best_model():
    """사용 가능한 최신/고성능 AI 모델 자동 선택"""
    try:
        models_raw = groq_client.models.list()
        available_models = [m.id for m in models_raw.data]
        
        def model_scorer(model_id):
            score = 0
            model_id = model_id.lower()
            if "llama" in model_id: score += 1000
            elif "mixtral" in model_id: score += 500
            elif "gemma" in model_id: score += 100
            
            version_match = re.search(r'(\d+\.?\d*)', model_id)
            if version_match:
                try:
                    version = float(version_match.group(1))
                    score += version * 100 
                except: pass

            if "70b" in model_id: score += 50
            elif "8b" in model_id: score += 10
            if "versatile" in model_id: score += 5
            return score

        available_models.sort(key=model_scorer, reverse=True)
        print(f"🤖 AI 모델 우선순위: {available_models[:3]}")
        return available_models
    except Exception as e:
        print(f"⚠️ 모델 조회 실패, 기본값 사용: {e}")
        return ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

MODELS_TO_TRY = get_best_model()

def ai_category_editor(category, news_batch):
    """뉴스 기사 선별 및 요약 (30개 목표, 20~40% 길이)"""
    if not news_batch: return []
    limited_batch = news_batch[:50]
    
    raw_text = ""
    for i, n in enumerate(limited_batch):
        clean_desc = n['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        raw_text += f"[{i}] Title: {n['title']} / Context: {clean_desc}\n"
    
    prompt = f"""
    Task: Select highly relevant news items for '{category}'. 
    Target Quantity: Try to select up to 30 items if they are relevant.
    
    Constraints: 
    1. English Title: Translate naturally.
    2. English Summary: 
       - Write a DETAILED narrative summary (approx. 20-40% length of a typical article).
       - DO NOT use bullet points. Write 5-8 sentences in a cohesive paragraph.
       - Include Who, When, Where, Why based on the context.
    3. AI Score (0.0-10.0): Judge based on importance and trendiness.
    4. Return JSON format strictly.

    News List:
    {raw_text}

    Output JSON Format:
    {{
        "articles": [
            {{ "original_index": 0, "eng_title": "...", "summary": "Detailed summary...", "score": 8.5 }}
        ]
    }}
    """
    
    for model in MODELS_TO_TRY:
        try:
            res = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": f"You are a K-Enter Journalist for {category}."},
                          {"role": "user", "content": prompt}], 
                model=model, response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            articles = data.get('articles', [])
            if articles: return articles
        except Exception as e:
            print(f"      ⚠️ {model} 오류 ({str(e)[:60]}...). 다음 모델 시도.")
            continue
    return []

def ai_analyze_keywords(titles):
    """기사 제목 기반 트렌드 키워드 추출"""
    titles_text = "\n".join([f"- {t}" for t in titles])
    prompt = f"""
    Analyze the following K-Entertainment news titles and identify the TOP 10 most trending keywords.
    [Rules]
    1. Extract specific Entities: Person Name (e.g., "Lee Min-ho", NOT "Lee"), Group Name (e.g., "BTS"), Drama/Movie Title (e.g., "Squid Game").
    2. Merge related concepts: If "Jin" and "BTS" are both popular, use "BTS Jin".
    3. EXCLUDE generic words: Do NOT use words like "Variety", "Actor", "K-pop", "Review", "Netizens", "Update", "Official", "Comeback", "Teaser".
    4. Return JSON format with 'keyword' and estimated 'count' (importance score 1-100).
    [Titles]
    {titles_text}
    [Output Format JSON]
    {{
        "keywords": [
            {{ "keyword": "BTS Jin", "count": 95, "rank": 1 }},
            {{ "keyword": "Squid Game 2", "count": 80, "rank": 2 }}
        ]
    }}
    """
    
    for model in MODELS_TO_TRY:
        try:
            res = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": "You are a K-Trend Analyst."},
                          {"role": "user", "content": prompt}], 
                model=model, response_format={"type": "json_object"}
            )
            result = json.loads(res.choices[0].message.content)
            keywords = result.get('keywords', [])
            if keywords: return keywords
        except Exception as e:
            print(f"      ⚠️ {model} 분석 실패: {e}")
            continue
    return []

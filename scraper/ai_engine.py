import json
import re
from config import groq_client

def get_best_model():
    """사용 가능한 최신/고성능 AI 모델 자동 선택 (버전 숫자 기반)"""
    try:
        models_raw = groq_client.models.list()
        available_models = [m.id for m in models_raw.data]
        
        def model_scorer(model_id):
            score = 0
            mid = model_id.lower()
            
            # 1. 버전 숫자 추출 (예: llama-3.3 -> 3.3)
            version_match = re.search(r'(\d+\.?\d*)', mid)
            if version_match:
                try:
                    version = float(version_match.group(1))
                    score += version * 1000  # 버전이 높을수록 최우선
                except: pass

            # 2. 모델 크기 가산점
            if "70b" in mid: score += 500
            elif "8b" in mid: score += 100
            
            # 3. 모델 계열 가산점
            if "llama" in mid: score += 50
            elif "mixtral" in mid: score += 40
            
            return score

        available_models.sort(key=model_scorer, reverse=True)
        print(f"🤖 AI 모델 우선순위: {available_models[:3]}")
        return available_models
    except Exception as e:
        print(f"⚠️ 모델 조회 실패, 기본값 사용: {e}")
        return ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

MODELS_TO_TRY = get_best_model()

def ai_category_editor(category, news_batch):
    """뉴스 기사 선별, 요약 및 점수 부여"""
    if not news_batch: return []
    
    # 최대한 많은 후보군을 AI에게 전달
    limited_batch = news_batch[:60] 
    
    raw_text = ""
    for i, n in enumerate(limited_batch):
        clean_desc = n['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        raw_text += f"[{i}] Title: {n['title']} / Link: {n['link']} / Context: {clean_desc}\n"
    
    # [수정] 카테고리별 점수 정책 차등 적용 (이원화 전략)
    if category == 'k-culture':
        # [전략 1] 마이너 카테고리: 기사량 확보를 위해 '후한 점수' (Generous)
        score_instruction = """
        This is 'K-Culture' (Food, Fashion, Travel). Since news volume is typically low:
        - Be GENEROUS with scoring.
        - If the article is relevant to Korea, give at least 6.0.
        - If it's interesting or informative, give 7.5~8.5.
        - Only give < 5.0 if it is completely irrelevant or spam.
        """
    else:
        # [전략 2] 메인 카테고리: 퀄리티 확보를 위해 '엄격한 기준' (Strict/Objective)
        score_instruction = """
        This is MAIN Entertainment news (K-Pop, Drama, Actors). Volume is high:
        - Be STRICT/OBJECTIVE with scoring.
        - Standard/Routine news (e.g., simple schedule updates) -> 5.0~6.5
        - Good news (e.g., new release, casting) -> 7.0~8.5
        - HUGE Breaking news (e.g., global awards, dating reveal) -> 9.0~10.0
        """

    prompt = f"""
    Task: Select the best 30 news items for '{category}'.
    
    [Selection Rules]
    1. Score >= 4.0: MUST include articles with score 4.0 or higher.
    2. Diversity: If multiple articles cover the same topic, select ones with different angles or sources.
    3. Deduplication: Do not select nearly identical articles.

    [Output Constraints]
    1. English Title: Translate naturally.
    2. English Summary: 
       - Summarize to 40-50% of original length.
       - Create a rich, narrative paragraph (5-8 sentences). NO bullet points.
    3. AI Score (0.0-10.0): 
       - {score_instruction}
    4. Return JSON format strictly.

    News List:
    {raw_text}

    Output JSON Format:
    {{
        "articles": [
            {{ "original_index": 0, "eng_title": "...", "summary": "...", "score": 8.5 }}
        ]
    }}
    """
    
    for model in MODELS_TO_TRY:
        try:
            res = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": f"You are a generic K-Enter Journalist for {category}."},
                          {"role": "user", "content": prompt}], 
                model=model, 
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            articles = data.get('articles', [])
            if articles: return articles
        except Exception as e:
            print(f"      ⚠️ {model} 오류. 다음 모델 시도.")
            continue
    return []

def ai_analyze_keywords(titles):
    """기사 제목 기반 트렌드 키워드 추출"""
    titles_text = "\n".join([f"- {t}" for t in titles])
    
    # [수정] 구체적 예시 삭제 후 일반적 템플릿 적용
    prompt = f"""
    Analyze the following K-Entertainment news titles and identify the TOP 10 most trending keywords.
    [Rules]
    1. Extract specific Entities: Person Name, Group Name, Drama/Movie Title.
    2. Merge related concepts: "BTS Jin" instead of "Jin".
    3. EXCLUDE generic words: Variety, Actor, K-pop, Review, Netizens, Update, Official.
    4. Return JSON format with 'keyword' and estimated 'count' (1-100).
    
    [Titles]
    {titles_text}
    
    [Output Format JSON]
    {{
        "keywords": [
            {{ "keyword": "Most Mentioned Keyword", "count": 95, "rank": 1 }},
            {{ "keyword": "Second Keyword", "count": 80, "rank": 2 }}
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

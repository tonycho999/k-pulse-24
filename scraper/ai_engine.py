import os
import sys
import json
import re
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq

# 한글 깨짐 방지
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# =========================================================
# [1. 환경변수 및 클라이언트 설정]
# =========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# [Supabase 클라이언트 초기화]
supabase: Client = None
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Warning (config.py): Supabase 환경변수가 설정되지 않았습니다.")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Warning: Supabase 클라이언트 초기화 실패: {e}")

# [Groq 클라이언트 초기화]
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except:
        pass

# [1. 씨앗 키워드 설정 (Seed Keywords)]
CATEGORY_SEEDS = {
    "k-pop": ["멜론 차트 순위", "빌보드 K-pop 차트", "인기가요 1위", "K-pop 신곡 반응", "아이돌 뮤직비디오 조회수"],
    "k-drama": ["드라마 시청률 순위", "넷플릭스 한국 드라마 순위", "티빙 드라마 인기", "화제성 드라마 순위", "방영 예정 드라마 기대작"],
    "k-movie": ["박스오피스 예매율", "넷플릭스 영화 순위", "한국 영화 관객수", "개봉 영화 평점"],
    "k-entertain": ["미스트롯", "미스터트롯", "예능 시청률 순위", "OTT 예능 트렌드", "유튜브 인기 예능", "화제성 예능 프로그램"],
    "k-culture": ["서울 핫플레이스 웨이팅", "한국 유행 음식", "성수동 팝업스토어", "한국 패션 트렌드", "한국 여행 필수 코스"]
}

# [2. 설정 상수]
NAVER_DISPLAY_COUNT = 100 
TOP_RANK_LIMIT = 30  

# =========================================================
# 1. 모델 선택 로직 (Groq 전용)
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
            if any(x in mid for x in ['vision', 'whisper', 'audio', 'guard', 'safe']): continue
            valid_models.append(m.id)
        valid_models.sort(key=lambda x: '70b' in x, reverse=True) 
        return valid_models
    except: return []

# =========================================================
# 2. AI 답변 정제기 및 호출 마스터
# =========================================================

def clean_ai_response(text):
    if not text: return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            if "{" in part or "[" in part:
                cleaned = part.replace("json", "").strip()
                break
    return cleaned

def ask_ai_master(system_prompt, user_input):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key: return ""
    
    models = get_groq_text_models()
    client = Groq(api_key=groq_key)
    
    for model_id in models:
        try:
            completion = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
                temperature=0.2 
            )
            res = completion.choices[0].message.content.strip()
            if res: return clean_ai_response(res)
        except:
            continue
    return ""

def parse_json_result(text):
    if not text: return []
    try: return json.loads(text)
    except: pass
    try:
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: pass
    return []

# =========================================================
# 3. [핵심] 카테고리별 엄격 분류
# =========================================================

def extract_top_entities(category, news_text_data):
    specific_rule = ""
    if category.lower() == 'k-drama':
        specific_rule = """
        [STRICT K-DRAMA MODE]
        1. 'content' MUST be a REAL Scripted Drama/Series Title.
        2. NEVER include Audition programs, Survival shows, or Music competitions (e.g., 'Miss Trot', 'Mr. Trot', 'Singles Inferno').
        3. If it has judges or voting, it is NOT a drama. These belong to 'k-entertain'.
        """
    elif category.lower() == 'k-movie':
        specific_rule = "[STRICT K-MOVIE MODE] 'content' MUST be a theatrical film title only. No TV shows."
    elif category.lower() == 'k-pop':
        specific_rule = "[STRICT K-POP MODE] 'content' MUST be a Song, Album, or Group name. No drama titles."
    elif category.lower() == 'k-culture':
        specific_rule = "[STRICT K-CULTURE MODE] Focus on Lifestyle, Food, Places, Festivals, and Fashion trends."

    system_prompt = f"""
    You are an expert K-Content Analyst for '{category}'. 
    {specific_rule}
    [TASK] Extract keywords ONLY belonging to '{category}'.
    [OUTPUT] JSON LIST: [{{"keyword": "English Title", "type": "content/person"}}]
    """
    
    user_input = news_text_data[:20000] 
    raw_result = ask_ai_master(system_prompt, user_input)
    parsed = parse_json_result(raw_result)
    
    if isinstance(parsed, list):
        seen = set()
        unique_list = []
        for item in parsed:
            if isinstance(item, dict) and 'keyword' in item and 'type' in item:
                kw = item['keyword']
                if kw not in seen:
                    seen.add(kw)
                    unique_list.append(item)
        return unique_list
    return []

# =========================================================
# 4. 브리핑 생성 (제목 자동 생성을 위해 JSON 반환으로 수정)
# =========================================================

def synthesize_briefing(keyword, news_contents):
    # [수정] 헤드라인과 요약을 함께 생성하도록 지시
    system_prompt = f"""
    You are a Professional News Editor. Topic: {keyword}
    [TASK] 
    1. Create a CATCHY, specific headline (No "[keyword] Update" style).
    2. Write a 5-10 line news briefing in English.
    [FORMAT] Return JSON ONLY: {{"title": "Creative Headline", "summary": "Briefing contents..."}}
    """
    user_input = "\n\n".join(news_contents)[:40000] 
    result = ask_ai_master(system_prompt, user_input)
    
    # 딕셔너리 형태로 반환하여 main.py에서 활용 가능하게 함
    parsed_data = parse_json_result(result)
    
    if not parsed_data or not isinstance(parsed_data, dict) or not parsed_data.get('summary'):
        return None
    return parsed_data

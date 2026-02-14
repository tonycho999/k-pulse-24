import os
import json
import time
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. 환경변수 로드
load_dotenv()

# 2. Supabase 클라이언트 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Google Gemini 설정
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# ---------------------------------------------------------
# [핵심 기능] 안전한 모델 선택기 (서비스 종료 대비)
# ---------------------------------------------------------
def select_safe_model():
    """
    1지망부터 순서대로 모델이 존재하는지 확인하고,
    가장 먼저 발견되는 '사용 가능한' 모델을 선택합니다.
    """
    # 우리가 원하는 모델 후보군 (순서가 중요합니다!)
    # 1순위: 현재 가장 안정적이고 무료 량이 많은 모델
    # 2순위: 미래에 나올 버전 (미리 적어둠)
    # 3순위: 구버전 백업
    candidates = [
        "models/gemini-1.5-flash",      # [1지망] 현재 표준 (무료 1500회/일)
        "models/gemini-2.0-flash",      # [2지망] 미래 출시 대비 (혹시 1.5가 망하면 이거 씀)
        "models/gemini-1.5-flash-001",  # [3지망] 특정 버전 고정
        "models/gemini-1.5-flash-002",  # [4지망] 업데이트 버전
        "models/gemini-flash-latest"    # [5지망] 최후의 보루 (다 없으면 이거라도)
    ]

    try:
        print("🔍 사용 가능한 AI 모델 목록 조회 중...")
        # 현재 구글 서버에 살아있는 모델 목록을 다 가져옵니다.
        available_models = [m.name for m in genai.list_models()]
        
        for candidate in candidates:
            if candidate in available_models:
                print(f"✅ 모델 확정: {candidate} (서비스 중)")
                return candidate
        
        # 후보군이 다 없으면? (거의 불가능하지만)
        # 검색 기능은 안 되더라도 텍스트라도 되는 모델을 찾습니다.
        print("⚠️ 후보 모델을 찾을 수 없어 'gemini-1.5-flash'를 강제 시도합니다.")
        return "models/gemini-1.5-flash"

    except Exception as e:
        print(f"⚠️ 모델 조회 실패 ({e}). 기본값으로 진행합니다.")
        return "models/gemini-1.5-flash"

# 여기서 함수를 실행해 최적의 모델을 변수에 담습니다.
SELECTED_MODEL_NAME = select_safe_model()
model = genai.GenerativeModel(SELECTED_MODEL_NAME, tools='google_search_retrieval')

# ---------------------------------------------------------
# [설정] 카테고리별 프롬프트 가이드
# ---------------------------------------------------------
CATEGORIES = {
    "K-Pop": {
        "news_focus": "가수, 아이돌, 그룹 멤버의 활동 및 이슈",
        "rank_focus": "현재 음원 차트 상위권 노래 제목(Song Title)"
    },
    "K-Drama": {
        "news_focus": "드라마 출연 배우의 캐스팅, 인터뷰, 논란",
        "rank_focus": "현재 방영중이거나 OTT 상위권 드라마 제목(Drama Title)"
    },
    "K-Movie": {
        "news_focus": "영화 배우의 동향, 무대인사, 인터뷰",
        "rank_focus": "현재 박스오피스 상위권 영화 제목(Movie Title)"
    },
    "K-Variety": {
        "news_focus": "예능인, 방송인, 패널의 에피소드",
        "rank_focus": "현재 방영중인 예능 프로그램 제목(Show Title)"
    },
    "K-Culture": {
        "news_focus": "핫플레이스, 축제, 팝업스토어 (장소/Place 위주)",
        "rank_focus": "유행하는 음식, 뷰티템, 패션, 밈 (물건/Item 위주)"
    }
}

# ---------------------------------------------------------
# [기능] Gemini 검색 및 데이터 생성
# ---------------------------------------------------------
def fetch_data_from_gemini(category_name, instructions):
    print(f"🤖 [Gemini] '{category_name}' 분석 중... (Model: {SELECTED_MODEL_NAME})")
    
    prompt = f"""
    [Role]
    당신은 20년 경력의 연예부 기자입니다. 팩트에 기반한 최신 트렌드를 분석합니다.

    [Task]
    현재 시점(Latest)의 '{category_name}' 관련 데이터를 검색하여 JSON으로 작성하십시오.

    [Requirements]
    1. **뉴스(News)**: {instructions['news_focus']} 중심으로 화제가 높은 10개를 선정하십시오.
       - 중복된 주제는 피하고 다양하게 구성하십시오.
       - 요약은 150자 내외로 핵심만 담으십시오.
    2. **랭킹(Ranking)**: {instructions['rank_focus']} 중심으로 인기 순위 TOP 10을 선정하십시오.
       - 뉴스에 나온 내용과 겹치지 않게 '작품/대상' 위주로 뽑으십시오.
       - 절대 중복된 항목이 있어서는 안 됩니다.

    [Output Format (JSON Only)]
    {{
      "news_updates": [
        {{
          "keyword": "주제어 (예: 뉴진스, 김수현)",
          "title": "기사 제목",
          "summary": "기사 요약",
          "link": "관련 기사 링크 (없으면 검색된 출처)"
        }},
        ... (10 items)
      ],
      "rankings": [
        {{ "rank": 1, "title": "제목/이름", "meta": "부가정보 (가수명/방송사 등)" }},
        ... (10 items)
      ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"❌ [Error] {category_name} 처리 중 오류: {e}")
        return None

# ---------------------------------------------------------
# [기능] 데이터베이스 저장 (Live + Archive + Ranking)
# ---------------------------------------------------------
def update_database(category, data):
    # 1. 뉴스 데이터 처리
    news_list = data.get("news_updates", [])
    if news_list:
        clean_news = []
        for item in news_list:
            clean_news.append({
                "category": category,
                "keyword": item["keyword"],
                "title": item["title"],
                "summary": item["summary"],
                "link": item.get("link", ""),
                "created_at": "now()"
            })
        
        # [A] 아카이브 저장
        try:
            supabase.table("search_archive").upsert(clean_news, on_conflict="category,keyword,title").execute()
            print(f"   🗄️ [Archive] 뉴스 {len(clean_news)}개 보관 완료")
        except Exception as e:
            print(f"   ⚠️ 아카이브 저장 실패: {e}")

        # [B] 라이브 뉴스 저장
        try:
            supabase.table("live_news").upsert(clean_news, on_conflict="category,keyword,title").execute()
            print(f"   💾 [Live] 뉴스 {len(clean_news)}개 업데이트 완료")
        except Exception as e:
            print(f"   ⚠️ 라이브 저장 실패: {e}")

    # 2. 뉴스 롤링 업데이트
    try:
        res = supabase.table("live_news").select("id").eq("category", category).order("created_at", desc=True).execute()
        all_ids = [row['id'] for row in res.data]
        
        if len(all_ids) > 30:
            ids_to_delete = all_ids[30:]
            supabase.table("live_news").delete().in_("id", ids_to_delete).execute()
            print(f"   🧹 [Clean] 오래된 뉴스 {len(ids_to_delete)}개 삭제")
    except Exception as e:
        print(f"   ⚠️ 롤링 업데이트 실패: {e}")

    # 3. 랭킹 데이터 처리
    rank_list = data.get("rankings", [])
    if rank_list:
        clean_ranks = []
        for item in rank_list:
            clean_ranks.append({
                "category": category,
                "rank": item["rank"],
                "title": item["title"],
                "meta_info": item.get("meta", ""),
                "updated_at": "now()"
            })
        
        try:
            supabase.table("live_rankings").upsert(clean_ranks, on_conflict="category,rank").execute()
            print(f"   🏆 랭킹 TOP 10 갱신 완료")
        except Exception as e:
            print(f"   ⚠️ 랭킹 저장 실패: {e}")

def main():
    print("🚀 뉴스 및 랭킹 업데이트 시작")
    print(f"ℹ️ 사용할 모델: {SELECTED_MODEL_NAME}")
    
    for category, instructions in CATEGORIES.items():
        data = fetch_data_from_gemini(category, instructions)
        if data:
            update_database(category, data)
        else:
            print(f"⚠️ {category} 데이터 수집 실패 (Quota 초과 등)")
        
        # API 호출 제한 방지 (15초 대기)
        print("⏳ 다음 작업을 위해 15초 대기...")
        time.sleep(15)

    print("✅ 모든 작업 완료")

if __name__ == "__main__":
    main()

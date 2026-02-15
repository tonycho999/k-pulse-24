import gemini_api
import database
import naver_api
from datetime import datetime

def run_category_process(category):
    print(f"\n🚀 [Processing] {category} with Google Search Grounding")

    # 1. 카테고리별 베테랑 기자 페르소나 질문 정의
    prompts = {
        "K-Drama": "너는 20년 차 베테랑 연예부 기자야. 최근 24시간 동안의 뉴스 데이터를 실시간 검색해서 한국 드라마와 배우에 대한 기사 중 가장 화제가 된 10개를 분석해줘. 이를 바탕으로 현재 가장 화제가 되는 배우에 대해 심층 기사를 작성해주고, 추가로 드라마 화제성 순위 1위부터 10위를 선정해줘. 오늘의 전반적인 드라마 시장 트렌드를 요약한 뒤, 모든 내용을 영어로 번역하여 JSON 형식으로 보내줘.",
        "K-Movie": "너는 20년 차 베테랑 영화 전문 기자야. 지난 24시간 동안의 뉴스 데이터를 실시간 검색해서 한국 영화, 개봉작, 영화 배우에 대한 기사 중 화제가 된 10개를 분석해줘. 이를 바탕으로 현재 가장 주목받는 배우 혹은 감독에 대한 전문 기사를 작성하고, 현재 박스오피스 및 영화 화제성 1위부터 10위 순위를 매겨줘. 오늘자 한국 영화계의 주요 동향을 요약하여 영어로 번역한 후 JSON 형식으로 보내줘.",
        "K-Entertain": "너는 20년 차 베테랑 방송 전문 기자야. 최근 24시간 동안의 뉴스 데이터를 실시간 검색해서 한국 예능 프로그램과 출연진에 대한 기사 중 반응이 뜨거운 10개를 분석해줘. 이를 바탕으로 현재 가장 화제인 예능인(스타)에 대한 기사를 작성하고, 예능 프로그램 화제성 순위 1위부터 10위를 선정해줘. 오늘의 예능 판도와 트렌드를 심층 분석한 내용을 영어로 번역하여 JSON 형식으로 보내줘.",
        "K-Culture": "너는 20년 차 베테랑 문화부 기자야. 최근 24시간 동안의 뉴스 데이터를 실시간 검색해서 한국의 핫플레이스, 축제, 전통문화, 미식 트렌드에 대한 기사 중 화제가 된 10개를 분석해줘. (아이돌/드라마 등 연예인 기사는 제외해.) 이를 바탕으로 현재 가장 인기 있는 명소나 문화 현상에 대해 기사를 작성해주고, 문화/여행 키워드 순위 1위부터 10위를 선정해줘. 오늘의 한국 라이프스타일 트렌드를 요약하여 영어로 번역한 후 JSON 형식으로 보내줘.",
        "K-Pop": "너는 20년 차 베테랑 연예부 기자야. 최근 24시간 동안의 뉴스 데이터를 실시간 검색해서 K-pop 가수와 신곡에 대한 기사 중 가장 화제가 된 10개를 분석해줘. 이를 바탕으로 현재 가장 화제가 되는 가수(그룹명)에 대해서 기사를 작성해주고, 추가로 K-pop 곡 순위 1위부터 10위를 선정하고, 오늘의 전반적인 K-pop 트렌드를 심층 요약해서 영어로 번역한 후에 JSON 형식으로 보내줘."
    }

    # JSON 규격 강제를 위한 프롬프트 엔지니어링
    final_prompt = prompts[category] + """
    
    [Format Requirement]
    Return ONLY a JSON object with the following keys:
    {
      "target_kr": "Main Subject Name in Korean",
      "target_en": "Main Subject Name in English",
      "headline": "Professional English Headline",
      "content": "Professional English Article Body (4-5 paragraphs)",
      "rankings": [
        {"rank": 1, "title_en": "English Title", "title_kr": "Korean Title", "score": 95}
      ],
      "trend_summary": "In-depth English trend summary"
    }
    """

    # 2. AI 실행 (Google Search Grounding)
    print(f"   🔍 AI is searching and analyzing {category} news...")
    data = gemini_api.ask_gemini_with_search(final_prompt)
    
    if not data or "rankings" not in data:
        print(f"   ❌ Failed to get valid data for {category}")
        return

    # 3. 라이브 랭킹 업데이트
    database.save_rankings_to_db(data.get("rankings", []))

    # 4. 쿨타임 체크 (DB 중복 방지)
    target_en = data.get("target_en")
    target_kr = data.get("target_kr")
    
    if database.is_keyword_used_recently(category, target_en, hours=4):
        print(f"   🕒 '{target_en}' is on cooldown. Skipping article publication.")
        return

    # 5. 이미지 보완 (네이버 이미지 검색 API 활용)
    # 정식 API를 사용하여 고화질 HTTPS 이미지를 가져옵니다.
    print(f"   📸 Fetching high-quality image for '{target_kr}'...")
    final_image = naver_api.get_target_image(target_kr)

    # 6. 최종 DB 저장
    news_item = {
        "category": category,
        "keyword": target_en,
        "title": data.get("headline"),
        "summary": data.get("content"),
        "image_url": final_image,
        "score": 100,
        "created_at": datetime.now().isoformat(),
        "likes": 0
    }
    
    database.save_news_to_live([news_item])
    # 아카이브 저장 및 데이터 클린업 (필요 시)
    database.save_news_to_archive([news_item])
    
    print(f"   🎉 SUCCESS: '{data.get('headline')}' has been published.")

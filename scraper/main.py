import sys
import os
import time
from datetime import datetime, timedelta
from dateutil import parser # 날짜 파싱용 (없으면 pip install python-dateutil)
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from scraper import crawler, ai_engine, repository
from scraper.config import CATEGORY_SEEDS

load_dotenv()

# [설정] 상위 30개 분석
TARGET_RANK_LIMIT = 30 

# [도구] 24시간 이내인지 확인하는 함수
def is_within_24h(date_str):
    if not date_str: return False
    try:
        # 네이버 API 날짜 포맷 (Fri, 14 Feb 2026 10:00:00 +0900) 등 처리
        pub_date = parser.parse(date_str)
        # 타임존 정보 제거 (단순 비교용)
        if pub_date.tzinfo:
            pub_date = pub_date.replace(tzinfo=None)
            
        now = datetime.now()
        diff = now - pub_date
        return diff <= timedelta(hours=24)
    except:
        return False # 날짜 파싱 실패 시 안전하게 제외

def run_master_scraper():
    print(f"🚀 K-Enter Trend Master 가동 시작: {datetime.now()}")
    
    for category, seeds in CATEGORY_SEEDS.items():
        print(f"\n📂 [{category.upper()}] 트렌드 분석 시작")
        
        # ==========================================
        # [1단계] 씨앗 데이터 수집 (24시간 이내)
        # ==========================================
        raw_text_data = [] # 제목 + 요약본
        
        try:
            for seed in seeds:
                # 100개 정도 넉넉히 가져와서 날짜로 자름
                news_items = crawler.get_naver_api_news(seed, display=50)
                
                for item in news_items:
                    # 24시간 필터링
                    if is_within_24h(item.get('pubDate')):
                        # 제목과 요약본을 합쳐서 분석 데이터로 사용
                        combined_text = f"Title: {item['title']}\nSummary: {item['description']}"
                        raw_text_data.append(combined_text)
                        
            print(f"   🌱 24시간 내 유효 기사 수집: {len(raw_text_data)}개")
            
            if len(raw_text_data) < 5:
                print("   ⚠️ 기사가 너무 적어 스킵합니다.")
                continue
                
        except Exception as e:
            print(f"   ⚠️ 씨앗 수집 오류: {e}")
            continue
        
        # ==========================================
        # [2단계] AI 키워드 추출 및 정체 분류
        # ==========================================
        # top_entities = [{'keyword': 'Hype Boy', 'type': 'content'}, ...]
        top_entities = ai_engine.extract_top_entities(category, "\n".join(raw_text_data))
        
        if not top_entities: 
            print("   ⚠️ 키워드 추출 실패")
            continue
            
        print(f"   💎 추출된 키워드 (Top 5): {', '.join([e['keyword'] for e in top_entities[:5]])}...")

        # ==========================================
        # [3단계] 상위 30개 키워드 심층 분석
        # ==========================================
        category_news_list = []
        target_list = top_entities[:TARGET_RANK_LIMIT]
        
        for rank, entity in enumerate(target_list):
            kw = entity.get('keyword')
            k_type = entity.get('type', 'content') # 기본값 content
            
            print(f"   🔍 Rank {rank+1}: '{kw}' ({k_type}) 분석 중...")
            
            try:
                # 1. 검색 (최신순 sort='date' 권장하지만 정확도 위해 sim 후 날짜 필터링)
                raw_articles = crawler.get_naver_api_news(kw, display=30)
                if not raw_articles: continue

                full_contents = []
                main_image = None
                
                # 2. 기사 순회 (24시간 이내 + 키워드 검증)
                valid_article_count = 0
                
                for art in raw_articles:
                    # 날짜 필터링
                    if not is_within_24h(art.get('pubDate')):
                        continue
                        
                    # 본문 크롤링
                    text, img = crawler.get_article_data(art['link'], target_keyword=kw)
                    
                    # 키워드 검증 (본문에 키워드가 없으면 가짜 뉴스로 간주)
                    # 영어로 번역된 키워드일 수 있으므로 느슨하게 체크하거나, 
                    # 크롤러 레벨에서 이미 체크했다고 가정.
                    if text: 
                        full_contents.append(text)
                        valid_article_count += 1
                        
                        # 이미지 확보
                        if not main_image and img:
                            if img.startswith("http://"): img = img.replace("http://", "https://")
                            main_image = img
                            
                    # 5개 정도만 모으면 충분
                    if valid_article_count >= 5:
                        break

                # 3. 정보 부족 시 처리
                if not full_contents:
                    print(f"      ☁️ '{kw}': 유효 기사 없음 (Skip)")
                    continue

                # ==========================================
                # [4단계] AI 브리핑 생성 (영어, 5~20줄)
                # ==========================================
                briefing = ai_engine.synthesize_briefing(kw, full_contents)
                
                # AI가 'INVALID_DATA'를 줬다면 저장하지 않음
                if not briefing:
                    print(f"      🗑️ '{kw}': 내용 부실로 폐기")
                    continue
                
                # 평점 계산 (순위 기반, 최소 7.0)
                ai_score = round(9.9 - (rank * 0.1), 1)
                if ai_score < 7.0: ai_score = 7.0

                final_img = main_image or f"[https://placehold.co/600x400/111/cyan?text=](https://placehold.co/600x400/111/cyan?text=){kw}"

                news_item = {
                    "category": category,
                    "rank": rank + 1,
                    "keyword": kw,
                    "type": k_type,
                    "title": f"[{kw}] News Update",
                    "summary": briefing,
                    "link": None, # [요청] 링크 None 저장
                    "image_url": final_img,
                    "score": ai_score,
                    "likes": 0, "dislikes": 0,
                    "created_at": datetime.now().isoformat(),
                    "published_at": datetime.now().isoformat()
                }
                category_news_list.append(news_item)
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"      ⚠️ '{kw}' 처리 중 에러: {e}")
                continue

        # ==========================================
        # [5단계] 데이터베이스 분산 저장
        # ==========================================
        if category_news_list:
            print(f"   💾 저장 시작: 총 {len(category_news_list)}개 뉴스 생성됨")
            
            # 1. Live News: 1~30위 생성된 모든 뉴스 저장 (사람 포함)
            repository.refresh_live_news(category, category_news_list)
            
            # 2. Trending Rankings: 'content' 타입인 것만 골라서 Top 10 저장
            # (사람 이름 제외, 곡명/작품명만)
            content_only_list = [n for n in category_news_list if n.get('type') == 'content']
            if content_only_list:
                repository.update_sidebar_rankings(category, content_only_list[:10])
            else:
                # 만약 content 타입이 하나도 없으면 비워두기보다 상위권 몇 개라도 넣는 비상 로직 (필요 시 주석 해제)
                # repository.update_sidebar_rankings(category, category_news_list[:5])
                pass
            
            # 3. Search Archive: 평점 7.0 이상만 저장
            high_score_news = [n for n in category_news_list if n['score'] >= 7.0]
            if high_score_news:
                repository.save_to_archive(high_score_news)

    print("\n🎉 전체 업데이트 완료.")

if __name__ == "__main__":
    run_master_scraper()

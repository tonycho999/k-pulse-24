import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# 모듈 import 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# 필수 모듈 불러오기
from scraper import crawler, ai_engine, repository
from scraper.config import CATEGORY_SEEDS, TOP_RANK_LIMIT

load_dotenv()

def run_master_scraper():
    print(f"🚀 K-Enter Trend Master 가동 시작: {datetime.now()}")
    
    # 설정된 5개 카테고리 순회
    for category, seeds in CATEGORY_SEEDS.items():
        print(f"\n📂 [{category.upper()}] 트렌드 분석 시작")
        
        # ---------------------------------------------------------
        # [1단계] 씨앗 수집 (Seed Search)
        # ---------------------------------------------------------
        seed_titles = []
        try:
            for seed in seeds:
                # display 파라미터 사용 (crawler.py 업데이트 필수)
                news = crawler.get_naver_api_news(seed, display=20)
                seed_titles.extend([n['title'] for n in news])
            
            seed_titles = list(set(seed_titles)) # 중복 제거
            print(f"   🌱 원석 수집 완료: {len(seed_titles)}개의 제목 확보")
        except Exception as e:
            print(f"   ⚠️ 씨앗 수집 중 오류: {e}")
            continue
        
        # ---------------------------------------------------------
        # [2단계] 키워드 추출 (AI Mining)
        # ---------------------------------------------------------
        top_keywords = ai_engine.extract_top_entities(category, seed_titles)
        
        if not top_keywords:
            print("   ⚠️ 키워드 추출 실패. 다음 카테고리로 이동.")
            continue
            
        print(f"   💎 추출된 랭킹(Top {len(top_keywords)}): {', '.join(top_keywords[:5])}...")

        # ---------------------------------------------------------
        # [3단계] 키워드별 종합 요약 (Deep Dive & Synthesis)
        # ---------------------------------------------------------
        category_news_list = []
        target_keywords = top_keywords[:TOP_RANK_LIMIT] # 설정된 개수(30개)만큼 처리
        
        for rank, kw in enumerate(target_keywords):
            print(f"   🔍 Rank {rank+1}: '{kw}' 종합 요약 중...")
            
            try:
                # 1. 해당 키워드로 기사 검색
                raw_articles = crawler.get_naver_api_news(kw, display=10)
                if not raw_articles:
                    continue

                # 2. 본문 및 이미지 수집 (여러 기사 통합)
                full_contents = []
                main_image = None
                
                for art in raw_articles[:5]: # 상위 5개 기사만 참조
                    text, img = crawler.get_article_data(art['link'])
                    if text: 
                        full_contents.append(text)
                    
                    # [이미지 처리] 첫 번째 유효한 이미지를 메인으로 설정
                    if not main_image and img:
                        # http -> https 강제 변환 (보안 이슈 해결)
                        if img.startswith("http://"):
                            img = img.replace("http://", "https://")
                        main_image = img

                # 3. 데이터 포장 (내용이 있을 경우만)
                if full_contents:
                    # AI에게 종합 브리핑 작성 요청
                    briefing = ai_engine.synthesize_briefing(kw, full_contents)
                    
                    # 이미지가 없으면 플레이스홀더 사용
                    final_img = main_image or f"https://placehold.co/600x400/111/cyan?text={kw}"

                    news_item = {
                        "category": category,
                        "rank": rank + 1,
                        "keyword": kw,
                        "title": f"[{kw}] Key Trends & Issues", # 제목은 키워드 중심으로 통일
                        "summary": briefing,
                        "link": None,            # 🚨 요청사항: 기사 링크는 저장하지 않음 (NULL)
                        "image_url": final_img,  # 🚨 이미지는 저장함 (HTTPS 처리됨)
                        "score": 10.0 - (rank * 0.1), # 순위에 따른 점수 부여
                        "likes": 0, 
                        "dislikes": 0,
                        "created_at": datetime.now().isoformat(),
                        "published_at": datetime.now().isoformat()
                    }
                    category_news_list.append(news_item)
                
                # API 호출 속도 조절 (차단 방지)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ⚠️ '{kw}' 처리 실패: {e}")
                continue

        # ---------------------------------------------------------
        # [4단계] DB 저장 (Repository 호출)
        # ---------------------------------------------------------
        if category_news_list:
            # 1. 상위 10개는 아카이브(역사)에 저장
            repository.save_to_archive(category_news_list[:10])
            
            # 2. Live News 테이블은 해당 카테고리 전체 교체 (Refresh)
            repository.refresh_live_news(category, category_news_list)

    print("\n🎉 모든 카테고리 업데이트가 완료되었습니다.")

if __name__ == "__main__":
    run_master_scraper()

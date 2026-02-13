import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import time
from datetime import datetime
from dotenv import load_dotenv

from scraper.config import CATEGORY_MAP
from scraper import crawler, ai_engine, repository, update_rankings

load_dotenv()

def run_scraper():
    print("🚀 7단계 마스터 엔진 가동 (Rules 1-6 Applied)...")
    
    for category, keywords in CATEGORY_MAP.items():
        try:
            print(f"\n📂 {category.upper()} 부문 처리 중...")

            # [규칙 1] 수집 (최신순 정렬됨)
            raw_news = []
            for kw in keywords: 
                raw_news.extend(crawler.get_naver_api_news(kw))
            
            # [규칙 2] 중복 제거
            existing_links = repository.get_existing_links(category)
            
            new_candidate_news = []
            seen_links = set()
            for n in raw_news:
                if n['link'] not in existing_links and n['link'] not in seen_links:
                    new_candidate_news.append(n)
                    seen_links.add(n['link'])
            
            print(f"   🔎 수집: {len(raw_news)}개 -> 중복 제거 후: {len(new_candidate_news)}개")

            if not new_candidate_news:
                continue

            # [규칙 3] 최신 기사 70개 선정 -> AI 평가
            # 70개가 안 되면 있는 만큼만 보냄
            ai_input_news = new_candidate_news[:70]

            # AI 선별 (점수 부여 및 요약)
            analyzed_list = ai_engine.ai_category_editor(category, ai_input_news)
            print(f"   ㄴ AI 분석 완료: {len(analyzed_list)}개")

            if analyzed_list:
                # [규칙 3 후반] 점수 기반 상위 30개 선정
                # 점수(score) 내림차순 정렬
                analyzed_list.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                # 상위 30개만 자르기 (규칙 4: 새로운 기사 30개 저장)
                top_30_news = analyzed_list[:30]
                
                new_data_list = []
                for art in top_30_news:
                    idx = art.get('original_index')
                    if idx is None or idx >= len(ai_input_news): continue
                    
                    orig = ai_input_news[idx]
                    img = crawler.get_article_image(orig['link']) or f"https://placehold.co/600x400/111/cyan?text={category}"

                    # Rank 컬럼 제거됨
                    news_item = {
                        "category": category, 
                        "title": art.get('eng_title', orig['title']),
                        "summary": art.get('summary', 'Summary not available.'), 
                        "link": orig['link'], 
                        "image_url": img,
                        "score": art.get('score', 5.0), 
                        "likes": 0, 
                        "dislikes": 0, 
                        "created_at": datetime.now().isoformat(),
                        "published_at": orig.get('published_at', datetime.now()).isoformat()
                    }
                    new_data_list.append(news_item)
                
                # [규칙 4] DB 저장 (30개) + [아카이빙]
                repository.save_news(new_data_list)

            # [규칙 5 & 6] 슬롯 관리 (전체 30개 유지, 시간/점수 삭제)
            repository.manage_slots(category)

        except Exception as e:
            print(f"⚠️ Error processing category {category}: {e}")
            continue

    # 키워드 분석 (옵션)
    try:
        print("\n📊 AI 키워드 트렌드 분석 시작...")
        titles = repository.get_recent_titles()
        if titles and hasattr(ai_engine, 'ai_analyze_keywords'):
            keywords = ai_engine.ai_analyze_keywords(titles)
            if keywords:
                repository.update_keywords_db(keywords)
    except Exception as e:
        print(f"⚠️ 키워드 분석 오류: {e}")
    
    print("🎉 뉴스 데이터 처리 작업 완료.")

def main():
    print("🚀 K-Enter AI News Bot Started...")
    
    # 순위 업데이트
    update_rankings.update_rankings() 
    
    # 뉴스 수집 시작
    run_scraper()
    
    print("✅ All Tasks Completed.")

if __name__ == "__main__":
    main()

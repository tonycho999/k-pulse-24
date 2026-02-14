# scraper/main.py
import time
import schedule
from datetime import datetime
import config
import processor

# 현재 순서 인덱스
current_idx = 0

def job():
    global current_idx
    # 1. 카테고리 선정
    category = config.CATEGORY_ORDER[current_idx]
    
    # 2. 로직 실행
    print(f"\n⏰ [Schedule] Starting job for '{category}' at {datetime.now()}")
    processor.run_category_process(category)
    
    # 3. 다음 카테고리로 변경 (순환)
    current_idx = (current_idx + 1) % len(config.CATEGORY_ORDER)

def run_scheduler():
    print("🤖 News Bot Scheduler Started...")
    print("   - Runs at :12 and :42 every hour.")
    
    # 매 시 12분, 42분에 실행
    schedule.every().hour.at(":12").do(job)
    schedule.every().hour.at(":42").do(job)

    # (테스트용) 실행 즉시 한번 돌려보려면 아래 주석 해제
    # job()

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    run_scheduler()

import time
import schedule
from datetime import datetime
import config
import processor

# 현재 카테고리 인덱스
current_idx = 0

def job():
    global current_idx
    category = config.CATEGORY_ORDER[current_idx]
    
    print(f"\n⏰ [Job Start] {category} at {datetime.now()}")
    processor.run_category(category)
    
    # 다음 카테고리로 변경
    current_idx = (current_idx + 1) % len(config.CATEGORY_ORDER)

def main():
    print("🤖 Bot Scheduler Started...")
    
    # 매 시 12분, 42분 실행
    schedule.every().hour.at(":12").do(job)
    schedule.every().hour.at(":42").do(job)
    
    # (테스트용) 실행 시 바로 한 번 돌리려면 아래 주석 해제
    # job()

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()

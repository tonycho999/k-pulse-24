import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq

# 한글 깨짐 방지
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# [환경변수 설정]
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
# 네이버 뉴스에서 '원석'을 캐기 위한 광범위한 키워드
CATEGORY_SEEDS = {
    "k-pop": ["컴백", "빌보드", "아이돌", "뮤직", "비디오", "챌린지", "포토카드", "월드투어", "가수"],
    "k-drama": ["드라마", "시청률", "넷플릭스", "OTT", "배우", "캐스팅", "대본리딩", "종영"],
    "k-movie": ["영화", "개봉", "박스오피스", "시사회", "영화제", "관객", "무대인사"],
    "k-entertain": ["예능", "유튜브", "개그맨", "코미디언", "방송", "개그우먼"],
    "k-culture": ["푸드", "뷰티", "웹툰", "팝업스토어", "패션", "음식", "해외반응", "관광지", "축제"]
}

# [2. 설정 상수]
TOP_RANK_LIMIT = 30  # 카테고리당 30위까지 선정

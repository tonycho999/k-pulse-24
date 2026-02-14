'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { Lock, Zap } from 'lucide-react';
import { User } from '@supabase/supabase-js'; // User 타입 임포트

import Header from '@/components/Header';
import CategoryNav from '@/components/CategoryNav';
import InsightBanner from '@/components/InsightBanner';
import NewsFeed from '@/components/NewsFeed';
import Sidebar from '@/components/Sidebar';
import ArticleModal from '@/components/ArticleModal';
import MobileFloatingBtn from '@/components/MobileFloatingBtn';
import AdBanner from '@/components/AdBanner';
import { LiveNewsItem } from '@/types';

// localStorage 키 상수화
const WELCOME_MODAL_KEY = 'hasSeenWelcome_v1';

interface HomeClientProps {
  initialNews: LiveNewsItem[];
}

export default function HomeClient({ initialNews }: HomeClientProps) {
  
  // ✅ [보안 필터] 이미지 주소만 업그레이드 (링크 검사 제거)
  const filterSecureNews = useCallback((items: LiveNewsItem[]) => {
    if (!items) return [];
    return items.map(item => ({
        ...item,
        // 이미지 주소가 http면 https로 변환
        image_url: item.image_url ? item.image_url.replace('http://', 'https://') : null
      }));
  }, []);

  // 1. 상태 관리
  const [news, setNews] = useState<LiveNewsItem[]>(filterSecureNews(initialNews));
  const [category, setCategory] = useState('All');
  const [selectedArticle, setSelectedArticle] = useState<LiveNewsItem | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [user, setUser] = useState<User | null>(null); // User 타입 적용
  
  const [showWelcome, setShowWelcome] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  // 2. 초기화 및 인증 체크
  useEffect(() => {
    const checkUser = async () => {
      const { data } = await supabase.auth.getUser();
      setUser(data.user);
    };
    checkUser();
    
    const hasSeenWelcome = localStorage.getItem(WELCOME_MODAL_KEY);
    if (!hasSeenWelcome) {
        // setTimeout 타이머 클리어 처리를 위해 변수에 할당
        const timer = setTimeout(() => setShowWelcome(true), 1000);
        return () => clearTimeout(timer);
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  // 3. [핵심 수정] 카테고리 변경 시 정렬 로직 분기 (All: 평점순, 나머지: 랭킹순)
  const handleCategoryChange = useCallback(async (newCategory: string) => {
    setCategory(newCategory);
    setLoading(true);

    try {
      // 쿼리 시작
      let query = supabase.from('live_news').select('*');

      if (newCategory === 'All') {
        // ✅ [수정] All 트렌드는 '평점(score)' 높은 순으로 정렬
        query = query.order('score', { ascending: false });
      } else {
        // ✅ [유지] 개별 카테고리는 소문자로 변환하여 조회 + '랭킹(rank)' 순 정렬
        query = query
          .eq('category', newCategory)
          .order('rank', { ascending: true });
      }

      // 공통: 30개 제한
      query = query.limit(30);

      const { data, error } = await query;

      if (!error && data) {
        setNews(filterSecureNews(data as LiveNewsItem[]));
      }
    } catch (error) {
      console.error("Fetch Error:", error);
    } finally {
      setLoading(false);
    }
  }, [filterSecureNews]); // filterSecureNews 의존성 추가

  // 4. 좋아요 핸들러
  const handleVote = useCallback(async (id: string, type: 'likes' | 'dislikes') => {
    if (!user) {
      alert("Please sign in to vote!");
      return;
    }

    if (type === 'dislikes') {
       alert("Dislike feature is coming soon!");
       return;
    }

    setNews(prev => prev.map(item => item.id === id ? { ...item, likes: item.likes + 1 } : item));
    
    // selectedArticle 상태 업데이트 (현재 보고 있는 기사라면)
    setSelectedArticle((prev) => {
        if (prev && prev.id === id) {
            return { ...prev, likes: prev.likes + 1 };
        }
        return prev;
    });

    await supabase.rpc('increment_vote', { row_id: id });
  }, [user]); // user 의존성 추가

  // 5. 클라이언트 사이드 필터링 (All일 때는 전체 표시, 아니면 카테고리 소문자로 비교)
  // useMemo를 사용하여 불필요한 연산 방지
  // const displayNewsRaw = user ? news : news.slice(0, 1); // 기존 로직 (로그인 안하면 1개만 보임) -> 아래 렌더링 로직에서 처리됨
  
  // 6. 이벤트 리스너
  useEffect(() => {
    const handleSearchModalOpen = (e: CustomEvent<LiveNewsItem>) => { // CustomEvent 타입 적용
      if (e.detail) setSelectedArticle(e.detail);
    };
    window.addEventListener('open-news-modal', handleSearchModalOpen as EventListener);
    return () => window.removeEventListener('open-news-modal', handleSearchModalOpen as EventListener);
  }, []);

  const closeWelcome = () => {
    if (dontShowAgain) localStorage.setItem(WELCOME_MODAL_KEY, 'true');
    setShowWelcome(false);
  };

  const handleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  };

  // 렌더링을 위한 필터링된 뉴스 목록 계산
  const filteredDisplayNews = category === 'All' 
    ? news 
    : news.filter(item => item.category === category);
  
  // 로그인 안 했을 때 보여줄 뉴스 (1개만)
  const displayedNews = user ? filteredDisplayNews : filteredDisplayNews.slice(0, 1);


  return (
    /* ✅ 배경색 다크모드 제거 및 가로 스크롤 방지 추가 */
    <main className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans overflow-x-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-0 w-full">
        <Header />
        
        <div className="flex flex-col gap-0 w-full">
          <div className="mb-1 w-full overflow-hidden">
             <CategoryNav active={category} setCategory={handleCategoryChange} />
          </div>
          
          <div className="mt-0 w-full"> 
             <InsightBanner insight={news.length > 0 ? news[0].summary : undefined} />
          </div>
          
          <div className="mt-2 w-full">
             <AdBanner />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mt-6 w-full">
          <div className="col-span-1 md:col-span-3 relative w-full">
            {/* 필터링된 뉴스를 전달 */}
            <NewsFeed 
              news={displayedNews} 
              loading={loading || isTranslating} 
              onOpen={setSelectedArticle} 
            />
            
            {/* ✅ 로그인 유도 구역: 모바일 최적화 및 다크모드 제거 */}
            {!user && !loading && news.length > 0 && (
              <div className="mt-4 sm:mt-6 relative w-full">
                 <div className="space-y-4 sm:space-y-6 opacity-40 blur-md select-none pointer-events-none grayscale">
                    <div className="h-32 sm:h-40 bg-white rounded-2xl sm:rounded-3xl border border-slate-200" />
                    <div className="h-32 sm:h-40 bg-white rounded-2xl sm:rounded-3xl border border-slate-200" />
                 </div>
                 
                 <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
                    <div className="bg-white/95 backdrop-blur-2xl p-6 sm:p-8 rounded-[24px] sm:rounded-[32px] shadow-2xl border border-slate-100 text-center w-full max-w-[320px] mx-auto">
                        <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-3 shadow-lg shadow-cyan-200">
                           <Lock className="text-white" size={20} />
                        </div>
                        <h3 className="text-lg font-black text-slate-900 mb-1 tracking-tight">Want to see more?</h3>
                        <p className="text-xs text-slate-500 mb-5 leading-relaxed">
                           Sign in to unlock <span className="font-bold text-cyan-600">Real-time K-Trends</span> & <span className="font-bold text-cyan-600">AI Analysis</span>.
                        </p>
                        <button onClick={handleLogin} className="w-full py-3 bg-slate-900 text-white text-sm font-bold rounded-xl active:scale-95 transition-transform shadow-xl">
                          Sign in with Google
                        </button>
                    </div>
                 </div>
              </div>
            )}
          </div>
          
          <div className="hidden md:block col-span-1">
            <Sidebar news={news} category={category} />
          </div>
        </div>
      </div>

      {selectedArticle && (
        <ArticleModal 
          article={selectedArticle} 
          onClose={() => setSelectedArticle(null)} 
          onVote={handleVote} // 타입 에러 해결됨
        />
      )}
      
      <MobileFloatingBtn />
      
      {showWelcome && !user && (
        <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">
           <div className="bg-white w-full max-w-md rounded-[32px] p-1 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
              <div className="bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 p-8 rounded-[28px] text-center relative overflow-hidden">
                 <div className="absolute top-0 left-0 w-full h-full opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')]"></div>
                 <div className="relative z-10">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-white/20 backdrop-blur-md mb-4 border border-white/30 shadow-lg">
                       <Zap className="text-yellow-300 fill-yellow-300" size={24} />
                    </div>
                    <h2 className="text-2xl font-black text-white mb-3 tracking-tight leading-tight">⚡️ Real-time K-News Radar</h2>
                    <div className="text-white/95 font-medium text-sm mb-8 leading-relaxed space-y-2 opacity-90">
                       <p>Stop waiting for late translations.</p>
                       <p>Access breaking <span className="text-yellow-300 font-bold">K-Pop & Drama</span> articles the second they are published in Korea.</p>
                       <p>Experience the world's fastest K-Trend source.</p>
                    </div>
                    <button onClick={closeWelcome} className="w-full py-4 bg-white text-slate-900 font-black text-lg rounded-2xl hover:bg-slate-50 hover:scale-[1.02] transition-all shadow-xl">
                       Start Monitoring Now
                    </button>
                 </div>
              </div>
              <div className="p-4 bg-white text-center">
                 <label className="flex items-center justify-center gap-2 cursor-pointer group select-none">
                    <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500 transition-all" checked={dontShowAgain} onChange={(e) => setDontShowAgain(e.target.checked)} />
                    <span className="text-xs font-bold text-slate-400 group-hover:text-slate-600 transition-colors">Don't show this again</span>
                 </label>
              </div>
           </div>
        </div>
      )}
    </main>
  );
}

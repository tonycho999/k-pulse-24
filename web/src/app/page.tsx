'use client';

import { useState, useEffect } from 'react';
import HotKeywords from '@/components/HotKeywords';
import GlobalReactions from '@/components/GlobalReactions';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

export default function Home() {
  const [articles, setArticles] = useState<any[]>([]); 
  const [user, setUser] = useState<any>(null);
  const supabase = createClientComponentClient();

  // 데이터 로드 & 유저 체크
  useEffect(() => {
    const init = async () => {
      // 1. 세션 확인
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);

      // 2. [공개된] 뉴스만 가져오기
      const { data } = await supabase
        .from('live_news')
        .select('*')
        .eq('is_published', true) // 공개된 것만!
        .order('id', { ascending: false });
      
      if (data) setArticles(data);
    };
    init();
  }, []);

  const handleLogin = async () => {
    // Supabase 구글 로그인 (설정 필요)
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  };

  return (
    <main className="min-h-screen bg-black text-white p-4 md:p-8 font-sans">
      
      {/* --- 헤더 --- */}
      <header className="flex justify-between items-center mb-8 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
            <img src="/logo.png" alt="K-POP 24" className="h-14 md:h-16 w-auto object-contain drop-shadow-[0_0_15px_rgba(34,211,238,0.6)]" />
        </div>

        {user ? (
          <div className="flex items-center gap-3">
             <span className="text-cyan-400 text-sm font-bold hidden md:inline">
               Agent {user.email?.split('@')[0]}
             </span>
             <button onClick={() => supabase.auth.signOut()} className="text-xs text-gray-500 border border-gray-700 px-3 py-1 rounded hover:bg-gray-800">
               Log Out
             </button>
          </div>
        ) : (
          <button 
            onClick={handleLogin}
            className="bg-cyan-500 text-black px-5 py-2 rounded-full text-sm font-bold hover:bg-cyan-400 transition-all shadow-[0_0_15px_rgba(34,211,238,0.4)] animate-pulse"
          >
            LOG IN (FREE)
          </button>
        )}
      </header>

      {/* --- 뉴스 피드 --- */}
      <section className="mb-8 max-w-7xl mx-auto">
        <h2 className="text-xl font-bold mb-4 text-gray-200">Live Briefing</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {articles.map((news) => (
            <div key={news.id} className="group relative h-80 rounded-xl overflow-hidden border border-gray-800 hover:border-cyan-500 transition-all bg-gray-900">
              
              {/* 배경 이미지 */}
              <div className="absolute inset-0">
                <img src={news.image_url || "/logo.png"} className="w-full h-full object-cover opacity-50 group-hover:opacity-30 transition-opacity" />
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />

              {/* 콘텐츠 */}
              <div className="absolute bottom-0 left-0 p-5 w-full">
                 <div className="flex gap-2 mb-2">
                    <span className="text-xs text-cyan-300 font-bold bg-cyan-900/40 px-2 py-0.5 rounded border border-cyan-500/30">
                      {news.artist}
                    </span>
                    {/* 키워드(해시태그) 노출 */}
                    {news.keywords?.slice(0, 1).map((tag: string, i: number) => (
                        <span key={i} className="text-[10px] text-pink-400 border border-pink-500/30 px-1.5 py-0.5 rounded">
                            {tag}
                        </span>
                    ))}
                 </div>

                 <h3 className="text-white font-bold text-lg leading-snug mb-2 line-clamp-2">
                    {news.title}
                 </h3>
                 
                 {/* 로그인 여부에 따른 블러 처리 (핵심) */}
                 <div className="relative">
                    <p className={`text-sm text-gray-300 line-clamp-3 ${!user ? 'blur-sm select-none opacity-50' : ''}`}>
                      {news.summary}
                    </p>
                    
                    {!user && (
                      <div className="absolute inset-0 flex items-center justify-center pt-2">
                        <button onClick={handleLogin} className="text-xs font-bold text-cyan-400 border border-cyan-500 px-3 py-1 rounded-full bg-black/80 hover:bg-cyan-500 hover:text-black transition-all">
                          🔒 Login to Read
                        </button>
                      </div>
                    )}
                 </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* --- 하단 분석 데이터 (컴포넌트 연동) --- */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-7xl mx-auto pb-10">
        <HotKeywords />
        <GlobalReactions />
      </section>

    </main>
  );
}

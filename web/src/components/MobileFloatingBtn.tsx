'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Flame, X, Trophy, TrendingUp, ChevronRight } from 'lucide-react';

export default function MobileFloatingBtn() {
  const [isOpen, setIsOpen] = useState(false);
  const [keywords, setKeywords] = useState<any[]>([]);
  const [topNews, setTopNews] = useState<any[]>([]);

  // 데이터 가져오기 (컴포넌트가 열릴 때 한 번만 실행해도 됨)
  useEffect(() => {
    const fetchData = async () => {
      // 1. 트렌드 키워드 Top 10
      const { data: kwData } = await supabase
        .from('trending_keywords')
        .select('*')
        .order('rank', { ascending: true })
        .limit(10);
      if (kwData) setKeywords(kwData);

      // 2. 인기 뉴스 Top 5 (점수순)
      const { data: newsData } = await supabase
        .from('live_news')
        .select('title, category, score, link')
        .order('score', { ascending: false })
        .limit(5);
      if (newsData) setTopNews(newsData);
    };

    fetchData();
  }, []);

  return (
    <>
      {/* 1. 플로팅 버튼 (PC에서는 숨김: md:hidden) */}
      <button
        onClick={() => setIsOpen(true)}
        className={`md:hidden fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-lg transition-transform hover:scale-110 active:scale-95 flex items-center justify-center
          ${isOpen ? 'bg-slate-800 rotate-90' : 'bg-gradient-to-r from-orange-500 to-red-600 animate-bounce-slow'}
        `}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <Flame className="w-7 h-7 text-white fill-white" />
        )}
      </button>

      {/* 2. 바텀 시트 (Bottom Sheet) */}
      {/* 배경 어둡게 처리 (Overlay) */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* 실제 올라오는 패널 */}
      <div
        className={`fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-[32px] p-6 shadow-2xl transition-transform duration-300 ease-out md:hidden max-h-[85vh] overflow-y-auto
          ${isOpen ? 'translate-y-0' : 'translate-y-full'}
        `}
      >
        {/* 핸들바 (손잡이) */}
        <div className="w-12 h-1.5 bg-slate-200 rounded-full mx-auto mb-6" />

        <div className="space-y-8 pb-10">
          
          {/* 섹션 1: 실시간 트렌드 키워드 */}
          <div>
            <h3 className="text-lg font-black text-slate-800 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-red-500" />
              Real-time Trends
            </h3>
            <div className="flex flex-wrap gap-2">
              {keywords.map((item, idx) => (
                <span 
                  key={item.id} 
                  className={`px-4 py-2 rounded-full text-sm font-bold border shadow-sm
                    ${idx < 3 
                      ? 'bg-red-50 border-red-100 text-red-600' 
                      : 'bg-slate-50 border-slate-100 text-slate-600'
                    }`}
                >
                  <span className="mr-1.5 opacity-50">#{item.rank}</span>
                  {item.keyword}
                </span>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-100" />

          {/* 섹션 2: 지금 가장 핫한 뉴스 */}
          <div>
            <h3 className="text-lg font-black text-slate-800 mb-4 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-amber-500" />
              Top Voted News
            </h3>
            <div className="space-y-3">
              {topNews.map((news, idx) => (
                <a 
                  key={idx} 
                  href={news.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start justify-between group p-3 rounded-2xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100"
                >
                  <div className="flex gap-3">
                    <span className="flex-shrink-0 w-6 h-6 bg-slate-900 text-white rounded-full flex items-center justify-center text-xs font-bold">
                      {idx + 1}
                    </span>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
                        {news.category}
                      </span>
                      <h4 className="text-sm font-bold text-slate-700 leading-snug line-clamp-2 group-hover:text-blue-600">
                        {news.title}
                      </h4>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-300 mt-1" />
                </a>
              ))}
            </div>
          </div>

        </div>
      </div>
    </>
  );
}

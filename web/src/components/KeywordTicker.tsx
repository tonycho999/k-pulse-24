'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, TrendingUp, Hash } from 'lucide-react';

// 데이터 타입 정의
interface TrendItem {
  id: number;
  rank: number;
  keyword: string;
  count: number;
}

export default function KeywordTicker() {
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [index, setIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKeywords = async () => {
      // [수정] live_news가 아니라 분석된 'trending_keywords' 테이블에서 가져옴
      const { data, error } = await supabase
        .from('trending_keywords')
        .select('*')
        .order('rank', { ascending: true })
        .limit(10);

      if (data && !error) {
        setTrends(data);
      }
      setLoading(false);
    };

    fetchKeywords();
  }, []);

  // 3초마다 롤링
  useEffect(() => {
    if (isOpen || trends.length === 0) return; 
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % trends.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [isOpen, trends]); // trends 의존성 확인

  if (loading) return <div className="h-12 animate-pulse bg-slate-100 rounded-2xl mb-6" />;

  // 데이터가 없을 때 (아직 분석 전일 경우) 예외 처리
  if (!loading && trends.length === 0) return null;

  return (
    <div className="w-full max-w-md mx-auto mb-6 relative z-[60]">
      {/* 티커 메인 영역 */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="cursor-pointer bg-white border border-slate-100 shadow-sm rounded-2xl px-5 py-3 flex items-center justify-between transition-all hover:border-cyan-200 active:scale-[0.98]"
      >
        <div className="flex items-center gap-3 flex-1 overflow-hidden">
          {/* 라벨 디자인 약간 수정 */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg shadow-sm shadow-cyan-200">
            <TrendingUp size={12} className="text-white" />
            <span className="text-[10px] text-white font-black uppercase tracking-tight">Trends</span>
          </div>
          
          <div className="flex-1 h-6 overflow-hidden relative flex items-center">
            <AnimatePresence mode="wait">
              {trends[index] && (
                <motion.div 
                  key={trends[index].id} // 고유 ID 사용
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -20, opacity: 0 }}
                  transition={{ duration: 0.4, ease: "backOut" }}
                  className="flex items-center gap-2 text-slate-700 font-bold text-sm absolute w-full"
                >
                  <span className="text-cyan-600 font-black tabular-nums">{trends[index].rank}.</span>
                  <span className="truncate">{trends[index].keyword}</span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        
        <ChevronDown 
          size={16} 
          className={`text-slate-300 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </div>

      {/* 펼쳐졌을 때 보이는 리스트 (Dropdown) */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-16 left-0 w-full bg-white/95 backdrop-blur-xl border border-slate-100 rounded-3xl p-4 shadow-xl shadow-slate-200/50 flex flex-col gap-1 overflow-hidden"
          >
            <div className="text-[10px] font-black text-slate-400 mb-2 px-2 flex justify-between uppercase tracking-widest">
              <span>Real-time Keywords</span>
              <span className="text-cyan-500 flex items-center gap-1">
                <Hash size={10} /> Top 10
              </span>
            </div>
            
            <div className="grid grid-cols-1 gap-1">
              {trends.map((item) => (
                <div 
                  key={item.id} 
                  className="group flex items-center justify-between p-2 rounded-xl hover:bg-cyan-50 transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <span className={`text-sm font-black tabular-nums w-4 ${item.rank <= 3 ? 'text-cyan-500' : 'text-slate-300'}`}>
                      {item.rank}
                    </span>
                    <span className="text-sm font-bold text-slate-700 group-hover:text-cyan-700 truncate">
                      {item.keyword}
                    </span>
                  </div>
                  
                  {/* 언급 횟수 (Count) 표시 - 신뢰도 상승 */}
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-medium text-slate-400 group-hover:text-cyan-500 transition-colors">
                      {item.count} mentions
                    </span>
                    {item.rank <= 3 && (
                      <span className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

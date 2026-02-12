'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase'; // 1. 공용 인스턴스 임포트
import { Flame } from 'lucide-react'; // 아이콘 추가

export default function HotKeywords() {
  const [keywords, setKeywords] = useState<{ text: string; count: number }[]>([]);

  // 2. 에러의 원인이던 const supabase = createClient(); 줄을 삭제했습니다.

  useEffect(() => {
    const fetchKeywords = async () => {
      const { data } = await supabase
        .from('live_news')
        .select('category') // 현재 스키마에 맞춰 category나 keywords를 활용
        .order('created_at', { ascending: false });

      if (data) {
        // 데이터에서 카테고리나 키워드 빈도수 계산 로직
        const allTags = data.map(item => item.category);
        const counts = allTags.reduce((acc: any, tag: string) => {
          acc[tag] = (acc[tag] || 0) + 1;
          return acc;
        }, {});

        const sorted = Object.keys(counts)
          .map(tag => ({ text: tag, count: counts[tag] }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);

        setKeywords(sorted);
      }
    };
    fetchKeywords();
  }, []);

  return (
    // 3. 디자인: 화이트 배경, 둥근 모서리, 부드러운 그림자로 변경 (web2.jpg 스타일)
    <div className="bg-white border border-slate-100 rounded-[32px] p-8 h-full shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-sm font-black text-slate-800 mb-6 flex items-center gap-2 uppercase tracking-wider">
        <Flame className="w-5 h-5 text-orange-500 fill-current" /> 
        Trending Keywords
      </h3>
      
      <div className="space-y-6">
        {keywords.length > 0 ? (
          keywords.map((item, idx) => (
            <div key={idx} className="group">
              <div className="flex justify-between items-center text-xs mb-2">
                <span className="text-slate-700 font-bold">
                  <span className="text-cyan-500 mr-2 font-black">0{idx + 1}</span> 
                  {item.text.toUpperCase()}
                </span>
                <span className="text-slate-400 font-bold">Score {item.count * 10}</span>
              </div>
              
              {/* 바 디자인 수정: 사이언 그라데이션 적용 */}
              <div className="w-full bg-slate-50 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full rounded-full transition-all duration-1000 ease-out" 
                  style={{ width: `${Math.min(item.count * 20, 100)}%` }}
                ></div>
              </div>
            </div>
          ))
        ) : (
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-10 bg-slate-50 animate-pulse rounded-xl" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

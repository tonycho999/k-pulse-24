'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Activity } from 'lucide-react';
import { motion } from 'framer-motion';

export default function VibeCheck() {
  // 초기값 설정
  const [stats, setStats] = useState([
    { label: 'Excitement', val: 0, color: 'bg-cyan-400', icon: '⚡' },
    { label: 'Expectation', val: 0, color: 'bg-orange-400', icon: '🔥' },
    { label: 'Shock', val: 0, color: 'bg-yellow-400', icon: '😲' }
  ]);

  useEffect(() => {
    const fetchVibe = async () => {
      try {
        // ✅ 실제 DB에서 최근 뉴스 50개의 점수와 좋아요 데이터를 가져옴
        const { data, error } = await supabase
          .from('live_news')
          .select('likes, score')
          .limit(50);

        if (!error && data && data.length > 0) {
          // 1. 데이터 계산
          const totalLikes = data.reduce((acc, curr) => acc + (curr.likes || 0), 0);
          const avgScore = data.reduce((acc, curr) => acc + (curr.score || 0), 0) / data.length;
          
          // 2. 알고리즘: 점수가 높고 좋아요가 많을수록 Excitement 증가
          // (기본 점수에서 보정치를 더해 100% 비율로 환산)
          let excitement = Math.min(92, Math.max(40, avgScore - 10 + (totalLikes * 2)));
          let expectation = Math.max(5, (100 - excitement) * 0.7);
          let shock = 100 - excitement - expectation;

          // 소수점 제거
          excitement = Math.round(excitement);
          expectation = Math.round(expectation);
          shock = 100 - excitement - expectation;

          // 3. 상태 업데이트
          setStats([
            { label: 'Excitement', val: excitement, color: 'bg-cyan-400', icon: '⚡' },
            { label: 'Expectation', val: expectation, color: 'bg-orange-400', icon: '🔥' },
            { label: 'Shock', val: shock, color: 'bg-yellow-400', icon: '😲' }
          ]);
        }
      } catch (e) {
        console.error("VibeCheck Error:", e);
      }
    };

    fetchVibe();
  }, []);

  return (
    <section className="bg-white dark:bg-slate-900 rounded-[32px] p-6 border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2 mb-6">
        <Activity size={18} className="text-cyan-500 animate-pulse" />
        <h3 className="font-black text-slate-800 dark:text-slate-200 uppercase tracking-wider text-sm">
          AI Vibe Check
        </h3>
      </div>
      
      <div className="space-y-6">
        {stats.map(stat => (
          <div key={stat.label}>
            <div className="flex justify-between items-end mb-2">
              <span className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <span className="text-sm filter drop-shadow-sm">{stat.icon}</span> {stat.label}
              </span>
              <span className="text-sm font-black text-slate-800 dark:text-white">{stat.val}%</span>
            </div>
            <div className="h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }} 
                animate={{ width: `${stat.val}%` }} 
                transition={{ duration: 1.5, ease: "circOut" }}
                className={`h-full ${stat.color} rounded-full shadow-[0_0_10px_rgba(0,0,0,0.1)]`} 
              />
            </div>
          </div>
        ))}
      </div>
      
      <p className="mt-6 text-[10px] text-slate-400 font-medium leading-relaxed border-t border-slate-50 dark:border-slate-800 pt-3">
        * Analysis based on real-time news sentiment score & social reactions.
      </p>
    </section>
  );
}

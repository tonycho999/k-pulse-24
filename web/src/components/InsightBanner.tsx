'use client';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import { useMemo } from 'react';

interface InsightBannerProps {
  insight?: string;
}

export default function InsightBanner({ insight }: InsightBannerProps) {
  const content = insight || "Analyzing global K-Entertainment trends in real-time... ⚡️ Breaking News & Viral Rankings";

  // ✅ [수정 핵심] 글자 수에 상관없이 '속도'를 일정하게 고정합니다.
  const duration = useMemo(() => {
    // 1자당 이동하는 데 걸리는 시간(초)을 설정합니다.
    // 이 수치가 낮을수록 빠르고, 높을수록 느려집니다. (0.3~0.5 추천)
    const speedFactor = 0.4; 
    
    // 글자 수에 speedFactor를 곱하여 이동 시간을 결정합니다.
    // 결과적으로 글자가 길어지면 시간도 그만큼 늘어나서 '속도'는 항상 일정해집니다.
    const calculatedDuration = content.length * speedFactor;

    // 너무 짧은 글자의 경우 너무 빨리 사라지는 것을 방지하기 위해 최소 시간을 보장합니다.
    return Math.max(calculatedDuration, 20); 
  }, [content]);

  return (
    <div className="mt-1 mb-2 px-1 py-1 bg-cyan-50 dark:bg-slate-900 border border-cyan-100 dark:border-slate-800 rounded-2xl flex items-center gap-0 overflow-hidden shadow-sm relative group">
      
      {/* 고정 라벨 (Z-index로 흐르는 글자보다 위에 위치) */}
      <div className="flex items-center gap-2 bg-cyan-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl z-20 shadow-md mr-2 shrink-0">
        <Zap className="text-yellow-500 w-4 h-4 animate-pulse fill-yellow-500" />
        <span className="text-cyan-700 dark:text-cyan-400 uppercase font-black text-[11px] tracking-widest whitespace-nowrap">
          Insight
        </span>
      </div>

      {/* 흐르는 텍스트 영역 */}
      <div className="flex-1 overflow-hidden relative flex items-center h-full">
        <motion.div
          key={content} // ✅ 내용이 바뀌면 애니메이션을 새로 시작하도록 키 설정
          initial={{ x: "100%" }}
          animate={{ x: "-100%" }}
          transition={{
            repeat: Infinity,
            duration: duration, // ✅ 계산된 동적 시간 적용
            ease: "linear",
          }}
          className="whitespace-nowrap text-sm font-bold text-slate-600 dark:text-slate-400 flex items-center"
        >
          {content}
          <span className="opacity-50 mx-10"> | </span> 
          <span className="opacity-50">{content}</span>
        </motion.div>
        
        {/* 우측 페이드 효과 */}
        <div className="absolute right-0 top-0 w-12 h-full bg-gradient-to-l from-cyan-50 dark:from-slate-900 to-transparent z-10"></div>
      </div>
    </div>
  );
}

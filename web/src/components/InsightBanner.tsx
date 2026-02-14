'use client';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';

interface InsightBannerProps {
  insight?: string;
}

export default function InsightBanner({ insight }: InsightBannerProps) {
  const content = insight || "Analyzing global K-Entertainment trends in real-time... ⚡️ Breaking News & Viral Rankings";

  return (
    <div className="mt-1 mb-2 px-1 py-1 bg-cyan-50 dark:bg-slate-900 border border-cyan-100 dark:border-slate-800 rounded-2xl flex items-center gap-0 overflow-hidden shadow-sm relative group">
      
      {/* 고정 라벨 */}
      <div className="flex items-center gap-2 bg-cyan-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl z-20 shadow-md mr-2 shrink-0">
        <Zap className="text-yellow-500 w-4 h-4 animate-pulse fill-yellow-500" />
        <span className="text-cyan-700 dark:text-cyan-400 uppercase font-black text-[11px] tracking-widest whitespace-nowrap">
          Insight
        </span>
      </div>

      {/* 흐르는 텍스트 영역 */}
      <div className="flex-1 overflow-hidden relative flex items-center h-full mask-linear-fade">
        <motion.div
          initial={{ x: "100%" }} // 오른쪽 끝에서 시작
          animate={{ x: "-100%" }} // 왼쪽 끝으로 이동
          transition={{
            repeat: Infinity,
            // ✅ [수정 핵심] 속도 조절 (숫자가 클수록 느려짐)
            // 20 -> 50 으로 변경하여 읽기 편한 속도로 늦춤
            duration: 50, 
            ease: "linear",
          }}
          className="whitespace-nowrap text-sm font-bold text-slate-600 dark:text-slate-400 flex items-center"
        >
          {content}
          {/* 반복 시 자연스러운 연결을 위해 간격과 복제본 추가 */}
          <span className="opacity-50 mx-10"> | </span> 
          <span className="opacity-50">{content}</span>
        </motion.div>
        
        {/* 오른쪽 끝 페이드 아웃 효과 */}
        <div className="absolute right-0 top-0 w-8 h-full bg-gradient-to-l from-cyan-50 dark:from-slate-900 to-transparent z-10"></div>
      </div>
    </div>
  );
}

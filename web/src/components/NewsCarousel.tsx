'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';

export default function NewsCarousel({ news }: { news: any[] }) {
  const [isPaused, setIsPaused] = useState(false);

  // 데이터가 적을 경우를 대비해 목록을 복사하여 무한 루프 구현
  const duplicatedNews = [...news, ...news, ...news];

  return (
    <div className="w-full overflow-hidden bg-black/20 py-10 relative">
      {/* 배경 네온 라인 장식 */}
      <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-30" />
      
      <motion.div
        className="flex gap-6 whitespace-nowrap"
        animate={isPaused ? {} : { x: [0, -1000] }} // 움직이는 거리 조절
        transition={{
          x: {
            repeat: Infinity,
            repeatType: "loop",
            duration: 40, // 숫자가 높을수록 천천히 흐릅니다.
            ease: "linear",
          },
        }}
        onHoverStart={() => setIsPaused(true)}
        onHoverEnd={() => setIsPaused(false)}
      >
        {duplicatedNews.map((item, idx) => (
          <div
            key={idx}
            className="inline-block min-w-[350px] max-w-[350px] bg-black/60 border border-cyan-900/50 p-6 rounded-lg backdrop-blur-xl relative group hover:border-cyan-400 transition-all cursor-pointer"
          >
            {/* 사이버펑크 디자인 요소 */}
            <div className="absolute top-0 right-0 p-2 text-[10px] font-mono text-cyan-500/50">
              ID: {idx.toString().padStart(3, '0')}
            </div>
            <div className="w-1 h-8 bg-cyan-500 absolute left-0 top-10 group-hover:h-16 transition-all" />

            {/* 아티스트 & 태그 */}
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xs font-black bg-cyan-500 text-black px-2 py-0.5 rounded">
                {item.artist}
              </span>
              <span className="text-[10px] text-cyan-400 font-mono">
                {item.keywords?.[0] || '#K-PULSE'}
              </span>
            </div>

            {/* 제목 & 요약 */}
            <h3 className="text-lg font-bold text-white mb-2 truncate">
              {item.title}
            </h3>
            <p className="text-sm text-gray-400 whitespace-normal line-clamp-2 mb-6">
              {item.summary}
            </p>

            {/* Vibe Check 결과 미리보기 */}
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] font-mono text-gray-500">
                <span>VIBE_ANALYSIS</span>
                <span className="text-cyan-400">{item.reactions?.excitement}%</span>
              </div>
              <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-cyan-500 shadow-[0_0_10px_#06b6d4]" 
                  style={{ width: `${item.reactions?.excitement}%` }}
                />
              </div>
            </div>

            {/* 하단 버튼 효과 */}
            <div className="mt-4 pt-4 border-t border-gray-800 flex justify-between items-center">
              <span className="text-[10px] text-gray-600 font-mono">ENCRYPTED_DATA</span>
              <button className="text-[10px] text-cyan-500 font-bold hover:text-white uppercase tracking-tighter">
                Access Node ➔
              </button>
            </div>
          </div>
        ))}
      </motion.div>
      
      <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-fuchsia-500 to-transparent opacity-30" />
    </div>
  );
}

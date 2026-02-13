'use client';

import { motion } from 'framer-motion';
import { ThumbsUp, ThumbsDown, Share2 } from 'lucide-react';
import { LiveNewsItem } from '@/types'; // 위에서 만든 타입 import

interface NewsFeedProps {
  news: LiveNewsItem[];
  loading: boolean;
  onOpen: (article: LiveNewsItem) => void;
}

export default function NewsFeed({ news, loading, onOpen }: NewsFeedProps) {
  
  // 1. 공유 핸들러 함수
  const handleShare = async (e: React.MouseEvent, title: string, url: string) => {
    e.stopPropagation();
    try {
      if (navigator.share) {
        await navigator.share({
          title: title,
          text: `Check out this K-Trend: ${title}`,
          url: url,
        });
      } else {
        await navigator.clipboard.writeText(url);
        alert('Link copied to clipboard! 🔗');
      }
    } catch (err) {
      console.error('Error sharing:', err);
    }
  };

  // 2. 로딩 상태 UI
  if (loading) {
    return (
      <div className="lg:col-span-8 h-96 flex flex-col items-center justify-center gap-4 text-slate-300 font-black tracking-widest animate-pulse">
        <div className="w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
        LOADING TRENDS...
      </div>
    );
  }

  // 3. 뉴스 데이터가 없을 때
  if (!news || news.length === 0) {
    return (
      <div className="lg:col-span-8 h-96 flex flex-col items-center justify-center text-slate-400">
        <p className="font-bold text-lg">No news available yet.</p>
        <p className="text-sm">Please wait for the next update.</p>
      </div>
    );
  }

  return (
    <div className="lg:col-span-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {news.map((item) => {
          // DB의 rank 컬럼 사용 (없으면 index로 대체)
          const displayRank = item.rank; 
          
          // 레이아웃 결정 로직 (1~2위: 대형, 3~6위: 중형, 7위~: 리스트형)
          const isHero = displayRank <= 2;
          const isGrid = displayRank > 2 && displayRank <= 6;
          
          // 카드 스타일 클래스 정의
          const cardClass = isHero 
            ? "md:col-span-2 aspect-[4/3] relative overflow-hidden group shadow-xl hover:shadow-2xl hover:shadow-cyan-500/20" 
            : isGrid 
              ? "md:col-span-1 aspect-square relative overflow-hidden group shadow-md hover:shadow-xl hover:shadow-cyan-500/10"
              : "md:col-span-4 bg-white dark:bg-slate-900 p-4 flex items-center gap-4 rounded-3xl border border-slate-100 dark:border-slate-800 hover:border-cyan-300 transition-all shadow-sm";

          // [A] Hero & Grid Style (이미지 배경)
          if (isHero || isGrid) {
            return (
              <motion.div
                key={item.id}
                layoutId={item.id}
                onClick={() => onOpen(item)}
                className={`${cardClass} rounded-[32px] cursor-pointer bg-slate-900 transition-all duration-500`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ y: -5 }}
              >
                {/* 배경 이미지 */}
                <img 
                  src={item.image_url || `https://placehold.co/800x600/111/cyan?text=${item.category}`} 
                  className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 group-hover:scale-105 transition-all duration-700" 
                  alt={item.title} 
                />
                
                {/* 그라데이션 오버레이 */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent p-6 flex flex-col justify-end">
                  
                  {/* 상단 뱃지 영역 */}
                  <div className="absolute top-4 left-4 flex gap-2">
                     <span className="px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-[10px] font-black text-white uppercase border border-white/20 shadow-lg">
                      #{displayRank} {item.category}
                    </span>
                    {/* 키워드 뱃지 추가 */}
                    <span className="px-2 py-1 bg-cyan-500 rounded-full text-[10px] font-bold text-white uppercase shadow-lg">
                      {item.keyword}
                    </span>
                  </div>

                  {/* 텍스트 영역 */}
                  <h2 className={`${isHero ? 'text-2xl' : 'text-lg'} font-bold text-white leading-tight mb-2 line-clamp-2 drop-shadow-md`}>
                    {item.title}
                  </h2>
                  
                  {isHero && (
                    <p className="text-sm text-slate-300 line-clamp-2 mb-4 opacity-80 font-medium">
                      {item.summary}
                    </p>
                  )}

                  {/* 하단 액션 버튼 */}
                  <div className="flex justify-between items-end mt-2">
                     <div className="flex gap-4">
                        <span className="flex items-center gap-1.5 text-xs font-bold text-cyan-400">
                          <ThumbsUp size={14} className="fill-current"/> {item.likes}
                        </span>
                        <span className="flex items-center gap-1.5 text-xs font-bold text-pink-400 opacity-60">
                          <ThumbsDown size={14}/> {item.dislikes}
                        </span>
                     </div>
                     <button 
                       onClick={(e) => handleShare(e, item.title, item.link)}
                       className="p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors backdrop-blur-sm"
                     >
                        <Share2 size={16} />
                     </button>
                  </div>
                </div>
              </motion.div>
            );
          }

          // [B] List Style (리스트형)
          return (
            <motion.div
              key={item.id}
              onClick={() => onOpen(item)}
              className={`${cardClass} cursor-pointer group`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              {/* 썸네일 */}
              <div className="w-20 h-20 rounded-2xl bg-slate-100 overflow-hidden flex-shrink-0 relative">
                <img 
                  src={item.image_url || `https://placehold.co/100x100?text=${item.category}`} 
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
                  alt="" 
                />
                <div className="absolute top-0 left-0 bg-black/60 backdrop-blur-sm text-white text-[10px] font-black px-2 py-1 rounded-br-lg">
                  #{displayRank}
                </div>
              </div>
              
              {/* 콘텐츠 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-black text-cyan-600 dark:text-cyan-400 uppercase tracking-wide">
                    {item.category} • {item.keyword}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {new Date(item.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>
                <h3 className="font-bold text-slate-800 dark:text-slate-200 line-clamp-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1 mt-0.5">
                  {item.summary}
                </p>
              </div>

              {/* 우측 정보 */}
              <div className="flex flex-col items-end gap-2 pr-2">
                <span className="text-xs font-black text-slate-300 dark:text-slate-600">
                  {item.score.toFixed(1)}
                </span>
                
                <div className="flex gap-3 text-[10px] font-bold text-slate-400 items-center">
                  <span className="flex items-center gap-1 hover:text-cyan-500 transition-colors">
                    <ThumbsUp size={12}/> {item.likes}
                  </span>
                  <button 
                    onClick={(e) => handleShare(e, item.title, item.link)}
                    className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-400 hover:text-cyan-500 transition-colors"
                  >
                    <Share2 size={14} />
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

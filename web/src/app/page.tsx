'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, Star, ThumbsUp, ThumbsDown, X, 
  TrendingUp, Activity, Trophy, User 
} from 'lucide-react';

const CATEGORIES = [
  { label: 'All Trends', value: 'All' },
  { label: 'K-POP', value: 'k-pop' },
  { label: 'K-Drama', value: 'k-drama' },
  { label: 'K-Movie', value: 'k-movie' },
  { label: 'Variety', value: 'k-entertain' },
  { label: 'K-Culture', value: 'k-culture' }
];

export default function Home() {
  const [news, setNews] = useState<any[]>([]);
  const [category, setCategory] = useState('All');
  const [selectedArticle, setSelectedArticle] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    setLoading(true);
    const { data } = await supabase
      .from('live_news')
      .select('*')
      .order('rank', { ascending: true });
    if (data) setNews(data);
    setLoading(false);
  };

  const handleVote = async (id: string, type: 'likes' | 'dislikes', e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    await supabase.rpc('increment_vote', { row_id: id, col_name: type });
    setNews(prev => prev.map(item => 
      item.id === id ? { ...item, [type]: item[type] + 1 } : item
    ));
    if (selectedArticle?.id === id) {
      setSelectedArticle((prev: any) => ({ ...prev, [type]: prev[type] + 1 }));
    }
  };

  // [로직] 카테고리 필터링 및 카테고리 내 독립 순위 부여
  const filteredNews = category === 'All' 
    ? news 
    : news.filter((item) => item.category === category);

  const mostLikedNews = [...news].sort((a, b) => b.likes - a.likes).slice(0, 3);
  const mostDislikedNews = [...news].sort((a, b) => b.dislikes - a.dislikes).slice(0, 3);

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans selection:bg-cyan-100">
      <div className="max-w-7xl mx-auto px-4 py-6">
        
        {/* 헤더: web2.jpg 스타일 */}
        <header className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-fuchsia-500 rounded-lg flex items-center justify-center text-white font-black text-xl italic shadow-sm">K</div>
            <h1 className="text-2xl font-black tracking-tighter text-slate-900 uppercase">K-Enter 24</h1>
          </div>
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 px-3 py-1.5 bg-cyan-50 rounded-full border border-cyan-100 text-cyan-600 font-bold text-xs hover:bg-cyan-100 transition-colors">
              <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" /> Live System
            </button>
            <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 border border-white shadow-sm cursor-pointer hover:bg-slate-300 transition-all">
              <User size={20} />
            </div>
          </div>
        </header>

        {/* 카테고리 탭: Pill 스타일 */}
        <nav className="flex gap-2 overflow-x-auto pb-4 mb-6 scrollbar-hide">
          {CATEGORIES.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setCategory(tab.value)}
              className={`px-8 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap border ${
                category === tab.value 
                ? 'bg-cyan-400 text-white border-cyan-400 shadow-md shadow-cyan-100' 
                : 'bg-white text-slate-500 border-slate-100 hover:border-cyan-200 hover:text-cyan-500 shadow-sm'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* AI Insight 배너: 슬림 스타일 */}
        <div className="mb-8 px-6 py-3 bg-cyan-50 border border-cyan-100 rounded-2xl flex items-center gap-3">
          <Zap className="text-yellow-500 w-5 h-5 flex-shrink-0" />
          <p className="text-sm font-bold text-slate-700 italic leading-none">
            <span className="text-cyan-600 uppercase mr-2 font-black tracking-wider">AI Insight:</span>
            {news[0]?.insight || "Analyzing global K-Entertainment trends in real-time..."}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* 메인 벤토 그리드 피드 */}
          <div className="lg:col-span-8 space-y-8">
            {loading ? (
              <div className="h-96 flex items-center justify-center text-slate-300 font-black tracking-[1em]">LOADING...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {filteredNews.map((item, index) => {
                  // [중요] 카테고리 내 독립 순위 (displayRank)
                  const displayRank = index + 1;
                  const isHero = displayRank <= 2;
                  const isGrid = displayRank > 2 && displayRank <= 6;
                  
                  // 디자인 클래스 분기
                  const cardClass = isHero 
                    ? "md:col-span-2 aspect-[4/3] relative overflow-hidden group shadow-xl hover:shadow-2xl" 
                    : isGrid 
                      ? "md:col-span-1 aspect-square relative overflow-hidden group shadow-md hover:shadow-xl"
                      : "md:col-span-4 bg-white p-4 flex items-center gap-4 rounded-3xl border border-slate-100 hover:border-cyan-300 transition-all shadow-sm";

                  if (isHero || isGrid) {
                    return (
                      <motion.div
                        key={item.id}
                        layoutId={item.id}
                        onClick={() => setSelectedArticle(item)}
                        className={`${cardClass} rounded-[32px] cursor-pointer bg-slate-900 transition-all duration-500`}
                      >
                        <img 
                          src={item.image_url || `https://placehold.co/800x600/111/cyan?text=${item.category}`} 
                          className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 group-hover:scale-105 transition-all duration-700" 
                          alt={item.title} 
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent p-6 flex flex-col justify-end">
                          <div className="flex justify-between items-start mb-2">
                            <span className="px-3 py-1 bg-white/20 backdrop-blur-md rounded-lg text-[10px] font-black text-white uppercase border border-white/20">#{displayRank} {item.category}</span>
                            <span className="px-2 py-1 bg-cyan-400 rounded-lg text-[10px] font-black text-white uppercase shadow-lg">Score {item.score}</span>
                          </div>
                          <h2 className={`${isHero ? 'text-2xl' : 'text-lg'} font-bold text-white leading-tight mb-2 line-clamp-2`}>{item.title}</h2>
                          {isHero && <p className="text-sm text-slate-300 line-clamp-2 mb-4 opacity-80">{item.summary}</p>}
                          <div className="flex gap-4 mt-2">
                             <span className="flex items-center gap-1 text-xs font-bold text-cyan-400"><ThumbsUp size={14}/> {item.likes}</span>
                             <span className="flex items-center gap-1 text-xs font-bold text-pink-400"><ThumbsDown size={14}/> {item.dislikes}</span>
                          </div>
                        </div>
                      </motion.div>
                    );
                  }

                  // Rank 7+ (List Style)
                  return (
                    <motion.div
                      key={item.id}
                      onClick={() => setSelectedArticle(item)}
                      className={`${cardClass} cursor-pointer group`}
                    >
                      <div className="w-20 h-20 rounded-2xl bg-slate-100 overflow-hidden flex-shrink-0 relative">
                        <img src={item.image_url} className="w-full h-full object-cover" alt="" />
                        <div className="absolute top-0 left-0 bg-black/50 text-white text-[8px] font-bold px-1.5 py-0.5 rounded-br-lg">#{displayRank}</div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] font-black text-cyan-500 uppercase">{item.category}</span>
                          <span className="text-[10px] text-slate-400">• {new Date(item.created_at).getHours()} hours ago</span>
                        </div>
                        <h3 className="font-bold text-slate-800 line-clamp-1 group-hover:text-cyan-500 transition-colors">{item.title}</h3>
                        <p className="text-xs text-slate-500 line-clamp-1">{item.summary}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2 pr-2">
                        <span className="text-xs font-black text-yellow-500">★ {item.score}</span>
                        <div className="flex gap-3 text-[10px] font-bold text-slate-400">
                          <span className="flex items-center gap-0.5"><ThumbsUp size={10}/> {item.likes}</span>
                          <span className="flex items-center gap-0.5"><ThumbsDown size={10}/> {item.dislikes}</span>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 사이드바 영역: web2.jpg 스타일 */}
          <aside className="lg:col-span-4 space-y-6">
            
            {/* 1. Trending Keywords: Tag Cloud Style */}
            <section className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-sm">
              <div className="flex items-center gap-2 mb-6">
                <TrendingUp size={18} className="text-orange-500" />
                <h3 className="font-black text-slate-800 uppercase tracking-wider text-sm">Trending Keywords</h3>
              </div>
              <div className="flex flex-wrap justify-center gap-x-4 gap-y-2">
                {[
                  { tag: '#SquidGame2', size: 'text-2xl', color: 'text-cyan-500' },
                  { tag: '#NewJeans', size: 'text-xl', color: 'text-orange-400' },
                  { tag: '#IVE', size: 'text-lg', color: 'text-pink-400' },
                  { tag: '#SongKang', size: 'text-base', color: 'text-green-500' },
                  { tag: '#BusanFilmFest', size: 'text-sm', color: 'text-purple-400' }
                ].map(item => (
                  <span key={item.tag} className={`${item.size} ${item.color} font-black cursor-pointer hover:scale-110 transition-transform`}>{item.tag}</span>
                ))}
              </div>
            </section>

            {/* 2. Live Vibe Check: Horizontal Bar Style */}
            <section className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-sm">
              <div className="flex items-center gap-2 mb-6">
                <Activity size={18} className="text-cyan-500" />
                <h3 className="font-black text-slate-800 uppercase tracking-wider text-sm">AI Vibe Check (Global)</h3>
              </div>
              <div className="space-y-6">
                {[
                  { label: 'Excitement', val: 75, color: 'bg-cyan-400', icon: '⚡' },
                  { label: 'Shock', val: 15, color: 'bg-yellow-400', icon: '⚠️' },
                  { label: 'Sadness', val: 10, color: 'bg-orange-400', icon: '😢' }
                ].map(stat => (
                  <div key={stat.label}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
                        <span className="grayscale">{stat.icon}</span> {stat.label}
                      </span>
                      <span className="text-sm font-black text-slate-800">{stat.val}%</span>
                    </div>
                    <div className="h-2.5 bg-slate-50 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }} 
                        animate={{ width: `${stat.val}%` }} 
                        className={`h-full ${stat.color} shadow-[0_0_10px_rgba(34,211,238,0.2)]`} 
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* 3. Most Liked Section */}
            <section className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-sm">
              <div className="flex items-center gap-2 mb-4 text-cyan-500">
                <Trophy size={18} />
                <h3 className="font-black text-slate-800 uppercase tracking-wider text-sm">Top Voted</h3>
              </div>
              <div className="space-y-4">
                {mostLikedNews.map(m => (
                  <div key={m.id} className="group cursor-pointer">
                    <p className="text-xs font-bold text-slate-700 line-clamp-2 group-hover:text-cyan-500 transition-colors mb-1">{m.title}</p>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black text-cyan-400">👍 {m.likes} Likes</span>
                      <span className="text-[10px] text-slate-300 font-bold uppercase">{m.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </div>

      {/* 상세 모달: Glassmorphism 스타일 */}
      <AnimatePresence>
        {selectedArticle && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-white/60 backdrop-blur-xl">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }} 
              animate={{ scale: 1, opacity: 1 }} 
              exit={{ scale: 0.95, opacity: 0 }} 
              className="bg-white border border-slate-200 p-8 md:p-12 rounded-[48px] max-w-2xl w-full relative shadow-[0_40px_100px_rgba(0,0,0,0.1)]"
            >
              <button onClick={() => setSelectedArticle(null)} className="absolute top-10 right-10 text-slate-300 hover:text-slate-900 transition-colors"><X size={32}/></button>
              
              <div className="mb-10">
                <div className="flex items-center gap-2 mb-4">
                   <span className="px-3 py-1 bg-cyan-100 text-cyan-600 text-[10px] font-black rounded-full uppercase tracking-widest">#{selectedArticle.rank} {selectedArticle.category}</span>
                   <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Global Archive</span>
                </div>
                <h2 className="text-3xl md:text-4xl font-black text-slate-900 leading-tight tracking-tight">{selectedArticle.title}</h2>
              </div>

              <div className="text-slate-600 text-lg leading-relaxed mb-10 max-h-[30vh] overflow-y-auto pr-4 custom-scrollbar">
                {selectedArticle.summary}
              </div>

              <div className="flex flex-col gap-6 p-8 bg-slate-50 rounded-[40px] border border-slate-100">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <Star className="text-yellow-400 fill-current w-10 h-10" /> 
                    <div className="flex flex-col">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">AI Chief Editor Score</span>
                      <span className="text-4xl font-black text-slate-900">{selectedArticle.score}</span>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <button onClick={() => handleVote(selectedArticle.id, 'likes')} className="w-16 h-16 rounded-3xl bg-white flex flex-col items-center justify-center gap-1 shadow-sm hover:shadow-md hover:bg-cyan-50 transition-all text-cyan-500">
                      <ThumbsUp size={24}/>
                      <span className="text-[10px] font-bold">{selectedArticle.likes}</span>
                    </button>
                    <button onClick={() => handleVote(selectedArticle.id, 'dislikes')} className="w-16 h-16 rounded-3xl bg-white flex flex-col items-center justify-center gap-1 shadow-sm hover:shadow-md hover:bg-pink-50 transition-all text-pink-500">
                      <ThumbsDown size={24}/>
                      <span className="text-[10px] font-bold">{selectedArticle.dislikes}</span>
                    </button>
                  </div>
                </div>
                <a 
                  href={selectedArticle.link} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="block text-center py-5 bg-slate-900 rounded-3xl font-black text-sm uppercase tracking-[0.3em] text-white hover:bg-cyan-500 transition-all shadow-xl shadow-slate-200"
                >
                  Visit Source Link
                </a>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

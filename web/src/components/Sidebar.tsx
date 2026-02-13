'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import KeywordTicker from './KeywordTicker';
import VibeCheck from './VibeCheck';
import RankingItem from './RankingItem';
import { Trophy, Flame, Music, Film, Tv, MapPin } from 'lucide-react';

interface SidebarProps {
  news: any[];
  category: string;
}

export default function Sidebar({ news, category }: SidebarProps) {
  const [rankings, setRankings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchRankings = async () => {
      const targetCategory = category === 'All' ? 'K-Pop' : category;
      
      if (!['K-Pop', 'K-Drama', 'K-Movie', 'K-Entertain', 'K-Culture'].includes(targetCategory)) {
          setRankings([]); 
          return;
      }

      setLoading(true);
      const { data, error } = await supabase
        .from('trending_rankings')
        .select('*')
        .eq('category', targetCategory)
        .order('rank', { ascending: true })
        .limit(5);

      if (!error && data) {
        setRankings(data);
      } else {
        setRankings([]);
      }
      setLoading(false);
    };

    fetchRankings();
  }, [category]);

  const getHeaderInfo = () => {
    switch (category) {
      case 'K-Pop': return { title: 'Daily Music Chart', icon: <Music size={18} /> };
      case 'K-Drama': return { title: 'Global Streaming Top 5', icon: <Tv size={18} /> };
      case 'K-Movie': return { title: 'Box Office Ranking', icon: <Film size={18} /> };
      case 'K-Entertain': return { title: 'Variety Show Buzz', icon: <Flame size={18} /> };
      case 'K-Culture': return { title: "What's Hot in Korea?", icon: <MapPin size={18} /> };
      default: return { title: 'Top Voted News', icon: <Trophy size={18} /> };
    }
  };

  const headerInfo = getHeaderInfo();
  const topLiked = [...news].sort((a, b) => (b.likes || 0) - (a.likes || 0)).slice(0, 3);

  return (
    <aside className="lg:col-span-4 space-y-6">
      
      {/* [위치 변경] 1. 카테고리 랭킹 섹션을 맨 위로 올림! */}
      {category !== 'All' && (
        <section className="bg-white dark:bg-slate-900 rounded-[32px] p-6 border border-slate-100 dark:border-slate-800 shadow-sm animate-in fade-in slide-in-from-right-4 duration-500">
          <div className="flex items-center gap-2 mb-4 text-cyan-600 dark:text-cyan-400 border-b border-slate-50 dark:border-slate-800 pb-3">
            {headerInfo.icon}
            <h3 className="font-black uppercase tracking-wider text-sm">
              {headerInfo.title}
            </h3>
          </div>
          
          <div className="space-y-1">
            {loading ? (
               <div className="text-center py-8 text-xs text-slate-400">Loading charts...</div>
            ) : rankings.length > 0 ? (
               rankings.map((item) => (
                 <RankingItem key={item.id} rank={item.rank} item={item} />
               ))
            ) : (
               <div className="text-center py-6 text-xs text-slate-400 italic">
                 No ranking data yet.<br/>(Check DB connection)
               </div>
            )}
          </div>
        </section>
      )}

      {/* 2. Hot Keywords (이제 두 번째로 내려옴) */}
      <KeywordTicker />

      {/* 3. AI Vibe Check */}
      <VibeCheck />
      
      {/* 4. Top Voted News */}
      <section className="bg-white dark:bg-slate-900 rounded-[32px] p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
        <div className="flex items-center gap-2 mb-6 text-cyan-500">
          <Trophy size={18} className="fill-current" />
          <h3 className="font-black text-slate-800 dark:text-slate-200 uppercase tracking-wider text-sm">
            Top Voted News
          </h3>
        </div>
        
        <div className="space-y-4">
          {topLiked.length > 0 ? (
            topLiked.map((m, idx) => (
              <div key={m.id} className="group cursor-pointer border-b border-slate-50 dark:border-slate-800 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-black text-slate-300 uppercase">Top 0{idx + 1}</span>
                  <span className="text-[10px] font-bold text-cyan-500 uppercase">{m.category}</span>
                </div>
                <p className="text-sm font-bold text-slate-700 dark:text-slate-300 line-clamp-2 group-hover:text-cyan-500 transition-colors mb-2">
                  {m.title}
                </p>
                <div className="flex items-center gap-3">
                    <span className="text-[10px] font-black text-cyan-600 bg-cyan-50 dark:bg-cyan-900/30 px-2 py-0.5 rounded-md">
                      👍 {m.likes} Likes
                    </span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400 text-center py-4 italic">No votes yet...</p>
          )}
        </div>
      </section>
    </aside>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

import Header from '@/components/Header';
import CategoryNav from '@/components/CategoryNav';
import InsightBanner from '@/components/InsightBanner';
import NewsFeed from '@/components/NewsFeed';
import Sidebar from '@/components/Sidebar';
import ArticleModal from '@/components/ArticleModal';
import MobileFloatingBtn from '@/components/MobileFloatingBtn';

export default function Home() {
  const [news, setNews] = useState<any[]>([]);
  const [category, setCategory] = useState('All');
  const [selectedArticle, setSelectedArticle] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isTranslating, setIsTranslating] = useState(false);

  useEffect(() => { fetchNews(); }, []);

  const fetchNews = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('live_news')
      .select('*')
      .order('score', { ascending: false });
      
    if (data && !error) { setNews(data); }
    setLoading(false);
  };

  // [추가] AI 실시간 번역 이벤트 리스너
  useEffect(() => {
    const handleTranslate = async (e: any) => {
      const targetLang = e.detail;
      if (isTranslating || news.length === 0) return;

      setIsTranslating(true);
      alert(`AI is translating your feed into [${targetLang}]...`);

      try {
        // 현재 뉴스 리스트의 요약본을 번역 API로 전송
        const translatedNews = await Promise.all(news.map(async (item) => {
          const res = await fetch('/api/translate', {
            method: 'POST',
            body: JSON.stringify({ text: item.summary, targetLang }),
          });
          const data = await res.json();
          return { ...item, summary: data.translatedText || item.summary };
        }));

        setNews(translatedNews);
      } catch (err) {
        console.error("Translation failed", err);
      } finally {
        setIsTranslating(false);
      }
    };

    window.addEventListener('ai-translate', handleTranslate);
    return () => window.removeEventListener('ai-translate', handleTranslate);
  }, [news, isTranslating]);

  const handleVote = async (id: string, type: 'likes' | 'dislikes') => {
    await supabase.rpc('increment_vote', { row_id: id, col_name: type });
    setNews(prev => prev.map(item => item.id === id ? { ...item, [type]: item[type] + 1 } : item));
    if (selectedArticle?.id === id) {
      setSelectedArticle((prev: any) => ({ ...prev, [type]: prev[type] + 1 }));
    }
  };

  const getFilteredNews = () => {
    if (category === 'All') {
      return [...news].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 30);
    } else {
      return news.filter(n => n.category === category).sort((a, b) => (a.rank || 99) - (b.rank || 99)).slice(0, 30);
    }
  };

  const filteredNews = getFilteredNews();

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans dark:bg-slate-950 dark:text-slate-200 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
        <Header />
        <CategoryNav active={category} setCategory={setCategory} />
        <InsightBanner insight={filteredNews[0]?.insight} />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mt-8">
          <div className="col-span-1 md:col-span-3">
            <NewsFeed news={filteredNews} loading={loading || isTranslating} onOpen={setSelectedArticle} />
          </div>
          <div className="hidden md:block col-span-1">
            <Sidebar news={news} />
          </div>
        </div>
      </div>
      <ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} onVote={handleVote} />
      <MobileFloatingBtn />
    </main>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import Header from '@/components/Header';
import CategoryNav from '@/components/CategoryNav';
import InsightBanner from '@/components/InsightBanner';
import NewsFeed from '@/components/NewsFeed';
import Sidebar from '@/components/Sidebar';
import ArticleModal from '@/components/ArticleModal';

export default function Home() {
  const [news, setNews] = useState<any[]>([]);
  const [category, setCategory] = useState('All');
  const [selectedArticle, setSelectedArticle] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // 데이터 로드
  useEffect(() => { fetchNews(); }, []);

  const fetchNews = async () => {
    setLoading(true);
    // 사이드바의 통계와 전체 랭킹 분석을 위해 모든 기사(최대 200개)를 가져옵니다.
    const { data, error } = await supabase
      .from('live_news')
      .select('*')
      .order('rank', { ascending: true });
    
    if (data && !error) {
      setNews(data);
    }
    setLoading(false);
  };

  // 투표 로직
  const handleVote = async (id: string, type: 'likes' | 'dislikes') => {
    await supabase.rpc('increment_vote', { row_id: id, col_name: type });
    
    // 리스트 상태 즉시 반영
    setNews(prev => prev.map(item => 
      item.id === id ? { ...item, [type]: item[type] + 1 } : item
    ));

    // 상세 팝업 상태 즉시 반영
    if (selectedArticle?.id === id) {
      setSelectedArticle((prev: any) => ({ ...prev, [type]: prev[type] + 1 }));
    }
  };

  /**
   * [필터링 로직]
   * 메인 피드에는 사용자가 선택한 카테고리의 상위 30개만 보여줍니다.
   */
  const filteredNews = (category === 'All' 
    ? news 
    : news.filter(n => n.category === category)
  ).slice(0, 30);

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans overflow-x-hidden">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* 1. 헤더 (로고 & 로그인) */}
        <Header />

        {/* 2. 네비게이션 (K-Entertain 포함) */}
        <CategoryNav active={category} setCategory={setCategory} />
        
        {/* 3. AI 인사이트 배너 */}
        <InsightBanner insight={news[0]?.insight} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* 4. 메인 뉴스 피드 (Top 30) */}
          <NewsFeed 
            news={filteredNews} 
            loading={loading} 
            onOpen={setSelectedArticle} 
          />

          {/* 5. 사이드바 (여기에 키워드, 바이브, 투표가 모두 들어있어야 합니다) */}
          <Sidebar news={news} />
        </div>
      </div>

      {/* 6. 기사 상세 모달 */}
      <ArticleModal 
        article={selectedArticle} 
        onClose={() => setSelectedArticle(null)} 
        onVote={handleVote} 
      />
    </div>
  );
}

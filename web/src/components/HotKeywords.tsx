'use client';

import { useState, useEffect } from 'react';
import { createClient } from '@/utils/supabase/client';

export default function HotKeywords() {
  const [keywords, setKeywords] = useState<{ text: string; count: number }[]>([]);
  const supabase = createClient();

  useEffect(() => {
    const fetchKeywords = async () => {
      const { data } = await supabase
        .from('live_news')
        .select('keywords')
        .eq('is_published', true);

      if (data) {
        const allTags = data.flatMap(item => item.keywords || []);
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
    <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 h-full shadow-lg">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        🔥 Real-Time Keywords <span className="text-xs text-cyan-500 font-normal">Ranked by AI</span>
      </h3>
      <div className="space-y-4">
        {keywords.length > 0 ? (
          keywords.map((item, idx) => (
            <div key={idx} className="group">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-300 font-medium">
                  <span className="text-cyan-400 mr-2">{idx + 1}.</span> {item.text}
                </span>
                <span className="text-gray-500 text-xs">AI Impact: {item.count * 10}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2.5 rounded-full transition-all duration-1000" 
                  style={{ width: `${Math.min(item.count * 10, 100)}%` }}
                ></div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-500 text-sm animate-pulse">Analyzing latest trends...</p>
        )}
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

const DEFAULT_VIBE = { excitement: 33, shock: 33, sadness: 34 };

export default function VibeCheck() {
  const [vibe, setVibe] = useState(DEFAULT_VIBE);
  const supabase = createClientComponentClient();

  useEffect(() => {
    const fetchVibe = async () => {
      const { data } = await supabase
        .from('live_news')
        .select('vibe')
        .eq('is_published', true)
        .order('created_at', { ascending: false })
        .limit(1)
        .single();
      
      if (data?.vibe) setVibe(data.vibe);
    };
    fetchVibe();
  }, [supabase]);

  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 h-full flex flex-col justify-center">
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        🔮 AI Vibe Check <span className="text-xs text-gray-500 font-normal">(Sentiment Analysis)</span>
      </h3>
      
      <div className="space-y-6">
        {/* Excitement */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-pink-400 font-bold">🤩 Excitement</span>
            <span className="text-white">{vibe.excitement}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
            <div className="bg-gradient-to-r from-pink-500 to-purple-600 h-full rounded-full transition-all duration-1000" style={{ width: `${vibe.excitement}%` }}></div>
          </div>
        </div>

        {/* Shock */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-yellow-400 font-bold">⚡ Shock / Buzz</span>
            <span className="text-white">{vibe.shock}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
            <div className="bg-gradient-to-r from-yellow-400 to-orange-500 h-full rounded-full transition-all duration-1000" style={{ width: `${vibe.shock}%` }}></div>
          </div>
        </div>

        {/* Sadness */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-blue-400 font-bold">💧 Sadness / Serious</span>
            <span className="text-white">{vibe.sadness}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
            <div className="bg-gradient-to-r from-cyan-400 to-blue-600 h-full rounded-full transition-all duration-1000" style={{ width: `${vibe.sadness}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}

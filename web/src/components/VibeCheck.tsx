'use client';
import { Activity } from 'lucide-react';
import { motion } from 'framer-motion';

export default function VibeCheck() {
  // 실전에서는 DB의 reactions 데이터를 계산해서 넣습니다.
  const stats = [
    { label: 'Excitement', val: 75, color: 'bg-cyan-400', icon: '⚡' },
    { label: 'Shock', val: 15, color: 'bg-yellow-400', icon: '⚠️' },
    { label: 'Sadness', val: 10, color: 'bg-orange-400', icon: '😢' }
  ];

  return (
    <section className="bg-white rounded-[32px] p-8 border border-slate-100 shadow-sm">
      <div className="flex items-center gap-2 mb-6">
        <Activity size={18} className="text-cyan-500" />
        <h3 className="font-black text-slate-800 uppercase tracking-wider text-sm">AI Vibe Check</h3>
      </div>
      <div className="space-y-6">
        {stats.map(stat => (
          <div key={stat.label}>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
                {stat.icon} {stat.label}
              </span>
              <span className="text-sm font-black text-slate-800">{stat.val}%</span>
            </div>
            <div className="h-2.5 bg-slate-50 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }} 
                animate={{ width: `${stat.val}%` }} 
                className={`h-full ${stat.color}`} 
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

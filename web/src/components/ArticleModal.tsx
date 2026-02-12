'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Star, ThumbsUp, ThumbsDown } from 'lucide-react';

export default function ArticleModal({ article, onClose, onVote }: any) {
  return (
    <AnimatePresence>
      {article && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-white/60 backdrop-blur-xl">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="bg-white border border-slate-200 p-8 md:p-12 rounded-[48px] max-w-2xl w-full relative shadow-2xl">
            <button onClick={onClose} className="absolute top-10 right-10 text-slate-300 hover:text-slate-900"><X size={32}/></button>
            <div className="mb-10">
              <span className="px-3 py-1 bg-cyan-100 text-cyan-600 text-[10px] font-black rounded-full uppercase">#{article.rank} {article.category}</span>
              <h2 className="text-3xl font-black text-slate-900 mt-4 leading-tight">{article.title}</h2>
            </div>
            <div className="text-slate-600 text-lg leading-relaxed mb-10 max-h-[30vh] overflow-y-auto pr-4">{article.summary}</div>
            <div className="flex flex-col gap-6 p-8 bg-slate-50 rounded-[40px] border border-slate-100">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3"><Star className="text-yellow-400 fill-current w-10 h-10" /><span className="text-4xl font-black">{article.score}</span></div>
                <div className="flex gap-4">
                  <button onClick={() => onVote(article.id, 'likes')} className="w-16 h-16 rounded-3xl bg-white flex flex-col items-center justify-center text-cyan-500 shadow-sm hover:shadow-md"><ThumbsUp size={24}/><span>{article.likes}</span></button>
                  <button onClick={() => onVote(article.id, 'dislikes')} className="w-16 h-16 rounded-3xl bg-white flex flex-col items-center justify-center text-pink-500 shadow-sm hover:shadow-md"><ThumbsDown size={24}/><span>{article.dislikes}</span></button>
                </div>
              </div>
              <a href={article.link} target="_blank" className="block text-center py-5 bg-slate-900 rounded-3xl font-black text-white hover:bg-cyan-500 transition-all">Visit Source Link</a>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

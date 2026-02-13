'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { 
  User, LogOut, Settings, ChevronDown, 
  ShieldCheck, Sun, Moon, Languages 
} from 'lucide-react';

export default function Header() {
  const [user, setUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [langCode, setLangCode] = useState('EN'); 

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user));
    
    // 다크모드 초기화
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }

    // 브라우저 언어 감지
    const browserLang = navigator.language.split('-')[0].toUpperCase();
    setLangCode(browserLang); // KO, EN 등 실제 코드 유지

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  const toggleDarkMode = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    if (newDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  const handleAiTranslate = () => {
    // EN일 때도 작동하게 하거나 사용자에게 알림을 줍니다.
    console.log("Translation requested for:", langCode);
    window.dispatchEvent(new CustomEvent('ai-translate', { detail: langCode }));
    alert(`AI Translation to [${langCode}] started!`); // 동작 확인용
  };

  const handleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/callback` },
    });
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setMenuOpen(false);
  };

  return (
    // mb-6을 mb-2로 수정하여 하단 banner와의 간격을 줄임
    <header className="flex justify-between items-center mb-2 py-2 border-b border-slate-100 dark:border-slate-800 transition-colors">
      <div className="flex items-center gap-2 sm:gap-4">
        <div className="w-[120px] sm:w-[140px] h-[60px] flex items-center justify-center overflow-hidden">
          <img src="/logo.png" alt="Logo" className="w-full h-full object-contain" />
        </div>
        
        <div className="flex flex-col ml-1 sm:ml-2 border-l border-slate-200 dark:border-slate-700 pl-2 sm:pl-3">
             <div className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                <span className="text-[9px] sm:text-[10px] font-black text-cyan-500 uppercase tracking-tighter">Live</span>
             </div>
             <span className="text-[10px] sm:text-[11px] font-bold text-slate-400 dark:text-slate-500 leading-none mt-0.5 whitespace-nowrap uppercase">
               1,240 Monitoring
             </span>
        </div>
      </div>

      <div className="flex items-center gap-2 relative">
        {/* 다크모드 토글 버튼 */}
        <button 
          onClick={(e) => { e.preventDefault(); toggleDarkMode(); }} 
          className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors"
        >
          {isDark ? <Sun size={20} className="text-yellow-500" /> : <Moon size={20} />}
        </button>

        {/* 언어 설정 버튼 */}
        <button 
          onClick={(e) => { e.preventDefault(); handleAiTranslate(); }}
          className="px-3 py-1.5 bg-cyan-50 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400 rounded-full flex items-center gap-2 border border-cyan-100 dark:border-cyan-800 transition-all hover:scale-105 active:scale-95"
        >
          <Languages size={18} />
          <span className="text-[11px] font-black uppercase">{langCode}</span>
        </button>

        <div className="h-4 w-[1px] bg-slate-200 dark:bg-slate-700 mx-1 hidden sm:block" />

        {user ? (
          <div className="relative">
            <button onClick={() => setMenuOpen(!menuOpen)} className="flex items-center gap-2 px-2 py-1.5 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-full shadow-sm">
              <div className="w-7 h-7 rounded-full bg-slate-100 overflow-hidden">
                {user.user_metadata?.avatar_url ? <img src={user.user_metadata.avatar_url} alt="profile" /> : <User size={16} />}
              </div>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {menuOpen && (
              <div className="absolute right-0 mt-3 w-56 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-[24px] shadow-xl z-[100] p-2">
                <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl">
                  <LogOut size={18} /> Log Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <button onClick={handleLogin} className="px-5 py-2 text-sm font-black text-white bg-slate-900 dark:bg-cyan-600 rounded-full hover:shadow-lg transition-all">
            Sign In
          </button>
        )}
      </div>
    </header>
  );
}

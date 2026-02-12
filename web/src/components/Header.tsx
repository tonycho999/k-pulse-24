'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase'; // 1. 공용 인스턴스 사용 (createClient 제거)
import { User, LogOut, Settings, ChevronDown, ShieldCheck } from 'lucide-react';

export default function Header() {
  const [user, setUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);
    };
    getUser();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

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
    <header className="flex justify-between items-center mb-8 py-4">
      {/* 2. 로고 영역: logo.png 적용 및 디자인 변경 */}
      <div className="flex items-center gap-3 group cursor-pointer">
        <div className="w-10 h-10 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center justify-center group-hover:shadow-md transition-all">
          <img src="/logo.png" alt="K-ENTER 24 Logo" className="w-8 h-8 object-contain" />
        </div>
        <div className="flex flex-col">
          <h1 className="text-xl font-black tracking-tighter text-slate-900 leading-none">
            K-ENTER <span className="text-cyan-500">24</span>
          </h1>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">
            AI Curation Service
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4 relative">
        {user ? (
          <div className="relative">
            {/* 로그인 상태: web2.jpg 스타일의 사용자 버튼 */}
            <button 
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-100 rounded-full hover:border-cyan-200 hover:shadow-sm transition-all group"
            >
              <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 overflow-hidden border border-white">
                {user.user_metadata?.avatar_url ? (
                  <img src={user.user_metadata.avatar_url} alt="profile" />
                ) : (
                  <User size={16} />
                )}
              </div>
              <span className="text-xs font-bold text-slate-700 max-w-[80px] truncate">
                {user.email?.split('@')[0]}
              </span>
              <ChevronDown size={14} className={`text-slate-300 transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* 드롭다운 메뉴: 라이트 테마 & 부드러운 그림자 */}
            {menuOpen && (
              <div className="absolute right-0 mt-3 w-56 bg-white border border-slate-100 rounded-[24px] shadow-xl shadow-slate-200/50 overflow-hidden z-[100] p-2">
                <div className="px-4 py-3 bg-slate-50 rounded-2xl mb-1">
                  <div className="flex items-center gap-2 mb-1">
                    <ShieldCheck size={14} className="text-cyan-500" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Account Status</span>
                  </div>
                  <p className="text-sm font-black text-slate-800 tracking-tight">Standard Member</p>
                </div>

                <div className="py-1">
                  <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-50 rounded-xl transition-colors">
                    <Settings size={18} className="text-slate-400" />
                    Settings
                  </button>
                  <button 
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                  >
                    <LogOut size={18} />
                    Log Out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* 비로그인 상태: web2.jpg 스타일의 로그인 버튼 */
          <button 
            onClick={handleLogin}
            className="px-6 py-2.5 text-sm font-black text-white bg-slate-900 rounded-full hover:bg-cyan-500 hover:shadow-lg hover:shadow-cyan-100 transition-all active:scale-95"
          >
            Sign In
          </button>
        )}
      </div>
    </header>
  );
}

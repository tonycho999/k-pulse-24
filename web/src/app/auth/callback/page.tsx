'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';

// 1. 실제 로직을 수행하는 내부 컴포넌트
function AuthContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('Processing login...');

  useEffect(() => {
    const handleAuth = async () => {
      // A. URL에 'code'가 있는지 확인 (PKCE 방식 - 최신 Supabase)
      const code = searchParams.get('code');
      
      if (code) {
        setStatus('Verifying security code...');
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (!error) {
          router.push('/'); 
          return;
        }
      }

      // B. URL에 'access_token'이 있는지 확인 (Implicit 방식 - 구형)
      if (typeof window !== 'undefined') {
        const hash = window.location.hash;
        if (hash && hash.includes('access_token')) {
          setStatus('Verifying token...');
          // access_token은 supabase가 자동으로 감지하여 세션을 맺습니다.
        }
      }

      // C. 세션 최종 확인
      // 잠시 대기 후 세션 확인 (토큰 처리 시간 확보)
      setTimeout(async () => {
          const { data: { session } } = await supabase.auth.getSession();
          if (session) {
            router.push('/');
          } else {
            const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
              if (event === 'SIGNED_IN' || session) {
                router.push('/');
              }
            });
            return () => subscription.unsubscribe();
          }
      }, 500);
    };

    handleAuth();
  }, [router, searchParams]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 border-4 border-slate-200 border-t-cyan-500 rounded-full animate-spin"></div>
      <p className="text-slate-500 font-bold text-sm animate-pulse">{status}</p>
    </div>
  );
}

// 2. 메인 페이지 컴포넌트 (Suspense로 감싸서 빌드 에러 방지)
export default function AuthCallback() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white dark:bg-slate-950">
      <Suspense fallback={
        <div className="flex flex-col items-center gap-4">
           <div className="w-12 h-12 border-4 border-slate-200 border-t-cyan-500 rounded-full animate-spin"></div>
           <p className="text-slate-500 font-bold text-sm">Loading authentication...</p>
        </div>
      }>
        <AuthContent />
      </Suspense>
    </div>
  );
}

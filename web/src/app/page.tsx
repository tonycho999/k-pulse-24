import { supabase } from '@/lib/supabase';
import HomeClient from '@/components/HomeClient';

// 👇 60초마다 ISR (데이터 갱신)
export const revalidate = 60;

export default async function Page() {
  // 1. 서버 사이드에서 뉴스 데이터 가져오기
  // [수정 포인트] score 내림차순 -> rank 오름차순 (1위가 맨 앞으로 오게)
  const { data: news, error } = await supabase
    .from('live_news')
    .select('*')
    .order('rank', { ascending: true }); // 1위부터 순서대로 가져옴

  if (error) {
    console.error('Failed to fetch news:', error);
  }

  // 2. 가져온 데이터를 클라이언트 컴포넌트에 전달
  return <HomeClient initialNews={news || []} />;
}

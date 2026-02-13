import { MetadataRoute } from 'next';
import { supabase } from '@/lib/supabase'; // (선택) 나중에 뉴스 기사별로도 만들 수 있음

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://k-enter24.com';

  // 1. 고정 페이지들
  const routes = [
    '',
    '/auth/login',
    // 필요한 페이지가 더 있다면 추가
  ].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 1,
  }));

  // (심화) 나중에 뉴스 기사 1000개도 구글에 각각 노출하고 싶다면 여기서 DB를 불러와서 추가하면 됩니다.
  // 지금은 메인 페이지만 잘 긁어가도 충분합니다.

  return [...routes];
}

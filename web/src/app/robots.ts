import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: '/private/', // (선택) 봇이 접근하면 안 되는 경로
    },
    sitemap: 'https://k-enter24.com/sitemap.xml',
  };
}

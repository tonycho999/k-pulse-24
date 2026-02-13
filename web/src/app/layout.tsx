import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

// [SEO] 구글 검색 노출을 위한 메타데이터
export const metadata: Metadata = {
  title: 'K-ENTER 24 | Real-time K-Pop & K-Drama News',
  description: 'The world\'s fastest source for K-Entertainment news. Monitoring 1,200+ articles daily in real-time. BTS, BLACKPINK, NewJeans updates instantly.',
  keywords: ['K-Pop', 'K-Drama', 'Korean News', 'Real-time News', 'BTS', 'BLACKPINK', 'NewJeans'],
  openGraph: {
    title: 'K-ENTER 24',
    description: 'Real-time K-News Radar. Stop waiting for translations.',
    url: 'https://k-enter24.com',
    siteName: 'K-ENTER 24',
    images: [
      {
        url: '/og-image.png', // public 폴더에 대표 이미지 하나 넣어주시면 좋습니다.
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html >
  );
}

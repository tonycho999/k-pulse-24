import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: ['placehold.co', 'i.namu.wiki', 'wallpapercave.com', 'ssl.pstatic.net', 'imgnews.pstatic.net'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
};

export default nextConfig;

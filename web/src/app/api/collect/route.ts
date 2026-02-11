import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import Groq from 'groq-sdk';
import { google } from 'googleapis';

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!);
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const customSearch = google.customsearch('v1');

const preciseDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function GET(request: Request) {
  const now = new Date();
  const mins = now.getMinutes();
  const hour = now.getHours();

  try {
    // ---------------------------------------------------------
    // PHASE 1: 뉴스 스크랩 (00:01 ~ 00:05 사이 랜덤 시작)
    // ---------------------------------------------------------
    if (mins >= 1 && mins <= 5) {
      const msDelay = Math.random() * 240000; 
      await preciseDelay(msDelay);

      // 정교한 쿼리: 주제어 랜덤 선정 + 노이즈 제거 (SNS, 유튜브 제외)
      const topics = ["comeback", "debut", "world tour", "billboard", "official announcement"];
      const topic = topics[Math.floor(Math.random() * topics.length)];
      const refinedQuery = `K-POP (idol OR group) "${topic}" -site:youtube.com -site:instagram.com -site:twitter.com -site:facebook.com`;

      const res = await customSearch.cse.list({
        auth: process.env.GOOGLE_SEARCH_API_KEY,
        cx: process.env.GOOGLE_SEARCH_ENGINE_ID,
        q: refinedQuery,
        dateRestrict: 'd1', // 전날 00:00 ~ 23:00 대상 (24시간 이내)
        num: 10,
        sort: 'date'
      });

      const items = res.data.items || [];
      for (const item of items) {
        await supabase.from('raw_news').upsert({
          link: item.link,
          title: item.title,
          snippet: item.snippet,
          source: item.displayLink,
          image_url: item.pagemap?.cse_image?.[0]?.src || null
        }, { onConflict: 'link' });
      }
      return NextResponse.json({ step: 'Scraping Done', query: topic });
    }

    // ---------------------------------------------------------
    // PHASE 2: AI 요약 & Vibe 분석 (00:20 ~ 00:22 사이 랜덤 시작)
    // ---------------------------------------------------------
    if (mins >= 20 && mins <= 25) {
      const msDelay = Math.random() * 120000;
      await preciseDelay(msDelay);

      const { data: rawData } = await supabase.from('raw_news').select('*').limit(10);
      if (!rawData || rawData.length === 0) return NextResponse.json({ status: 'Empty' });

      for (const article of rawData) {
        const prompt = `Analyze: "${article.title}". 
        Return JSON ONLY: {
          "artist": "Artist Name",
          "summary": "1 sentence cyberpunk summary",
          "keywords": ["#tag1", "#tag2", "#tag3"],
          "vibe": { "excitement": 0, "shock": 0, "sadness": 0 }
        }`;

        const chat = await groq.chat.completions.create({
          messages: [{ role: "user", content: prompt }],
          model: "llama3-8b-8192",
          response_format: { type: "json_object" }
        });

        const result = JSON.parse(chat.choices[0]?.message?.content || "{}");
        
        await supabase.from('live_news').insert({
          artist: result.artist,
          title: article.title,
          summary: result.summary,
          keywords: result.keywords, // text[] 형식
          reactions: result.vibe,    // jsonb 형식 (VibeCheck 데이터)
          image_url: article.image_url,
          source: article.source,
          is_published: false
        });
      }
      return NextResponse.json({ step: 'AI Analysis Done' });
    }

    // ---------------------------------------------------------
    // PHASE 3: 배포(01:00) & 아카이빙(23:00) & 24시간 데이터 삭제
    // ---------------------------------------------------------
    if (mins === 0) {
      // 1. 배포: 숨겨진 뉴스 공개
      await supabase.from('live_news').update({ 
        is_published: true, 
        published_at: new Date().toISOString() 
      }).eq('is_published', false);

      // 2. 24시간 지난 원본 삭제
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      await supabase.from('raw_news').delete().lt('created_at', yesterday);

      // 3. 23:00 영구 보존 아카이빙
      if (hour === 23) {
        const { data: currentNews } = await supabase.from('live_news').select('*').eq('is_published', true);
        if (currentNews) {
          const archive = currentNews.map(n => ({
            artist: n.artist, title: n.title, summary: n.summary,
            image_url: n.image_url, keywords: n.keywords, reactions: n.reactions
          }));
          await supabase.from('archive_news').insert(archive);
        }
      }
      return NextResponse.json({ step: 'Maintenance Done' });
    }

    return NextResponse.json({ status: 'Standby' });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

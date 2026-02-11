import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import Groq from 'groq-sdk';
import { google } from 'googleapis';

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!);
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const customSearch = google.customsearch('v1');

// 1ms 단위의 정밀한 딜레이를 위한 유틸리티
const preciseDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function GET(request: Request) {
  const now = new Date();
  const mins = now.getMinutes();
  const hour = now.getHours();

  try {
    // ---------------------------------------------------------
    // 1. 뉴스 스크랩 (00:01 ~ 00:05 사이 1ms 단위 랜덤 시작)
    // ---------------------------------------------------------
    if (mins >= 1 && mins <= 5) {
      const msDelay = Math.random() * 240000; // 최대 4분(240,000ms) 사이 랜덤
      await preciseDelay(msDelay);

      // 전날 00:00~23:00 범위 기사 수집 (특정 가수 리스트 없음)
      const res = await customSearch.cse.list({
        auth: process.env.GOOGLE_SEARCH_API_KEY,
        cx: process.env.GOOGLE_SEARCH_ENGINE_ID,
        q: "K-POP news global",
        dateRestrict: 'd1', 
        num: 10,
      });

      const items = res.data.items || [];
      for (const item of items) {
        await supabase.from('raw_news').upsert({
          link: item.link,
          title: item.title,
          snippet: item.snippet,
          image_url: item.pagemap?.cse_image?.[0]?.src || null,
          created_at: new Date().toISOString()
        }, { onConflict: 'link' });
      }
      return NextResponse.json({ status: 'Phase 1: Scraping Complete' });
    }

    // ---------------------------------------------------------
    // 2. AI 요약 & Vibe 분석 (00:20 ~ 00:22 사이 랜덤 시작)
    // ---------------------------------------------------------
    if (mins >= 20 && mins <= 22) {
      const msDelay = Math.random() * 120000; // 최대 2분 사이 랜덤
      await preciseDelay(msDelay);

      const { data: rawData } = await supabase.from('raw_news').select('*').limit(10);
      if (!rawData) return NextResponse.json({ status: 'No raw data' });

      for (const article of rawData) {
        // 요구사항: 해시태그 3개 + Vibe 수치(%) 추출
        const prompt = `
          Analyze: "${article.title}"
          1. Identify Artist.
          2. 1-sentence Cyberpunk style summary.
          3. Exactly 3 hashtags (e.g. #NewEra).
          4. Evaluate Vibe percentages (excitement, shock, sadness) totaling 100%.
          Return JSON ONLY:
          {
            "artist": "string",
            "summary": "string",
            "keywords": ["#","#","#"],
            "vibe": { "excitement": 0, "shock": 0, "sadness": 0 }
          }
        `;

        const chat = await groq.chat.completions.create({
          messages: [{ role: "user", content: prompt }],
          model: "llama3-8b-8192",
          response_format: { type: "json_object" }
        });

        const result = JSON.parse(chat.choices[0]?.message?.content || "{}");
        await supabase.from('live_news').insert({
          artist: result.artist,
          summary: result.summary,
          keywords: result.keywords,
          vibe: result.vibe, // VibeCheck 컴포넌트용 데이터
          image_url: article.image_url,
          is_published: false // 01:00에 공개 예정
        });
      }
      return NextResponse.json({ status: 'Phase 2: AI Processing Complete' });
    }

    // ---------------------------------------------------------
    // 3. 배포, 정리, 아카이빙 (매시간 00분 정각 실행)
    // ---------------------------------------------------------
    if (mins === 0) {
      // (1) 요약본 웹 화면 적용 (is_published -> true)
      await supabase.from('live_news').update({ is_published: true }).eq('is_published', false);

      // (2) 24시간 지난 기사 삭제
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      await supabase.from('raw_news').delete().lt('created_at', yesterday);

      // (3) 23:00 기사 영구 보존 아카이빙
      if (hour === 23) {
        const { data: todayNews } = await supabase.from('live_news').select('*').eq('is_published', true);
        if (todayNews) {
          const archive = todayNews.map(n => ({
            artist: n.artist,
            summary: n.summary,
            keywords: n.keywords,
            vibe: n.vibe,
            archived_date: new Date().toISOString()
          }));
          await supabase.from('archive_news').insert(archive);
        }
      }
      return NextResponse.json({ status: 'Phase 3: Deploy & Archive Complete' });
    }

    return NextResponse.json({ status: 'Standby' });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

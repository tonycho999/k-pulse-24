import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import Groq from 'groq-sdk';
import { google } from 'googleapis';

// 환경 변수 초기화
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const customSearch = google.customsearch('v1');

// 정밀 지연 함수
const preciseDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const authHeader = request.headers.get('authorization');
  const now = new Date();
  const mins = now.getMinutes();

  // 0. 보안 검증: GitHub Actions에서 보낸 시크릿 확인
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized Access Denied' }, { status: 401 });
  }

  try {
    // ---------------------------------------------------------
    // PHASE 1: 뉴스 스크랩 (01분~15분 사이 진행)
    // 구글(글로벌) + 네이버(국내) 하이브리드 수집
    // ---------------------------------------------------------
    if (mins >= 1 && mins <= 10) {
      // 01분~05분 사이 랜덤 시작으로 안정성 확보
      const msDelay = Math.random() * 240000; 
      await preciseDelay(msDelay);

      const query = "K-POP (idol OR group) comeback OR debut OR world tour";

      // 1. Google Custom Search (글로벌 소식)
      const googleRes = await customSearch.cse.list({
        auth: process.env.GOOGLE_SEARCH_API_KEY,
        cx: process.env.GOOGLE_SEARCH_ENGINE_ID,
        q: query,
        dateRestrict: 'd1', // 최근 24시간
        num: 5
      });

      // 2. Naver Search API (국내 소식)
      const naverRes = await fetch(
        `https://openapi.naver.com/v1/search/news.json?query=${encodeURIComponent(query)}&display=5&sort=sim`,
        {
          headers: {
            'X-Naver-Client-Id': process.env.NAVER_CLIENT_ID!,
            'X-Naver-Client-Secret': process.env.NAVER_CLIENT_SECRET!,
          }
        }
      );
      const naverData = await naverRes.json();

      // DB 저장: Google 결과
      const googleItems = googleRes.data.items || [];
      for (const item of googleItems) {
        await supabase.from('raw_news').upsert({
          link: item.link, 
          title: item.title, 
          snippet: item.snippet,
          source: item.displayLink, 
          image_url: item.pagemap?.cse_image?.[0]?.src || null
        }, { onConflict: 'link' });
      }

      // DB 저장: Naver 결과
      const naverItems = naverData.items || [];
      for (const item of naverItems) {
        await supabase.from('raw_news').upsert({
          link: item.link, 
          title: item.title.replace(/<[^>]*>?/gm, ''), // HTML 태그 제거
          snippet: item.description.replace(/<[^>]*>?/gm, ''),
          source: 'Naver News', 
          image_url: null // 네이버 뉴스는 별도 크롤링 없이는 이미지 URL을 제공하지 않음
        }, { onConflict: 'link' });
      }

      return NextResponse.json({ step: 'Scraping Completed', sources: ['Google', 'Naver'] });
    }

    // ---------------------------------------------------------
    // PHASE 2: AI 요약 & Vibe 분석 (20분~50분 사이 완료)
    // ---------------------------------------------------------
    if (mins >= 20 && mins <= 25) {
      const msDelay = Math.random() * 60000;
      await preciseDelay(msDelay);

      // 최신 raw 데이터 10개 추출
      const { data: rawData } = await supabase
        .from('raw_news')
        .select('*')
        .limit(10)
        .order('created_at', { ascending: false });

      if (!rawData || rawData.length === 0) return NextResponse.json({ status: 'No raw data to process' });

      for (const article of rawData) {
        const prompt = `Task: Analyze K-POP news for a cyberpunk dashboard.
        News Title: "${article.title}"
        Return JSON ONLY: 
        { 
          "artist": "string", 
          "summary": "1 short sentence in cyberpunk vibe", 
          "keywords": ["#tag1", "#tag2", "#tag3"], 
          "vibe": { "excitement": 0, "shock": 0, "sadness": 0 } 
        }`;

        const chat = await groq.chat.completions.create({
          messages: [{ role: "user", content: prompt }],
          model: "llama3-8b-8192",
          response_format: { type: "json_object" }
        });

        const result = JSON.parse(chat.choices[0]?.message?.content || "{}");
        
        // 분석 완료된 데이터를 live_news로 이전 (공개 대기 상태)
        await supabase.from('live_news').insert({
          artist: result.artist, 
          title: article.title, 
          summary: result.summary,
          keywords: result.keywords, 
          reactions: result.vibe, // DB 컬럼명 reactions와 매칭
          image_url: article.image_url, 
          source: article.source, 
          is_published: false
        });
      }
      return NextResponse.json({ step: 'AI Analysis & Vibe Check Done' });
    }

    // ---------------------------------------------------------
    // PHASE 3: 배포 (매 시간 정각)
    // ---------------------------------------------------------
    if (mins === 0) {
      await supabase.from('live_news')
        .update({ 
          is_published: true, 
          published_at: new Date().toISOString() 
        })
        .eq('is_published', false);

      // (옵션) 24시간 지난 raw_news 데이터 청소
      const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      await supabase.from('raw_news').delete().lt('created_at', dayAgo);

      return NextResponse.json({ step: 'Deployment Successful' });
    }

    return NextResponse.json({ status: 'Standby', currentMins: mins });
  } catch (err: any) {
    console.error('API Error:', err.message);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

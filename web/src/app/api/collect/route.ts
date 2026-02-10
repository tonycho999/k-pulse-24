// web/src/app/api/collect/route.ts
import { NextResponse } from 'next/server';
import Groq from 'groq-sdk';
import { google } from 'googleapis';

// 1. 설정: 환경변수 가져오기
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const customSearch = google.customsearch('v1');

export async function GET() {
  try {
    // A. 검색 대상 설정 (실제로는 DB에서 가져오거나, 트렌드 키워드를 사용)
    const targetArtist = "NewJeans"; 
    const query = `${targetArtist} recent news k-pop`;

    console.log(`🔍 Searching for: ${query}`);

    // B. Google Custom Search API 호출
    const googleRes = await customSearch.cse.list({
      auth: process.env.GOOGLE_SEARCH_API_KEY,
      cx: process.env.GOOGLE_SEARCH_ENGINE_ID,
      q: query,
      num: 3, // 상위 3개 기사만 참조
      dateRestrict: 'd1', // 지난 24시간 이내 기사
    });

    const items = googleRes.data.items;
    if (!items || items.length === 0) {
      return NextResponse.json({ message: "No news found today." });
    }

    // C. 검색된 텍스트 합치기 (AI에게 던져줄 소스)
    const combinedText = items.map((item: any) => 
      `Title: ${item.title}\nSnippet: ${item.snippet}`
    ).join("\n\n");

    console.log("🤖 Asking AI to summarize...");

    // D. Groq (Llama 3)에게 요약 요청
    const chatCompletion = await groq.chat.completions.create({
      messages: [
        {
          role: "system",
          content: `You are a professional K-POP news editor. 
          Summarize the provided news snippets into ONE concise article in English.
          - Style: Professional, engaging, suitable for fans.
          - Length: Under 300 characters.
          - Output Format: JSON with keys 'title' and 'summary'.`
        },
        {
          role: "user",
          content: `News Source:\n${combinedText}`
        }
      ],
      model: "llama3-8b-8192",
      response_format: { type: "json_object" }, // JSON 모드 강제
    });

    // E. 결과 파싱 및 응답
    const aiContent = chatCompletion.choices[0]?.message?.content || "{}";
    const result = JSON.parse(aiContent);

    // TODO: 여기서 Supabase DB에 insert 하는 로직이 들어갑니다.
    // await supabase.from('news').insert({ ...Result, artist: targetArtist });

    return NextResponse.json({
      success: true,
      artist: targetArtist,
      data: result,
      source_count: items.length
    });

  } catch (error: any) {
    console.error("❌ Error in AI Collector:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

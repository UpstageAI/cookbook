import { NextRequest, NextResponse } from 'next/server';
import { ChatRequest, BackendResponse, ErrorResponse } from '@/types/chat';

// 기존 인터페이스 제거 (타입 파일로 이동됨)
// interface ChatRequest {
//   query: string;
// }

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json();
    const { query } = body;
    

    

    
    
    // 백엔드 API 연동 준비
    // 실제 백엔드 연동 시, 아래 코드 사용
    const backendUrl = process.env.BACKEND_URL || 'http://0.0.0.0:5000';
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      // 백엔드 응답 상태에 따른 리다이렉션
      if (response.status === 401 || response.status === 403) {
        // 인증/권한 오류 - 메인 페이지로 리다이렉션
        return NextResponse.redirect(new URL('/', request.nextUrl.origin));
      } else if (response.status >= 500) {
        // 서버 오류 - 에러 페이지로 리다이렉션
        return NextResponse.redirect(new URL('/error', request.nextUrl.origin));
      }
      throw new Error(`Backend API error: ${response.statusText}`);
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in chat API:', error);
    
    // 심각한 오류일 경우 에러 페이지로 리다이렉션
    if ((error as Error).message.includes('Backend API error') || 
        (error as Error).message.includes('ECONNREFUSED') ||
        (error as Error).message.includes('fetch failed')) {
      return NextResponse.redirect(new URL('/error', request.nextUrl.origin));
    }
    
    return NextResponse.json(
      { error: 'Error regarding agent response about user query. Please try again.' } as ErrorResponse,
      { status: 500 }
    );
  }
} 
import { NextResponse } from 'next/server';
import { HighlightRequest, HighlightResponse } from '../types';

export async function POST(request: Request) {
  try {
    const body: HighlightRequest = await request.json();
    const { pdfId, prompt } = body;

    // TODO: Implement actual API call to backend
    const response = await fetch(`${process.env.BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pdfId, prompt }),
    });

    if (!response.ok) {
      throw new Error('Failed to get highlights');
    }

    const data: HighlightResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in highlight API:', error);
    return NextResponse.json(
      { error: 'Failed to get highlights' },
      { status: 500 }
    );
  }
} 
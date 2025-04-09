import { NextResponse } from 'next/server';
import { SummaryRequest, SummaryResponse } from '../types';

export async function POST(request: Request) {
  try {
    const body: SummaryRequest = await request.json();
    const { pdfId, systemPrompt } = body;

    // TODO: Implement actual API call to backend
    const response = await fetch(`${process.env.BACKEND_URL}/api/summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pdfId, systemPrompt }),
    });

    if (!response.ok) {
      throw new Error('Failed to get summary');
    }

    const data: SummaryResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in summary API:', error);
    return NextResponse.json(
      { error: 'Failed to get summary' },
      { status: 500 }
    );
  }
} 
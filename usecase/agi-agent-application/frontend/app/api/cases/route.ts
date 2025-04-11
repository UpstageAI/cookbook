import { NextResponse } from 'next/server';
import { CasesRequest, CasesResponse } from '../types';

export async function POST(request: Request) {
  try {
    const body: CasesRequest = await request.json();
    const { query } = body;

    // TODO: Implement actual API call to backend
    const response = await fetch(`${process.env.BACKEND_URL}/api/cases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error('Failed to get cases');
    }

    const data: CasesResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in cases API:', error);
    return NextResponse.json(
      { error: 'Failed to get cases' },
      { status: 500 }
    );
  }
} 
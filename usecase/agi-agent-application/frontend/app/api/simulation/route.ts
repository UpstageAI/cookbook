import { NextResponse } from 'next/server';
import { SimulationRequest, SimulationResponse } from '../types';

export async function POST(request: Request) {
  try {
    const body: SimulationRequest = await request.json();
    const { pdfId, query } = body;

    // TODO: Implement actual API call to backend
    const response = await fetch(`${process.env.BACKEND_URL}/api/simulation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pdfId, query }),
    });

    if (!response.ok) {
      throw new Error('Failed to get simulation');
    }

    const data: SimulationResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in simulation API:', error);
    return NextResponse.json(
      { error: 'Failed to get simulation' },
      { status: 500 }
    );
  }
} 
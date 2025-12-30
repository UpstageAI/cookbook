import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // CloudFront를 통해 ALB 호출
    const apiUrl = process.env.API_URL || 'https://d31ad140yvex7c.cloudfront.net/api'
    
    const response = await fetch(`${apiUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: body.query }),
      signal: AbortSignal.timeout(300000) // 5분 타임아웃
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('AWS API route error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch analysis data' },
      { status: 500 }
    )
  }
}
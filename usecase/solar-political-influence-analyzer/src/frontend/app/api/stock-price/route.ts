import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { company } = body
    
    if (!company) {
      return NextResponse.json(
        { error: 'Company parameter required' },
        { status: 400 }
      )
    }

    // CloudFront를 통해 ALB 호출
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://d31ad140yvex7c.cloudfront.net/api'
    
    const response = await fetch(`${backendUrl}/stock-price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ company }),
      signal: AbortSignal.timeout(10000) // 10초 타임아웃
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Stock price API route error:', error)
    return NextResponse.json(
      { 
        company: body?.company || 'Unknown',
        error: '주가 정보를 가져올 수 없습니다.' 
      },
      { status: 500 }
    )
  }
}
import { NextResponse } from 'next/server'

export async function GET(
  request: Request,
  { params }: { params: { fileId: string } }
) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000'
  const fileId = params.fileId
  
  try {
    const response = await fetch(`${backendUrl}/uploads/${fileId}`)
    
    if (!response.ok) {
      return new NextResponse('PDF not found', { status: 404 })
    }

    const pdfBuffer = await response.arrayBuffer()
    
    return new NextResponse(pdfBuffer, {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `inline; filename="document.pdf"`,
      },
    })
  } catch (error) {
    console.error('Error fetching PDF:', error)
    return new NextResponse('Error fetching PDF', { status: 500 })
  }
} 
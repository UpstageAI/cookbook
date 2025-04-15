import { NextResponse } from 'next/server';
import { PdfUploadResponse } from '../types';

export async function POST(request: Request) {
  try {
    console.log('1. Starting file upload process');

    // 1. 클라이언트로부터 FormData 추출
    const formData = await request.formData();
    console.log(formData)
    const file = formData.get('document') as File;
    console.log('2. Received file from client:', file?.name);

    if (!file) {
      console.log('Error: No file provided');
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    // 2. 파일 유효성 검사
    console.log('3. File type:', file.type);
    if (!file.type.includes('pdf')) {
      console.log('Error: Invalid file type');
      return NextResponse.json(
        { error: 'Only PDF files are allowed' },
        { status: 400 }
      );
    }

    // 3. 파일 크기 검사 (10MB)
    console.log('4. File size:', file.size);
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      console.log('Error: File too large');
      return NextResponse.json(
        { error: 'File size exceeds 10MB limit' },
        { status: 400 }
      );
    }

    // 4. 파일을 ArrayBuffer로 변환
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    console.log('5. File converted to buffer');

    // 5. 새로운 FormData 생성 (백엔드 전송용)
    const backendFormData = new FormData();
    backendFormData.append('file', new Blob([buffer], { type: file.type }), file.name);
    backendFormData.append('fileName', file.name);
    backendFormData.append('fileSize', file.size.toString());
    console.log('6. Created backend FormData');

    // 6. 백엔드 서버로 전송
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';
    console.log('7. Backend URL:', backendUrl);
    
    console.log('8. Sending request to backend:', `${backendUrl}/api/pdf-upload`);
    const backendResponse = await fetch(`${backendUrl}/api/pdf-upload`, {
      method: 'POST',
      body: backendFormData,
    });

    // 디버깅을 위한 응답 정보 로깅
    console.log('Response status:', backendResponse.status);
    console.log('Response headers:', Object.fromEntries(backendResponse.headers));

    // 7. 백엔드 응답 처리
    if (!backendResponse.ok) {
      const errorBody = await backendResponse.text();  // raw 응답 확인
      console.log('Error response:', errorBody);
      throw new Error(`Backend error: ${backendResponse.status}`);
    }
    
    // 8. 백엔드 응답을 클라이언트에 전달
    const responseData: PdfUploadResponse = await backendResponse.json();
    console.log(responseData)
    // 9. 성공 응답 반환
    return NextResponse.json(responseData);

  } catch (error) {
    // 10. 에러 로깅 및 응답
    console.error('Error in PDF upload:', error);
    
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : 'Failed to upload PDF',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
} 
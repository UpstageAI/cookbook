"use client"

import { useState, useEffect } from "react"
import { Document, Page, pdfjs } from "react-pdf"
import "react-pdf/dist/esm/Page/AnnotationLayer.css"
import "react-pdf/dist/esm/Page/TextLayer.css"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/hooks/use-toast"

// PDF.js worker 설정
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

interface PdfViewerProps {
  fileId: string
  onTextSelect?: (text: string) => void
  isLoading?: boolean
  url?: string
  highlightTexts?: string[] // 하이라이트할 텍스트 목록
  userHighlights?: string[] // 사용자가 하이라이트한 텍스트 목록
}

export function PdfViewer({
  fileId,
  onTextSelect,
  isLoading,
  url,
  highlightTexts = [],
  userHighlights = []
}: PdfViewerProps) {
  // console.log(highlightTexts)
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [highlights, setHighlights] = useState<
    Array<{
      text: string
      page: number
      position: { x: number; y: number }
      width: number
      height: number
      isUserHighlight?: boolean
    }>
  >([])
  const { toast } = useToast()

  // PDF 로드 시 텍스트 검색 및 하이라이트
  const onDocumentLoadSuccess = async ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    console.log(numPages)
    if (!url) return
    
    // 페이지 로드 후 하이라이트 처리
    processHighlights()
    console.log(numPages)
  }

  // userHighlights가 변경될 때마다 하이라이트 다시 처리
  useEffect(() => {
    if (numPages > 0 && url) {
      processHighlights()
    }
  }, [userHighlights, highlightTexts, numPages])

  // 하이라이트 처리 로직
  const processHighlights = async () => {
    if (!url) return
    
    const newHighlights: Array<{
      text: string
      page: number
      position: { x: number; y: number }
      width: number
      height: number
      isUserHighlight?: boolean
    }> = []
    
    try {
      // PDF 문서 가져오기
      const pdfDocument = await pdfjs.getDocument(url).promise
      
      // PDF 문서에서 직접 페이지 수를 가져와서 사용
      const totalPages = pdfDocument.numPages
      setNumPages(totalPages)
      
      // 중복 하이라이트 추적을 위한 집합
      const highlightedPositions = new Set();
      
      // 모든 페이지 처리
      for (let i = 1; i <= totalPages; i++) {
        const page = await pdfDocument.getPage(i)
        const scale = 0.99
        const viewport = page.getViewport({ scale })
        const textContent = await page.getTextContent()
        
        // 기본 하이라이트와 사용자 하이라이트 모두 처리
        const allHighlights = [
          ...highlightTexts.map(text => ({ text, isUser: false })),
          ...userHighlights.map(text => ({ text, isUser: true }))
        ]
        
        // 각 하이라이트 키워드에 대해 처리
        allHighlights.forEach(({ text, isUser }) => {
          if (!text || text.trim() === '') return
          // 대소문자 구분 없이 비교하기 위한 소문자 변환
          const lowercaseText = text.toLowerCase()
          
          // 각 텍스트 아이템에서 키워드 검색
          textContent.items.forEach((item: any) => {
            if (!item.str) return
            
            const itemText = item.str
            const lowercaseItemText = itemText.toLowerCase()
            
            // 이미 하이라이트된 위치인지 확인
            const positionKey = `${i}-${item.transform[4]}-${item.transform[5]}`;
            if (highlightedPositions.has(positionKey)) return;
            
            // 다음 조건 중 하나 충족시 하이라이트
            let shouldHighlight = false;
            
            // 1. 정확한 포함 관계
            if (lowercaseItemText.includes(lowercaseText)) {
              shouldHighlight = true;
            } 
            // 2. 긴 하이라이트 문장에 대한 처리 (문장이 길고, 의미 있는 단어가 있을 경우)
            else if (lowercaseText.length > 15) {
              // 문장에서 의미 있는 단어 추출 (3글자 이상)
              const significantWords = lowercaseText.split(/\s+/).filter(word => word.length > 3);
              
              // 단어들 중 충분한 수가 매칭되는지 확인 (예: 30% 이상)
              const matchCount = significantWords.filter(word => lowercaseItemText.includes(word)).length;
              shouldHighlight = matchCount > 0 && matchCount / significantWords.length >= 0.3;
            }
            
            if (shouldHighlight) {
              const transform = item.transform
              const x = transform[4] * scale
              const textHeight = (item.height || 20) * scale
              const y = viewport.height - transform[5] * scale - textHeight
              const textWidth = item.width * scale

              // 하이라이트 추가 및 위치 기록
              highlightedPositions.add(positionKey);
              newHighlights.push({
                text,
                page: i,
                position: { x, y },
                width: textWidth,
                height: textHeight,
                isUserHighlight: isUser
              })
            }
          })
        })
      }

      setHighlights(newHighlights)
    } catch (error) {
      console.error('Error processing highlights:', error)
      toast({
        title: "하이라이트 처리 오류",
        description: "PDF 내 텍스트 검색 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  if (isLoading) {
    return (
      <div className="w-full h-full rounded-lg border">
        <Skeleton className="w-full h-full" />
      </div>
    )
  }

  if (!url) {
    return (
      <div className="w-full h-full rounded-lg border flex items-center justify-center">
        <p className="text-muted-foreground">No PDF document loaded</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center justify-between p-1 border-b">
        <h2 className="text-sm font-medium">Finance Product PDF</h2>
      </div>

      <div className="w-full h-full rounded-lg relative overflow-auto p-0 border-0">
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<Skeleton className="w-full h-full" />}
        >
          <div className="flex flex-col items-center p-0">
            <div className="flex items-center gap-2 mb-1">
              <button
                onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
                disabled={pageNumber <= 1}
                className="px-2 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
              >
                이전
              </button>
              <span className="text-sm">
                {pageNumber} / {numPages}
              </span>
              <button
                onClick={() => setPageNumber((prev) => Math.min(prev + 1, numPages))}
                disabled={pageNumber >= numPages}
                className="px-2 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
              >
                다음
              </button>
            </div>
            <div className="mx-6 my-2">
              <Page
                pageNumber={pageNumber}
                scale={0.99}
                renderTextLayer={true}
                renderAnnotationLayer={true}
              >
                {/* 하이라이트 렌더링 - 두 가지 색상으로 표시 */}
                {highlights
                  .filter((h) => h.page === pageNumber)
                  .map((highlight, index) => (
                    <div
                      key={index}
                      className={`absolute opacity-50 pointer-events-none ${
                        highlight.isUserHighlight ? 'bg-blue-300' : 'bg-yellow-200'
                      }`}
                      style={{
                        left: `${highlight.position.x}px`,
                        top: `${highlight.position.y}px`,
                        width: `${highlight.width}px`,
                        height: `${highlight.height}px`,
                      }}
                    />
                  ))}
              </Page>
            </div>
          </div>
        </Document>
      </div>
    </div>
  )
}
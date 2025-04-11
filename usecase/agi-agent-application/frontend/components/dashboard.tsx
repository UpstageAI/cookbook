"use client"

import { useState, useEffect } from "react"
import { PdfViewer } from "@/components/pdf-viewer"
import { Overview } from "@/components/overview"
import { Chatbot } from "@/components/chatbot"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"
import { mockDocumentData } from "@/lib/mock-data"
import type { DisputeCase } from "@/lib/types"
import { useAppContext } from "@/lib/context"

interface DocumentData {
  overview: {
    summary: string;
    keyMetrics: {
      annualReturn: string;
      volatility: string;
      managementFee: string;
      minimumInvestment: string;
      lockupPeriod: string;
      riskLevel: "보통위험" | "매우높은위험" | "높은위험" | "낮은위험" | "매우낮은위험";
    };
    keyFindings: string[];
    recommendations: string[];
  }
}

export function Dashboard({ fileId, fileUrl }: { fileId: string; fileUrl?: string }) {
  const [activeTab, setActiveTab] = useState<string>("overview")
  const [documentData, setDocumentData] = useState<DocumentData>({
    overview: {
      summary: "",
      keyMetrics: {
        annualReturn: "-",
        volatility: "-",
        managementFee: "-",
        minimumInvestment: "-",
        lockupPeriod: "-",
        riskLevel: "보통위험",
      },
      keyFindings: [],
      recommendations: []
    }
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [pdfUrl, setPdfUrl] = useState<string | undefined>(fileUrl)
  const [selectedText, setSelectedText] = useState<string>("")
  const [highlightTexts, setHighlightTexts] = useState<string[]>([])
  const [userHighlights, setUserHighlights] = useState<string[]>([])
  const { toast } = useToast()
  const { activeTab: appContextActiveTab, setActiveTab: setAppContextActiveTab } = useAppContext()

  useEffect(() => {
    const loadData = () => {
      setIsLoading(true)
      try {
        // URL에서 파라미터 추출
        const urlParams = new URLSearchParams(window.location.search)
        const summary = urlParams.get('summary') || ""
        const keyValues = JSON.parse(urlParams.get('keyValues') || "{}")
        const keyFindings = JSON.parse(urlParams.get('keyFindings') || "[]")
        
        // 하이라이트 정보 추출
        const highlights = JSON.parse(urlParams.get('highlights') || "[]")
        setHighlightTexts(highlights)
        
        // documentData 설정
        setDocumentData({
          overview: {
            summary,
            keyMetrics: {
              annualReturn: keyValues.annualReturn || "-",
              volatility: keyValues.volatility || "-",
              managementFee: keyValues.managementFee || "-",
              minimumInvestment: keyValues.minimumInvestment || "-",
              lockupPeriod: keyValues.lockupPeriod || "-",
              riskLevel: keyValues.riskLevel || "보통위험",
            },
            keyFindings,
            recommendations: []
          }
        })
      } catch (error) {
        console.error('Error parsing URL parameters:', error)
        toast({
          title: "Error loading document",
          description: "There was an error loading the document data. Please try again.",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    if (typeof window !== 'undefined') {
      loadData()
    }
  }, [toast])

  useEffect(() => {
    if (fileUrl) {
      setPdfUrl(fileUrl)
    }
  }, [fileUrl])

  const handleTextSelection = (text: string) => {
    setSelectedText(text)
  }

  const handleUserHighlights = (highlights: string[]) => {
    // 새로운 하이라이트만 userHighlights에 추가 (중복 제거)
    const uniqueHighlights = Array.from(new Set([...userHighlights, ...highlights]))
    setUserHighlights(uniqueHighlights)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="h-[calc(100vh-8rem)] overflow-hidden rounded-lg border border-border">
        <PdfViewer 
          fileId={fileId} 
          onTextSelect={handleTextSelection} 
          isLoading={isLoading} 
          url={pdfUrl} 
          highlightTexts={highlightTexts}
          userHighlights={userHighlights}
        />
      </div>
      <div className="flex flex-col h-[calc(100vh-8rem)] overflow-hidden rounded-lg border border-border">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col h-full">
          <TabsList className="w-full justify-start border-b">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="chat">AI Assistant</TabsTrigger>
          </TabsList>
          <div className="flex-1 overflow-hidden">
            <TabsContent value="overview" className="h-full overflow-auto">
              <Overview data={documentData.overview} isLoading={isLoading} />
            </TabsContent>
            <TabsContent value="chat" className="h-full overflow-hidden">
              <Chatbot selectedText={selectedText} isLoading={isLoading} onHighlightsReceived={handleUserHighlights} />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  )
}


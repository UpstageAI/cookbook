"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation" // Add useSearchParams import
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { RelationshipGraph } from "@/components/relationship-graph"
import type { AnalysisReport } from "@/lib/types"
import { AlertCircle } from "lucide-react"
import { safeRender } from "@/lib/utils"

export function AnalysisContent() {
  const searchParams = useSearchParams()
  const [query, setQuery] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [apiResponse, setApiResponse] = useState<AnalysisReport | null>(null)

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search)
      const q = params.get("query") || params.get("q") || ""
      setQuery(q)
    }
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      if (!query) return

      try {
        setLoading(true)
        console.log("[v0] Fetching data for query:", query)

        // Use environment variable for API URL
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://ups-t3-alb-984329148.ap-northeast-2.elb.amazonaws.com"
        
        // 1. Job 생성
        const jobResponse = await fetch(`${apiUrl}/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query }),
        })

        if (!jobResponse.ok) {
          throw new Error("Failed to create job")
        }

        const { job_id } = await jobResponse.json()
        console.log("[v0] Job created:", job_id)

        // 2. Polling (3초마다 상태 확인)
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await fetch(`${apiUrl}/job/${job_id}`)
            if (!statusResponse.ok) {
              throw new Error("Failed to fetch job status")
            }

            const jobData = await statusResponse.json()
            console.log("[v0] Job status:", jobData.status)

            if (jobData.status === "completed") {
              clearInterval(pollInterval)
              setApiResponse(jobData.result)
              setLoading(false)
            } else if (jobData.status === "failed") {
              clearInterval(pollInterval)
              throw new Error(jobData.error || "Analysis failed")
            }
          } catch (err) {
            clearInterval(pollInterval)
            console.error("[v0] Polling error:", err)
            setError("분석 중 오류가 발생했습니다.")
            setLoading(false)
          }
        }, 3000)

        // 5분 후 타임아웃
        setTimeout(() => {
          clearInterval(pollInterval)
          if (loading) {
            setError("분석 시간이 초과되었습니다. 다시 시도해주세요.")
            setLoading(false)
          }
        }, 300000)

      } catch (err) {
        console.error("[v0] Error fetching data:", err)
        setError("분석 대상을 가져오는데 실패했습니다. 다시 시도해주세요.")
        setLoading(false)
      }
    }

    fetchData()
  }, [query])

  if (!query) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-2">
          <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" />
          <p className="text-muted-foreground">검색어를 입력해주세요</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="text-center space-y-4">
          <Spinner className="w-12 h-12 mx-auto" />
          <div className="space-y-2">
            <p className="font-medium">관계도를 분석하고 있습니다...</p>
            <p className="text-sm text-muted-foreground">정책, 산업, 기업 간의 연결고리를 찾는 중입니다</p>
            <p className="text-xs text-muted-foreground/80">심층 분석에는 시간이 소요될 수 있습니다.</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !apiResponse) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-2">
          <AlertCircle className="w-12 h-12 text-destructive mx-auto" />
          <p className="text-muted-foreground">{error || "분석 결과를 불러올 수 없습니다"}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-2xl md:text-3xl font-bold">{safeRender(apiResponse.report_title)}</h2>
          <Badge variant="secondary" className="text-xs">
            {safeRender(apiResponse.time_range)}
          </Badge>
        </div>
        <p className="text-muted-foreground leading-relaxed">
          <span className="font-medium text-foreground">{query}</span>에 대한 정치·경제 관계도 분석 결과입니다. 노드를
          클릭하면 상세 정보와 근거를 확인할 수 있습니다.
        </p>
      </div>

      {/* Graph Visualization */}
      <Card className="p-4 md:p-6">
        <RelationshipGraph data={apiResponse} />
      </Card>

      {/* Notes */}
      {apiResponse.notes && (
        <Card className="p-4 bg-muted/50 border-muted">
          <p className="text-sm text-muted-foreground leading-relaxed">
            <span className="font-medium text-foreground">참고사항:</span> {safeRender(apiResponse.notes)}
          </p>
        </Card>
      )}
    </div>
  )
}

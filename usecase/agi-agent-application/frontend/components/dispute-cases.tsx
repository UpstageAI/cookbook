"use client"

import { useState, useEffect } from "react"
import { AlertTriangle, ChevronRight, ExternalLink, Filter } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import type { DisputeCase } from "@/lib/types"
import { DisputeTrendChart } from "@/components/dispute-trend-chart"

interface DisputeCasesProps {
  data?: {
    cases: DisputeCase[]
    totalCases: number
    trendData: { month: string; count: number }[]
  }
  isLoading: boolean
  selectedId?: string | null
}

export function DisputeCases({ data, isLoading, selectedId }: DisputeCasesProps) {
  const [selectedCase, setSelectedCase] = useState<DisputeCase | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  // Provide default values if data is undefined
  const safeData = data || {
    cases: [],
    totalCases: 0,
    trendData: [],
  }

  // 선택된 ID가 있으면 해당 사례를 찾아 대화상자를 엽니다
  useEffect(() => {
    if (selectedId && !isLoading) {
      const foundCase = safeData.cases.find(c => c.id === selectedId);
      if (foundCase) {
        setSelectedCase(foundCase);
        setIsDialogOpen(true);
      }
    }
  }, [selectedId, isLoading, safeData.cases]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-40 w-full" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    )
  }

  const handleCaseClick = (disputeCase: DisputeCase) => {
    setSelectedCase(disputeCase)
    setIsDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Related Dispute Cases</h2>
        <p className="text-muted-foreground">Similar dispute cases found in our legal database</p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Dispute Trends</CardTitle>
          <CardDescription>Historical trends of similar dispute cases over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <DisputeTrendChart data={safeData.trendData} />
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium">Found {safeData.totalCases} related cases</span>
        </div>
        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-2" />
          Filter Cases
        </Button>
      </div>

      <div className="space-y-4">
        {safeData.cases.map((disputeCase) => (
          <Card
            key={disputeCase.id}
            className="hover:bg-muted/50 transition-colors cursor-pointer"
            onClick={() => handleCaseClick(disputeCase)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{disputeCase.title}</h3>
                    <Badge variant={disputeCase.status === "Resolved" ? "outline" : "secondary"}>
                      {disputeCase.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">{disputeCase.summary}</p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Case #{disputeCase.id}</span>
                    <span>•</span>
                    <span>{disputeCase.date}</span>
                    <span>•</span>
                    <span>{disputeCase.jurisdiction}</span>
                  </div>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        {selectedCase && (
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <span>{selectedCase.title}</span>
                <Badge variant={selectedCase.status === "Resolved" ? "outline" : "secondary"}>
                  {selectedCase.status}
                </Badge>
              </DialogTitle>
              <DialogDescription>
                Case #{selectedCase.id} • {selectedCase.date} • {selectedCase.jurisdiction}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-1">Summary</h4>
                <p className="text-sm">{selectedCase.summary}</p>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-1">Key Issues</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {selectedCase.keyIssues.map((issue, index) => (
                    <li key={index}>{issue}</li>
                  ))}
                </ul>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-1">Outcome</h4>
                <p className="text-sm">{selectedCase.outcome}</p>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-1">Relevance to Your Document</h4>
                <div className="flex items-start gap-2 bg-amber-50 p-3 rounded-md border border-amber-200">
                  <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800">{selectedCase.relevance}</p>
                </div>
              </div>
              <div className="flex justify-end">
                <Button variant="outline" size="sm">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Full Case Details
                </Button>
              </div>
            </div>
          </DialogContent>
        )}
      </Dialog>
    </div>
  )
}


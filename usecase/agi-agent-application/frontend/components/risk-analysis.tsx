"use client"

import { AlertTriangle, AlertCircle, CheckCircle, Info } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { RiskChart } from "@/components/risk-chart"
import type { RiskScore } from "@/lib/types"

interface RiskAnalysisProps {
  data?: {
    overallRisk: number
    riskScores: RiskScore[]
    keyFindings: string[]
    recommendations: string[]
  }
  isLoading: boolean
}

export function RiskAnalysis({ data, isLoading }: RiskAnalysisProps) {
  // Provide default values if data is undefined
  const safeData = data || {
    overallRisk: 0,
    riskScores: [],
    keyFindings: [],
    recommendations: [],
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-40 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    )
  }

  const getRiskColor = (score: number) => {
    if (score < 30) return "text-green-500"
    if (score < 70) return "text-amber-500"
    return "text-red-500"
  }

  const getRiskIcon = (score: number) => {
    if (score < 30) return <CheckCircle className="h-5 w-5 text-green-500" />
    if (score < 70) return <AlertCircle className="h-5 w-5 text-amber-500" />
    return <AlertTriangle className="h-5 w-5 text-red-500" />
  }

  const getRiskBadge = (score: number) => {
    if (score < 30)
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          Low Risk
        </Badge>
      )
    if (score < 70)
      return (
        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
          Medium Risk
        </Badge>
      )
    return (
      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
        High Risk
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Risk Analysis</h2>
        <p className="text-muted-foreground">Analysis of potential risks in the financial document</p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between">
            <span>Overall Risk Assessment</span>
            {getRiskBadge(safeData.overallRisk)}
          </CardTitle>
          <CardDescription>Based on our analysis of the document clauses and terms</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Risk Score</span>
                <span className={`font-bold ${getRiskColor(safeData.overallRisk)}`}>{safeData.overallRisk}%</span>
              </div>
              <Progress value={safeData.overallRisk} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="h-64">
        <RiskChart data={safeData.riskScores} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Key Findings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {safeData.keyFindings.map((finding, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-sm">{finding}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {safeData.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                  <span className="text-sm">{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Risk Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {safeData.riskScores.map((risk, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getRiskIcon(risk.score)}
                    <span className="font-medium">{risk.category}</span>
                  </div>
                  <span className={`font-bold ${getRiskColor(risk.score)}`}>{risk.score}%</span>
                </div>
                <Progress value={risk.score} className="h-2" />
                <p className="text-sm text-muted-foreground">{risk.description}</p>
                {index < safeData.riskScores.length - 1 && <Separator className="my-2" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


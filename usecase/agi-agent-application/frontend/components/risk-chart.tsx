"use client"

import { Card } from "@/components/ui/card"
import type { RiskScore } from "@/lib/types"
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "@/components/ui/chart"

interface RiskChartProps {
  data?: RiskScore[]
}

export function RiskChart({ data = [] }: RiskChartProps) {
  const chartData = data.map((item) => ({
    name: item.category,
    value: item.score,
    fill: getRiskColor(item.score),
  }))

  function getRiskColor(score: number) {
    if (score < 30) return "#22c55e" // green-500
    if (score < 70) return "#f59e0b" // amber-500
    return "#ef4444" // red-500
  }

  return (
    <Card className="h-full p-4">
      <h3 className="text-lg font-semibold mb-4">Risk Category Comparison</h3>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12 }}
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            formatter={(value) => [`${value}%`, "Risk Score"]}
            contentStyle={{
              borderRadius: "6px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}


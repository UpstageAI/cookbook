"use client"

import { Line, LineChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "@/components/ui/chart"

interface DisputeTrendChartProps {
  data?: { month: string; count: number }[]
}

export function DisputeTrendChart({ data = [] }: DisputeTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value) => [`${value} cases`, "Disputes"]}
          contentStyle={{
            borderRadius: "6px",
            border: "1px solid #e2e8f0",
            boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
          }}
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#6366f1"
          strokeWidth={2}
          dot={{ r: 4, strokeWidth: 2 }}
          activeDot={{ r: 6, strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}


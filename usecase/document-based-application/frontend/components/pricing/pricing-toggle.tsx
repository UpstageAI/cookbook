"use client"

import { useState } from "react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

export function PricingToggle() {
  const [isYearly, setIsYearly] = useState(false)

  return (
    <div className="flex items-center justify-center mb-10 space-x-4">
      <Label htmlFor="billing-toggle" className="font-medium">
        Monthly
      </Label>
      <Switch id="billing-toggle" checked={isYearly} onCheckedChange={setIsYearly} />
      <Label htmlFor="billing-toggle" className="font-medium">
        Yearly
        {isYearly && (
          <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">Save 20%</span>
        )}
      </Label>
    </div>
  )
}

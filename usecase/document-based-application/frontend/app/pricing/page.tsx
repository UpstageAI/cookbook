import { PricingCards } from "@/components/pricing/pricing-cards"
import { PricingHeader } from "@/components/pricing/pricing-header"
import { PricingToggle } from "@/components/pricing/pricing-toggle"

export default function PricingPage() {
  return (
    <div className="container max-w-6xl py-12 md:py-24">
      <PricingHeader />
      <PricingToggle />
      <PricingCards />
    </div>
  )
}

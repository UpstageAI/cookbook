"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Check } from "lucide-react"

const pricingPlans = [
  {
    name: "Free",
    emoji: "💸",
    price: {
      monthly: 0,
      yearly: 0,
    },
    description: "For individuals just getting started",
    features: ["10 documents per month", "Summary & Slack integration", "Basic classification", "Limited support"],
    cta: "Start for Free",
    popular: false,
  },
  {
    name: "Pro",
    emoji: "🚀",
    price: {
      monthly: 29,
      yearly: 279,
    },
    description: "For professionals and small teams",
    features: ["100 documents", "Notion, Calendar, and Slack actions", "Smart search + timeline", "Email support"],
    cta: "Upgrade to Pro",
    popular: true,
  },
  {
    name: "Team",
    emoji: "🧑‍🤝‍🧑",
    price: {
      monthly: 99,
      yearly: 949,
    },
    description: "Includes 20 users",
    features: ["500 documents", "Shared workspace", "Drive/Slack/Notion sync", "Document memory across users"],
    cta: "Start Team Plan",
    popular: false,
  },
  {
    name: "Enterprise",
    emoji: "🏢",
    price: {
      monthly: null,
      yearly: null,
    },
    description: "For large organizations with custom needs",
    features: [
      "Unlimited documents",
      "Dedicated AI instance (custom RAG)",
      "SOC2-compliant audit logs",
      "Onboarding support & API SLA",
    ],
    cta: "Contact Sales",
    popular: false,
  },
]

export function PricingCards() {
  const [isYearly, setIsYearly] = useState(false)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
      {pricingPlans.map((plan) => (
        <Card
          key={plan.name}
          className={`flex flex-col h-full transition-all duration-200 hover:shadow-lg ${
            plan.popular ? "border-primary shadow-md" : "border-border"
          }`}
        >
          {plan.popular && (
            <div className="absolute top-0 right-0 transform translate-x-2 -translate-y-2">
              <span className="bg-primary text-primary-foreground text-xs font-medium px-3 py-1 rounded-full">
                Most Popular
              </span>
            </div>
          )}
          <CardHeader>
            <div className="text-2xl mb-2">{plan.emoji}</div>
            <CardTitle className="text-2xl">{plan.name}</CardTitle>
            <CardDescription>{plan.description}</CardDescription>
          </CardHeader>
          <CardContent className="flex-grow">
            <div className="mb-6">
              {plan.price.monthly === null ? (
                <div className="text-3xl font-bold">Custom pricing</div>
              ) : (
                <div className="flex items-baseline">
                  <span className="text-3xl font-bold">${isYearly ? plan.price.yearly : plan.price.monthly}</span>
                  <span className="text-muted-foreground ml-2">
                    {plan.price.monthly > 0 && (isYearly ? "/year" : "/month per user")}
                  </span>
                </div>
              )}
            </div>
            <ul className="space-y-3">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </CardContent>
          <CardFooter>
            <Button
              className={`w-full ${
                plan.name === "Enterprise"
                  ? "bg-secondary hover:bg-secondary/90"
                  : plan.popular
                    ? "bg-primary hover:bg-primary/90"
                    : ""
              }`}
              variant={plan.name === "Enterprise" ? "secondary" : "default"}
            >
              {plan.cta}
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}

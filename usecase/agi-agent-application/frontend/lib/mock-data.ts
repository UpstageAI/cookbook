import type { RiskScore, DisputeCase } from "@/lib/types"

// Mock risk scores
const riskScores: RiskScore[] = [
  {
    category: "Legal Compliance",
    score: 35,
    description: "Some potential compliance issues with recent regulatory changes.",
  },
  {
    category: "Fee Structure",
    score: 65,
    description: "Higher than average fees with complex calculation methods.",
  },
  {
    category: "Liquidity Risk",
    score: 80,
    description: "Significant restrictions on withdrawals and redemptions.",
  },
  {
    category: "Market Risk",
    score: 55,
    description: "Moderate exposure to market volatility and economic downturns.",
  },
  {
    category: "Transparency",
    score: 40,
    description: "Some key information is not clearly disclosed or is difficult to understand.",
  },
]

// Mock dispute cases
const disputeCases: DisputeCase[] = [
  {
    id: "DC-2023-1045",
    title: "Smith v. Financial Products Corp",
    status: "Resolved",
    date: "Mar 15, 2023",
    jurisdiction: "Federal Court",
    summary:
      "Investor claimed that fee structure was misrepresented in the product documentation, leading to unexpected charges.",
    keyIssues: ["Misleading fee disclosure", "Inadequate risk warnings", "Failure to disclose conflicts of interest"],
    outcome: "Settled for $1.2M with agreement to revise disclosure documents.",
    relevance: "This case involved similar fee structure language to what appears in your document on page 24.",
  },
  {
    id: "DC-2022-0872",
    title: "Johnson Retirement Fund v. Investment Advisors Inc",
    status: "Ongoing",
    date: "Nov 8, 2022",
    jurisdiction: "State Court",
    summary:
      "Class action regarding hidden fees and charges that were not properly disclosed in the investment prospectus.",
    keyIssues: [
      "Hidden fees not disclosed in main documentation",
      "Misleading performance projections",
      "Inadequate risk disclosure",
    ],
    outcome: "Case is ongoing with preliminary injunction granted to plaintiffs.",
    relevance: "The dispute centers on similar liquidity restriction clauses found in your document section 5.3.",
  },
  {
    id: "DC-2022-0651",
    title: "Garcia v. Global Investment Partners",
    status: "Resolved",
    date: "Jul 22, 2022",
    jurisdiction: "Arbitration",
    summary:
      "Investor disputed the risk classification of the product, claiming it was marketed as lower risk than actual performance indicated.",
    keyIssues: [
      "Misclassification of risk level",
      "Aggressive marketing to unsuitable investors",
      "Failure to conduct proper suitability assessment",
    ],
    outcome: "Arbitrator ruled in favor of the investor, awarding $350,000 in damages.",
    relevance: "The risk classification methodology in this case is very similar to the one used in your document.",
  },
  {
    id: "DC-2021-1198",
    title: "Pension Trust v. Financial Services Group",
    status: "Resolved",
    date: "Dec 3, 2021",
    jurisdiction: "Federal Court",
    summary:
      "Institutional investor claimed that liquidity terms were substantially changed without proper notification.",
    keyIssues: [
      "Unilateral changes to redemption terms",
      "Inadequate notification of material changes",
      "Breach of fiduciary duty",
    ],
    outcome:
      "Court ruled in favor of defendant, finding that notification was adequate under the terms of the agreement.",
    relevance:
      "Your document contains similar language regarding the ability to change redemption terms with limited notice.",
  },
]

// Mock trend data
const trendData = [
  { month: "Jan", count: 12 },
  { month: "Feb", count: 15 },
  { month: "Mar", count: 18 },
  { month: "Apr", count: 14 },
  { month: "May", count: 21 },
  { month: "Jun", count: 25 },
  { month: "Jul", count: 30 },
  { month: "Aug", count: 28 },
  { month: "Sep", count: 32 },
  { month: "Oct", count: 35 },
  { month: "Nov", count: 38 },
  { month: "Dec", count: 42 },
]

// Mock overview data
const overviewData = {
  summary: `# Financial Product Overview

This investment product is a **structured note** with principal protection and market-linked returns. 

## Key Features

* 100% principal protection at maturity
* Returns linked to S&P 500 performance
* 5-year investment term
* Semi-annual interest payments

## Risk Considerations

The product carries moderate risk due to:

1. Market risk affecting potential returns
2. Liquidity constraints during the investment term
3. Credit risk of the issuing institution

> Note: Principal protection applies only if held to maturity.`,
  keyMetrics: {
    annualReturn: 7.5,
    volatility: 12.3,
    managementFee: 1.5,
    minimumInvestment: 25000,
    lockupPeriod: 36,
    riskLevel: "Medium" as const,
  },
  keyFindings: [
    "The document contains complex fee structures with potential hidden charges.",
    "Liquidity restrictions are more severe than industry standard.",
    "Dispute resolution clause requires mandatory arbitration.",
    "Risk disclosures are present but scattered throughout the document.",
    "Early termination penalties are significantly higher than comparable products.",
  ],
  recommendations: [
    "Review section 4.3 carefully for fee structure details.",
    "Consider liquidity needs before committing to this product.",
    "Consult with a financial advisor about alternative products with better liquidity terms.",
    "Request clarification on specific risk factors mentioned on page 18.",
    "Compare early termination penalties with other similar products in the market.",
  ],
}

// Mock highlighted clauses
const highlightedClauses = [
  {
    text: "The Company reserves the right to modify any terms of this agreement, including fees and redemption policies, with 30 days notice provided electronically to the email address on file.",
    risk: "High" as const,
    explanation:
      "This clause allows the financial institution to unilaterally change key terms of the agreement, including fees and redemption policies, with minimal notice. The electronic notification requirement may result in missed notifications if emails go to spam folders.",
    precedents: [
      {
        title: "Johnson v. Investment Partners (2021)",
        summary:
          "Court ruled that unilateral changes to fee structures with only electronic notification was insufficient, especially when resulting in significant financial impact.",
      },
      {
        title: "Regulatory Guidance 2022-03",
        summary:
          "Financial regulators have indicated that material changes to financial product terms should require affirmative consent, not just notification.",
      },
    ],
  },
  {
    text: "Redemption requests may be suspended or delayed at the sole discretion of the Company during periods of market disruption or other extraordinary circumstances.",
    risk: "High" as const,
    explanation:
      "This clause gives the financial institution unlimited discretion to suspend redemptions without clearly defining what constitutes 'market disruption' or 'extraordinary circumstances'. This could potentially lock up investor funds indefinitely.",
    precedents: [
      {
        title: "Retirement Fund v. Global Investments (2020)",
        summary:
          "Court found that similar vague language around redemption suspensions was unconscionable when used to prevent withdrawals during a moderate market correction.",
      },
    ],
  },
  {
    text: "All disputes arising under this agreement shall be resolved through binding arbitration in accordance with the rules of the Financial Industry Regulatory Authority.",
    risk: "Medium" as const,
    explanation:
      "This clause requires all disputes to be resolved through arbitration rather than court proceedings. While arbitration is a recognized dispute resolution method, it often favors financial institutions and limits investors' ability to participate in class actions.",
    precedents: [
      {
        title: "Consumer Financial Protection Bureau Study (2022)",
        summary:
          "Found that mandatory arbitration clauses significantly reduced consumer recovery amounts compared to court proceedings.",
      },
    ],
  },
]

// Mock dispute simulations
const disputeSimulations = [
  {
    situation:
      "You invested in a financial product with a 5-year term, but need to withdraw after 2 years due to unexpected medical expenses. The product has a 5% early withdrawal penalty.",
    conversation: [
      {
        role: "user" as const,
        content:
          "I need to withdraw my investment early due to medical expenses. The 5% penalty seems excessive given my circumstances. Is there any way to reduce or waive this fee?",
      },
      {
        role: "consultant" as const,
        content:
          "While the terms clearly state a 5% early withdrawal penalty, there is precedent for waiving or reducing fees in cases of financial hardship due to medical circumstances. You should submit a hardship waiver request with documentation of your medical expenses. In similar cases, financial institutions have reduced penalties to 1-2% or waived them entirely.",
      },
    ],
  },
  {
    situation:
      "You notice that the management fee on your account statements is 2.1%, but the prospectus stated a fee of 1.5%.",
    conversation: [
      {
        role: "user" as const,
        content:
          "I've been reviewing my statements and noticed that I'm being charged a 2.1% management fee, but the prospectus clearly stated 1.5%. What should I do about this discrepancy?",
      },
      {
        role: "consultant" as const,
        content:
          "This is a clear discrepancy that should be addressed. First, review the fine print in the prospectus for any language about fee adjustments or additional service fees. If there's no justification for the higher fee, contact the financial institution in writing to request clarification and correction. If they don't resolve it, you can file a complaint with FINRA or your state securities regulator. In similar cases, institutions have been required to refund the excess fees with interest.",
      },
    ],
  },
]

// Mock document data
export const mockDocumentData = {
  overallRisk: 65,
  riskScores,
  keyFindings: overviewData.keyFindings,
  recommendations: overviewData.recommendations,
  disputeCases: {
    cases: disputeCases,
    totalCases: 24,
    trendData,
  },
  overview: overviewData,
  highlightedClauses,
  disputeSimulations,
}


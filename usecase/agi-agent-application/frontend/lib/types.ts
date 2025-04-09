export interface RiskScore {
  category: string
  score: number
  description: string
}

export interface DisputeCase {
  id: string
  title: string
  status: string
  date: string
  jurisdiction: string
  summary: string
  keyIssues: string[]
  outcome: string
  relevance: string
}


'use client'

import Link from "next/link"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useRouter } from "next/navigation"
import { FormEvent } from "react"

export default function HomePage() {
  const router = useRouter()

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const query = formData.get('query') as string
    if (query?.trim()) {
      router.push(`/analysis?query=${encodeURIComponent(query.trim())}`)
    }
  }
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-background via-accent/30 to-background">
      {/* Header */}
      <header className="border-b border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">P</span>
              </div>
              <h1 className="text-xl font-bold">PIN</h1>
            </div>
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                분석 방법
              </Link>
              <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                데이터 소스
              </Link>
              <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                문의하기
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-3xl space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent text-accent-foreground text-sm font-medium mb-4">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              정치 테마주 관계도 분석 플랫폼
            </div>
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-balance leading-tight">
              정치와 경제의
              <br />
              <span className="text-primary">연결고리</span>를 발견하세요
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground text-balance max-w-2xl mx-auto leading-relaxed">
              정치인과 정책이 어떤 산업과 기업에 영향을 미치는지
              <br className="hidden sm:block" />
              한눈에 파악할 수 있는 인사이트를 제공합니다
            </p>
          </div>

          {/* Search Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                type="text"
                name="query"
                placeholder="정치인 이름 또는 정책을 입력하세요 (예: 이재명, 그린뉴딜)"
                className="pl-12 pr-4 py-6 text-lg rounded-xl border-2 focus:border-primary transition-colors"
                required
              />
            </div>
            <Button type="submit" size="lg" className="w-full py-6 text-lg rounded-xl font-semibold">
              관계도 분석 시작하기
            </Button>
          </form>

          {/* Quick Examples */}
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground text-center">빠른 검색:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {["이재명", "윤석열", "그린뉴딜", "반도체 지원", "법인세 인하"].map((example) => (
                <Link
                  key={example}
                  href={`/analysis?query=${encodeURIComponent(example)}`}
                  className="px-4 py-2 rounded-full bg-muted hover:bg-muted/80 text-sm font-medium transition-colors"
                >
                  {example}
                </Link>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-4 pt-8">
            <div className="p-6 rounded-xl bg-card border border-border space-y-2">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="font-semibold">실시간 분석</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                최신 뉴스와 데이터를 기반으로 실시간 관계도를 생성합니다
              </p>
            </div>
            <div className="p-6 rounded-xl bg-card border border-border space-y-2">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <h3 className="font-semibold">근거 기반</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                모든 연결에 대한 출처와 근거를 투명하게 제공합니다
              </p>
            </div>
            <div className="p-6 rounded-xl bg-card border border-border space-y-2">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                  />
                </svg>
              </div>
              <h3 className="font-semibold">주가 연동</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                관련 기업의 실시간 주가 정보를 함께 확인할 수 있습니다
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center text-sm text-muted-foreground">
            © 2025 PIN. 투자 결정은 본인의 책임하에 이루어져야 합니다.
          </p>
        </div>
      </footer>
    </div>
  )
}

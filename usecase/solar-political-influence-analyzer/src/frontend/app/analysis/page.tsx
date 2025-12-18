import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { AnalysisContent } from "@/components/analysis-content"
import { Skeleton } from "@/components/ui/skeleton"

export default function AnalysisPage() {
  // Query is now handled inside AnalysisContent via useSearchParams

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background sticky top-0 z-50 backdrop-blur-sm bg-background/95">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm" className="gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  <span className="hidden sm:inline">돌아가기</span>
                </Button>
              </Link>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-lg">P</span>
                </div>
                <h1 className="text-xl font-bold">PIN</h1>
              </div>
            </div>
            <div className="text-sm text-muted-foreground hidden md:block">정치 테마주 관계도 분석</div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-6">
        <AnalysisContent />
      </main>
    </div>
  )
}

function AnalysisLoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="border border-border rounded-xl p-8">
        <Skeleton className="h-[600px] w-full" />
      </div>
    </div>
  )
}

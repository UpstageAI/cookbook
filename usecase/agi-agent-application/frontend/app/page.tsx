import { Suspense } from "react"
import { FileUpload } from "@/components/file-upload"
import { DashboardSkeleton } from "@/components/dashboard-skeleton"

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container flex items-center h-16 px-4">
          <h1 className="text-xl font-bold">FinanceGuard</h1>
          <span className="ml-2 text-sm text-muted-foreground">Financial Product Risk Analysis</span>
        </div>
      </header>
      <main className="flex-1 container px-4 py-6">
        <FileUpload />
        <Suspense fallback={<DashboardSkeleton />}>
          <div className="mt-8 text-center text-muted-foreground">
            <p>Upload a financial document to begin analysis</p>
          </div>
        </Suspense>
      </main>
    </div>
  )
}


import { Skeleton } from "@/components/ui/skeleton"

export function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Skeleton className="h-[calc(100vh-8rem)]" />
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <div className="flex gap-2 mb-4">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
        </div>
        <Skeleton className="flex-1" />
      </div>
    </div>
  )
}


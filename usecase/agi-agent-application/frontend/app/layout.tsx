import type React from "react"
import "@/app/globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { AppProvider } from "@/lib/context"
import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "FinanceGuard",
  description: "Financial Product Risk Analysis",
  generator: "v0.dev",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
      <script src="//mozilla.github.io/pdf.js@/build/pdf.js"></script>
      </head>
      <body>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
          <AppProvider>
            {children}
          </AppProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}



import './globals.css'
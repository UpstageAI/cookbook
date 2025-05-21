"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { FileText, ArrowRight, CheckCircle, ChevronRight, Sparkles, Shield, BarChart, Clock, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { LoginForm } from "@/components/login-form"
import { SignupForm } from "@/components/signup-form"
import { motion } from "framer-motion"

export default function LandingPage() {
  const [activeForm, setActiveForm] = useState<"login" | "signup" | null>(null)
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleDemoClick = () => {
    router.push("/dashboard")
  }

  const handleSuccessfulAuth = () => {
    router.push("/dashboard")
  }

  const handlePricingClick = () => {
    router.push("/pricing")
  }

  const features = [
    {
      title: "Smart Document Analysis",
      description: "Upload any document and get instant insights with our advanced AI analysis.",
      icon: <Sparkles className="h-5 w-5" />,
    },
    {
      title: "Action Item Extraction",
      description: "Automatically identify and extract action items from meeting notes and documents.",
      icon: <CheckCircle className="h-5 w-5" />,
    },
    {
      title: "Data Visualization",
      description: "Transform tables and numbers into beautiful, insightful charts and graphs.",
      icon: <BarChart className="h-5 w-5" />,
    },
    {
      title: "Secure Document Handling",
      description: "Enterprise-grade security ensures your sensitive documents remain protected.",
      icon: <Shield className="h-5 w-5" />,
    },
    {
      title: "Time-Saving Automation",
      description: "Save hours of manual work with automated document processing and organization.",
      icon: <Clock className="h-5 w-5" />,
    },
    {
      title: "Team Collaboration",
      description: "Share insights and summaries with your team for better collaboration.",
      icon: <Users className="h-5 w-5" />,
    },
  ]

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-purple-500/5 to-background -z-10 pointer-events-none" />
      <div className="absolute inset-0 bg-[url('/placeholder.svg?height=800&width=1600')] bg-top bg-no-repeat opacity-5 -z-10 pointer-events-none" />

      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-md bg-gradient-to-r from-background/95 via-primary/5 to-background/95 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center max-w-7xl">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-gradient-to-br from-primary to-purple-600 p-1.5 shadow-lg">
              <FileText className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl tracking-tight">DocZilla</span>
          </div>
          <div className="flex gap-4 items-center">
            <nav className="hidden md:flex gap-8 mr-4">
              <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Features
              </a>
              <button onClick={handlePricingClick} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Pricing
              </button>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Documentation
              </a>
            </nav>
            <Button variant="ghost" onClick={() => setActiveForm("login")} className="text-sm">
              Log in
            </Button>
            <Button onClick={() => setActiveForm("signup")} className="text-sm">
              Sign up
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        {/* Hero section */}
        
        <section className="py-0 md:py-20 relative overflow-hidden scale-95">
          <div className="container mx-auto px-4 max-w-7xl relative z-10">
            <div className="grid md:grid-cols-2 gap-8 md:gap-4 items-center">
              <div className="md:pr-10">
                {mounted && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight leading-tight">
                    Make Documents Work for You with <span className="text-primary">AGI-Powered Understanding</span>
                    </h1>
                    <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                      Upload any document and let our AGI assistant analyze, extract, and take action on your behalf.
                      Save hours of manual work.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4">
                      <Button
                        size="lg"
                        onClick={() => setActiveForm("signup")}
                        className="rounded-full px-8 shadow-lg hover:shadow-primary/20 hover:scale-105 transition-all duration-200 gap-2"
                      >
                        Get Started <ArrowRight className="h-4 w-4" />
                      </Button>
                      <Button
                        size="lg"
                        variant="outline"
                        onClick={handleDemoClick}
                        className="rounded-full px-8 hover:bg-primary/5 transition-all duration-200"
                      >
                        Try Demo
                      </Button>
                    </div>
                  </motion.div>
                )}
              </div>
              {mounted && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  className="relative md:pl-8 md:pr-10"
                >

                  <div className="bg-gradient-to-br from-card via-card/95 to-card/90 rounded-2xl border border-border/50 shadow-xl overflow-hidden relative backdrop-blur-sm">
                    <div className="aspect-[4/3] bg-gradient-to-br from-background/80 to-muted/90 p-8 flex items-center justify-center">
                      <div className="text-center max-w-md">
                        <div className="rounded-full bg-gradient-to-br from-primary/20 to-purple-500/20 p-4 w-fit mx-auto mb-6">
                          <FileText className="h-16 w-16 text-primary" />
                        </div>
                        <h3 className="text-2xl font-semibold mb-4">Intelligent Document Processing</h3>
                        <p className="text-muted-foreground">
                          Upload PDFs, images, and documents for instant analysis and actionable insights.
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </section>

        {/* Features section */}
        <section id="features" className="py-15 md:py-30 bg-muted/30 relative mt-40">
          <div className="absolute inset-0 bg-gradient-to-b from-background to-transparent h-40 -top-40"></div>
          <div className="container mx-auto px-4 max-w-7xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Powerful Features</h2>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Our AI-powered platform helps you extract value from your documents with minimal effort.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  whileHover={{ y: -5, transition: { duration: 0.2 } }}
                  className="bg-card rounded-xl p-6 border border-border/50 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <div className="rounded-full bg-primary/10 p-3 w-fit mb-4">
                    <div className="text-primary">{feature.icon}</div>
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA section */}
        <section className="py-20 md:py-32">
          <div className="container mx-auto px-4 max-w-7xl">
            <div className="bg-gradient-to-r from-primary/10 to-purple-500/10 rounded-3xl p-12 md:p-16 text-center">
              <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to transform your document workflow?</h2>
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                Join thousands of professionals who save hours every week with DocZilla.
              </p>
              <Button
                size="lg"
                onClick={() => setActiveForm("signup")}
                className="rounded-full px-8 shadow-lg hover:shadow-primary/20 hover:scale-105 transition-all duration-200 gap-2"
              >
                Start Free Trial <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-muted/30 border-t border-border/40 py-12 md:py-16">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="rounded-md bg-primary p-1">
                  <FileText className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="font-bold text-lg">DocZilla</span>
              </div>
              <p className="text-sm text-muted-foreground mb-4">AI-powered document intelligence for modern teams.</p>
            </div>
            <div>
              <h4 className="font-medium mb-4">Product</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Integrations
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Changelog
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-4">Resources</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    API
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Guides
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Support
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-4">Company</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    Contact
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border/40 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-muted-foreground mb-4 md:mb-0">© 2025 DocZilla. All rights reserved.</p>
            <div className="flex gap-6">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Terms
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Privacy
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Cookies
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* Auth modal */}
      {activeForm && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="bg-card rounded-xl border border-border shadow-lg max-w-md w-full p-8 relative"
          >
            <button
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
              onClick={() => setActiveForm(null)}
            >
              ✕
            </button>
            {activeForm === "login" ? (
              <>
                <h2 className="text-2xl font-bold mb-6">Log in to DocZilla</h2>
                <LoginForm onSuccess={handleSuccessfulAuth} />
                <div className="mt-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    Don't have an account?{" "}
                    <button className="text-primary hover:underline" onClick={() => setActiveForm("signup")}>
                      Sign up
                    </button>
                  </p>
                </div>
              </>
            ) : (
              <>
                <h2 className="text-2xl font-bold mb-6">Create your account</h2>
                <SignupForm onSuccess={handleSuccessfulAuth} />
                <div className="mt-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    Already have an account?{" "}
                    <button className="text-primary hover:underline" onClick={() => setActiveForm("login")}>
                      Log in
                    </button>
                  </p>
                </div>
              </>
            )}
          </motion.div>
        </div>
      )}
    </div>
  )
}

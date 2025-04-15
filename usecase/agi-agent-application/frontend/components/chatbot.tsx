"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Sparkles, Copy, Check, AlertTriangle, Scale, Briefcase, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import ReactMarkdown from "react-markdown"
import { BackendResponse } from '@/types/chat'
import { useAppContext } from "@/lib/context"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Separator } from "@/components/ui/separator"

interface ChatbotProps {
  selectedText: string
  isLoading: boolean
  onHighlightsReceived?: (highlights: string[]) => void
}

type MessageContentType = "text" | "dispute-cases" | "simulation" | "highlighted-clause" | "dispute-case" | "dispute-simulation" | "risky_clause"

interface DisputeCase {
  id: string
  title: string
  summary: string
  keyPoints: string[]
  judgmentResult: string
  relevance: string
}

interface DisputeSimulation {
  situation: string
  conversation: {
    role: "user" | "consultant"
    content: string
  }[]
}

interface DisputeGroup {
  name: string
  simulations: DisputeSimulation[]
}

interface HighlightedClause {
  text: string
  risk: "High" | "Medium" | "Low"
  explanation: string
  precedents: {
    title: string
    summary: string
  }[]
}
//Risky_Commnents Interface Definition
interface Risky_Clause {
  text: string,
  risk: string,
  similarity: number
}


interface MessageContent {
  type: MessageContentType
  text?: string
  disputeCase?: DisputeCase
  disputes?: DisputeCase[]
  disputeSimulation?: DisputeSimulation
  disputeGroups?: DisputeGroup[]
  highlightedClause?: HighlightedClause
  risky_clause?: Risky_Clause
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: MessageContent
}

export function Chatbot({ selectedText, isLoading, onHighlightsReceived }: ChatbotProps) {
  
  // System Intro Message
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: {
        type: "text",
        text: `<div class="welcome-message">
<div class="welcome-header">
<h3>안녕하세요! 저는 여러분의 FinanceGuard AI 어시스턴트입니다.</h3>
<p>저희 서비스는 금융상품 문서를 쉽게 이해할 수 있도록 도와드리며, 특히 금융상품에 내재된 위험성을 파악하는 데 중점을 두고 있습니다.</p>
</div>
<div class="example-questions">
<h4>💡 다음과 같은 질문들을 해보면 좋아요</h4>
<ul>
<li><span class="tag risk">위험</span> 이 문서에 나타난 주요 위험 요소는 무엇인가요?</li>
<li><span class="tag case">판례</span> 수수료와 관련된 분쟁 사례를 보여주세요.</li>
<li><span class="tag simulation">시뮬레이션</span> 조기 인출 벌금에 대한 분쟁을 시뮬레이션 해주세요.</li>
<li><span class="tag highlight">조항</span> 수수료와 관련된 유해한 조항을 하이라이트 해주세요.</li>
</ul>
</div>
<div class="welcome-footer">
<p>이러한 정보를 통해 금융상품 구매 전에 잠재적 리스크를 명확하게 파악하고, 보다 안전한 재테크 결정을 내리실 수 있도록 지원합니다.</p>
</div>
</div>`,
      },
    },
  ])

  // User Input
  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const { setActiveTab, setSelectedDisputeId } = useAppContext()
  const [selectedDisputeCase, setSelectedDisputeCase] = useState<DisputeCase | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  // Update input when text is selected from PDF (아직 구현 안함.)
  useEffect(() => {
    if (selectedText) {
      setInput(selectedText)
      if (inputRef.current) {
        inputRef.current.focus()
      }
    }
  }, [selectedText])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: {
        type: "text",
        text: input,
      },
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsTyping(true)

    try {
      // 백엔드 API 호출
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const backendResponse: BackendResponse = await response.json();
      
      // 하이라이트 정보가 있으면 부모 컴포넌트에 전달
      if (backendResponse.highlights && Array.isArray(backendResponse.highlights) && onHighlightsReceived) {
        onHighlightsReceived(backendResponse.highlights);
      }
      
      let assistantMessage: Message;
      
      // 백엔드 응답 타입에 따라 메시지 생성
      switch (backendResponse.type) {
        case 'simple_dialogue':
          assistantMessage = {
            id: Date.now().toString(),
            role: "assistant",
            content: {
              type: "text",
              text: backendResponse.message,
            },
          };
          break;
          
        case 'highlighted_clause':
          // 하이라이트 정보를 부모 컴포넌트에 전달
          if (backendResponse.highlights && Array.isArray(backendResponse.highlights) && onHighlightsReceived) {
            onHighlightsReceived(backendResponse.highlights);
          }
          
          // 하이라이트 설명 메시지 생성
          assistantMessage = {
            id: Date.now().toString(),
            role: "assistant",
            content: {
              type: "text",
              text: `<div class="highlight-explanation">
                <h4>🔍 독소 조항 하이라이트</h4>
                <p>${backendResponse.message}</p>
                <div class="highlight-info">
                  <span class="badge bg-blue-100 text-blue-800 px-2 py-1 rounded">파란색 하이라이트로 PDF에 표시됨</span>
                </div>
              </div>`,
            },
          };
          break;
          
        case 'highlights':
          // 하이라이트 정보를 부모 컴포넌트에 전달
          if (backendResponse.highlights && Array.isArray(backendResponse.highlights) && onHighlightsReceived) {
            onHighlightsReceived(backendResponse.highlights);
          }
          
          // 하이라이트 설명 메시지 생성
          assistantMessage = {
            id: Date.now().toString(),
            role: "assistant",
            content: {
              type: "text",
              text: `<div class="highlight-explanation">
                <p>${backendResponse.rationale}</p>
                <p>PDF 내에 관련 독소조항을 파란색으로 표시했어요 🧐</p>
                <ul class="space-y-2 mt-2">
                  ${backendResponse.highlights.map(text => `
                  <li class="flex items-start gap-2">
                    <span class="text-blue-500 mt-0.5">✓</span>
                    <span class="text-sm bg-blue-50/50 px-2 py-1 rounded">${text}</span>
                  </li>`).join('')}
                </ul>
              </div>`,
            },
          };
          break;
          
        case 'simulation':
          if (backendResponse.disputeGroups && backendResponse.disputeGroups.length > 0) {
            // disputeGroups 형식을 DisputeGroup 인터페이스에 맞게 변환
            const transformedGroups: DisputeGroup[] = backendResponse.disputeGroups.map(group => {
              // 각 그룹에 대해 situation별로 대화 쌍을 구성
              const situationMap = new Map<string, {userMsg?: string, consultantMsg?: string}>();
              
              // 먼저 모든 메시지를 situation별로 분류
              group.simulations.forEach(sim => {
                if (!situationMap.has(sim.situation)) {
                  situationMap.set(sim.situation, {});
                }
                
                const entry = situationMap.get(sim.situation);
                if (sim.role === 'user') {
                  entry!.userMsg = sim.content || "";
                } else if (sim.role === 'consultant') {
                  entry!.consultantMsg = sim.content || "";
                }
              });
              
              // situation별로 user와 consultant 대화 쌍 구성
              const simulations: DisputeSimulation[] = [];
              situationMap.forEach((msgs, situation) => {
                // 대화 배열에 user와 consultant 메시지를 추가
                const conversation = [];
                
                // user 메시지가 있으면 추가
                if (msgs.userMsg) {
                  conversation.push({
                    role: "user" as const,
                    content: msgs.userMsg
                  });
                }
                
                // consultant 메시지가 있으면 추가
                if (msgs.consultantMsg) {
                  conversation.push({
                    role: "consultant" as const,
                    content: msgs.consultantMsg
                  });
                }
                
                // 대화가 있으면 시뮬레이션 추가
                if (conversation.length > 0) {
                  simulations.push({
                    situation,
                    conversation
                  });
                }
              });
              
              return {
                name: group.name,
                simulations
              };
            });

            assistantMessage = {
              id: Date.now().toString(),
              role: "assistant",
              content: {
                type: "dispute-simulation",
                text: backendResponse.message || "Here's a simulation of how disputes might play out:",
                disputeGroups: transformedGroups
              },
            };
          } else if (backendResponse.simulations && backendResponse.simulations.length > 0) {
            // 모든 시뮬레이션 항목을 그룹화하고 각각 개별 시뮬레이션으로 만들기
            const simulations: DisputeSimulation[] = [];
            
            // 각 situation별로 메시지 구성
            const situationMap = new Map<string, Array<{role: 'user' | 'consultant', content: string}>>();
            
            // 모든 시뮬레이션 항목을 순회하면서 처리
            backendResponse.simulations.forEach(sim => {
              const situation = sim.situation;
              
              // user/consultant 키 확인
              if ('user' in sim && sim.user) {
                if (!situationMap.has(situation)) {
                  situationMap.set(situation, []);
                }
                situationMap.get(situation)!.push({
                  role: 'user',
                  content: sim.user
                });
              }
              
              if ('consultant' in sim && sim.consultant) {
                if (!situationMap.has(situation)) {
                  situationMap.set(situation, []);
                }
                situationMap.get(situation)!.push({
                  role: 'consultant',
                  content: sim.consultant
                });
              }
            });
            
            // Map을 배열로 변환하여 각 상황별 시뮬레이션 생성
            for (const [situation, conversations] of situationMap.entries()) {
              simulations.push({
                situation,
                conversation: conversations
              });
            }
            
            // 시뮬레이션이 있으면 표시
            if (simulations.length > 0) {
              assistantMessage = {
                id: Date.now().toString(),
                role: "assistant",
                content: {
                  type: "dispute-simulation",
                  text: backendResponse.message || "Here's a simulation of how disputes might play out:",
                  // 가상의 그룹 이름으로 그룹화
                  disputeGroups: [
                    {
                      name: "투자 상품 관련 시뮬레이션",
                      simulations: simulations
                    }
                  ]
                },
              };
            } else {
              // 시뮬레이션 데이터가 없는 경우
              assistantMessage = {
                id: Date.now().toString(),
                role: "assistant",
                content: {
                  type: "text",
                  text: "시뮬레이션 데이터를 받을 수 없습니다. 다시 시도해 주세요.",
                },
              };
            }
          } else {
            // 시뮬레이션 데이터가 없는 경우
            assistantMessage = {
              id: Date.now().toString(),
              role: "assistant",
              content: {
                type: "text",
                text: "시뮬레이션 데이터를 받을 수 없습니다. 다시 시도해 주세요.",
              },
            };
          }
          break;
          
        case 'cases':
          assistantMessage = {
            id: Date.now().toString(),
            role: "assistant",
            content: {
              type: "dispute-cases",
              text: backendResponse.message || "금융 분쟁 사례들입니다. 자세한 내용을 보려면 사례를 클릭하세요:",
              disputes: backendResponse.disputes && backendResponse.disputes.length > 0 
                ? backendResponse.disputes.map((dispute, index) => ({
                    id: `DC-${Date.now()}-${index}`,
                    title: dispute.title,
                    summary: dispute.summary,
                    keyPoints: dispute['key points'].split('\n'),
                    judgmentResult: dispute['judge result'],
                    relevance: "이 사례가 귀하의 질문과 관련이 있습니다.",
                  }))
                : [],
            },
          };
          break;
          
        default:
          assistantMessage = {
            id: Date.now().toString(),
            role: "assistant",
            content: {
              type: "text",
              text: "응답을 받았지만 처리할 수 없는 형식입니다. 다시 시도해 주세요.",
            },
          };
      }
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      
      // 심각하지 않은 오류는 메시지로 표시
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: {
          type: "text",
          text: "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        },
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }

  const handleCopyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)

    toast({
      title: "Copied to clipboard",
      description: "The message has been copied to your clipboard",
    })
  }

  // 분쟁 사례 상세보기 모달을 여는 함수
  const handleViewDisputeDetails = (dispute: DisputeCase) => {
    setSelectedDisputeCase(dispute);
    setIsDialogOpen(true);
  }

  const renderMessageContent = (message: Message) => {
    const { content } = message

    switch (content.type) {
      case "text":
        // 환영 메시지인 경우 HTML로 직접 렌더링
        if (content.text?.includes('<div class="welcome-message">') || content.text?.includes('<div class="highlight-explanation">')) {
          return (
            <div 
              className="prose prose-sm prose-p:my-0.5 prose-headings:my-0.5 prose-ul:my-0.5 prose-li:my-0 dark:prose-invert max-w-none leading-tight"
              dangerouslySetInnerHTML={{ 
                __html: content.text
                  .replace('class="welcome-message"', 'class="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg p-1.5 shadow-sm"')
                  .replace('class="welcome-header"', 'class="mb-0"')
                  .replace('class="example-questions"', 'class="bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm mb-0 mt-0"')
                  .replace('class="welcome-footer"', 'class="text-sm text-gray-600 dark:text-gray-300 italic mt-0"')
                  .replace('class="highlight-explanation"', 'class="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg p-2 shadow-sm"')
                  .replace('class="highlight-info"', 'class="my-2 flex justify-center"')
                  .replace(/<h3>/g, '<h3 class="text-base font-semibold mb-0 mt-0 text-primary leading-none">')
                  .replace(/<h4>/g, '<h4 class="text-base font-semibold mb-2 mt-0 flex items-center leading-none text-blue-700">')
                  .replace(/<p>/g, '<p class="leading-normal mb-2 mt-0">')
                  .replace(/><p>/g, '><p class="mt-0">')
                  .replace(/<ul>/g, '<ul class="my-0 space-y-1">')
                  .replace(/<li>/g, '<li class="my-0 leading-normal">')
                  .replace(/class="tag risk"/g, 'class="inline-block mr-1 px-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100 text-xs font-medium rounded"')
                  .replace(/class="tag case"/g, 'class="inline-block mr-1 px-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100 text-xs font-medium rounded"')
                  .replace(/class="tag simulation"/g, 'class="inline-block mr-1 px-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100 text-xs font-medium rounded"')
                  .replace(/class="tag highlight"/g, 'class="inline-block mr-1 px-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100 text-xs font-medium rounded"')
                  .replace(/class="badge/g, 'class="inline-block px-2 py-1 text-sm font-medium rounded')
                  .replace(/class="mt-2"/g, 'class="mt-3 bg-white dark:bg-gray-800 rounded-lg p-2"')
              }} 
            />
          )
        }
        
        // 일반 텍스트 메시지는 ReactMarkdown으로 렌더링
        return (
          <div className="prose prose-sm prose-p:my-0.5 prose-headings:my-0.5 prose-ul:my-0.5 prose-li:my-0 dark:prose-invert max-w-none leading-tight">
            <ReactMarkdown>
              {content.text || ""}
            </ReactMarkdown>
          </div>
        )

      case "dispute-case":
        return (
          <div className="space-y-3">
            {content.text && <p>{content.text}</p>}
            {content.disputeCase && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Briefcase className="h-4 w-4" />
                    {content.disputeCase.title}
                  </CardTitle>
                  <CardDescription>Case #{content.disputeCase.id}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div>
                    <p className="font-medium mb-1">Summary</p>
                    <p>{content.disputeCase.summary}</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1">Key Points</p>
                    <ul className="list-disc list-inside space-y-1">
                      {content.disputeCase.keyPoints.map((point, index) => (
                        <li key={index}>{point}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium mb-1">Judgment</p>
                    <p>{content.disputeCase.judgmentResult}</p>
                  </div>
                  <div className="bg-amber-50 p-3 rounded-md border border-amber-200">
                    <p className="font-medium mb-1 text-amber-800">Relevance to Your Document</p>
                    <p className="text-amber-800">{content.disputeCase.relevance}</p>
                  </div>
                  <div className="flex justify-end">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => content.disputeCase?.id && handleViewDisputeDetails(content.disputeCase)}
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Full Case Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )

      case "dispute-simulation":
        return (
          <div className="space-y-4">
            {content.text && <p>{content.text}</p>}
            
            {/* 새로운 disputeGroups 형식 처리 */}
            {content.disputeGroups && content.disputeGroups.map((group, groupIndex) => (
              <div key={`group-${groupIndex}`} className="space-y-4">
                <h3 className="text-sm font-medium">{group.name}</h3>
                {group.simulations.map((sim, simIndex) => (
                  <Card key={`sim-${groupIndex}-${simIndex}`}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Scale className="h-4 w-4" />
                        Dispute Simulation
                      </CardTitle>
                      <CardDescription>How a potential dispute might be resolved</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3 text-sm">
                      <div className="bg-muted p-3 rounded-md">
                        <p className="font-medium mb-1">Situation</p>
                        <p>{sim.situation}</p>
                      </div>
                      <div>
                        <p className="font-medium mb-1">Conversation</p>
                        <div className="space-y-3">
                          {sim.conversation.map((item, index) => (
                            <div
                              key={index}
                              className={`flex gap-2 ${item.role === "consultant" ? "justify-start" : "justify-end"}`}
                            >
                              <div
                                className={`rounded-lg px-3 py-2 max-w-[90%] ${
                                  item.role === "consultant" ? "bg-muted" : "bg-primary text-primary-foreground"
                                }`}
                              >

                                <p>{item.content}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ))}

            {/* 기존 disputeSimulation 형식 처리 (하위 호환성 유지) */}
            {content.disputeSimulation && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Scale className="h-4 w-4" />
                    Dispute Simulation
                  </CardTitle>
                  <CardDescription>How a potential dispute might be resolved</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="bg-muted p-3 rounded-md">
                    <p className="font-medium mb-1">Situation</p>
                    <p>{content.disputeSimulation.situation}</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1">Conversation</p>
                    <div className="space-y-3">
                      {content.disputeSimulation.conversation.map((item, index) => (
                        <div
                          key={index}
                          className={`flex gap-2 ${item.role === "consultant" ? "justify-start" : "justify-end"}`}
                        >
                          <div
                            className={`rounded-lg px-3 py-2 max-w-[90%] ${
                              item.role === "consultant" ? "bg-muted" : "bg-primary text-primary-foreground"
                            }`}
                          >
                            <div className="text-xs font-medium mb-1">
                              {item.role === "consultant" ? "Financial Consultant" : "You"}
                            </div>
                            <p>{item.content}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )

      case "highlighted-clause":
        return (
          <div className="space-y-3">
            {content.text && <p>{content.text}</p>}
            {content.highlightedClause && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Highlighted Clause
                    <Badge
                      variant="outline"
                      className={`ml-auto ${
                        content.highlightedClause.risk === "High"
                          ? "bg-red-50 text-red-700 border-red-200"
                          : content.highlightedClause.risk === "Medium"
                            ? "bg-amber-50 text-amber-700 border-amber-200"
                            : "bg-green-50 text-green-700 border-green-200"
                      }`}
                    >
                      {content.highlightedClause.risk} Risk
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="bg-muted p-3 rounded-md border-l-4 border-red-500">
                    <p className="italic">"{content.highlightedClause.text}"</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1">Analysis</p>
                    <p>{content.highlightedClause.explanation}</p>
                  </div>
                  <div>
                    <p className="font-medium mb-1">Related Precedents</p>
                    <div className="space-y-2">
                      {content.highlightedClause.precedents.map((precedent, index) => (
                        <div key={index} className="bg-muted/50 p-2 rounded-md">
                          <p className="font-medium text-xs">{precedent.title}</p>
                          <p className="text-xs">{precedent.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )

      case "dispute-cases":
        return (
          <div className="space-y-3">
            {content.text && <p>{content.text}</p>}
            {content.disputes && content.disputes.length > 0 ? (
              <div className="space-y-2">
                {content.disputes.map((dispute) => (
                  <Card key={dispute.id} className="hover:bg-muted/50 transition-colors cursor-pointer">
                    <CardContent className="p-3">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-medium">{dispute.title}</h4>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="h-8 px-2"
                            onClick={() => handleViewDisputeDetails(dispute)}
                          >
                            <ExternalLink className="h-4 w-4" />
                            <span className="sr-only">View details</span>
                          </Button>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2">{dispute.summary}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">관련 분쟁 사례를 찾을 수 없습니다.</p>
            )}
          </div>
        )

      default:
        return <p>Unsupported message type</p>
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 p-4">
          <div className="space-y-4">
            <div className="flex gap-3">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-16 w-64" />
              </div>
            </div>
          </div>
        </div>
        <div className="border-t p-4">
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}>
              {message.role === "assistant" && (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
              )}
              <div
                className={`relative group rounded-lg px-3 py-2 max-w-[85%] ${
                  message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                {message.role === "assistant" && (
                  <button
                    onClick={() => {
                      const textContent =
                        message.content.type === "text" ? message.content.text || "" : JSON.stringify(message.content)
                      handleCopyMessage(message.id, textContent)
                    }}
                    className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label="Copy message"
                  >
                    {copiedId === message.id ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4 text-muted-foreground" />
                    )}
                  </button>
                )}
                <div className="space-y-1">
                  <div className="text-xs font-medium">{message.role === "user" ? "You" : "FinanceGuard AI"}</div>
                  <div className="text-sm whitespace-pre-wrap">{renderMessageContent(message)}</div>
                </div>
              </div>
              {message.role === "user" && (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary">
                  <User className="h-5 w-5 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
          {isTyping && (
            <div className="flex gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <div className="rounded-lg px-3 py-2 bg-muted max-w-[80%]">
                <div className="space-y-1">
                  <div className="text-xs font-medium">FinanceGuard AI</div>
                  <div className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-primary animate-bounce" />
                    <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:0.2s]" />
                    <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:0.4s]" />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      <div className="border-t p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSendMessage()
          }}
          className="flex items-center gap-2"
        >
          <Input
            ref={inputRef}
            placeholder="Ask about the document or selected text..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={!input.trim() || isTyping}>
            {isTyping ? <Sparkles className="h-5 w-5 animate-pulse" /> : <Send className="h-5 w-5" />}
            <span className="sr-only">Send message</span>
          </Button>
        </form>
      </div>
      
      {/* 분쟁 사례 상세 정보 모달 */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        {selectedDisputeCase && (
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-xl">{selectedDisputeCase.title}</DialogTitle>
              <DialogDescription>사례 #{selectedDisputeCase.id}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-1">요약</h4>
                <p className="text-sm">{selectedDisputeCase.summary}</p>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-1">주요 쟁점</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {selectedDisputeCase.keyPoints.map((point, index) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-1">판결 결과</h4>
                <p className="text-sm">{selectedDisputeCase.judgmentResult}</p>
              </div>
              <Separator />
              <div>
                <h4 className="font-medium mb-1">문서와의 관련성</h4>
                <div className="flex items-start gap-2 bg-amber-50 p-3 rounded-md border border-amber-200">
                  <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800">{selectedDisputeCase.relevance}</p>
                </div>
              </div>
            </div>
          </DialogContent>
        )}
      </Dialog>
    </div>
  )
}


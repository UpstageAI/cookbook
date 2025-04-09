// Summary API Types
export interface SummaryRequest {
  pdfId: string;
  systemPrompt: string;
}

export interface SummaryResponse {
  summary: {
    returns: number;
    riskLevel: string;
    keyTerms: string[];
    importantClauses: string[];
  };
}

// Highlight API Types
export interface HighlightRequest {
  pdfId: string;
  prompt: string;
}

export interface HighlightResponse {
  clauses: Array<{
    text: string;
    position: {
      pageNumber: number;
      boundingRect: {
        x1: number;
        y1: number;
        x2: number;
        y2: number;
        width: number;
        height: number;
      };
    };
    relatedCases: Array<{
      id: string;
      title: string;
      summary: string;
      keyPoints: string[];
      result: string;
    }>;
  }>;
}

// Chat API Types
export interface ChatRequest {
  query: string;
}

export interface ChatResponse {
  response: string;
  sources?: Array<{
    url: string;
    title: string;
    snippet: string;
  }>;
}

// Simulation API Types
export interface SimulationRequest {
  pdfId: string;
  query: string;
}

export interface SimulationResponse {
  simulation: {
    situation: string;
    conversation: Array<{
      role: 'user' | 'counselor';
      content: string;
    }>;
  };
}

// Cases API Types
export interface CasesRequest {
  query: string;
}

export interface CasesResponse {
  cases: Array<{
    title: string;
    summary: string;
    keyPoints: string[];
    result: string;
  }>;
}

// PDF Upload API Types
export interface PdfUploadResponse {
  pdfId: string;
  url: string;
  fileName: string;
  fileSize: number;
  uploadDate: string;
  status: 'success' | 'error';
} 
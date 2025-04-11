"use client"

import React, { createContext, useContext, useState, ReactNode } from 'react';

// 앱 전체 상태를 관리하는 컨텍스트
interface AppContextType {
  // 선택된 분쟁 사례 ID (Disputes 탭으로 이동 시 사용)
  selectedDisputeId: string | null;
  setSelectedDisputeId: (id: string | null) => void;
  
  // 현재 활성화된 탭 (Overview, Disputes, Chat 등)
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedDisputeId, setSelectedDisputeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');

  return (
    <AppContext.Provider 
      value={{ 
        selectedDisputeId, 
        setSelectedDisputeId,
        activeTab,
        setActiveTab
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

// 컨텍스트 훅
export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
} 
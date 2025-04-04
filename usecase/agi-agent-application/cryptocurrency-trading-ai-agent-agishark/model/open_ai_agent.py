import streamlit as st
import asyncio
import sys
import pandas as pd
import json
import logging
import os
import datetime
import traceback
from typing import Dict, List, Optional, Any
import threading
from datetime import timedelta

import pyupbit

from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, ModelSettings, function_tool, set_default_openai_key, RunConfig, WebSearchTool, FunctionTool
from tools.document_parser.document_parser import DocumentParser
from tools.information_extract.informaton_extract import information_extract
from tools.rag.agent_tools import search_rag_documents
from tools.upbit.upbit_api import get_available_coins_func, get_coin_price_info_func, buy_coin_func, sell_coin_func, check_order_status_func
from tools.search_X.search_X_tool import search_x_tool

def get_model_name(model_options):
    if model_options == "claude 3.7 sonnet":
        return "claude-3-7-sonnet-latest"
    elif model_options == "claude 3 haiku":
        return "claude-3-haiku-20240307"
    elif model_options == "gpt 4o mini":
        return "gpt-4o-mini"
    elif model_options == "gpt 4o":
        return "gpt-4o"
    elif model_options == "o3 mini":
        return "o3-mini"

# 문서에서 정보 추출하는 tool 생성
@function_tool
def extract_information_tool(img_path: str, fields_to_extract: str, required_fields: Optional[List[str]] = None):
    """
    이미지에서 지정된 정보를 추출합니다.
    
    Args:
        img_path: 이미지 파일 경로
        fields_to_extract: 추출할 필드와 설명 (JSON 형식의 문자열로 전달, 예: {"bank_name": "은행 이름", "amount": "거래 금액"})
        required_fields: 필수 필드 목록 (선택 사항)
    
    Returns:
        Dict: 추출된 정보 또는 오류
    """
    # 문자열을 딕셔너리로 변환
    import json
    try:
        fields_dict = json.loads(fields_to_extract)
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': '필드 정보가 유효한 JSON 형식이 아닙니다.'
        }
    
    # 스키마 속성 구성
    schema_properties = {}
    for field_name, description in fields_dict.items():
        schema_properties[field_name] = {
            "type": "string",
            "description": description
        }
    
    # information_extract 함수 호출
    return information_extract(img_path, schema_properties, required_fields)

# 문서 파싱 도구
@function_tool
def parse_document_tool(file_names: List[str]):
    """
    PDF 문서를 파싱하여 텍스트를 추출합니다.
    
    Args:
        file_names: PDF 파일 이름 목록 (확장자 없이)
    
    Returns:
        Dict: 문서 파싱 결과를 담은 딕셔너리
    """
    parser = DocumentParser()
    return parser.parse_document(file_names)

# Agent 객체 생성 함수
def create_agent(model_options):
    """
    Agent 객체를 생성합니다.
    """
    # 세션 상태에서 API 키 설정
    if 'openai_key' in st.session_state and st.session_state.openai_key:
        set_default_openai_key(st.session_state.openai_key)
    else:
        st.error("OpenAI API 키가 설정되지 않았습니다. API 설정 페이지에서 키를 입력해주세요.")
        return None
    
    # 투자 성향 정보 가져오기
    user_requirement = st.session_state.get('user_requirement', '')
    risk_style = st.session_state.get('risk_style', '공격적')
    period_style = st.session_state.get('period_style', '단기')
    
    # 포트폴리오 정보 가져오기
    portfolio_info = ""
    try:
        from page.portfolio import get_portfolio_info_from_trade
        from page.api_setting import get_upbit_trade_instance
        
        upbit_trade = get_upbit_trade_instance()
        if upbit_trade:
            portfolio_summary, coin_balances = get_portfolio_info_from_trade(upbit_trade)
            if portfolio_summary:
                portfolio_info += "\n\n# 사용자 포트폴리오 정보\n"
                portfolio_info += f"- 총 보유자산: {portfolio_summary.get('총보유자산', 0):,.0f} KRW\n"
                portfolio_info += f"- 총 평가손익: {portfolio_summary.get('총평가손익', 0):,.0f} KRW ({portfolio_summary.get('총수익률', 0):.2f}%)\n"
                portfolio_info += f"- 일평가수익률: {portfolio_summary.get('일평가수익률', 0):.2f}%\n"
                portfolio_info += f"- 보유 현금: {portfolio_summary.get('보유현금', 0):,.0f} KRW\n"
                portfolio_info += f"- 코인 평가금액: {portfolio_summary.get('코인평가금액', 0):,.0f} KRW\n"
                
                if not coin_balances.empty:
                    portfolio_info += "\n## 보유 코인 목록\n"
                    for idx, row in coin_balances.iterrows():
                        portfolio_info += f"- {row['코인']}: {row['수량']:.8f} 개, 평가금액: {row['평가금액']:,.0f} KRW, 수익률: {row['수익률']:.2f}%\n"
    except Exception as e:
        print(f"포트폴리오 정보 로딩 중 오류: {str(e)}")
    
    # 현재 날짜와 시간 정보 생성
    current_datetime = datetime.datetime.now()
    current_date_str = current_datetime.strftime("%Y년 %m월 %d일")
    current_time_str = current_datetime.strftime("%H시 %M분")
    current_weekday = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][current_datetime.weekday()]
    
    # pdf_files 디렉토리가 없을 경우 대비한 예외 처리
    pdf_files_base = []
    try:
        pdf_files = [f for f in os.listdir("tools/web2pdf/always_see_doc_storage") if f.endswith('.pdf')]
        pdf_files_base = [os.path.splitext(f)[0] for f in pdf_files]
    except (FileNotFoundError, OSError) as e:
        log_error(e, "PDF 파일 목록 조회 오류")
    
    # 이전 메시지 가져오기
    previous_messages = st.session_state.get('messages', [])
    context = ""
    
    # 최근 대화 기록을 context에 추가 (최대 5개 메시지)
    if len(previous_messages) > 1:  # 첫 메시지는 AI 인사말이므로 건너뜀
        context = "이전 대화 내용:\n"
        for i, msg in enumerate(previous_messages[-6:-1]):  # 최근 5개 메시지만
            if msg["role"] == "user":
                context += f"사용자: {msg['content']}\n"
            elif msg["role"] == "assistant":
                context += f"AI: {msg['content']}\n"
        context += "\n"
    
    # 자동 거래 에이전트 정보 추가
    auto_trader_info = ""
    if 'auto_trader' in st.session_state and st.session_state.auto_trader:
        trader = st.session_state.auto_trader
        
        # 자동 거래 에이전트 설정 정보
        auto_trader_info += "\n\n# 자동 거래 에이전트 정보\n"
        auto_trader_info += f"자동 거래 에이전트는 사용자의 계정에서 자동으로 거래를 실행할 수 있습니다.\n"
        
        if trader.is_running:
            status_info = trader.get_status()
            auto_trader_info += f"현재 상태: **실행 중**\n"
            auto_trader_info += f"설정: 분석 간격 {trader.interval_minutes}분, 최대 투자금 {trader.max_investment:,}원, "
            auto_trader_info += f"일일 최대 거래 횟수 {trader.max_trading_count}회 (현재 {status_info['daily_trading_count']}회 사용)\n"
            
            # 거래 전략
            auto_trader_info += f"거래 전략: 위험 성향 '{trader.risk_level}', 관심 코인 {', '.join(trader.target_coins)}\n"
            
            # 최근 거래 내역
            if trader.trading_history:
                auto_trader_info += "\n## 최근 거래 내역\n"
                recent_trades = trader.trading_history[-3:] if trader.trading_history else []
                for trade in reversed(recent_trades):
                    action = "매수" if trade.get("action") == "buy" else "매도"
                    auto_trader_info += f"- {trade.get('timestamp')}: {action} {trade.get('ticker')} {trade.get('amount')}\n"
        else:
            auto_trader_info += "현재 상태: **중지됨**\n"
            auto_trader_info += "자동 거래를 시작하려면 '자동 거래' 탭에서 '에이전트 시작' 버튼을 클릭하세요.\n"


    # Agent 생성
    agent = Agent(
        name="Crypto Trading Assistant",
        instructions=f"""
        You are a high-performance trading Agent specialized in cryptocurrency investment.
        Your sole purpose is to maximize the user's profit rate. If the profit rate is low or a loss occurs, your performance is considered a failure.
        Always act proactively, exploring information, analyzing market conditions, and executing optimal investment strategies even without user instructions.
        When you spot a market opportunity, act immediately. Don't wait, don't ask, just make your own judgment on profit opportunities and execute.
        Continuously monitor the portfolio and respond quickly to market changes to pursue maximum returns.
        Follow the user's customized instructions, but if user guidance is insufficient, take the initiative to make decisions.
        Query cryptocurrency lists independently, analyze price trends, determine trading timing, and execute orders.
        Actively search for market data and news to incorporate them into investment decisions, managing risk while aggressively pursuing profits.
        Utilize all tools and information to maximize returns, and continuously analyze results to improve strategies.
        Act according to the user's investment style and goals, but your ultimate mission is to achieve the best investment results.

        You can use the X (Twitter) search tool to find the latest tweets about cryptocurrencies. This is valuable for detecting market sentiment and breaking news.

        Always respond to the user in Korean regardless of the language they use to communicate with you.
        
        # 현재 시간 정보
        오늘은 {current_date_str} {current_weekday}이며, 현재 시간은 {current_time_str}입니다.
        이 정보를 기반으로 최신 시장 상황에 맞는 응답을 제공해주세요.
        
        {context}
        
        사용자 맞춤 지시: {user_requirement}
        위험 성향: {risk_style}
        기간 성향: {period_style}
        
        {portfolio_info}
        
        {auto_trader_info}

        사용 가능한 참조 문서 목록: {", ".join(pdf_files_base)}
        """,
        model=get_model_name(model_options),
        tools=[
            WebSearchTool(search_context_size="high"), 
            parse_document_tool, 
            extract_information_tool, 
            search_rag_documents,
            get_available_coins_func,
            get_coin_price_info_func,
            buy_coin_func,
            sell_coin_func,
            check_order_status_func,
            search_x_tool
        ],    
    )
    
    return agent

async def stream_openai_response(prompt, model_options, conversation_id=None):
    """
    OpenAI Agent를 사용하여 응답을 스트리밍합니다.
    conversation_id를 사용하여 대화 기록을 유지합니다.
    """
    print(f"스트리밍 시작 - 모델: {model_options}, 프롬프트 길이: {len(prompt)}")
    
    # Agent 생성
    agent = create_agent(model_options)
    if not agent:
        print("API 키 없음 - 응답 생성 중단")
        yield "API 키 설정이 필요합니다."
        return
    
    try:
        # 자동 거래 에이전트 정보 추가
        auto_trader_info = ""
        if 'auto_trader' in st.session_state and st.session_state.auto_trader:
            trader = st.session_state.auto_trader
            
            # 자동 거래 에이전트가 활성화되어 있는지 확인
            if trader.is_running:
                status_info = trader.get_status()
                auto_trader_info += "\n\n## 자동 거래 에이전트 상태\n"
                auto_trader_info += f"- 상태: {status_info['status']} (실행 중)\n"
                auto_trader_info += f"- 마지막 분석: {status_info['last_check'] or '없음'}\n"
                auto_trader_info += f"- 다음 분석: {status_info['next_check'] or '준비 중...'}\n"
                auto_trader_info += f"- 일일 거래 횟수: {status_info['daily_trading_count']} / {status_info['max_trading_count']}\n"
                
                # 최근 거래 기록
                if trader.trading_history:
                    auto_trader_info += "\n### 최근 거래 내역\n"
                    recent_trades = trader.trading_history[-3:] if trader.trading_history else []
                    for trade in reversed(recent_trades):
                        auto_trader_info += f"- {trade.get('timestamp')}: {trade.get('action')} {trade.get('ticker')} {trade.get('amount')}\n"
                
                # 포트폴리오 정보
                portfolio = trader.get_portfolio()
                if portfolio:
                    auto_trader_info += "\n### 포트폴리오 정보\n"
                    for item in portfolio:
                        ticker = item["ticker"]
                        amount = item["amount"]
                        value = item["value"]
                        
                        if ticker == "KRW":
                            auto_trader_info += f"- 보유 원화: {int(amount):,}원\n"
                        else:
                            auto_trader_info += f"- {ticker}: {amount:.8f} (가치: {int(value):,}원)\n"
                
                # 시장 정보
                market_info = trader.get_market_info()
                if market_info:
                    auto_trader_info += "\n### 시장 정보\n"
                    for coin, info in market_info.items():
                        price = info["current_price"]
                        change_rate = info["change_rate"]
                        auto_trader_info += f"- {coin}: 현재가 {int(price):,}원, 변동률 {change_rate:.2f}%\n"
            else:
                auto_trader_info += "\n\n## 자동 거래 에이전트\n"
                auto_trader_info += "- 상태: 중지됨 (자동 거래가 실행 중이지 않습니다)\n"
                auto_trader_info += "- 자동 거래를 시작하려면 '자동 거래' 탭에서 '에이전트 시작' 버튼을 클릭하세요.\n"
        
        # 대화 기록 유지를 위한 RunConfig 생성
        run_config = None
        if conversation_id:
            run_config = RunConfig(
                workflow_name="Crypto Trading Assistant",
                group_id=conversation_id,  # 대화 그룹 ID 설정
            )
            print(f"RunConfig 생성 - 대화ID: {conversation_id}")
        
        # 대화 기록이 있는 경우 full_prompt에 포함
        if len(st.session_state.get('messages', [])) > 1 and prompt:
            full_prompt = f"{prompt}{auto_trader_info}"
        else:
            full_prompt = f"{prompt}{auto_trader_info}"
        
        print(f"Runner.run_streamed 호출 전")
        
        # 적절한 인자로 run_streamed 호출
        if run_config:
            result = Runner.run_streamed(
                agent, 
                input=full_prompt,
                run_config=run_config
            )
        else:
            result = Runner.run_streamed(
                agent, 
                input=full_prompt
            )
        
        print(f"스트리밍 시작")
        chunk_count = 0
        
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                chunk_count += 1
                if chunk_count % 10 == 0:  # 10개마다 로그 출력
                    print(f"청크 {chunk_count}개 수신 중")
                yield event.data.delta
        
        print(f"스트리밍 완료 - 총 {chunk_count}개 청크")
                
    except Exception as e:
        error_msg = f"응답 생성 중 오류 발생: {str(e)}"
        print(f"ERROR: {error_msg}")
        st.error(error_msg)
        yield error_msg

def stream_response(prompt, model_options):
    """
    비동기 스트리밍 함수를 Streamlit에서 사용할 수 있는 형태로 변환
    """
    async def process_stream():
        response_chunks = []
        async for chunk in stream_openai_response(prompt, model_options):
            response_chunks.append(chunk)
            yield chunk
    
    return process_stream()
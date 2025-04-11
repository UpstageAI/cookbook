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

# Create tool to extract information from documents
@function_tool
def extract_information_tool(img_path: str, fields_to_extract: str, required_fields: Optional[List[str]] = None):
    """
    Extract specified information from an image.
    
    Args:
        img_path: Path to the image file
        fields_to_extract: Fields to extract and their descriptions (passed as a JSON string, e.g. {"bank_name": "bank name", "amount": "transaction amount"})
        required_fields: List of required fields (optional)
    
    Returns:
        Dict: Extracted information or error
    """
    # Convert string to dictionary
    import json
    try:
        fields_dict = json.loads(fields_to_extract)
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'Field information is not in valid JSON format.'
        }
    
    # Configure schema properties
    schema_properties = {}
    for field_name, description in fields_dict.items():
        schema_properties[field_name] = {
            "type": "string",
            "description": description
        }
    
    # Call information_extract function
    return information_extract(img_path, schema_properties, required_fields)

# Document parsing tool
@function_tool
def parse_document_tool(file_names: List[str]):
    """
    Parse PDF documents to extract text.
    
    Args:
        file_names: List of PDF file names (without extension)
    
    Returns:
        Dict: Dictionary containing document parsing results
    """
    parser = DocumentParser()
    return parser.parse_document(file_names)

# Function to create Agent object
def create_agent(model_options):
    """
    Create an Agent object.
    """
    # Set API key from session state
    if 'openai_key' in st.session_state and st.session_state.openai_key:
        set_default_openai_key(st.session_state.openai_key)
    else:
        st.error("OpenAI API key is not set. Please enter your key in the API Settings page.")
        return None
    
    # Get investment preference information
    user_requirement = st.session_state.get('user_requirement', '')
    risk_style = st.session_state.get('risk_style', 'Aggressive')
    period_style = st.session_state.get('period_style', 'Short-term')
    
    # Get portfolio information
    portfolio_info = ""
    try:
        from page.portfolio import get_portfolio_info_from_trade
        from page.api_setting import get_upbit_trade_instance
        
        upbit_trade = get_upbit_trade_instance()
        if upbit_trade:
            portfolio_summary, coin_balances = get_portfolio_info_from_trade(upbit_trade)
            if portfolio_summary:
                portfolio_info += "\n\n# User Portfolio Information\n"
                portfolio_info += f"- Total Assets: {portfolio_summary.get('Total Assets', 0):,.0f} KRW\n"
                portfolio_info += f"- Total Profit/Loss: {portfolio_summary.get('Total Profit/Loss', 0):,.0f} KRW ({portfolio_summary.get('Total Return Rate', 0):.2f}%)\n"
                portfolio_info += f"- Daily Return Rate: {portfolio_summary.get('Daily Return Rate', 0):.2f}%\n"
                portfolio_info += f"- Cash Balance: {portfolio_summary.get('Cash Balance', 0):,.0f} KRW\n"
                portfolio_info += f"- Coin Evaluation Amount: {portfolio_summary.get('Coin Evaluation Amount', 0):,.0f} KRW\n"
                
                if not coin_balances.empty:
                    portfolio_info += "\n## Coin Holdings\n"
                    for idx, row in coin_balances.iterrows():
                        portfolio_info += f"- {row['Coin']}: {row['Quantity']:.8f} coins, Evaluation Amount: {row['Evaluation Amount']:,.0f} KRW, Return Rate: {row['Rate of Return']:.2f}%\n"
    except Exception as e:
        print(f"Error loading portfolio information: {str(e)}")
    
    # Generate current date and time information
    current_datetime = datetime.datetime.now()
    current_date_str = current_datetime.strftime("%Y-%m-%d")
    current_time_str = current_datetime.strftime("%H:%M")
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_weekday = weekdays[current_datetime.weekday()]
    
    # Exception handling for when pdf_files directory doesn't exist
    pdf_files_base = []
    try:
        pdf_files = [f for f in os.listdir("tools/web2pdf/always_see_doc_storage") if f.endswith('.pdf')]
        pdf_files_base = [os.path.splitext(f)[0] for f in pdf_files]
    except (FileNotFoundError, OSError) as e:
        print(f"Error getting PDF file list: {str(e)}")
    
    # Get previous messages
    previous_messages = st.session_state.get('messages', [])
    context = ""
    
    # Add recent conversation history to context (max 5 messages)
    if len(previous_messages) > 1:  # Skip first message (AI greeting)
        context = "Previous conversation:\n"
        for i, msg in enumerate(previous_messages[-6:-1]):  # Only recent 5 messages
            if msg["role"] == "user":
                context += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                context += f"AI: {msg['content']}\n"
        context += "\n"
    
    # Add auto trader agent information
    auto_trader_info = ""
    if 'auto_trader' in st.session_state and st.session_state.auto_trader:
        trader = st.session_state.auto_trader
        
        # Auto trader agent settings information
        auto_trader_info += "\n\n# Auto Trading Agent Information\n"
        auto_trader_info += f"The auto trading agent can automatically execute trades in your account.\n"
        
        if trader.is_running:
            status_info = trader.get_status()
            auto_trader_info += f"Current status: **Running**\n"
            auto_trader_info += f"Settings: Analysis interval {trader.interval_minutes} minutes, Maximum investment {trader.max_investment:,} KRW, "
            auto_trader_info += f"Maximum daily trades {trader.max_trading_count} (currently used {status_info['daily_trading_count']})\n"
            
            # Trading strategy
            auto_trader_info += f"Trading strategy: Risk level '{trader.risk_level}', Target coins {', '.join(trader.target_coins)}\n"
            
            # Recent trade history
            if trader.trading_history:
                auto_trader_info += "\n## Recent Trade History\n"
                recent_trades = trader.trading_history[-3:] if trader.trading_history else []
                for trade in reversed(recent_trades):
                    action = "Buy" if trade.get("action") == "buy" else "Sell"
                    auto_trader_info += f"- {trade.get('timestamp')}: {action} {trade.get('ticker')} {trade.get('amount')}\n"
        else:
            auto_trader_info += "Current status: **Stopped**\n"
            auto_trader_info += "To start auto trading, click the 'Start Agent' button in the 'Auto Trading' tab.\n"


    # Create Agent
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
        
        # Current Time Information
        Today is {current_date_str} {current_weekday}, and the current time is {current_time_str}.
        Please provide responses appropriate to the latest market situation based on this information.
        
        {context}
        
        Custom User Instructions: {user_requirement}
        Risk Preference: {risk_style}
        Time Horizon: {period_style}
        
        {portfolio_info}
        
        {auto_trader_info}

        Available reference documents: {", ".join(pdf_files_base)}
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
    Stream responses using OpenAI Agent.
    Uses conversation_id to maintain conversation history.
    """
    print(f"Streaming started - Model: {model_options}, Prompt length: {len(prompt)}")
    
    # Create Agent
    agent = create_agent(model_options)
    if not agent:
        print("No API key - Response generation stopped")
        yield "API key setup required."
        return
    
    try:
        # Add auto trader agent information
        auto_trader_info = ""
        if 'auto_trader' in st.session_state and st.session_state.auto_trader:
            trader = st.session_state.auto_trader
            
            # Check if auto trader agent is active
            if trader.is_running:
                status_info = trader.get_status()
                auto_trader_info += "\n\n## Auto Trading Agent Status\n"
                auto_trader_info += f"- Status: {status_info['status']} (Running)\n"
                auto_trader_info += f"- Last Analysis: {status_info['last_check'] or 'None'}\n"
                auto_trader_info += f"- Next Analysis: {status_info['next_check'] or 'Preparing...'}\n"
                auto_trader_info += f"- Daily Trade Count: {status_info['daily_trading_count']} / {status_info['max_trading_count']}\n"
                
                # Recent trade history
                if trader.trading_history:
                    auto_trader_info += "\n### Recent Trade History\n"
                    recent_trades = trader.trading_history[-3:] if trader.trading_history else []
                    for trade in reversed(recent_trades):
                        auto_trader_info += f"- {trade.get('timestamp')}: {trade.get('action')} {trade.get('ticker')} {trade.get('amount')}\n"
                
                # Portfolio information
                portfolio = trader.get_portfolio()
                if portfolio:
                    auto_trader_info += "\n### Portfolio Information\n"
                    for item in portfolio:
                        ticker = item["ticker"]
                        amount = item["amount"]
                        value = item["value"]
                        
                        if ticker == "KRW":
                            auto_trader_info += f"- KRW Balance: {int(amount):,} KRW\n"
                        else:
                            auto_trader_info += f"- {ticker}: {amount:.8f} (Value: {int(value):,} KRW)\n"
                
                # Market information
                market_info = trader.get_market_info()
                if market_info:
                    auto_trader_info += "\n### Market Information\n"
                    for coin, info in market_info.items():
                        price = info["current_price"]
                        change_rate = info["change_rate"]
                        auto_trader_info += f"- {coin}: Current Price {int(price):,} KRW, Change Rate {change_rate:.2f}%\n"
            else:
                auto_trader_info += "\n\n## Auto Trading Agent\n"
                auto_trader_info += "- Status: Stopped (Auto trading is not running)\n"
                auto_trader_info += "- To start auto trading, click the 'Start Agent' button in the 'Auto Trading' tab.\n"
        
        # Create RunConfig for conversation history
        run_config = None
        if conversation_id:
            run_config = RunConfig(
                workflow_name="Crypto Trading Assistant",
                group_id=conversation_id,  # Set conversation group ID
            )
            print(f"RunConfig created - Conversation ID: {conversation_id}")
        
        # Include conversation history in full_prompt if available
        if len(st.session_state.get('messages', [])) > 1 and prompt:
            full_prompt = f"{prompt}{auto_trader_info}"
        else:
            full_prompt = f"{prompt}{auto_trader_info}"
        
        print(f"Before calling Runner.run_streamed")
        
        # Call run_streamed with appropriate arguments
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
        
        print(f"Streaming started")
        chunk_count = 0
        
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                chunk_count += 1
                if chunk_count % 10 == 0:  # Log every 10 chunks
                    print(f"Receiving chunk {chunk_count}")
                yield event.data.delta
        
        print(f"Streaming completed - Total {chunk_count} chunks")
                
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"ERROR: {error_msg}")
        st.error(error_msg)
        yield error_msg

def stream_response(prompt, model_options):
    """
    Convert async streaming function to a form usable in Streamlit
    """
    async def process_stream():
        response_chunks = []
        async for chunk in stream_openai_response(prompt, model_options):
            response_chunks.append(chunk)
            yield chunk
    
    return process_stream()
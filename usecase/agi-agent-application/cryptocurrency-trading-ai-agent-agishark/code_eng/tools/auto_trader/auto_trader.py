import streamlit as st
import os
import time
import json
import threading
import asyncio
import schedule
from datetime import datetime, timedelta
import pandas as pd

# Import required modules
from agents import Agent, Runner, set_default_openai_key, RunConfig, function_tool
from tools.upbit.upbit_api import buy_coin_func, sell_coin_func
from tools.upbit.UPBIT import Trade

class AutoTrader:
    def __init__(self, 
                access_key=None, 
                secret_key=None, 
                model_options="gpt-4o-mini", 
                interval_minutes=5, 
                max_investment=100000,
                max_trading_count=3):
        """
        Initialize automatic buy/sell agent
        
        Args:
            access_key: Upbit access key
            secret_key: Upbit secret key
            model_options: Model to use
            interval_minutes: Interval (in minutes) for making buy/sell decisions
            max_investment: Maximum investment amount
            max_trading_count: Maximum number of trades per day
        """
        # Set Upbit API keys
        self.access_key = access_key or st.session_state.get('upbit_access_key', '')
        self.secret_key = secret_key or st.session_state.get('upbit_secret_key', '')
        
        # Set OpenAI API key
        self.openai_key = st.session_state.get('openai_key', '')
        
        # Create trade instance
        self.trade = Trade(access_key=self.access_key, secret_key=self.secret_key)
        
        # Save settings
        self.model_options = model_options
        self.interval_minutes = interval_minutes
        self.max_investment = max_investment
        self.max_trading_count = max_trading_count
        
        # Trading history storage
        self.trading_history = []
        self.daily_trading_count = 0
        self.last_trading_date = None
        
        # Thread and execution control
        self.is_running = False
        self.thread = None
        
        # Status information
        self.status = "Ready"
        self.last_check_time = None
        self.next_check_time = None
        
        # Buy/sell strategy settings
        self.target_coins = ["BTC", "ETH", "XRP", "SOL", "ADA"]  # Default coins of interest
        self.risk_level = "neutral"  # Default risk profile
        
        # Log storage
        self.logs = []
        
        # Operation settings
        self.daily_trade_volume = 100000  # Default daily trading volume (KRW)
        
        # Thread related
        self.trading_thread = None
        self.stop_event = threading.Event()
        
        # Callback function
        self.trade_callback = None
        
    def log(self, message, level="INFO"):
        """Record log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {"timestamp": timestamp, "level": level, "message": message}
        self.logs.append(log_entry)
        print(f"[{level}] {timestamp}: {message}")
        
        # Delete oldest logs if there are too many
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]

    @function_tool
    def buy_coin(self, ticker: str, price_type: str, amount: float, limit_price: float = None):
        """
        Tool for agent to buy coins
        
        Args:
            ticker: Coin ticker (e.g., 'BTC')
            price_type: 'market' or 'limit'
            amount: Purchase amount (in KRW)
            limit_price: Price for limit orders
        """
        self.log(f"LLM agent buy request: {ticker} {amount} KRW ({price_type})", "INFO")
        
        try:
            # Check daily trading limit
            current_date = datetime.now().date()
            if self.last_trading_date != current_date:
                self.last_trading_date = current_date
                self.daily_trading_count = 0
            
            if self.daily_trading_count >= self.max_trading_count:
                return {
                    "success": False,
                    "message": f"Skipping trade as it exceeds maximum daily trading count ({self.max_trading_count})."
                }
            
            # Add KRW prefix
            if not ticker.startswith("KRW-"):
                ticker = f"KRW-{ticker}"
            
            # Limit amount
            amount = min(amount, self.max_investment)
            
            # Check current KRW balance
            krw_balance = self.trade.get_balance("KRW")
            if krw_balance < amount:
                self.log(f"Adjusting trade amount due to insufficient KRW balance ({krw_balance}).", "WARNING")
                amount = krw_balance * 0.95  # Use only 95% to account for fees
            
            # Check minimum order amount
            if amount < 5000:
                return {
                    "success": False,
                    "message": f"Skipping trade as amount ({amount} KRW) is less than minimum order amount (5,000 KRW)"
                }
            
            # Process based on order type
            if price_type == "market":
                self.log(f"Starting market buy order for {ticker} {amount} KRW", "INFO")
                result = self.trade.buy_market_order(ticker, amount)
            else:  # limit
                if not limit_price or limit_price <= 0:
                    return {
                        "success": False,
                        "message": "Valid price is required for limit orders."
                    }
                
                volume = amount / limit_price
                self.log(f"Starting limit buy order for {ticker} {volume} units at {limit_price} KRW", "INFO")
                result = self.trade.buy_limit_order(ticker, limit_price, volume)
            
            if result and 'uuid' in result:
                # Save trade record
                trade_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "buy",
                    "ticker": ticker,
                    "amount": amount,
                    "price_type": price_type,
                    "limit_price": limit_price if price_type == "limit" else None,
                    "result": result,
                    "reason": "LLM agent buy decision"
                }
                self.trading_history.append(trade_record)
                self.daily_trading_count += 1
                
                self.log(f"Buy order completed: {ticker}, Order ID: {result['uuid']}", "INFO")
                
                # Send trade notification
                self.notify_trade(trade_record)
                
                return {
                    "success": True,
                    "message": f"Buy order for {ticker} has been placed.",
                    "order_id": result['uuid']
                }
            else:
                self.log(f"Buy order failed: {ticker}", "ERROR")
                return {
                    "success": False,
                    "message": f"Buy order failed: {result}"
                }
        except Exception as e:
            self.log(f"Error occurred during buy order: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"Error occurred during buy order: {str(e)}"
            }

    @function_tool
    def sell_coin(self, ticker: str, price_type: str, amount: str = "all", limit_price: float = None):
        """
        Tool for agent to sell coins
        
        Args:
            ticker: Coin ticker (e.g., 'BTC')
            price_type: 'market' or 'limit'
            amount: Sell amount (coin quantity or 'all')
            limit_price: Price for limit orders
        """
        self.log(f"LLM agent sell request: {ticker} {amount} ({price_type})", "INFO")
        
        try:
            # Check daily trading limit
            current_date = datetime.now().date()
            if self.last_trading_date != current_date:
                self.last_trading_date = current_date
                self.daily_trading_count = 0
            
            if self.daily_trading_count >= self.max_trading_count:
                return {
                    "success": False,
                    "message": f"Skipping trade as it exceeds maximum daily trading count ({self.max_trading_count})."
                }
            
            # Add KRW prefix
            if not ticker.startswith("KRW-"):
                ticker = f"KRW-{ticker}"
            
            # Check holdings
            coin_balance = self.trade.get_balance(ticker)
            if not coin_balance or coin_balance <= 0:
                return {
                    "success": False,
                    "message": f"Skipping sell as there is no {ticker} balance."
                }
            
            # Determine sell volume
            volume = None  # Default to sell all
            if amount not in ["all", "전량"]:
                try:
                    volume = float(amount)
                    if volume > coin_balance:
                        self.log(f"Sell amount ({volume}) exceeds balance ({coin_balance}).", "WARNING")
                        volume = coin_balance
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid sell amount: {amount}. Please specify a number or 'all'."
                    }
            
            # Process based on order type
            if price_type == "market":
                self.log(f"Starting market sell order for {ticker} {volume if volume else 'all'}", "INFO")
                result = self.trade.sell_market_order(ticker, volume)
            else:  # limit
                if not limit_price or limit_price <= 0:
                    return {
                        "success": False,
                        "message": "Valid price is required for limit orders."
                    }
                
                sell_volume = volume if volume else coin_balance
                self.log(f"Starting limit sell order for {ticker} {sell_volume} units at {limit_price} KRW", "INFO")
                result = self.trade.sell_limit_order(ticker, limit_price, sell_volume)
            
            if result and 'uuid' in result:
                # Save trade record
                trade_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "sell",
                    "ticker": ticker,
                    "amount": volume if volume else "all",
                    "price_type": price_type,
                    "limit_price": limit_price if price_type == "limit" else None,
                    "result": result,
                    "reason": "LLM agent sell decision"
                }
                self.trading_history.append(trade_record)
                self.daily_trading_count += 1
                
                self.log(f"Sell order completed: {ticker}, Order ID: {result['uuid']}", "INFO")
                
                # Send trade notification
                self.notify_trade(trade_record)
                
                result = {
                    'success': True,
                    'message': f"Sell order for {ticker} {volume if volume else 'all'} has been placed. Order ID: {result['uuid']}\nYou can check the order execution results in the 'Transaction History' tab.",
                    'order_id': result['uuid'],
                    'order_info': result
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                self.log(f"Sell order failed: {ticker}", "ERROR")
                return {
                    "success": False,
                    "message": f"Sell order failed: {result}"
                }
        except Exception as e:
            self.log(f"Error occurred during sell order: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"Error occurred during sell order: {str(e)}"
            }
    
    def create_agent(self):
        """Create LLM agent"""
        if not self.openai_key:
            self.log("OpenAI API key is not set", "ERROR")
            return None
            
        set_default_openai_key(self.openai_key)
        
        # Get recent trading history
        recent_trades = self.trading_history[-5:] if self.trading_history else []
        recent_trades_str = "\n".join([
            f"- {trade['timestamp']}: {trade['action']} {trade['ticker']} ({trade['reason']})"
            for trade in recent_trades
        ])
        
        # Get current portfolio information
        portfolio = self.get_portfolio()
        portfolio_str = "\n".join([
            f"- {item['ticker']}: {item['amount']} ({item['value']} KRW)"
            for item in portfolio
        ])
        
        # Get current market information
        market_info = self.get_market_info()
        market_info_str = "\n".join([
            f"- {coin}: Current price {info['current_price']} KRW, 24h change {info['change_rate']}%"
            for coin, info in market_info.items()
        ])
        
        # Create agent
        agent = Agent(
            name="Auto Trading Agent",
            instructions=f"""
            You are a cryptocurrency automatic trading agent. You need to analyze the current market situation and portfolio to make buy/sell decisions.
            
            # Configuration
            - Maximum investment: {self.max_investment} KRW
            - Decision interval: {self.interval_minutes} minutes
            - Maximum daily trades: {self.max_trading_count} (currently used: {self.daily_trading_count})
            - Risk profile: {self.risk_level}
            - Target coins: {', '.join(self.target_coins)}
            
            # Current Portfolio
            {portfolio_str}
            
            # Current Market Situation
            {market_info_str}
            
            # Recent Trading History
            {recent_trades_str}
            
            # Trading Guidelines
            1. Analyze the current market situation to make buy or sell decisions.
            2. Clearly explain the reason for each decision.
            3. Specifically designate which coins to buy/sell and the amount.
            4. Make decisions according to the risk profile (neutral: balanced investment, aggressive: high risk/high return, conservative: emphasis on stability)
            
            # How to Use Trading Tools
            - To buy, use the buy_coin tool. You must specify ticker, order type (market or limit), amount, and limit price.
            - To sell, use the sell_coin tool. You must specify ticker, order type (market or limit), quantity (or "all"), and limit price.
            
            # Important Notes
            - Daily trading is limited, so only trade when there's a definite opportunity.
            - For buy orders, it's better to use only a portion of funds rather than 100%.
            - Only sell coins that you currently hold.
            
            Based on your analysis, directly call the trading tools to execute trades. If you decide not to trade, please explain why.
            """,
            model=get_model_name(self.model_options),
            tools=[self.buy_coin, self.sell_coin]
        )
        return agent
    
    def get_portfolio(self):
        """Get current portfolio information"""
        try:
            portfolio = []
            
            # Check KRW balance
            krw_balance = self.trade.get_balance("KRW")
            if krw_balance:
                portfolio.append({
                    "ticker": "KRW",
                    "amount": krw_balance,
                    "value": krw_balance
                })
            
            # Check balance for each coin
            for coin in self.target_coins:
                ticker = f"KRW-{coin}"
                amount = self.trade.get_balance(ticker)
                if amount and amount > 0:
                    price = self.trade.get_current_price(ticker)
                    value = price * amount if price else 0
                    portfolio.append({
                        "ticker": coin,
                        "amount": amount,
                        "value": value
                    })
            
            return portfolio
        except Exception as e:
            self.log(f"Failed to get portfolio information: {str(e)}", "ERROR")
            return []
    
    def get_market_info(self):
        """Get current market information"""
        try:
            market_info = {}
            
            for coin in self.target_coins:
                ticker = f"KRW-{coin}"
                
                # Check current price
                current_price = self.trade.get_current_price(ticker)
                
                # 24-hour candle data
                ohlcv = self.trade.get_ohlcv(ticker, interval="day", count=2)
                
                if ohlcv is not None and not ohlcv.empty:
                    prev_close = ohlcv['close'].iloc[-2]
                    change_rate = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    
                    market_info[coin] = {
                        "current_price": current_price,
                        "open_price": ohlcv['open'].iloc[-1],
                        "high_price": ohlcv['high'].iloc[-1],
                        "low_price": ohlcv['low'].iloc[-1],
                        "volume": ohlcv['volume'].iloc[-1],
                        "change_rate": round(change_rate, 2)
                    }
            
            return market_info
        except Exception as e:
            self.log(f"Failed to get market information: {str(e)}", "ERROR")
            return {}
    
    async def get_trading_decision(self):
        """Request trading decision from LLM"""
        try:
            agent = self.create_agent()
            if not agent:
                return None
            
            prompt = "Analyze the current market situation and portfolio to make buy or sell decisions, and execute trades directly using trading tools if necessary."
            
            result = await Runner.run(
                agent, 
                input=prompt,
                run_config=RunConfig(
                    workflow_name="Auto Trading Decision",
                    group_id=f"auto_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            )
            
            return result
        except Exception as e:
            self.log(f"Failed to request trading decision: {str(e)}", "ERROR")
            return None
    
    async def check_and_trade(self):
        """Market analysis and trade execution"""
        try:
            self.status = "Analyzing..."
            self.last_check_time = datetime.now()
            self.next_check_time = self.last_check_time + timedelta(minutes=self.interval_minutes)
            
            self.log("Starting market analysis and trading decision", "INFO")
            
            # Request trading decision from LLM
            decision_text = await self.get_trading_decision()
            
            if not decision_text:
                self.log("Failed to get trading decision.", "WARNING")
                self.status = "Analysis failed"
                return
            
            # Save trading execution result
            self.log(f"Trading decision result: {decision_text[:100]}...", "INFO")
            self.status = "Waiting"
            
            self.log(f"Trading cycle completed", "INFO")
            
        except Exception as e:
            self.log(f"Error during trading cycle: {str(e)}", "ERROR")
            self.status = "Error occurred"
    
    async def run_loop(self):
        """Main loop for periodic trading decisions"""
        self.log("Starting automatic trading loop", "INFO")
        
        while self.is_running:
            try:
                await self.check_and_trade()
                
                # Wait until next check time
                wait_seconds = self.interval_minutes * 60
                self.log(f"Next analysis scheduled in {wait_seconds} seconds", "INFO")
                
                # Async wait (divided into small intervals to allow cancellation)
                wait_chunk = 5  # Check every 5 seconds
                for _ in range(wait_seconds // wait_chunk):
                    if not self.is_running:
                        break
                    await asyncio.sleep(wait_chunk)
                
                # Wait remaining time
                if self.is_running and wait_seconds % wait_chunk > 0:
                    await asyncio.sleep(wait_seconds % wait_chunk)
                    
            except Exception as e:
                self.log(f"Auto trading loop error: {str(e)}", "ERROR")
                await asyncio.sleep(60)  # Wait 1 minute after error before retrying
    
    def start(self):
        """Start automatic trading"""
        if self.is_running:
            return False
        
        if not self.access_key or not self.secret_key:
            self.log("Upbit API keys are not set.", "ERROR")
            return False
        
        if not self.openai_key:
            self.log("OpenAI API key is not set.", "ERROR")
            return False
        
        # Check overall market status
        market_all = self.trade.get_market_all()
        if not market_all:
            self.log("Failed to get market information. Check your API keys.", "ERROR")
            return False
        
        self.is_running = True
        self.status = "Started"
        self.log("Automatic trading started", "INFO")
        
        # Run async loop
        async def start_loop():
            await self.run_loop()
        
        # Run event loop in new thread
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_loop())
        
        self.thread = threading.Thread(target=run_async_loop)
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def stop(self):
        """Stop automatic trading"""
        if not self.is_running:
            return False
        
        self.is_running = False
        self.status = "Stopped"
        self.log("Automatic trading stopped", "INFO")
        
        if self.thread and self.thread.is_alive():
            # Wait for thread to terminate (max 10 seconds)
            self.thread.join(timeout=10)
        
        self.thread = None
        return True
    
    def get_status(self):
        """Return current status information"""
        return {
            "is_running": self.is_running,
            "status": self.status,
            "last_check": self.last_check_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_check_time else None,
            "next_check": self.next_check_time.strftime("%Y-%m-%d %H:%M:%S") if self.next_check_time else None,
            "daily_trading_count": self.daily_trading_count,
            "max_trading_count": self.max_trading_count,
            "trading_history_count": len(self.trading_history),
            "model": self.model_options,
            "interval_minutes": self.interval_minutes
        }
    
    def update_settings(self, settings):
        """Update settings"""
        restart_required = False
        
        # Change settings
        if 'interval_minutes' in settings:
            if self.interval_minutes != settings['interval_minutes']:
                self.interval_minutes = settings['interval_minutes']
                restart_required = True
        
        if 'max_investment' in settings:
            self.max_investment = settings['max_investment']
        
        if 'max_trading_count' in settings:
            self.max_trading_count = settings['max_trading_count']
        
        if 'target_coins' in settings:
            self.target_coins = settings['target_coins']
        
        if 'risk_level' in settings:
            self.risk_level = settings['risk_level']
        
        if 'model_options' in settings:
            if self.model_options != settings['model_options']:
                self.model_options = settings['model_options']
                restart_required = True
        
        return restart_required
        
    def update_operation_settings(self, interval_minutes=None, max_investment=None, max_trading_count=None):
        """Update trading settings"""
        if interval_minutes is not None:
            self.interval_minutes = interval_minutes
            self.log(f"Analysis interval set to {interval_minutes} minutes.", "INFO")
            
        if max_investment is not None:
            self.max_investment = max_investment
            self.log(f"Maximum investment amount set to {max_investment:,} KRW.", "INFO")
            
        if max_trading_count is not None:
            self.max_trading_count = max_trading_count
            self.log(f"Maximum daily trading count set to {max_trading_count}.", "INFO")
            
        return True

    def set_trade_callback(self, callback_func):
        """Set callback function for trade events"""
        self.trade_callback = callback_func
        self.log(f"Trade callback function has been set.", "INFO")
        
    def notify_trade(self, trade_info):
        """Call callback function when trade occurs"""
        if self.trade_callback:
            try:
                self.trade_callback(trade_info)
                self.log(f"Trade notification sent: {trade_info.get('timestamp')} {trade_info.get('action')} {trade_info.get('ticker')}", "INFO")
            except Exception as e:
                self.log(f"Error while sending trade notification: {str(e)}", "ERROR") 
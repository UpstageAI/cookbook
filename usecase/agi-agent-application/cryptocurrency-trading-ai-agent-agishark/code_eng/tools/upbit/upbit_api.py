import streamlit as st
import asyncio
import json
import logging
import os
import traceback
from typing import Dict, List, Optional, Any, Union
import datetime
from agents import Agent, FunctionTool, function_tool, RunContextWrapper

# Logging setup (if needed)
logger = logging.getLogger("crypto_agent")


# Import UpbitTrader directly
try:
    from upbit.upbit_trader import UpbitTrader
except ImportError:
    # Alternative implementation if upbit_trader module is missing
    class UpbitTrader:
        def __init__(self, access_key, secret_key):
            self.access_key = access_key
            self.secret_key = secret_key
            self.is_valid = False
            
        def get_balance(self, ticker):
            log_error(None, f"UpbitTrader module could not be loaded.")
            return 0

# Logging setup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"crypto_agent_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Logger configuration
logger = logging.getLogger("crypto_agent")
logger.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Stream handler (console output)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Format settings
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Debug mode configuration
def set_debug_mode(enable=True):
    """Set debug mode"""
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = enable
    else:
        st.session_state.debug_mode = enable
    logger.info(f"Debug mode: {enable}")

# Error logging and debug info display function
def log_error(error, context=None, show_tb=True):
    """Log errors and display debug information"""
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    
    logger.error(error_msg)
    if show_tb:
        tb = traceback.format_exc()
        logger.error(f"Traceback:\n{tb}")
    
    if st.session_state.get('debug_mode', False):
        st.error(error_msg)
        if show_tb:
            with st.expander("Detailed Error Information"):
                st.code(tb)
    else:
        st.error("An error has occurred. Please check the logs for details.")

# Debug info logging function
def log_info(message, data=None):
    """Log debug information"""
    logger.info(message)
    if data:
        logger.debug(f"{message} - Data: {json.dumps(data, ensure_ascii=False)}")
    
    if st.session_state.get('debug_mode', False) and data:
        with st.expander(f"Debug Info: {message}"):
            st.json(data)


# Function to get Upbit instance
def get_upbit_instance() -> Any:
    """Returns Upbit API instance."""
    upbit_access = st.session_state.get('upbit_access_key', '')
    upbit_secret = st.session_state.get('upbit_secret_key', '')
    
    if upbit_access and upbit_secret:
        try:
            import pyupbit
            upbit = pyupbit.Upbit(upbit_access, upbit_secret)
            return upbit
        except Exception as e:
            log_error(e, "Error while creating Upbit instance")
    
    return None

# Function to get Upbit trader instance
def get_upbit_trade_instance() -> Any:
    """Returns Upbit trader instance."""
    upbit_access = st.session_state.get('upbit_access_key', '')
    upbit_secret = st.session_state.get('upbit_secret_key', '')
    
    if upbit_access and upbit_secret:
        try:
            trader = UpbitTrader(upbit_access, upbit_secret)
            return trader
        except Exception as e:
            log_error(e, "Error while creating Upbit trader instance")
    
    return None



@function_tool
async def get_available_coins_func(action_type: Optional[str] = None) -> str:
    """
    Returns a list of tradable coins and currently held coins.
    If the user is trying to sell, only displays the coins they currently hold.
    
    Args:
        action_type: Transaction type ('buy' or 'sell')
    """
    log_info("get_available_coins function called")
    
    try:
        upbit = get_upbit_instance()
        
        if upbit:
            log_info("get_available_coins: Attempting to fetch real data with valid Upbit instance")
            
            # Query user's portfolio coins
            portfolio_coins = []
            try:
                balances = upbit.get_balances()
                for balance in balances:
                    if balance['currency'] != 'KRW' and float(balance['balance']) > 0:
                        portfolio_coins.append({
                            'ticker': f"KRW-{balance['currency']}",
                            'korean_name': balance['currency'],  # API doesn't provide Korean names separately
                            'balance': float(balance['balance']),
                            'avg_buy_price': float(balance['avg_buy_price'])
                        })
            except Exception as e:
                log_error(e, "Error while querying portfolio coins")
                # Continue despite error
            
            # For sell purpose, return only portfolio coins
            if action_type == "sell":
                log_info("get_available_coins: Filtering coin list for selling (portfolio coins only)")
                if not portfolio_coins:
                    return json.dumps({
                        "success": True,
                        "message": "You don't currently hold any coins.",
                        "coins": []
                    }, ensure_ascii=False)
                
                return json.dumps({
                    "success": True,
                    "message": f"Found {len(portfolio_coins)} coins in your portfolio.",
                    "coins": portfolio_coins
                }, ensure_ascii=False)
            
            # Query KRW market coins
            try:
                import pyupbit
                markets = pyupbit.get_tickers(fiat="KRW")
                market_info = []
                
                # Get market information
                for market in markets[:20]:  # Process only top 20 (for speed)
                    try:
                        ticker_info = pyupbit.get_current_price(market)
                        if ticker_info:
                            market_info.append({
                                'market': market,
                                'korean_name': market.replace('KRW-', '')
                            })
                    except:
                        continue
            except Exception as e:
                log_error(e, "Error while querying KRW market coins")
                market_info = []
            
            krw_markets = market_info
            log_info(f"get_available_coins: {len(krw_markets)} KRW market coins found")
            
            # Filter recommended coins based on risk profile (example)
            risk_style = st.session_state.get('risk_style', 'neutral')
            risk_filters = {
                'conservative': lambda m: m['market'] in ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOGE'],
                'neutral': lambda m: True,  # Allow all coins
                'aggressive': lambda m: True   # Allow all coins
            }
            
            filtered_markets = [m for m in krw_markets if risk_filters.get(risk_style, lambda x: True)(m)]
            
            # Limit results (max 10)
            result_markets = filtered_markets[:10] if len(filtered_markets) > 10 else filtered_markets
            
            # Format results
            coins = []
            for market in result_markets:
                coins.append({
                    'ticker': market['market'],
                    'korean_name': market['korean_name']
                })
            
            log_info("get_available_coins: Success")
            return json.dumps({
                "success": True,
                "message": f"Found {len(coins)} tradable coins.",
                "coins": coins,
                "portfolio": portfolio_coins  # Add portfolio information
            }, ensure_ascii=False)
            
        else:  # No upbit API instance
            # Demo data - when no API key is connected
            log_info("get_available_coins: Returning demo data without API connection")
            
            # Demo portfolio coin list
            demo_portfolio = [
                {'ticker': 'KRW-BTC', 'korean_name': 'Bitcoin', 'balance': 0.001, 'avg_buy_price': 65000000},
                {'ticker': 'KRW-ETH', 'korean_name': 'Ethereum', 'balance': 0.05, 'avg_buy_price': 3500000}
            ]
            
            # For sell purpose, return only demo portfolio coins
            if action_type == "sell":
                return json.dumps({
                    "success": True,
                    "message": "Found 2 coins in your portfolio. (Demo mode)",
                    "coins": demo_portfolio,
                    "is_demo": True
                }, ensure_ascii=False)
            
            # Demo tradable coin list
            demo_coins = [
                {'ticker': 'KRW-BTC', 'korean_name': 'Bitcoin'},
                {'ticker': 'KRW-ETH', 'korean_name': 'Ethereum'},
                {'ticker': 'KRW-XRP', 'korean_name': 'Ripple'},
                {'ticker': 'KRW-ADA', 'korean_name': 'Cardano'},
                {'ticker': 'KRW-DOGE', 'korean_name': 'Dogecoin'},
                {'ticker': 'KRW-SOL', 'korean_name': 'Solana'},
                {'ticker': 'KRW-DOT', 'korean_name': 'Polkadot'},
                {'ticker': 'KRW-AVAX', 'korean_name': 'Avalanche'}
            ]
            
            return json.dumps({
                "success": True, 
                "message": "Found 8 tradable coins. (Demo mode)",
                "coins": demo_coins,
                "portfolio": demo_portfolio,
                "is_demo": True
            }, ensure_ascii=False)
            
    except Exception as e:
        log_error(e, "Error during get_available_coins function execution")
        return json.dumps({
            "success": False,
            "message": f"Error while querying coin list: {str(e)}",
            "coins": []
        }, ensure_ascii=False)


@function_tool
async def get_coin_price_info_func(ticker: str) -> str:
    """
    Query coin price information.
    
    Args:
        ticker: Coin ticker symbol (e.g., 'BTC')
    """
    log_info("get_coin_price_info function called")
    
    # Process ticker
    ticker = ticker.upper()
    
    # Error if ticker is missing
    if not ticker:
        error_msg = "Ticker value is required."
        log_error(None, error_msg, show_tb=False)
        return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
    
    # Add KRW prefix
    if not ticker.startswith("KRW-"):
        ticker = f"KRW-{ticker}"
    
    log_info("get_coin_price_info: Ticker parsing complete", {"ticker": ticker})
    
    try:
        # Query data using pyupbit
        try:
            import pyupbit
            
            # Query current price
            current_price = pyupbit.get_current_price(ticker)
            log_info("get_coin_price_info: Current price query result", {"price": current_price})
            
            # Query holdings
            upbit = get_upbit_instance()
            balance_info = {"balance": 0, "avg_buy_price": 0}
            
            if upbit:
                coin_currency = ticker.replace("KRW-", "")
                balances = upbit.get_balances()
                for balance in balances:
                    if balance['currency'] == coin_currency:
                        balance_info = {
                            "balance": float(balance['balance']),
                            "avg_buy_price": float(balance['avg_buy_price'])
                        }
                        break
            
            log_info("get_coin_price_info: Balance query result", balance_info)
            
            # Query daily candle data
            df = pyupbit.get_ohlcv(ticker, interval="day", count=7)
            log_info("get_coin_price_info: OHLCV data query successful")
            
            # Format data
            ohlcv_data = []
            for idx, row in df.iterrows():
                ohlcv_data.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume'])
                })
            
            # Combine data
            result = {
                "success": True,
                "ticker": ticker,
                "current_price": current_price,
                "balance_info": balance_info,
                "ohlcv_data": ohlcv_data
            }
            
            log_info("get_coin_price_info: Success")
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            error_msg = f"Error while querying coin price information: {str(e)}"
            log_error(e, error_msg)
            return json.dumps({"success": False, "message": error_msg, "ticker": ticker}, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"Unexpected error while querying coin price information: {str(e)}"
        log_error(e, error_msg)
        return json.dumps({"success": False, "message": error_msg, "ticker": ticker}, ensure_ascii=False)


@function_tool
async def buy_coin_func(ticker: str, price_type: str, amount: float, limit_price: Optional[float]) -> str:
    """
    Buy coin function
    
    Args:
        ticker: Coin ticker symbol (e.g., 'BTC')
        price_type: 'market' or 'limit'
        amount: Purchase amount (in KRW)
        limit_price: Price for limit orders
    """
    try:
        # Start logging
        log_info("buy_coin function called", {"ticker": ticker, "price_type": price_type, "amount": amount, "limit_price": limit_price})
        print(f"Buy function called: {ticker}, {price_type}, {amount}, {limit_price}")
        
        # Process ticker
        ticker = ticker.upper()
        
        # Validate ticker
        if not ticker:
            error_msg = "Ticker is not specified."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Add KRW market prefix if missing
        if not ticker.startswith("KRW-"):
            ticker = f"KRW-{ticker}"
        log_info(f"buy_coin: Coin name extracted", {"ticker": ticker})
        
        # Get upbit instance
        upbit = get_upbit_instance()
        if not upbit:
            error_msg = "Unable to create Upbit API instance. Please check your API key settings."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        log_info(f"buy_coin: Valid Upbit instance confirmed")
        
        # Check order type
        price_type = price_type.lower()
        if price_type not in ["market", "limit"]:
            error_msg = f"Unsupported order type: {price_type}. Only 'market' or 'limit' can be used."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Validate amount
        if amount <= 0:
            error_msg = f"Invalid purchase amount: {amount}. Must be positive."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Check if buying all (equal to KRW balance)
        krw_balance = 0
        try:
            balances = upbit.get_balances()
            for balance in balances:
                if balance['currency'] == 'KRW':
                    krw_balance = float(balance['balance'])
                    break
            
            # If amount is 99% or more of KRW balance, it's considered buying all
            if amount >= krw_balance * 0.99:
                # Use 99.95% to account for fees
                amount = krw_balance * 0.9995
                log_info(f"buy_coin: Determined as buy all. Amount adjusted for fees", {"original": krw_balance, "adjusted": amount})
        except Exception as e:
            log_error(e, "buy_coin: Error while checking KRW balance")
            # Continue without adjustment if there's an error
        
        order_type = None
        order_result = None
        
        # Handle market and limit orders separately
        if price_type == "market":
            log_info(f"buy_coin: Attempting market buy", {"ticker": ticker, "amount": amount})
            print(f"Market buy order: {ticker}, {amount}KRW")
            order_type = "market"
            try:
                order_result = upbit.buy_market_order(ticker, amount)
                log_info(f"buy_coin: Order result", {"result": order_result})
            except Exception as e:
                error_msg = f"Error during market buy: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
                
        else:  # limit order
            if not limit_price or limit_price <= 0:
                error_msg = "Valid 'limit_price' is required for limit orders."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
            # Calculate volume (amount / limit price)
            volume = amount / limit_price
            
            log_info(f"buy_coin: Attempting limit buy", {"ticker": ticker, "price": limit_price, "volume": volume})
            print(f"Limit buy order: {ticker}, price: {limit_price}KRW, quantity: {volume}")
            order_type = "limit"
            try:
                order_result = upbit.buy_limit_order(ticker, limit_price, volume)
                log_info(f"buy_coin: Order result", {"result": order_result})
            except Exception as e:
                error_msg = f"Error during limit buy: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Return order result
        if order_result and 'uuid' in order_result:
            result = {
                'success': True,
                'message': f"{ticker} {order_type} buy order has been submitted. Order ID: {order_result['uuid']}\nYou can check the order settlement results in the 'Transaction History' tab.",
                'order_id': order_result['uuid'],
                'order_info': order_result
            }
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"Order was successful but did not receive an order ID: {order_result}"
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"Unexpected error during buy order: {str(e)}"
        log_error(e, error_msg)
        return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)


@function_tool
async def sell_coin_func(ticker: str, price_type: str, amount: Union[str, float], limit_price: Optional[float]) -> str:
    """
    Coin sell function
    
    Args:
        ticker: Coin ticker symbol (e.g., 'BTC')
        price_type: 'market' or 'limit'
        amount: Amount to sell (coin quantity or 'all')
        limit_price: Price for limit orders
    """
    try:
        # Start logging
        log_info("sell_coin function called", {"ticker": ticker, "price_type": price_type, "amount": amount, "limit_price": limit_price})
        print(f"Sell function called: {ticker}, {price_type}, {amount}, {limit_price}")
        
        # Process ticker
        ticker = ticker.upper()
        
        # Validate ticker
        if not ticker:
            error_msg = "Ticker is not specified."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Add KRW market prefix if missing
        if not ticker.startswith("KRW-"):
            ticker = f"KRW-{ticker}"
        log_info(f"sell_coin: Coin name extracted", {"ticker": ticker})
        
        # Get upbit instance
        upbit = get_upbit_instance()
        if not upbit:
            error_msg = "Unable to create Upbit API instance. Please check your API key settings."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        log_info(f"sell_coin: Valid Upbit instance confirmed")
        
        # Check order type
        price_type = price_type.lower()
        if price_type not in ["market", "limit"]:
            error_msg = f"Unsupported order type: {price_type}. Only 'market' or 'limit' can be used."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Check holdings - based on portfolio
        coin_currency = ticker.replace("KRW-", "")
        coin_balance = 0
        try:
            balances = upbit.get_balances()
            for balance in balances:
                if balance['currency'] == coin_currency:
                    coin_balance = float(balance['balance'])
                    break
            
            log_info(f"sell_coin: Coin balance check", {"ticker": ticker, "balance": coin_balance})
            
            if coin_balance <= 0:
                error_msg = f"You don't have any {coin_currency} coins. Cannot sell."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        except Exception as e:
            error_msg = f"Error while checking coin balance: {str(e)}"
            log_error(e, error_msg)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Parse amount
        amount_value = None
        
        # Selling all
        if isinstance(amount, str) and amount.lower() in ["all", "전체", "전량"]:
            amount_value = coin_balance
            log_info(f"sell_coin: Sell all request", {"coin_balance": coin_balance})
        else:
            try:
                amount_value = float(amount)
                # Error if more than holding
                if amount_value > coin_balance:
                    error_msg = f"Sell amount ({amount_value}) is greater than your balance ({coin_balance})."
                    log_error(None, error_msg, show_tb=False)
                    return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            except ValueError:
                error_msg = f"Invalid sell amount: {amount}. Please specify a number or 'all'."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Check if amount is valid
        if amount_value <= 0:
            error_msg = f"Invalid sell amount: {amount_value}. Must be positive."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        order_type = None
        order_result = None
        
        # Handle market and limit orders separately
        if price_type == "market":
            log_info(f"sell_coin: Attempting market sell", {"ticker": ticker, "amount": amount_value})
            print(f"Market sell order: {ticker}, {amount_value} units")
            order_type = "market"
            try:
                order_result = upbit.sell_market_order(ticker, amount_value)
                log_info(f"sell_coin: Order result", {"result": order_result})
            except Exception as e:
                error_msg = f"Error during market sell: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
                
        else:  # limit order
            if not limit_price or limit_price <= 0:
                error_msg = "Valid 'limit_price' is required for limit orders."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
            log_info(f"sell_coin: Attempting limit sell", {"ticker": ticker, "price": limit_price, "amount": amount_value})
            print(f"Limit sell order: {ticker}, price: {limit_price}KRW, quantity: {amount_value} units")
            order_type = "limit"
            try:
                order_result = upbit.sell_limit_order(ticker, limit_price, amount_value)
                log_info(f"sell_coin: Order result", {"result": order_result})
            except Exception as e:
                error_msg = f"Error during limit sell: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # Return order result
        if order_result and 'uuid' in order_result:
            result = {
                'success': True,
                'message': f"{ticker} {order_type} sell order has been submitted. Order ID: {order_result['uuid']}\nYou can check the order settlement results in the 'Transaction History' tab.",
                'order_id': order_result['uuid'],
                'order_info': order_result
            }
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"Order was successful but did not receive an order ID: {order_result}"
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"Unexpected error during sell order: {str(e)}"
        log_error(e, error_msg)
        return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)

@function_tool
async def check_order_status_func(order_id: str) -> str:
    """
    Check the status of an order.
    
    Args:
        order_id: ID (UUID) of the order to check
    """
    function_name = "check_order_status"
    log_info(f"{function_name} function called", {"order_id": order_id})
    
    try:
        # Validate order ID
        if not order_id:
            error_msg = "Order ID is not specified."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        log_info(f"{function_name}: Parameters verified", {"order_id": order_id})
        
        st.write(f"Checking order status...")
        upbit_trade = get_upbit_trade_instance()
        
        if upbit_trade and upbit_trade.is_valid:
            log_info(f"{function_name}: Valid Upbit instance confirmed")
            # Query order status
            order_result = upbit_trade.get_order(order_id)
            log_info(f"{function_name}: Order query result", {"result": order_result})
            
            if order_result and 'uuid' in order_result:
                # Process order information
                order_info = {
                    'order_id': order_result['uuid'],
                    'status': order_result['state'],
                    'side': 'buy' if order_result['side'] == 'bid' else 'sell',
                    'price': float(order_result['price']) if order_result['price'] else None,
                    'volume': float(order_result['volume']) if order_result['volume'] else None,
                    'executed_volume': float(order_result['executed_volume']) if order_result['executed_volume'] else 0,
                    'remaining_volume': float(order_result['remaining_volume']) if order_result['remaining_volume'] else 0,
                    'created_at': order_result['created_at'],
                    'market': order_result['market'],
                    'order_type': order_result['ord_type']
                }
                
                # Status localization
                status_map = {
                    'wait': 'Waiting',
                    'watch': 'Reserved',
                    'done': 'Completed',
                    'cancel': 'Canceled'
                }
                order_info['status_korean'] = status_map.get(order_result['state'], order_result['state'])
                
                # Calculate execution status and rate
                if order_info['executed_volume'] > 0:
                    order_info['is_executed'] = True
                    if order_info['volume'] > 0:
                        order_info['execution_rate'] = (order_info['executed_volume'] / order_info['volume']) * 100
                    else:
                        order_info['execution_rate'] = 0
                else:
                    order_info['is_executed'] = False
                    order_info['execution_rate'] = 0
                
                log_info(f"{function_name}: Order information processing complete", {"processed_info": order_info})
                
                result = {
                    'success': True,
                    'message': f"Order query successful: {order_info['status_korean']}",
                    'order_info': order_info
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                log_info(f"{function_name}: Order query failed", {"order_id": order_id})
                result = {
                    'success': False,
                    'message': f"Order query failed: {order_result}",
                    'order_info': None
                }
                return json.dumps(result, ensure_ascii=False)
        
        # No API key or invalid
        log_info(f"{function_name}: No API key or invalid")
        result = {
            'success': False,
            'message': "API key is not set or is invalid. Please check your key on the API Settings page.",
            'order_info': None,
            'is_demo': True
        }
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        log_error(e, f"{function_name} error during function execution")
        result = {
            'success': False,
            'message': f"Error while checking order status: {str(e)}",
            'order_info': None
        }
        return json.dumps(result, ensure_ascii=False)

# Tool schema definitions
GET_AVAILABLE_COINS_SCHEMA = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False
}

GET_COIN_PRICE_INFO_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {
            "type": "string",
            "description": "Ticker of the coin to query (e.g., 'KRW-BTC' or 'BTC')"
        }
    },
    "required": ["ticker"],
    "additionalProperties": False
}

BUY_COIN_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {
            "type": "string",
            "description": "Ticker of the coin to buy (e.g., 'KRW-BTC' or 'BTC')"
        },
        "price": {
            "type": ["number", "null"],
            "description": "Order price for limit buy. null for market order."
        },
        "amount": {
            "type": ["number", "null"],
            "description": "Amount to buy (KRW) or quantity. For market orders, KRW amount; for limit orders, coin quantity."
        }
    },
    "required": ["ticker", "price", "amount"],
    "additionalProperties": False
}

SELL_COIN_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {
            "type": "string",
            "description": "Ticker of the coin to sell (e.g., 'KRW-BTC' or 'BTC')"
        },
        "price": {
            "type": ["number", "null"],
            "description": "Order price for limit sell. null for market order."
        },
        "amount": {
            "type": ["number", "null"],
            "description": "Quantity of coins to sell. null to sell all holdings."
        }
    },
    "required": ["ticker", "price", "amount"],
    "additionalProperties": False
}

CHECK_ORDER_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {
            "type": "string",
            "description": "ID (UUID) of the order to check"
        }
    },
    "required": ["order_id"],
    "additionalProperties": False
}

# Wrapper for tool functions
async def tool_wrapper(func, ctx, args, retries=2):
    """
    Wrapper for tool function calls - provides error handling and retry functionality
    """
    function_name = func.__name__
    attempt = 0
    last_error = None
    
    while attempt <= retries:
        try:
            if attempt > 0:
                log_info(f"{function_name}: Retry {attempt}/{retries}")
                
            return await func(ctx, args)
        except Exception as e:
            last_error = e
            log_error(e, f"Error during {function_name} function execution (attempt {attempt+1}/{retries+1})")
            attempt += 1
            
            # Wait briefly before retry if this isn't the last attempt
            if attempt <= retries:
                await asyncio.sleep(1)  # Wait 1 second
    
    # When all retries fail
    log_error(last_error, f"{function_name} function execution failed - maximum retry count exceeded")
    
    # Default error response
    error_response = {
        'success': False,
        'message': f"Function execution failed: {str(last_error)} (maximum retry count exceeded)",
        'error': str(last_error)
    }
    return json.dumps(error_response, ensure_ascii=False)




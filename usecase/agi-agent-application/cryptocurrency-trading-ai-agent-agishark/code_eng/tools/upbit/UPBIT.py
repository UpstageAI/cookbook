import jwt
import hashlib
import os
import requests
import uuid
from urllib.parse import urlencode, unquote

import pyupbit

from datetime import datetime, timedelta
import time

class Trade:
    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key if access_key else '{Enter ACCESS KEY : }'
        self.secret_key = secret_key if secret_key else '{Enter SECRET KEY : }'
        self.server_url = 'https://api.upbit.com'
        
        # API key validity status
        self.is_valid = False
        
        try:
            if self.access_key != '{Enter ACCESS KEY : }' and self.secret_key != '{Enter SECRET KEY : }':
                # Create pyupbit instance
                self.upbit = pyupbit.Upbit(access_key, secret_key)
                # Simple validity check
                try:
                    balance = self.upbit.get_balance("KRW")
                    if balance is not None:
                        self.is_valid = True
                    else:
                        print("⚠️ Warning: API key authentication failed")
                except Exception as e:
                    print(f"⚠️ Warning: Error during API authentication: {e}")
            else:
                self.upbit = None
                print("⚠️ Warning: Real API keys are not set. Some functions may be limited.")
        except Exception as e:
            self.upbit = None
            print(f"⚠️ Warning: Error initializing Upbit API: {e}")
    
    def get_order_history(self, ticker_or_uuid="", state=None, page=1, limit=100, states=None):
        """Query order history (improved version, enhanced pagination support)
        
        Args:
            ticker_or_uuid (str): Ticker name or order UUID (empty: query all orders)
            state (str): deprecated, use states instead.
            page (int): Page number to query (starts from 1)
            limit (int): Number of requests (max 100)
            states (list): List of order states to query (e.g., ["wait", "done"]), None to try all states
        
        Returns:
            list: List of order history
        """
        if not self.is_valid or not self.upbit:
            print("Valid API key is not set.")
            return []
        
        # Process states argument (maintain compatibility with state argument)
        if states is None:
            if state: # Use existing state argument if present
                target_states = [state]
            else: # Query all states if both are missing
                target_states = ["wait", "done", "cancel"]
        else:
            target_states = states
        
        all_results = []
        try:
            # Try using pyupbit library (modified ticker_or_uuid handling)
            for current_state in target_states:
                try:
                    call_args = {}
                    if ticker_or_uuid:
                        if len(ticker_or_uuid) > 30 and '-' in ticker_or_uuid:
                            call_args['uuids'] = [ticker_or_uuid]
                        else:
                            call_args['market'] = ticker_or_uuid
                    call_args['state'] = current_state
                    call_args['limit'] = limit
                    call_args['page'] = page
                    
                    print(f"[Debug] pyupbit.get_order call: {call_args}")
                    result = self.upbit.get_order(**call_args)
                    print(f"[Debug] pyupbit.get_order result ({current_state}, page={page}): {type(result)}")
                    
                    if isinstance(result, list):
                        all_results.extend(result)
                    elif isinstance(result, dict) and 'error' not in result:
                        all_results.append(result)
                    elif isinstance(result, dict) and 'error' in result:
                        print(f"[Debug] pyupbit.get_order returned error: {result['error']}")
                
                except Exception as e:
                    print(f"Error querying pyupbit {current_state} state orders: {str(e)}")
                    print(f"[Debug] pyupbit error occurred. Attempting direct API call (page={page})...")
                    # Pass page argument during fallback
                    direct_result = self._get_orders_direct_api(ticker_or_uuid=ticker_or_uuid, state=current_state, page=page, limit=limit)
                    if isinstance(direct_result, list):
                        all_results.extend(direct_result)
                    elif isinstance(direct_result, dict) and 'error' not in direct_result:
                        all_results.append(direct_result)
                    elif isinstance(direct_result, dict) and 'error' in direct_result:
                        print(f"[Debug] Direct API call also returned error: {direct_result['error']}")
            
            if all_results:
                print(f"[Debug] Page {page} returned {len(all_results)} order results")
                return all_results
            else:
                print(f"[Debug] Page {page} pyupbit and direct API calls returned no results.")
                return []
        
        except Exception as e:
            print(f"Exception occurred during get_order_history(page={page}): {str(e)}")
            return []
    
    def _get_orders_direct_api(self, ticker_or_uuid=None, state=None, page=1, limit=100):
        """Query order history by direct API call"""
        try:
            query = {'limit': limit, 'page': page}
            if ticker_or_uuid:
                if len(ticker_or_uuid) >= 30:
                    query['uuid'] = ticker_or_uuid
                else:
                    query['market'] = ticker_or_uuid
            if state:
                query['state'] = state
            
            query_string = urlencode(query).encode()
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            
            payload = {
                'access_key': self.access_key,
                'nonce': str(uuid.uuid4()),
                'query_hash': query_hash,
                'query_hash_alg': 'SHA512'
            }
            
            jwt_token = jwt.encode(payload, self.secret_key)
            if isinstance(jwt_token, bytes):
                jwt_token = jwt_token.decode('utf-8')
                
            authorize_token = f'Bearer {jwt_token}'
            headers = {'Authorization': authorize_token}
            
            print(f"[Debug] Direct API call: GET {self.server_url}/v1/orders, Params: {query}")
            response = requests.get(f"{self.server_url}/v1/orders", params=query, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API request failed (HTTP {response.status_code}): {response.text}")
                try:
                    return response.json()
                except:
                    return []
        except Exception as e:
            print(f"Error during direct API call: {e}")
            return []
    
    def orders_status(self, orderid): 
        """Query individual order details"""
        if not self.is_valid:
            return {}
            
        try:
            query = {'uuid': orderid}
            query_string = urlencode(query).encode()
            
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            
            payload = {
                'access_key': self.access_key,
                'nonce': str(uuid.uuid4()),
                'query_hash': query_hash,
                'query_hash_alg': 'SHA512'
            }
            
            jwt_token = jwt.encode(payload, self.secret_key)
            # Convert JWT encoding result to string if it's bytes
            if isinstance(jwt_token, bytes):
                jwt_token = jwt_token.decode('utf-8')
                
            authorize_token = f'Bearer {jwt_token}'
            headers = {'Authorization': authorize_token}
            
            response = requests.get(f"{self.server_url}/v1/order", params=query, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Order detail query failed (HTTP {response.status_code}): {response.text}")
                return {}
        except Exception as e:
            print(f"Error during order detail query: {e}")
            return {}
    
    def get_balance(self, ticker): 
        """Query specific coin balance"""
        if not self.is_valid or not self.upbit:
            return 0
            
        try:
            return self.upbit.get_balance(ticker)
        except Exception as e:
            print(f"Balance query failed: {e}")
            try:
                # Try direct API call
                query = {}
                query_string = urlencode(query).encode()
                
                m = hashlib.sha512()
                m.update(query_string)
                query_hash = m.hexdigest()
                
                payload = {
                    'access_key': self.access_key,
                    'nonce': str(uuid.uuid4()),
                    'query_hash': query_hash,
                    'query_hash_alg': 'SHA512'
                }
                
                jwt_token = jwt.encode(payload, self.secret_key)
                if isinstance(jwt_token, bytes):
                    jwt_token = jwt_token.decode('utf-8')
                    
                authorize_token = f'Bearer {jwt_token}'
                headers = {'Authorization': authorize_token}
                
                response = requests.get(f"{self.server_url}/v1/accounts", headers=headers)
                
                if response.status_code == 200:
                    accounts = response.json()
                    for account in accounts:
                        if account['currency'] == ticker.split('-')[-1]:
                            return float(account['balance'])
                    return 0
                else:
                    return 0
            except Exception:
                return 0
    
    def get_current_price(self, ticker): 
        """Query current price of specific coin"""
        try:
            return pyupbit.get_current_price(ticker)
        except Exception as e:
            print(f"Current price query failed: {e}")
            return 0
    
    def get_order(self, orderid): 
        """Query specific order information"""
        return self.orders_status(orderid)
    
    def get_ohlcv(self, ticker, interval, count): 
        """Query chart data for specific coin"""
        try:
            return pyupbit.get_ohlcv(ticker, interval=interval, count=count)
        except Exception as e:
            print(f"Chart data query failed: {e}")
            return None
    
    def get_market_all(self): 
        """Query all coin prices"""
        try:
            url = "https://api.upbit.com/v1/market/all"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Market data query failed (HTTP {response.status_code})")
                return []
        except Exception as e:
            print(f"Error during market data query: {e}")
            return []
    
    def get_market_detail(self, market): 
        """Query detailed information for specific coin"""
        try:
            return pyupbit.get_market_detail(market)
        except Exception as e:
            print(f"Market detail query failed: {e}")
            return {}
    
    def buy_market_order(self, ticker, amount): 
        """Market buy order"""
        if not self.is_valid or not self.upbit:
            print("Cannot execute order because valid API key is not set.")
            return None
            
        try:
            result = self.upbit.buy_market_order(ticker, amount)
            print(f"Market buy order: {ticker}, {amount}KRW")
            return result
        except Exception as e:
            print(f"Market buy order failed: {e}")
            return None

    def sell_market_order(self, ticker, volume=None): 
        """Market sell order"""
        if not self.is_valid or not self.upbit:
            print("Cannot execute order because valid API key is not set.")
            return None
            
        try:
            if volume is None:
                # Sell all
                available_volume = self.upbit.get_balance(ticker)
                if available_volume > 0:
                    result = self.upbit.sell_market_order(ticker, available_volume)
                    print(f"Full market sell order: {ticker}, {available_volume}{ticker.split('-')[1]}")
                    return result
                else:
                    print(f"No {ticker} quantity to sell.")
                    return None
            else:
                # Sell specified quantity
                result = self.upbit.sell_market_order(ticker, volume)
                print(f"Market sell order: {ticker}, {volume}{ticker.split('-')[1]}")
                return result
        except Exception as e:
            print(f"Market sell order failed: {e}")
            return None

    def buy_limit_order(self, ticker, price, volume): 
        """Limit buy order"""
        if not self.is_valid or not self.upbit:
            print("Cannot execute order because valid API key is not set.")
            return None
            
        try:
            result = self.upbit.buy_limit_order(ticker, price, volume)
            print(f"Limit buy order: {ticker}, price: {price}KRW, quantity: {volume}")
            return result
        except Exception as e:
            print(f"Limit buy order failed: {e}")
            return None

    def sell_limit_order(self, ticker, price, volume=None): 
        """Limit sell order"""
        if not self.is_valid or not self.upbit:
            print("Cannot execute order because valid API key is not set.")
            return None
            
        try:
            if volume is None:
                # Sell all
                available_volume = self.upbit.get_balance(ticker)
                if available_volume > 0:
                    result = self.upbit.sell_limit_order(ticker, price, available_volume)
                    print(f"Full limit sell order: {ticker}, price: {price}KRW, quantity: {available_volume}")
                    return result
                else:
                    print(f"No {ticker} quantity to sell.")
                    return None
            else:
                # Sell specified quantity
                result = self.upbit.sell_limit_order(ticker, price, volume)
                print(f"Limit sell order: {ticker}, price: {price}KRW, quantity: {volume}")
                return result
        except Exception as e:
            print(f"Limit sell order failed: {e}")
            return None

    def cancel_order(self, uuid): 
        """Cancel order"""
        if not self.is_valid or not self.upbit:
            print("Cannot execute order cancellation because valid API key is not set.")
            return None
            
        try:
            result = self.upbit.cancel_order(uuid)
            print(f"Order cancellation: {uuid}")
            return result
        except Exception as e:
            print(f"Order cancellation failed: {e}")
            return None

    def Strategy(self, ticker, k):
        df=pyupbit.get_ohlcv(ticker, interval="day", count=200)
        df['range']=df['high']-df['low']
        df['target']=df['open']+df['range'].shift(1)
        df['bull']=df['open']>df['target']
        df['ma5']=df['close'].rolling(window=5).mean()
        df['buy']=df['bull']&df['close']>df['ma5']
        df['sell']=df['bull']&df['close']<df['ma5']

        if df['buy'].iloc[-1]:
            return pyupbit.buy_limit(ticker, k)
        elif df['sell'].iloc[-1]:
            return pyupbit.sell_limit(ticker, k)
    
    def run(self):
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(e)
                time.sleep(1) 
    
    def schedule_job(self):
        schedule.every(1).seconds.do(self.run) 
    
    def start(self):
        self.schedule_job()
        self.run()
    
    def auto_trade(self, ticker, invest_amount, strategy="vb", k=0.5): # Execute automatic trading
        """
        Execute automatic trading
    
        Args:
            ticker (str): Coin ticker (e.g., "KRW-BTC")
            invest_amount (float): Investment amount (KRW)
            strategy (str, optional): Strategy selection ("vb": Volatility Breakout)
            k (float, optional): k value for Volatility Breakout strategy
        
        Returns:
            dict: Order result
        """
        try:
            # Check current time
            now = datetime.now()
        
            if strategy == "vb":
                # Volatility Breakout strategy
                df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            
                # Calculate volatility
                prev_range = df['high'].iloc[-2] - df['low'].iloc[-2]
                target_price = df['open'].iloc[-1] + (prev_range * k)
            
                # Check current price
                current_price = pyupbit.get_current_price(ticker)
            
                # Buy condition: Current price is above target price, and between 09:00~20:00
                if (current_price >= target_price) and (9 <= now.hour < 20):
                    # Check available cash
                    krw_balance = self.upbit.get_balance("KRW")
                
                    # Check minimum order amount (minimum 5000 KRW)
                    order_amount = min(invest_amount, krw_balance)
                    if order_amount >= 5000:
                        return self.buy_market_order(ticker, order_amount)
                    else:
                        print(f"Insufficient available amount for order: {order_amount}KRW")
                        return None
            
                # Sell condition: Between 08:50~09:00, sell all
                elif (8 == now.hour and now.minute >= 50) or (now.hour == 9 and now.minute < 1):
                    return self.sell_market_order(ticker)
            
                else:
                    print(f"Trading conditions not met: Current price {current_price}, Target price {target_price}")
                    return None
            else:
                print(f"Unsupported strategy: {strategy}")
                return None
            
        except Exception as e:
            print(f"Automatic trading execution failed: {e}")
            return None 
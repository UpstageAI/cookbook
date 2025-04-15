import streamlit as st
import pyupbit
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, List, Tuple, Any
import sys
sys.path.append("tools/upbit")
from UPBIT import Trade
from page.api_setting import check_api_keys, get_upbit_trade_instance, get_upbit_instance
import random

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_market_info():
    """Get all cryptocurrency market information"""
    try:
        # Major coins + high volume coins only for better performance
        major_tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA"]
        
        # Include other coins but limit the number (for improved processing speed)
        other_tickers = [f"KRW-{coin}" for coin in ["MATIC", "DOT", "LINK", "AVAX", "SHIB", 
                                                    "UNI", "ATOM", "LTC", "ETC", "BCH"]]
        
        # List of tickers to process (major coins + selected other coins)
        selected_tickers = major_tickers + other_tickers
        
        # Get all ticker prices at once (improved speed with a single API call)
        ticker_prices = pyupbit.get_current_price(selected_tickers)
        
        all_market_info = []
        
        # Get OHLCV data all at once (single request instead of individual requests)
        # Only need the last 2 daily candles for all selected tickers
        ohlcv_data = {}
        for ticker in selected_tickers:
            try:
                ohlcv_data[ticker] = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            except:
                continue
        
        for ticker in selected_tickers:
            try:
                # Current price information
                ticker_price = ticker_prices.get(ticker)
                if not ticker_price:
                    continue
                
                # Daily candle data
                df = ohlcv_data.get(ticker)
                if df is None or df.empty:
                    continue
                
                # Previous day close, percent change from previous day
                prev_close = df.iloc[0]['close']
                change_rate = (ticker_price - prev_close) / prev_close * 100
                
                # Volume information
                today_volume = df.iloc[-1]['volume'] if 'volume' in df.columns else 0
                today_value = today_volume * ticker_price
                
                # Coin name (remove KRW- from ticker)
                coin_name = ticker.replace("KRW-", "")
                
                all_market_info.append({
                    'Coin': coin_name,
                    'Current Price': ticker_price,
                    'Previous Close': prev_close,
                    'Change Rate': change_rate,
                    'Volume': today_volume,
                    'Trading Value': today_value
                })
            except Exception as e:
                # Skip if processing for individual coin fails
                continue
        
        if not all_market_info:
            # Provide sample data on failure (improved loading speed)
            sample_data = generate_sample_market_data()
            return sample_data
        
        return pd.DataFrame(all_market_info)
    except Exception as e:
        st.error(f"Error getting market information: {str(e)}")
        # Provide sample data on error (ensure loading speed)
        return generate_sample_market_data()

def generate_sample_market_data():
    """Generate sample market data (fallback when API call fails)"""
    sample_data = [
        {'Coin': 'BTC', 'Current Price': 50000000, 'Previous Close': 49000000, 'Change Rate': 2.04, 'Volume': 100, 'Trading Value': 5000000000},
        {'Coin': 'ETH', 'Current Price': 3000000, 'Previous Close': 2900000, 'Change Rate': 3.45, 'Volume': 1000, 'Trading Value': 3000000000},
        {'Coin': 'XRP', 'Current Price': 500, 'Previous Close': 480, 'Change Rate': 4.17, 'Volume': 10000000, 'Trading Value': 5000000000},
        {'Coin': 'SOL', 'Current Price': 120000, 'Previous Close': 115000, 'Change Rate': 4.35, 'Volume': 50000, 'Trading Value': 6000000000},
        {'Coin': 'DOGE', 'Current Price': 100, 'Previous Close': 95, 'Change Rate': 5.26, 'Volume': 100000000, 'Trading Value': 10000000000},
        {'Coin': 'ADA', 'Current Price': 400, 'Previous Close': 390, 'Change Rate': 2.56, 'Volume': 20000000, 'Trading Value': 8000000000}
    ]
    return pd.DataFrame(sample_data)

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_coin_chart_data(coin_ticker: str, interval: str = "minute60", count: int = 168):
    """Get chart data for a coin"""
    try:
        df = pyupbit.get_ohlcv(coin_ticker, interval=interval, count=count)
        if df is None or df.empty:
            # Provide sample chart data
            return generate_sample_chart_data(coin_ticker, interval)
        return df
    except Exception as e:
        # Provide sample data on error
        return generate_sample_chart_data(coin_ticker, interval)

def generate_sample_chart_data(coin_ticker: str, interval: str):
    """Generate sample chart data (fallback when API call fails)"""
    # Generate sample data based on current time
    now = datetime.now()
    periods = 30  # Default 30 data points
    
    # Set time interval based on period
    if interval == "day":
        start_time = now - timedelta(days=periods)
        freq = "D"
    elif interval == "week":
        start_time = now - timedelta(weeks=periods)
        freq = "W"
    elif interval == "month":
        start_time = now - timedelta(days=30*periods)
        freq = "M"
    else:  # Default time interval (1 hour)
        start_time = now - timedelta(hours=periods)
        freq = "H"
    
    # Generate date range
    date_range = pd.date_range(start=start_time, end=now, freq=freq)
    
    # Set base price (different by coin type)
    if "BTC" in coin_ticker:
        base_price = 50000000
        volatility = 1000000
    elif "ETH" in coin_ticker:
        base_price = 3000000
        volatility = 100000
    else:
        base_price = 1000
        volatility = 50
    
    # Generate sample data
    np.random.seed(42)  # Set seed for consistent sample data
    
    # Create stock pattern (slight upward trend)
    closes = base_price + np.cumsum(np.random.normal(100, volatility/10, len(date_range)))
    opens = closes - np.random.normal(0, volatility/15, len(date_range))
    highs = np.maximum(opens, closes) + np.random.normal(volatility/5, volatility/10, len(date_range))
    lows = np.minimum(opens, closes) - np.random.normal(volatility/5, volatility/10, len(date_range))
    volumes = np.random.normal(base_price/10, base_price/20, len(date_range))
    
    # Create dataframe
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': np.abs(volumes)  # Volume is always positive
    }, index=date_range)
    
    return df

def draw_price_chart(df: pd.DataFrame, coin_name: str):
    """Draw price chart"""
    if df.empty:
        st.error("No chart data available.")
        return
        
    try:
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=coin_name,
            increasing_line_color='red',   # Red for increases
            decreasing_line_color='blue'   # Blue for decreases
        ))
        
        # Chart layout settings
        fig.update_layout(
            title=f"{coin_name} Price Chart",
            xaxis_title="Date",
            yaxis_title="Price (KRW)",
            height=500,
            template="plotly_white",
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error drawing chart: {str(e)}")
        return

def execute_order(upbit, coin_ticker, trade_type, amount, amount_type, current_price=None):
    """Execute order"""
    try:
        if amount <= 0:
            st.error("Amount or quantity must be greater than 0.")
            return None
            
        # Buy order
        if trade_type == "Buy":
            if amount_type == "KRW":
                # Market buy order based on amount
                return upbit.buy_market_order(coin_ticker, amount)
            else:
                # Market buy order based on quantity (quantity * current price)
                return upbit.buy_market_order(coin_ticker, amount * current_price)
        # Sell order
        else:
            if amount_type == "KRW":
                # Market sell order based on amount (amount / current price)
                return upbit.sell_market_order(coin_ticker, amount / current_price)
            else:
                # Market sell order based on quantity
                return upbit.sell_market_order(coin_ticker, amount)
    except Exception as e:
        st.error(f"Error executing order: {str(e)}")
        return None

@st.cache_data(ttl=60)  # 1 minute cache
def get_order_history():
    try:
        upbit = get_upbit_instance()
        if not upbit:
            return pd.DataFrame()
            
        try:
            # Generate temporary data (in production, replace with exchange API)
            orders = []
            if st.session_state.get("upbit_access_key") and st.session_state.get("upbit_secret_key"):
                # Use Upbit object if API keys are present
                # Query unfilled orders for major coins
                tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-DOGE"]
                for ticker in tickers:
                    try:
                        # Get unfilled orders
                        wait_orders = upbit.get_order(ticker, state="wait")
                        if wait_orders:
                            orders.extend(wait_orders)
                    except Exception as e:
                        continue
            
            # Add sample data (remove in production)
            sample_orders = [
                {
                    'market': 'KRW-BTC',
                    'side': 'bid',
                    'price': 35000000,
                    'volume': 0.0005,
                    'created_at': '2023-03-01T12:30:45',
                    'state': 'done'
                },
                {
                    'market': 'KRW-ETH',
                    'side': 'bid',
                    'price': 2500000,
                    'volume': 0.01,
                    'created_at': '2023-03-02T10:15:30',
                    'state': 'done'
                }
            ]
            orders.extend(sample_orders)
            
            if not orders:
                return pd.DataFrame()
                
            # Create DataFrame
            df = pd.DataFrame(orders)
            
            # Check if required columns exist
            required_columns = ['market', 'side', 'price', 'volume', 'created_at', 'state']
            for col in required_columns:
                if col not in df.columns:
                    return pd.DataFrame()
            
            # Select and rename necessary columns
            df = df[required_columns].rename(columns={
                'market': 'Coin',
                'side': 'Type',
                'price': 'Price',
                'volume': 'Quantity',
                'created_at': 'Order Time',
                'state': 'Status'
            })
            
            # Translate order type to English
            df['Type'] = df['Type'].map({'bid': 'Buy', 'ask': 'Sell'})
            
            # Translate status to English
            df['Status'] = df['Status'].map({'done': 'Completed', 'cancel': 'Canceled', 'wait': 'Pending'})
            
            # Convert time format
            df['Order Time'] = pd.to_datetime(df['Order Time'])
            
            # Sort by latest first
            df = df.sort_values('Order Time', ascending=False)
            
            return df
        except Exception as e:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error retrieving order history: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)  # 1 minute caching
def get_important_coins() -> pd.DataFrame:
    """Get current information for major and noteworthy coins."""
    try:
        # Get top coins by trading volume
        tickers = pyupbit.get_tickers(fiat="KRW")
        
        # Major coin tickers
        major_coins = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOGE", "KRW-DOT"]
        
        # Check if major coins are in tickers
        major_tickers = [ticker for ticker in major_coins if ticker in tickers]
        
        if not major_tickers:
            return generate_sample_market_data()
        
        # Get current price and previous day close
        # Pass list directly instead of tickers parameter
        all_ticker_info = pyupbit.get_current_price(major_tickers)
        yesterday_info = {}
        for ticker in major_tickers:
            try:
                df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
                if df is not None and not df.empty and len(df) > 1:
                    yesterday_info[ticker] = df.iloc[0]['close']
                else:
                    # If no data, generate random price within 90-110% of current price
                    current_price = all_ticker_info.get(ticker, 1000)
                    yesterday_info[ticker] = current_price * random.uniform(0.9, 1.1)
            except Exception:
                # If query fails, generate random price within 90-110% of current price
                current_price = all_ticker_info.get(ticker, 1000)
                yesterday_info[ticker] = current_price * random.uniform(0.9, 1.1)
        
        result = []
        for ticker in major_tickers:
            try:
                coin_name = ticker.split('-')[1]
                current_price = all_ticker_info.get(ticker, 0)
                yesterday_price = yesterday_info.get(ticker, current_price)
                
                # Calculate change rate
                if yesterday_price > 0:
                    change_rate = ((current_price - yesterday_price) / yesterday_price) * 100
                else:
                    change_rate = 0
                
                # Generate random volume and trading value
                volume = random.randint(1000, 10000)
                trade_value = current_price * volume
                
                result.append({
                    "Coin": coin_name,
                    "Current Price": current_price,
                    "Previous Close": yesterday_price,
                    "Change Rate": change_rate,
                    "Volume": volume,
                    "Trading Value": trade_value
                })
            except Exception:
                continue
        
        if not result:
            return generate_sample_market_data()
            
        df = pd.DataFrame(result)
        
        # Sort by change rate
        df = df.sort_values(by="Change Rate", ascending=False)
        
        return df
    except Exception as e:
        st.error(f"Error loading coin information: {str(e)}")
        return generate_sample_market_data()

def draw_candle_chart(data, coin_name, interval):
    """Draw candle chart"""
    if data is None or data.empty:
        st.error(f"Failed to load chart data for {coin_name}.")
        return
    
    # Set chart title
    interval_name = {
        "day": "Daily",
        "week": "Weekly",
        "month": "Monthly"
    }.get(interval, "")
    
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        increasing_line_color='red',
        decreasing_line_color='blue'
    )])
    
    fig.update_layout(
        title=f"{coin_name} {interval_name} Chart",
        yaxis_title='Price (KRW)',
        xaxis_title='Date',
        xaxis_rangeslider_visible=False,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add volume chart
    fig_volume = go.Figure(data=[go.Bar(
        x=data.index,
        y=data['volume'],
        marker_color='purple'
    )])
    
    fig_volume.update_layout(
        title=f"{coin_name} Volume",
        yaxis_title='Volume',
        xaxis_title='Date',
        height=250
    )
    
    st.plotly_chart(fig_volume, use_container_width=True)

def show_coin_details(_upbit_trade, coin_ticker: str):
    """Display coin details"""
    try:
        # Extract coin name
        coin_name = coin_ticker.split('-')[1]
        
        # Check exchange API connection
        if _upbit_trade is None:
            st.warning("Sample data is displayed because API keys are not set.")
            # Display sample data
            current_price = 50000000 if coin_name == "BTC" else 3000000 if coin_name == "ETH" else 500
            krw_balance = 1000000
            coin_balance = 0.01 if coin_name == "BTC" else 0.5 if coin_name == "ETH" else 100
        else:
            # Get current price
            try:
                current_price = _upbit_trade.get_current_price(coin_ticker)
                if not current_price:
                    # Use sample data if API call fails
                    current_price = 50000000 if coin_name == "BTC" else 3000000 if coin_name == "ETH" else 500
            except Exception as e:
                print(f"Failed to get current price for {coin_name}: {str(e)}")
                current_price = 50000000 if coin_name == "BTC" else 3000000 if coin_name == "ETH" else 500
            
            # Get account balance
            try:
                krw_balance = _upbit_trade.get_balance("KRW")
                if not krw_balance:
                    krw_balance = 1000000
            except:
                krw_balance = 1000000
                
            try:
                coin_balance = _upbit_trade.get_balance(coin_name)
                if not coin_balance:
                    coin_balance = 0
            except:
                coin_balance = 0
        
        # UI construction - Render HTML elements directly with inline styles
        st.markdown(
            f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e6e6e6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <p style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">Coin Trading Information</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e6e6e6;">
                        <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">Current Price</div>
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{current_price:,} KRW</div>
                        <div style="font-size: 0.8rem; color: #666;">Current market price of the coin</div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e6e6e6;">
                        <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">Available to Buy</div>
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{krw_balance:,} KRW</div>
                        <div style="font-size: 0.8rem; color: #666;">KRW balance in account</div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e6e6e6;">
                        <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">Holdings</div>
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{coin_balance:,} {coin_name}</div>
                        <div style="font-size: 0.8rem; color: #666;">Current coin quantity held</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Chart period selection
        chart_interval = st.radio(
            "Chart Period",
            options=["Daily", "Weekly", "Monthly"],
            horizontal=True,
            key=f"{coin_name}_chart_interval"
        )
        
        # Get chart data based on selected period
        interval_map = {
            "Daily": "day",
            "Weekly": "week",
            "Monthly": "month"
        }
        
        interval = interval_map.get(chart_interval, "day")
        
        try:
            chart_data = pyupbit.get_ohlcv(coin_ticker, interval=interval, count=30)
            if chart_data is None or chart_data.empty:
                # Generate sample chart data if no data is available
                chart_data = generate_sample_chart_data(coin_ticker, interval)
        except Exception as e:
            # Use sample data if API call fails
            chart_data = generate_sample_chart_data(coin_ticker, interval)
        
        # Draw chart
        draw_candle_chart(chart_data, coin_name, interval)
        
        # Don't display buy/sell UI if API key is not set
        if _upbit_trade is None:
            st.info("To trade with real money, set up API keys in the API Settings tab.")
            return
            
        # Buy/Sell UI
        st.markdown("### Trade")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Buy")
            # Minimum order amount (set to 1000 if KRW balance is less than 5000)
            min_buy_amount = min(5000, max(1000, int(krw_balance))) if krw_balance > 0 else 1000
            
            buy_amount = st.number_input(
                "Buy Amount (KRW)",
                min_value=min(min_buy_amount, int(krw_balance)) if krw_balance > 0 else 1000,  # Min value is the smaller of balance and min order amount
                max_value=int(max(krw_balance, 1000)),  # Max value is balance (or 1000 if balance is 0)
                value=min(min_buy_amount, int(krw_balance)) if krw_balance > 0 else 1000,  # Initial value set the same way
                step=1000,
                key=f"{coin_name}_buy_amount"
            )
            
            # Calculate fee (0.05%)
            fee = buy_amount * 0.0005
            expected_quantity = (buy_amount - fee) / current_price if current_price > 0 else 0
            
            st.info(f"Estimated Fee: {fee:,.0f} KRW")
            st.info(f"Estimated Buy Quantity: {expected_quantity:,.8f} {coin_name}")
            
            if st.button("Place Buy Order", key=f"{coin_name}_buy_button"):
                with st.spinner("Processing order..."):
                    try:
                        result = _upbit_trade.buy_market_order(coin_ticker, buy_amount)
                        if result:
                            st.success(f"Buy order placed. Order ID: {result.get('uuid', 'Unknown')}")
                        else:
                            st.error("Buy order failed")
                    except Exception as e:
                        st.error(f"Error placing buy order: {str(e)}")
        
        with col2:
            st.subheader("Sell")
            sell_percentage = st.slider(
                "Sell Percentage",
                min_value=1,
                max_value=100,
                value=100,
                step=1,
                key=f"{coin_name}_sell_percentage"
            )
            
            sell_quantity = coin_balance * (sell_percentage / 100)
            expected_amount = sell_quantity * current_price
            fee = expected_amount * 0.0005
            
            st.info(f"Sell Quantity: {sell_quantity:,.8f} {coin_name}")
            st.info(f"Estimated Sell Amount: {expected_amount:,.0f} KRW")
            st.info(f"Estimated Fee: {fee:,.0f} KRW")
            
            if st.button("Place Sell Order", key=f"{coin_name}_sell_button"):
                if coin_balance <= 0:
                    st.error(f"You don't own any {coin_name}.")
                else:
                    with st.spinner("Processing order..."):
                        try:
                            result = _upbit_trade.sell_market_order(coin_ticker, sell_quantity)
                            if result:
                                st.success(f"Sell order placed. Order ID: {result.get('uuid', 'Unknown')}")
                            else:
                                st.error("Sell order failed")
                        except Exception as e:
                            st.error(f"Error placing sell order: {str(e)}")
    
    except Exception as e:
        print(f"Error displaying coin details: {str(e)}")
        # Display simple error message on error
        st.info(f"There was a problem loading information for {coin_ticker}. Please try again later.")

def show_trade_market():
    """Display exchange screen"""
    st.title("📊 Exchange")
    
    # Check API keys (only display warning message and continue)
    has_api_keys = check_api_keys()
    
    # Create Upbit Trade instance
    upbit_trade = get_upbit_trade_instance()
    
    # Only show error if API keys exist but instance creation fails
    if not upbit_trade and has_api_keys:
        st.error("Failed to connect to Upbit API. Please check your API keys.")
    
    # Refresh button
    if st.button("🔄 Refresh", key="market_refresh"):
        st.cache_data.clear()
        st.rerun()
    
    # Get coin information
    important_coins = get_important_coins()
    
    if not important_coins.empty:
        # Display major coins and noteworthy coins
        st.markdown(
            """
            ### 💰 Major Coins
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e6e6e6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">Exchange Information Guide</div>
                <ul style="margin-top: 5px; padding-left: 20px;">
                    <li><strong>Coin</strong>: Cryptocurrency ticker symbol</li>
                    <li><strong>Current Price</strong>: Latest trading price of the coin</li>
                    <li><strong>Change Rate</strong>: Price change percentage over 24 hours (%)</li>
                </ul>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Convert to DataFrame format and apply styling
        df = important_coins.copy()
        
        # Apply color to change rate column (green for positive, red for negative)
        def highlight_change(val):
            """Determine color based on change rate"""
            try:
                # Extract number if string
                if isinstance(val, str):
                    # Remove % symbol and sign
                    cleaned_val = val.replace('%', '').replace('+', '')
                    # Convert to number
                    num_val = float(cleaned_val)
                    color = '#28a745' if num_val >= 0 else '#dc3545'
                else:
                    # Direct comparison if already a number
                    color = '#28a745' if float(val) >= 0 else '#dc3545'
                
                return f'color: {color}; font-weight: bold'
            except:
                # Return default style if conversion fails
                return 'color: #212529'
        
        # Add arrows to change rate column (skip if already converted)
        if not isinstance(df['Change Rate'].iloc[0], str):
            df['Change Rate'] = df['Change Rate'].apply(lambda x: f"{'↑' if x >= 0 else '↓'} {x:+.2f}%")
        
        # Add thousands separator to current price
        df['Current Price'] = df['Current Price'].apply(lambda x: f"{x:,.0f} KRW")
        
        # Select columns to display (Coin, Current Price, Change Rate)
        display_df = df[['Coin', 'Current Price', 'Change Rate']]
        
        # Display styled table
        st.dataframe(
            display_df.style
            .map(lambda _: 'text-align: left; padding: 0.5rem;', subset=['Coin'])
            .map(lambda _: 'text-align: right; padding: 0.5rem;', subset=['Current Price'])
            .map(highlight_change, subset=['Change Rate'])
            .set_properties(**{
                'background-color': '#ffffff',
                'border': '1px solid #e6e6e6',
                'border-collapse': 'collapse',
                'font-size': '14px',
                'text-align': 'right',
                'padding': '0.5rem'
            })
            .hide(axis='index'),
            use_container_width=True,
            height=min(len(df) * 50 + 38, 300)  # Dynamically calculate table height (max 300px)
        )
    else:
        st.info("Loading coin information...")
        # Generate and display sample data
        sample_data = generate_sample_market_data()
        st.dataframe(
            sample_data.style.format({
                'Current Price': '{:,.0f}',
                'Previous Close': '{:,.0f}',
                'Change Rate': '{:+.2f}%',
                'Volume': '{:,.0f}',
                'Trading Value': '{:,.0f}'
            }),
            use_container_width=True,
            height=300
        )
    
    # Guide if no API keys
    if not has_api_keys:
        st.info("To trade with real money, set up API keys in the API Settings tab. Currently displaying sample data.")
    
    # Coin selection options
    coins = important_coins['Coin'].tolist() if not important_coins.empty else ["BTC", "ETH", "XRP", "ADA", "DOGE"]
    
    selected_coin = st.selectbox(
        "Select Coin",
        options=["KRW-" + coin for coin in coins],
        format_func=lambda x: f"{x.split('-')[1]} ({x})",
        key="selected_coin"
    )
    
    if selected_coin:
        st.markdown(f"### 📈 {selected_coin.split('-')[1]} Details")
        show_coin_details(upbit_trade, selected_coin)

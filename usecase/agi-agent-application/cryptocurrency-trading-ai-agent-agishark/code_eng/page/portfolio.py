import streamlit as st
import pyupbit
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import plotly.graph_objects as go
import sys
import numpy as np
sys.path.append("tools/upbit")
from UPBIT import Trade
from page.api_setting import check_api_keys, get_upbit_instance, get_upbit_trade_instance

def format_number(number: float) -> str:
    """Number formatting"""
    return f"{number:,.2f}"

@st.cache_data(ttl=300)  # Increased to 5 minute cache
def get_portfolio_info():
    try:
        upbit = get_upbit_instance()
        if not upbit:
            return None, pd.DataFrame()
            
        # Get asset holdings
        balances = upbit.get_balances()
        if not balances:
            return None, pd.DataFrame()
            
        # KRW balance
        krw_balance = float(next((b['balance'] for b in balances if b['currency'] == 'KRW'), 0))
        
        # Coin holdings
        coin_balances = []
        total_investment = 0
        total_current_value = 0
        
        for balance in balances:
            if balance['currency'] != 'KRW':
                ticker = f"KRW-{balance['currency']}"
                current_price = pyupbit.get_current_price(ticker)
                
                if current_price:
                    quantity = float(balance['balance'])
                    avg_buy_price = float(balance['avg_buy_price'])
                    current_value = quantity * current_price
                    investment = quantity * avg_buy_price
                    
                    coin_balances.append({
                        'Coin': balance['currency'],
                        'Quantity': quantity,
                        'Avg Buy Price': avg_buy_price,
                        'Current Price': current_price,
                        'Evaluation Amount': current_value,
                        'Investment Amount': investment,
                        'Profit/Loss': current_value - investment,
                        'Rate of Return': ((current_price - avg_buy_price) / avg_buy_price) * 100
                    })
                    
                    total_investment += investment
                    total_current_value += current_value
        
        # Portfolio summary
        portfolio_summary = {
            'Total Assets': total_current_value + krw_balance,
            'Total Investment': total_investment,
            'Total Profit/Loss': total_current_value - total_investment,
            'Total Return Rate': ((total_current_value - total_investment) / total_investment * 100) if total_investment > 0 else 0,
            'Cash Balance': krw_balance
        }
        
        # Create DataFrame
        df = pd.DataFrame(coin_balances)
        if not df.empty:
            df = df.sort_values('Evaluation Amount', ascending=False)
        
        return portfolio_summary, df
        
    except Exception as e:
        st.error(f"Error retrieving portfolio information: {str(e)}")
        return None, pd.DataFrame()

def generate_sample_portfolio_data():
    """Generate sample portfolio data (substitute for when API call fails)"""
    # Portfolio summary
    portfolio_summary = {
        'Total Assets': 10000000,
        'Total Investment': 8000000,
        'Total Profit/Loss': 2000000,
        'Total Return Rate': 25.0,
        'Cash Balance': 2000000,
        'Daily Return Rate': 1.5
    }
    
    # Coin holdings
    sample_coins = [
        {'Coin': 'BTC', 'Quantity': 0.01, 'Avg Buy Price': 48000000, 'Current Price': 50000000, 
         'Evaluation Amount': 500000, 'Investment Amount': 480000, 'Profit/Loss': 20000, 'Rate of Return': 4.17},
        {'Coin': 'ETH', 'Quantity': 0.5, 'Avg Buy Price': 2800000, 'Current Price': 3000000, 
         'Evaluation Amount': 1500000, 'Investment Amount': 1400000, 'Profit/Loss': 100000, 'Rate of Return': 7.14},
        {'Coin': 'XRP', 'Quantity': 10000, 'Avg Buy Price': 450, 'Current Price': 500, 
         'Evaluation Amount': 5000000, 'Investment Amount': 4500000, 'Profit/Loss': 500000, 'Rate of Return': 11.11},
        {'Coin': 'SOL', 'Quantity': 10, 'Avg Buy Price': 100000, 'Current Price': 120000, 
         'Evaluation Amount': 1200000, 'Investment Amount': 1000000, 'Profit/Loss': 200000, 'Rate of Return': 20.0},
    ]
    
    return portfolio_summary, pd.DataFrame(sample_coins)

def calculate_daily_profit_rate(_upbit_trade):
    """Calculate daily rate of return"""
    try:
        # Major coin list (check only major coins to improve speed instead of all coins)
        major_tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA"]
        
        # Compare 24-hour ago price information with current price
        today_total = 0
        yesterday_total = 0
        
        # Get all prices at once (one API call instead of multiple API calls)
        current_prices = pyupbit.get_current_price(major_tickers)
        
        for ticker in major_tickers:
            coin_name = ticker.split('-')[1]
            balance = _upbit_trade.get_balance(coin_name)
            
            if balance > 0:
                # Current price
                current_price = current_prices.get(ticker, 0)
                
                if current_price > 0:
                    # Price 24 hours ago
                    today_value = balance * current_price
                    
                    # Get previous day's closing price from daily candle data
                    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
                    if df is not None and not df.empty:
                        yesterday_price = df.iloc[0]['close']
                        yesterday_value = balance * yesterday_price
                        
                        today_total += today_value
                        yesterday_total += yesterday_value
        
        # Include cash
        krw_balance = _upbit_trade.get_balance("KRW")
        today_total += krw_balance
        yesterday_total += krw_balance
        
        # Calculate daily return rate
        if yesterday_total > 0:
            daily_profit_rate = ((today_total - yesterday_total) / yesterday_total) * 100
            return daily_profit_rate
        else:
            return 0
            
    except Exception as e:
        return 0  # Return default value on error (display as 0% in UI)

@st.cache_data(ttl=300)  # Increased to 5 minute cache
def get_portfolio_info_from_trade(_upbit_trade):
    """Get portfolio information using Trade class"""
    try:
        if not _upbit_trade:
            # Return sample data if no API keys or instance creation failed
            return generate_sample_portfolio_data()
        
        # Try to load real data if API key is set and instance was created
        try:
            # KRW balance
            krw_balance = _upbit_trade.get_balance("KRW")
            
            # Coin holdings
            coin_balances = []
            total_investment = 0
            total_current_value = 0
            
            # Try to query actual balance
            upbit_balances = _upbit_trade.upbit.get_balances()
            
            if upbit_balances and len(upbit_balances) > 0:
                # Get all KRW market tickers and current prices
                tickers = pyupbit.get_tickers(fiat="KRW")
                current_prices = pyupbit.get_current_price(tickers)
                
                # Process balance information
                for balance in upbit_balances:
                    if balance['currency'] == 'KRW':
                        continue  # Skip KRW
                    
                    coin_name = balance['currency']
                    ticker = f"KRW-{coin_name}"
                    
                    if ticker in tickers:
                        # Quantity
                        quantity = float(balance['balance'])
                        
                        if quantity > 0:
                            # Average purchase price
                            avg_buy_price = float(balance['avg_buy_price'])
                            
                            # Current price
                            current_price = current_prices.get(ticker, 0)
                            if current_price <= 0:
                                current_price = _upbit_trade.get_current_price(ticker) or 0
                            
                            # Calculate evaluation amount and profit/loss
                            current_value = quantity * current_price
                            investment = quantity * avg_buy_price
                            
                            # Calculate return rate
                            profit_rate = 0
                            if avg_buy_price > 0:
                                profit_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100
                            
                            # Add coin information
                            coin_balances.append({
                                'Coin': coin_name,
                                'Quantity': quantity,
                                'Avg Buy Price': avg_buy_price,
                                'Current Price': current_price,
                                'Evaluation Amount': current_value,
                                'Investment Amount': investment,
                                'Profit/Loss': current_value - investment,
                                'Rate of Return': profit_rate
                            })
                            
                            # Update totals
                            total_investment += investment
                            total_current_value += current_value
            
            # Continue only if there are actual coins held
            if coin_balances:
                # Calculate daily return rate
                daily_profit_rate = calculate_daily_profit_rate(_upbit_trade)
                
                # Portfolio summary information
                portfolio_summary = {
                    'Total Assets': total_current_value + krw_balance,
                    'Total Investment': total_investment,
                    'Total Profit/Loss': total_current_value - total_investment,
                    'Total Return Rate': ((total_current_value - total_investment) / total_investment * 100) if total_investment > 0 else 0,
                    'Cash Balance': krw_balance,
                    'Daily Return Rate': daily_profit_rate,
                    'Coin Evaluation Amount': total_current_value  # Add coin evaluation amount
                }
                
                # Create DataFrame
                df = pd.DataFrame(coin_balances)
                if not df.empty:
                    df = df.sort_values('Evaluation Amount', ascending=False)
                
                # Return actual data
                return portfolio_summary, df
            
            # Return sample data if no coins are held
            st.info("There are no coins in your Upbit account. Displaying sample data.")
            return generate_sample_portfolio_data()
            
        except Exception as e:
            # Substitute sample data if error occurs during API call
            st.error(f"Error retrieving portfolio information from Upbit API: {str(e)}")
            return generate_sample_portfolio_data()
        
    except Exception as e:
        st.error(f"Portfolio information retrieval error: {str(e)}")
        # Return sample data on error
        return generate_sample_portfolio_data()

def show_portfolio():
    """Display portfolio"""
    st.title("📂 Portfolio")
    
    # Check API keys
    has_api_keys = check_api_keys()
    
    # Create Upbit Trade instance
    upbit_trade = get_upbit_trade_instance()
    
    # Refresh button
    if st.button("🔄 Refresh", key="portfolio_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Get portfolio information
    portfolio_summary, coin_balances = get_portfolio_info_from_trade(upbit_trade)
    
    # Add portfolio summary information explanation
    with st.expander("Portfolio Metrics Explanation"):
        portfolio_summary_html = """
        <div class="data-container">
            <ul style="margin-top: 5px; padding-left: 20px;">
                <li><strong>Total Assets</strong>: Total assets including cash and coin evaluation amount</li>
                <li><strong>Total Profit/Loss</strong>: Current profit/loss amount from coin investments</li>
                <li><strong>Daily Return Rate</strong>: Portfolio return rate over 24 hours</li>
                <li><strong>Cash Balance</strong>: Available cash balance for investment</li>
                <li><strong>Coin Evaluation Amount</strong>: Current value of all coins held</li>
                <li><strong>Total Investment</strong>: Total amount used for coin purchases</li>
            </ul>
        </div>
        """
    st.write(portfolio_summary_html, unsafe_allow_html=True)
    
    if not has_api_keys:
        st.info("Sample data is currently being displayed. To view actual data, set up API keys in the API Settings tab.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Total assets
        total_assets = portfolio_summary['Total Assets']
        formatted_total_assets = f"{total_assets:,.0f}"
        st.metric("Total Assets", f"{formatted_total_assets} KRW")
    
    with col2:
        # Total profit/loss and return rate
        total_profit = portfolio_summary['Total Profit/Loss']
        total_profit_rate = portfolio_summary['Total Return Rate']
        
        formatted_total_profit = f"{total_profit:,.0f}"
        profit_delta = f"{total_profit_rate:+.2f}%"
        
        st.metric("Total Profit/Loss", f"{formatted_total_profit} KRW", 
                 delta=profit_delta, 
                 delta_color="normal")
    
    with col3:
        # Display daily return rate
        daily_profit_rate = portfolio_summary.get('Daily Return Rate', 0)
        daily_profit = f"{daily_profit_rate:+.2f}%" if daily_profit_rate != 0 else "0.00%"
        st.metric("Daily Return Rate", daily_profit,
                 delta_color="normal")
    
    # Additional metrics in second row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Cash balance
        cash = portfolio_summary['Cash Balance']
        formatted_cash = f"{cash:,.0f}"
        st.metric("Cash Balance", f"{formatted_cash} KRW")
    
    with col2:
        # Coin evaluation amount
        coin_value = portfolio_summary.get('Coin Evaluation Amount', 0)
        formatted_coin_value = f"{coin_value:,.0f}"
        st.metric("Coin Evaluation Amount", f"{formatted_coin_value} KRW")
    
    with col3:
        # Total investment amount
        total_investment = portfolio_summary['Total Investment']
        formatted_investment = f"{total_investment:,.0f}"
        st.metric("Total Investment", f"{formatted_investment} KRW")
    
    # Display coin holdings by coin
    st.markdown("### 💰 Coin Holdings")
    
    # Pagination handling
    page_size = 5  # Number of coins to display per page
    if 'portfolio_page' not in st.session_state:
        st.session_state.portfolio_page = 0
    
    total_pages = (len(coin_balances) + page_size - 1) // page_size if not coin_balances.empty else 1
    start_idx = st.session_state.portfolio_page * page_size
    end_idx = min(start_idx + page_size, len(coin_balances))
    
    # Page selection
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            if st.button("Previous", key="prev_page", disabled=st.session_state.portfolio_page <= 0):
                st.session_state.portfolio_page -= 1
                st.rerun()
        with col2:
            pagination_info = f"<div style='text-align: center'>Page {st.session_state.portfolio_page + 1}/{total_pages}</div>"
            st.write(pagination_info, unsafe_allow_html=True)
        with col3:
            if st.button("Next", key="next_page", disabled=st.session_state.portfolio_page >= total_pages - 1):
                st.session_state.portfolio_page += 1
                st.rerun()
    
    # Display current page's coin list
    if not coin_balances.empty:
        # Show only data for current page
        page_data = coin_balances.iloc[start_idx:end_idx]
        
        # Convert to DataFrame for styling
        df = page_data.copy()
        
        # Apply color based on return rate (positive is green, negative is red)
        def style_change(val):
            try:
                # Extract number if it's a string
                if isinstance(val, str):
                    # Remove arrows and spaces
                    num_str = val.replace('↑', '').replace('↓', '').strip()
                    # Remove % and KRW symbols
                    num_str = num_str.replace('%', '').replace('KRW', '')
                    # Remove + sign
                    num_str = num_str.replace('+', '')
                    # Remove commas
                    num_str = num_str.replace(',', '')
                    # Convert to number
                    num_val = float(num_str)
                    # Determine color
                    color = '#28a745' if num_val >= 0 else '#dc3545'
                else:
                    # Direct comparison for number types
                    color = '#28a745' if float(val) >= 0 else '#dc3545'
                
                return f'color: {color}; font-weight: bold'
            except:
                # Return default for values that can't be converted
                return 'color: #212529'
        
        # Add arrows to return rate column (skip if already converted)
        if not isinstance(df['Rate of Return'].iloc[0], str):
            df['Return Rate Display'] = df['Rate of Return'].apply(lambda x: f"{'↑' if x >= 0 else '↓'} {x:+.2f}%")
        
        # Add color and sign to profit/loss
        if 'Profit/Loss Display' not in df.columns:
            df['Profit/Loss Display'] = df['Profit/Loss'].apply(lambda x: f"{'+' if x >= 0 else ''}{x:,.0f} KRW")
        
        # Number formatting
        df['Current Price Display'] = df['Current Price'].apply(lambda x: f"{x:,.0f} KRW")
        df['Avg Buy Price Display'] = df['Avg Buy Price'].apply(lambda x: f"{x:,.0f} KRW")
        df['Evaluation Amount Display'] = df['Evaluation Amount'].apply(lambda x: f"{x:,.0f} KRW")
        df['Investment Amount Display'] = df['Investment Amount'].apply(lambda x: f"{x:,.0f} KRW")
        
        # Select columns to display
        display_columns = ['Coin', 'Quantity', 'Current Price Display', 'Avg Buy Price Display', 'Evaluation Amount Display', 'Profit/Loss Display', 'Return Rate Display']
        display_df = df[display_columns].rename(columns={
            'Current Price Display': 'Current Price',
            'Avg Buy Price Display': 'Avg Buy Price',
            'Evaluation Amount Display': 'Evaluation Amount',
            'Profit/Loss Display': 'Profit/Loss',
            'Return Rate Display': 'Return Rate'
        })
        
        # Display styled table
        st.dataframe(
            display_df.style
            .map(lambda _: 'text-align: left; font-weight: bold; padding: 0.5rem;', subset=['Coin'])
            .map(lambda _: 'text-align: right; padding: 0.5rem;', subset=['Quantity', 'Current Price', 'Avg Buy Price', 'Evaluation Amount'])
            .map(style_change, subset=['Return Rate'])
            .map(lambda x: style_change(x), subset=['Profit/Loss'])
            .set_properties(**{
                'background-color': '#ffffff',
                'border': '1px solid #e6e6e6',
                'border-collapse': 'collapse',
                'font-size': '14px',
                'padding': '0.5rem'
            })
            .hide(axis='index'),
            use_container_width=True,
            height=min(len(df) * 55 + 38, 350)  # Dynamically calculate table height (max 350px)
        )
        
        # Show detailed information (provided in collapsible section if needed)
        with st.expander("View Detailed Coin Information"):
            for idx, row in page_data.iterrows():
                # Display coin details in card format
                profit_rate = row['Rate of Return']
                profit_color = "#28a745" if profit_rate >= 0 else "#dc3545"
                profit_sign = "+" if profit_rate >= 0 else ""
                
                # Calculate progress bar value (bar length based on return rate)
                progress_value = min(max((profit_rate + 20) * 2, 0), 100) / 100.0
                
                st.markdown(f"### {row['Coin']} Details")
                
                # Display key information in 2-column grid
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Quantity", f"{row['Quantity']:.8f}")
                    st.metric("Current Price", f"{row['Current Price']:,.0f} KRW")
                    st.metric("Avg Buy Price", f"{row['Avg Buy Price']:,.0f} KRW")
                with col2:
                    st.metric("Evaluation Amount", f"{row['Evaluation Amount']:,.0f} KRW")
                    st.metric("Investment Amount", f"{row['Investment Amount']:,.0f} KRW")
                    st.metric("Profit/Loss", f"{row['Profit/Loss']:,.0f} KRW", 
                             delta=f"{profit_sign}{profit_rate:.2f}%",
                             delta_color="normal")
                
                st.markdown("---")
    else:
        st.info("You don't have any coins.")

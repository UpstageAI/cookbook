import streamlit as st
import pyupbit
import pandas as pd
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import sys
sys.path.append("tools/upbit")
from UPBIT import Trade
from page.api_setting import check_api_keys, get_upbit_trade_instance
import requests
import hashlib
import jwt
import uuid as uuid_module
from urllib.parse import urlencode
import time

# Style settings
st.markdown("""
    <style>
    .order-card {
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .order-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .buy-order {
        background-color: rgba(255, 240, 240, 0.3);
        border-left: 4px solid #ff4b4b;
    }
    .sell-order {
        background-color: rgba(240, 240, 255, 0.3);
        border-left: 4px solid #4b4bff;
    }
    .transaction-card {
        /* background-color: rgba(240, 255, 240, 0.3); */ /* Commented out as it's set directly in Python */
        border-left: 4px solid #4bff4b;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 25px;
        border: 1px solid #ddd;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    /* Even card CSS selector removed (handled in Python) */
    /* .transaction-card:nth-child(even) { ... } */
    .status-done {
        color: #4bff4b;
        font-weight: bold;
        background-color: rgba(75, 255, 75, 0.1);
        padding: 5px 10px;
        border-radius: 20px;
    }
    .status-wait {
        color: #ffbb00;
        font-weight: bold;
        background-color: rgba(255, 187, 0, 0.1);
        padding: 5px 10px;
        border-radius: 20px;
    }
    .status-cancel {
        color: #aaaaaa;
        font-weight: bold;
        background-color: rgba(170, 170, 170, 0.1);
        padding: 5px 10px;
        border-radius: 20px;
    }
    .coin-name {
        font-weight: bold;
        font-size: 1.2rem;
        margin: 0;
    }
    .price-value {
        font-weight: bold;
        color: #333;
    }
    .info-label {
        color: #666;
        font-size: 0.9rem;
    }
    .info-divider {
        margin: 10px 0;
        border-top: 1px solid #eee;
    }
    </style>
""", unsafe_allow_html=True)

def format_number(number: float) -> str:
    """Format number with thousand separators"""
    return f"{number:,.0f}"

def format_date(date_string: str) -> str:
    """Format date string"""
    if not date_string:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
        
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f%z")
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        try:
            dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            try:
                dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M")
            except:
                # Return original if date format is changed or incorrect
                return date_string

@st.cache_data(ttl=300)
def get_user_orders(_upbit_trade, max_pages=5) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Retrieve user's order history and transaction history (multiple pages, restructured code)"""
    orders_columns = ["Order Time", "Coin", "Type", "Order Method", "Order Price", "Order Amount", "Executed Amount", "Unfilled Amount", "Total Order Value", "Status", "Order ID"]
    transactions_columns = ["Execution Time", "Coin", "Type", "Trade Volume", "Trade Price", "Trade Amount", "Fee", "Order Time", "Order ID"]
    all_api_orders = []

    if not _upbit_trade or not _upbit_trade.is_valid:
        st.error("Failed to create Upbit instance or authenticate API keys.")
        return pd.DataFrame(columns=orders_columns), pd.DataFrame(columns=transactions_columns)

    # 1. Multiple page API calls
    try:
        for page_num in range(1, max_pages + 1):
            page_orders = _upbit_trade.get_order_history(page=page_num, limit=100)

            if isinstance(page_orders, list):
                if not page_orders:
                    break
                all_api_orders.extend(page_orders)
            else:
                break
    except Exception as api_call_error:
        st.error(f"Error during API call: {str(api_call_error)}")
        return pd.DataFrame(columns=orders_columns), pd.DataFrame(columns=transactions_columns)

    # 2. Process collected data
    processed_orders = []
    processed_transactions = []
    error_count = 0

    if not all_api_orders:
        st.warning("Could not collect valid order data from API.")
    else:
        for i, order in enumerate(all_api_orders):
            try:
                if isinstance(order, dict) and 'error' in order:
                    error_count += 1
                    continue

                market = order.get('market', ''); side = order.get('side', ''); state = order.get('state', '')
                if not market or not side or not state:
                    continue

                ord_type = order.get('ord_type', ''); created_at = order.get('created_at', ''); uuid = order.get('uuid', '')
                order_price_str = order.get('price'); order_price = float(order_price_str) if order_price_str is not None else 0.0
                volume = float(order.get('volume', 0) or 0); executed_volume = float(order.get('executed_volume', 0) or 0)
                remaining_volume = volume - executed_volume; paid_fee = float(order.get('paid_fee', 0) or 0)

                coin = market.replace("KRW-", ""); order_type_str = "Buy" if side == 'bid' else "Sell"
                order_state_str = "Completed" if state == 'done' else "Waiting" if state == 'wait' else "Canceled"
                order_datetime_str = format_date(created_at)

                order_info = {
                    "Order Time": order_datetime_str, "Coin": coin, "Type": order_type_str, "Order Method": ord_type,
                    "Order Price": order_price, "Order Amount": volume, "Executed Amount": executed_volume,
                    "Unfilled Amount": remaining_volume, "Total Order Value": order_price * volume if order_price else 0.0,
                    "Status": order_state_str, "Order ID": uuid
                }
                processed_orders.append(order_info)

                if executed_volume > 0:
                    avg_price_str = order.get('avg_price')
                    trade_price = 0.0
                    if avg_price_str:
                        try:
                            trade_price = float(avg_price_str)
                        except (ValueError, TypeError):
                            trade_price = 0.0
                    if trade_price == 0.0 and order_price > 0: trade_price = order_price
                    if trade_price <= 0: continue
                    trade_volume = executed_volume
                    trade_amount = trade_price * trade_volume

                    transaction_info = {
                        "Execution Time": order_datetime_str,
                        "Coin": coin,
                        "Type": order_type_str,
                        "Trade Volume": trade_volume,
                        "Trade Price": trade_price,
                        "Trade Amount": trade_amount,
                        "Fee": paid_fee,
                        "Order Time": order_datetime_str,
                        "Order ID": uuid
                    }
                    processed_transactions.append(transaction_info)

            except Exception as process_error:
                error_count += 1
                continue

    # 3. Create final DataFrames and return
    orders_df = pd.DataFrame(columns=orders_columns)
    transactions_df = pd.DataFrame(columns=transactions_columns)

    if processed_orders:
        unique_orders = []
        seen_uuids_ord = set()
        for order in processed_orders:
             uuid = order.get("Order ID", "")
             if uuid not in seen_uuids_ord:
                 seen_uuids_ord.add(uuid)
                 unique_orders.append(order)
        orders_df = pd.DataFrame(unique_orders, columns=orders_columns)
        orders_df = orders_df.sort_values('Order Time', ascending=False)
        st.success(f"Loaded {len(orders_df)} order records (all statuses).")

    if processed_transactions:
        unique_transactions = []
        seen_uuids_tx = set()
        for tx in processed_transactions:
             uuid = tx.get("Order ID", "")
             if uuid not in seen_uuids_tx:
                 seen_uuids_tx.add(uuid)
                 unique_transactions.append(tx)
        transactions_df = pd.DataFrame(unique_transactions, columns=transactions_columns)
        transactions_df = transactions_df.sort_values('Execution Time', ascending=False)
        st.success(f"Loaded {len(transactions_df)} completed transaction records.")

    if orders_df.empty and transactions_df.empty:
        st.warning("No order/transaction records found.")

    return orders_df, transactions_df

def generate_sample_order_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate sample order and transaction data"""
    st.info("Displaying sample order history as there is no API connection. To view actual transaction history, set up API keys.")
    
    # Generate sample data
    today = datetime.now()
    sample_coins = ["BTC", "ETH", "XRP", "DOGE", "ADA", "SOL"]
    
    # Order status types
    order_states = ["Completed", "Waiting", "Canceled"]
    state_weights = [0.6, 0.3, 0.1]  # Ratio by status
    
    sample_orders = []
    order_uuid = 1000  # Starting value for sample order numbers
    
    # Generate more diverse transaction history (various times and prices)
    for i in range(40):  # Increased to 40
        # Wider time range (last 15 days)
        days_ago = i // 3
        hours_ago = (i % 24)
        minutes_ago = i * 5 % 60
        
        order_date = today - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        date_str = order_date.strftime("%Y-%m-%d %H:%M")
        
        # Select various coins
        coin_idx = (i + hash(date_str)) % len(sample_coins)
        coin = sample_coins[coin_idx]
        
        # Set prices by coin type (add volatility)
        import random
        price_variation = random.uniform(0.95, 1.05)  # 5% volatility
        
        if coin == "BTC":
            base_price = 50000000
            price = int(base_price * price_variation)
            volume = round(0.001 + (i * 0.0001), 8)
        elif coin == "ETH":
            base_price = 3000000
            price = int(base_price * price_variation)
            volume = round(0.01 + (i * 0.001), 8)
        elif coin == "SOL":
            base_price = 150000
            price = int(base_price * price_variation)
            volume = round(0.1 + (i * 0.01), 8)
        else:
            base_price = 500 + (i * 10)
            price = int(base_price * price_variation)
            volume = round(10 + i, 8)
            
        # Order type (Buy/Sell)
        order_type = "Buy" if i % 2 == 0 else "Sell"
        
        # Order status (selected according to weights)
        import numpy as np
        state = np.random.choice(order_states, p=state_weights)
        
        # Calculate executed amount (varies by status)
        if state == "Completed":
            executed_volume = volume
            remaining_volume = 0
        elif state == "Waiting":
            executed_volume = 0
            remaining_volume = volume
        else:  # Canceled
            if random.random() < 0.3:  # 30% chance of partial execution
                executed_volume = round(volume * random.uniform(0.1, 0.5), 8)
                remaining_volume = round(volume - executed_volume, 8)
            else:  # 70% chance of unfilled cancellation
                executed_volume = 0
                remaining_volume = volume
        
        # Order amount and fee
        amount = price * volume
        fee = amount * 0.0005
        
        # Generate order ID (similar to actual IDs)
        order_id = f"sample-{uuid_module.uuid4().hex[:12]}"
        
        sample_orders.append({
            "Order Time": date_str,
            "Coin": coin,
            "Type": order_type,
            "Order Method": ord_type,
            "Order Price": price,
            "Order Amount": volume,
            "Executed Amount": executed_volume,
            "Unfilled Amount": remaining_volume,
            "Total Order Value": amount,
            "Status": state,
            "Order ID": order_id
        })
    
    # Order history dataframe
    orders_df = pd.DataFrame(sample_orders)
    
    # Transaction history includes only completed orders
    transactions_df = orders_df[orders_df["Status"] == "Completed"].copy()
    
    # Sort by latest
    orders_df = orders_df.sort_values('Order Time', ascending=False)
    transactions_df = transactions_df.sort_values('Order Time', ascending=False)
    
    return orders_df, transactions_df

def show_trade_history():
    """Display transaction history screen (including partially executed canceled orders)"""
    st.title("📝 Transaction History")
    
    # Check API keys
    has_api_keys = check_api_keys()
    
    # Create Upbit Trade instance
    upbit_trade = get_upbit_trade_instance()
    
    # Refresh button and display options
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Refresh", key="history_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        display_mode = st.radio(
            "Display Format",
            ["Table", "Cards"],
            horizontal=True,
            key="display_mode"
        )
    
    with col3:
        if upbit_trade and has_api_keys:
            st.success("API is connected.")
        else:
            st.warning("API key setup required. Enter keys in the API Settings tab.")
    
    if not has_api_keys:
        st.info("To view actual transaction history, set up API keys in the API Settings tab.")
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <h3>How to Set Up API Keys</h3>
            <ol>
                <li>Log in to the Upbit website.</li>
                <li>Go to 'My Account' > 'Open API Management' in the upper right.</li>
                <li>Generate API keys and activate order functionality.</li>
                <li>Copy the issued Access Key and Secret Key.</li>
                <li>Register the keys in the 'API Settings' tab of this app.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get order history (all statuses) and transaction history (executed amount > 0)
    with st.spinner("Loading actual transaction history..."):
        orders_df, transactions_df = get_user_orders(upbit_trade)

    # Header change: Display transaction history
    st.subheader("💰 Transaction History")
    st.markdown("These are the actually executed transactions.")

    # Change data source to transactions_df
    if transactions_df.empty:
        st.warning("No executed transactions found.")
        return

    # Filtering options (target: transactions_df, status filter removed)
    st.markdown("#### 🔍 Filter")
    col1, col2 = st.columns(2) # Restored to 2 columns

    with col1:
        # Coin filter (based on transactions_df)
        coin_options = ["All"]
        if not transactions_df.empty and "Coin" in transactions_df.columns:
            coin_options.extend(sorted(transactions_df["Coin"].unique()))
        # Key recovery: order_coin_filter -> tx_coin_filter
        tx_coin = st.selectbox("Coin", options=coin_options, key="tx_coin_filter")

    with col2:
        # Type filter (Buy/Sell) (based on transactions_df)
        type_options = ["All"]
        if not transactions_df.empty and "Type" in transactions_df.columns:
            type_options.extend(sorted(transactions_df["Type"].unique()))
        # Key recovery: order_type_filter -> tx_type_filter
        tx_type = st.selectbox("Type", options=type_options, key="tx_type_filter")

    # Apply filtering (target: transactions_df)
    filtered_tx = transactions_df.copy()
    if tx_coin != "All" and "Coin" in filtered_tx.columns:
        filtered_tx = filtered_tx[filtered_tx["Coin"] == tx_coin]
    if tx_type != "All" and "Type" in filtered_tx.columns:
        filtered_tx = filtered_tx[filtered_tx["Type"] == tx_type]

    if filtered_tx.empty:
        st.info("No transaction history matching the filter criteria.")
    else:
        # Pagination (variable name recovery: orders -> tx)
        tx_per_page = 10 if display_mode == "Table" else 5
        if 'tx_page' not in st.session_state: # Key recovery
            st.session_state.tx_page = 0
        total_pages = max(1, (len(filtered_tx) + tx_per_page - 1) // tx_per_page)
        if st.session_state.tx_page >= total_pages:
            st.session_state.tx_page = 0
        start_idx = st.session_state.tx_page * tx_per_page
        end_idx = min(start_idx + tx_per_page, len(filtered_tx))
        page_tx = filtered_tx.iloc[start_idx:end_idx]

        if display_mode == "Table":
            # Restore table columns (focused on transaction info)
            display_columns = ["Execution Time", "Coin", "Type", "Trade Volume", "Trade Price", "Trade Amount", "Fee", "Order Time"]
            formatted_tx = page_tx.copy()

            # Data formatting (based on transaction info)
            if "Trade Price" in formatted_tx.columns: formatted_tx["Trade Price"] = formatted_tx["Trade Price"].apply(lambda x: f"{x:,.0f} KRW")
            if "Trade Amount" in formatted_tx.columns: formatted_tx["Trade Amount"] = formatted_tx["Trade Amount"].apply(lambda x: f"{x:,.0f} KRW")
            if "Fee" in formatted_tx.columns: formatted_tx["Fee"] = formatted_tx["Fee"].apply(lambda x: f"{x:,.4f} KRW")
            if "Trade Volume" in formatted_tx.columns: formatted_tx["Trade Volume"] = formatted_tx["Trade Volume"].apply(lambda x: f"{x:.8f}")

            # Styling (type)
            def highlight_tx_type(s):
                if s == "Buy": return 'background-color: rgba(255, 0, 0, 0.1); color: darkred; font-weight: bold'
                else: return 'background-color: rgba(0, 0, 255, 0.1); color: darkblue; font-weight: bold'

            st.dataframe(
                formatted_tx[display_columns].style
                .applymap(highlight_tx_type, subset=["Type"]),
                use_container_width=True,
                height=400
            )

        else: # Card format
            st.markdown('<div class="trade-cards-container">', unsafe_allow_html=True)
            for idx, (_, tx) in enumerate(page_tx.iterrows()):
                # Determine text and color based on type
                if tx["Type"] == "Buy":
                    tx_type_text = "Bought"
                    tx_type_color = "#ff4b4b" # Red
                else:
                    tx_type_text = "Sold"
                    tx_type_color = "#4b4bff" # Blue

                # Determine background color using index (idx) for even/odd
                if idx % 2 == 0: # Even index (first, third card etc.)
                    card_bg_color = "rgba(240, 255, 240, 0.3)" # Light green
                else: # Odd index (second, fourth card etc.)
                    card_bg_color = "#f8f9fa" # Light gray

                # Use transaction-card class, status always considered as completed
                tx_card = f"""
                <div class="transaction-card" style="background-color: {card_bg_color}; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; font-size: 1.2rem; font-weight: bold;">
                            {tx['Coin']} <span style='color: {tx_type_color};'>{tx_type_text}</span>
                        </h4>
                        <span class="status-done" style="padding: 5px 10px; border-radius: 20px;">Completed</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <p style="margin: 5px 0;"><strong>📅 Execution Time:</strong> {tx['Execution Time']}</p>
                            <p style="margin: 5px 0;"><strong>💰 Trade Price:</strong> {tx['Trade Price']:,.0f} KRW</p>
                            <p style="margin: 5px 0;"><strong>🔢 Trade Volume:</strong> {tx['Trade Volume']:.8f}</p>
                        </div>
                        <div>
                            <p style="margin: 5px 0;"><strong>💵 Trade Amount:</strong> {tx['Trade Amount']:,.0f} KRW</p>
                            <p style="margin: 5px 0;"><strong>🧾 Fee:</strong> {tx['Fee']:.4f} KRW</p>
                        </div>
                    </div>
                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                        <p style="font-size: 0.8em; color: #666; margin: 5px 0;"><strong>🔑 Order ID:</strong> {tx['Order ID']}</p>
                    </div>
                </div>
                """
                st.markdown(tx_card, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Pagination controls (key recovery: tx_page)
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if st.button("◀️ Previous", key="prev_tx", disabled=st.session_state.tx_page <= 0):
                    st.session_state.tx_page -= 1
                    st.rerun()
            with col2:
                paging_info = f"<div style='text-align:center'>Page {st.session_state.tx_page + 1} / {total_pages} (Total {len(filtered_tx)} transactions)</div>"
                st.markdown(paging_info, unsafe_allow_html=True)
            with col3:
                if st.button("Next ▶️", key="next_tx", disabled=st.session_state.tx_page >= total_pages - 1):
                    st.session_state.tx_page += 1
                    st.rerun()

    # Restore transaction history statistics section
    with st.expander("📊 Transaction History Statistics"):
         if not filtered_tx.empty:
             # Recover statistics calculation and display logic (based on transactions_df)
             coin_totals = filtered_tx.groupby("Coin")["Trade Amount"].sum().reset_index()
             st.markdown("##### Total Trading Amount by Coin")
             for _, row in coin_totals.iterrows():
                 st.markdown(f"**{row['Coin']}**: {row['Trade Amount']:.0f} KRW")

             buy_count = len(filtered_tx[filtered_tx["Type"] == "Buy"])
             sell_count = len(filtered_tx[filtered_tx["Type"] == "Sell"])
             if (buy_count + sell_count) > 0:
                 st.markdown("##### Buy/Sell Ratio")
                 st.markdown(f"Buy: {buy_count} transactions ({buy_count/(buy_count+sell_count)*100:.1f}%)")
                 st.markdown(f"Sell: {sell_count} transactions ({sell_count/(buy_count+sell_count)*100:.1f}%)")
             else:
                 st.markdown("##### Buy/Sell Ratio: No information")

             total_fee = filtered_tx["Fee"].sum()
             st.markdown(f"##### Total Fees Paid: {total_fee:.4f}")
         else:
             st.info("No statistics information to display.")

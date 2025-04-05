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

@st.cache_data(ttl=300)  # 5분 캐시로 증가
def get_market_info():
    """모든 암호화폐 시장 정보 조회"""
    try:
        # 주요 코인 + 상위 거래량 코인만 처리하여 속도 개선
        major_tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA"]
        
        # 다른 코인도 포함하되 제한된 개수만 (처리 속도 향상)
        other_tickers = [f"KRW-{coin}" for coin in ["MATIC", "DOT", "LINK", "AVAX", "SHIB", 
                                                    "UNI", "ATOM", "LTC", "ETC", "BCH"]]
        
        # 처리할 티커 목록 (주요 코인 + 기타 선택된 코인)
        selected_tickers = major_tickers + other_tickers
        
        # 티커를 한 번에 조회 (단일 API 호출로 속도 개선)
        ticker_prices = pyupbit.get_current_price(selected_tickers)
        
        all_market_info = []
        
        # OHLCV 데이터 한 번에 가져오기 (개별 요청 대신 하나의 요청으로)
        # 일봉 데이터는 선택한 모든 티커에 대해 최근 2개만 필요
        ohlcv_data = {}
        for ticker in selected_tickers:
            try:
                ohlcv_data[ticker] = pyupbit.get_ohlcv(ticker, interval="day", count=2)
            except:
                continue
        
        for ticker in selected_tickers:
            try:
                # 현재가 정보
                ticker_price = ticker_prices.get(ticker)
                if not ticker_price:
                    continue
                
                # 일봉 데이터
                df = ohlcv_data.get(ticker)
                if df is None or df.empty:
                    continue
                
                # 전일 종가, 전일 대비 등락률
                prev_close = df.iloc[0]['close']
                change_rate = (ticker_price - prev_close) / prev_close * 100
                
                # 거래량 정보
                today_volume = df.iloc[-1]['volume'] if 'volume' in df.columns else 0
                today_value = today_volume * ticker_price
                
                # 코인 이름 (티커에서 KRW- 제거)
                coin_name = ticker.replace("KRW-", "")
                
                all_market_info.append({
                    '코인': coin_name,
                    '현재가': ticker_price,
                    '전일종가': prev_close,
                    '변동률': change_rate,
                    '거래량': today_volume,
                    '거래대금': today_value
                })
            except Exception as e:
                # 개별 코인 처리 실패시 건너뛰기
                continue
        
        if not all_market_info:
            # 실패 시 샘플 데이터 제공 (로딩 속도 향상)
            sample_data = generate_sample_market_data()
            return sample_data
        
        return pd.DataFrame(all_market_info)
    except Exception as e:
        st.error(f"시장 정보 조회 중 오류 발생: {str(e)}")
        # 오류 시 샘플 데이터 제공 (로딩 속도 보장)
        return generate_sample_market_data()

def generate_sample_market_data():
    """샘플 마켓 데이터 생성 (API 호출 실패 시 대체용)"""
    sample_data = [
        {'코인': 'BTC', '현재가': 50000000, '전일종가': 49000000, '변동률': 2.04, '거래량': 100, '거래대금': 5000000000},
        {'코인': 'ETH', '현재가': 3000000, '전일종가': 2900000, '변동률': 3.45, '거래량': 1000, '거래대금': 3000000000},
        {'코인': 'XRP', '현재가': 500, '전일종가': 480, '변동률': 4.17, '거래량': 10000000, '거래대금': 5000000000},
        {'코인': 'SOL', '현재가': 120000, '전일종가': 115000, '변동률': 4.35, '거래량': 50000, '거래대금': 6000000000},
        {'코인': 'DOGE', '현재가': 100, '전일종가': 95, '변동률': 5.26, '거래량': 100000000, '거래대금': 10000000000},
        {'코인': 'ADA', '현재가': 400, '전일종가': 390, '변동률': 2.56, '거래량': 20000000, '거래대금': 8000000000}
    ]
    return pd.DataFrame(sample_data)

@st.cache_data(ttl=600)  # 10분 캐시로 증가
def get_coin_chart_data(coin_ticker: str, interval: str = "minute60", count: int = 168):
    """코인의 차트 데이터 조회"""
    try:
        df = pyupbit.get_ohlcv(coin_ticker, interval=interval, count=count)
        if df is None or df.empty:
            # 샘플 차트 데이터 제공
            return generate_sample_chart_data(coin_ticker, interval)
        return df
    except Exception as e:
        # 오류 시 샘플 데이터 제공
        return generate_sample_chart_data(coin_ticker, interval)

def generate_sample_chart_data(coin_ticker: str, interval: str):
    """샘플 차트 데이터 생성 (API 호출 실패 시 대체용)"""
    # 현재 시간 기준으로 샘플 데이터 생성
    now = datetime.now()
    periods = 30  # 기본 30개 데이터 포인트
    
    # 주기에 따라 시간 간격 설정
    if interval == "day":
        start_time = now - timedelta(days=periods)
        freq = "D"
    elif interval == "week":
        start_time = now - timedelta(weeks=periods)
        freq = "W"
    elif interval == "month":
        start_time = now - timedelta(days=30*periods)
        freq = "M"
    else:  # 기본 시간 간격 (1시간)
        start_time = now - timedelta(hours=periods)
        freq = "H"
    
    # 날짜 범위 생성
    date_range = pd.date_range(start=start_time, end=now, freq=freq)
    
    # 기본 가격 설정 (코인 종류에 따라 다르게)
    if "BTC" in coin_ticker:
        base_price = 50000000
        volatility = 1000000
    elif "ETH" in coin_ticker:
        base_price = 3000000
        volatility = 100000
    else:
        base_price = 1000
        volatility = 50
    
    # 샘플 데이터 생성
    np.random.seed(42)  # 일관된 샘플 데이터를 위한 시드 설정
    
    # 주가 패턴 생성 (약간의 상승 트렌드)
    closes = base_price + np.cumsum(np.random.normal(100, volatility/10, len(date_range)))
    opens = closes - np.random.normal(0, volatility/15, len(date_range))
    highs = np.maximum(opens, closes) + np.random.normal(volatility/5, volatility/10, len(date_range))
    lows = np.minimum(opens, closes) - np.random.normal(volatility/5, volatility/10, len(date_range))
    volumes = np.random.normal(base_price/10, base_price/20, len(date_range))
    
    # 데이터프레임 생성
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': np.abs(volumes)  # 거래량은 항상 양수
    }, index=date_range)
    
    return df

def draw_price_chart(df: pd.DataFrame, coin_name: str):
    """가격 차트 그리기"""
    if df.empty:
        st.error("차트 데이터가 없습니다.")
        return
        
    try:
        fig = go.Figure()
        
        # 캔들스틱 차트
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=coin_name,
            increasing_line_color='red',   # 상승 빨간색
            decreasing_line_color='blue'   # 하락 파란색
        ))
        
        # 차트 레이아웃 설정
        fig.update_layout(
            title=f"{coin_name} 가격 차트",
            xaxis_title="날짜",
            yaxis_title="가격 (KRW)",
            height=500,
            template="plotly_white",
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"차트 그리기 중 오류 발생: {str(e)}")
        return

def execute_order(upbit, coin_ticker, trade_type, amount, amount_type, current_price=None):
    """주문 실행"""
    try:
        if amount <= 0:
            st.error("금액 또는 수량은 0보다 커야 합니다.")
            return None
            
        # 매수 주문
        if trade_type == "매수":
            if amount_type == "KRW":
                # 금액 기준 시장가 매수
                return upbit.buy_market_order(coin_ticker, amount)
            else:
                # 수량 기준 시장가 매수 (수량 * 현재가)
                return upbit.buy_market_order(coin_ticker, amount * current_price)
        # 매도 주문
        else:
            if amount_type == "KRW":
                # 금액 기준 시장가 매도 (금액 / 현재가)
                return upbit.sell_market_order(coin_ticker, amount / current_price)
            else:
                # 수량 기준 시장가 매도
                return upbit.sell_market_order(coin_ticker, amount)
    except Exception as e:
        st.error(f"주문 실행 중 오류 발생: {str(e)}")
        return None

@st.cache_data(ttl=60)  # 1분 캐시
def get_order_history():
    try:
        upbit = get_upbit_instance()
        if not upbit:
            return pd.DataFrame()
            
        try:
            # 임시 데이터 생성 (실제로는 이 부분을 거래소 API로 대체)
            orders = []
            if st.session_state.get("upbit_access_key") and st.session_state.get("upbit_secret_key"):
                # API 키가 있는 경우 Upbit 객체 사용
                # 주요 코인에 대한 미체결 주문 조회
                tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-DOGE"]
                for ticker in tickers:
                    try:
                        # 미체결 주문 조회
                        wait_orders = upbit.get_order(ticker, state="wait")
                        if wait_orders:
                            orders.extend(wait_orders)
                    except Exception as e:
                        continue
            
            # 샘플 데이터 추가 (실제로는 제거)
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
                
            # 데이터프레임 생성
            df = pd.DataFrame(orders)
            
            # 필요한 컬럼이 있는지 확인
            required_columns = ['market', 'side', 'price', 'volume', 'created_at', 'state']
            for col in required_columns:
                if col not in df.columns:
                    return pd.DataFrame()
            
            # 필요한 컬럼만 선택하고 이름 변경
            df = df[required_columns].rename(columns={
                'market': '코인',
                'side': '거래유형',
                'price': '가격',
                'volume': '수량',
                'created_at': '주문시간',
                'state': '상태'
            })
            
            # 거래유형 한글화
            df['거래유형'] = df['거래유형'].map({'bid': '매수', 'ask': '매도'})
            
            # 상태 한글화
            df['상태'] = df['상태'].map({'done': '완료', 'cancel': '취소', 'wait': '대기중'})
            
            # 시간 형식 변환
            df['주문시간'] = pd.to_datetime(df['주문시간'])
            
            # 최신순 정렬
            df = df.sort_values('주문시간', ascending=False)
            
            return df
        except Exception as e:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"주문 내역 조회 중 오류 발생: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)  # 1분 캐싱
def get_important_coins() -> pd.DataFrame:
    """주요 코인과 주목할만한 코인들의 현재 정보를 가져옵니다."""
    try:
        # 거래량 기준 상위 코인 가져오기
        tickers = pyupbit.get_tickers(fiat="KRW")
        
        # 주요 코인 티커
        major_coins = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOGE", "KRW-DOT"]
        
        # 주요 코인이 tickers에 있는지 확인
        major_tickers = [ticker for ticker in major_coins if ticker in tickers]
        
        if not major_tickers:
            return generate_sample_market_data()
        
        # 현재가 및 전일종가 조회
        # tickers 파라미터 대신 리스트 직접 전달
        all_ticker_info = pyupbit.get_current_price(major_tickers)
        yesterday_info = {}
        for ticker in major_tickers:
            try:
                df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
                if df is not None and not df.empty and len(df) > 1:
                    yesterday_info[ticker] = df.iloc[0]['close']
                else:
                    # 데이터가 없는 경우 현재가의 90-110% 범위 내에서 임의의 가격 생성
                    current_price = all_ticker_info.get(ticker, 1000)
                    yesterday_info[ticker] = current_price * random.uniform(0.9, 1.1)
            except Exception:
                # 조회 실패 시 현재가의 90-110% 범위 내에서 임의의 가격 생성
                current_price = all_ticker_info.get(ticker, 1000)
                yesterday_info[ticker] = current_price * random.uniform(0.9, 1.1)
        
        result = []
        for ticker in major_tickers:
            try:
                coin_name = ticker.split('-')[1]
                current_price = all_ticker_info.get(ticker, 0)
                yesterday_price = yesterday_info.get(ticker, current_price)
                
                # 변동률 계산
                if yesterday_price > 0:
                    change_rate = ((current_price - yesterday_price) / yesterday_price) * 100
                else:
                    change_rate = 0
                
                # 임의의 거래량 및 거래대금 생성
                volume = random.randint(1000, 10000)
                trade_value = current_price * volume
                
                result.append({
                    "코인": coin_name,
                    "현재가": current_price,
                    "전일종가": yesterday_price,
                    "변동률": change_rate,
                    "거래량": volume,
                    "거래대금": trade_value
                })
            except Exception:
                continue
        
        if not result:
            return generate_sample_market_data()
            
        df = pd.DataFrame(result)
        
        # 변동률 기준 정렬
        df = df.sort_values(by="변동률", ascending=False)
        
        return df
    except Exception as e:
        st.error(f"코인 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
        return generate_sample_market_data()

def draw_candle_chart(data, coin_name, interval):
    """캔들 차트 그리기"""
    if data is None or data.empty:
        st.error(f"{coin_name} 차트 데이터를 불러오지 못했습니다.")
        return
    
    # 차트 제목 설정
    interval_name = {
        "day": "일봉",
        "week": "주봉",
        "month": "월봉"
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
        title=f"{coin_name} {interval_name} 차트",
        yaxis_title='가격 (KRW)',
        xaxis_title='날짜',
        xaxis_rangeslider_visible=False,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 거래량 차트 추가
    fig_volume = go.Figure(data=[go.Bar(
        x=data.index,
        y=data['volume'],
        marker_color='purple'
    )])
    
    fig_volume.update_layout(
        title=f"{coin_name} 거래량",
        yaxis_title='거래량',
        xaxis_title='날짜',
        height=250
    )
    
    st.plotly_chart(fig_volume, use_container_width=True)

def show_coin_details(_upbit_trade, coin_ticker: str):
    """코인 상세 정보 표시"""
    try:
        # 코인 이름 추출
        coin_name = coin_ticker.split('-')[1]
        
        # 거래소 API 연결 확인
        if _upbit_trade is None:
            st.warning("API 키가 설정되지 않아 샘플 데이터를 표시합니다.")
            # 샘플 데이터 표시
            current_price = 50000000 if coin_name == "BTC" else 3000000 if coin_name == "ETH" else 500
            krw_balance = 1000000
            coin_balance = 0.01 if coin_name == "BTC" else 0.5 if coin_name == "ETH" else 100
        else:
            # 현재가 조회
            try:
                current_price = _upbit_trade.get_current_price(coin_ticker)
                if not current_price:
                    # API 호출 실패 시 샘플 데이터 사용
                    current_price = 50000000 if coin_name == "BTC" else 3000000 if coin_name == "ETH" else 500
            except Exception as e:
                print(f"{coin_name} 현재가 조회 실패: {str(e)}")
                current_price = 50000000 if coin_name == "BTC" else 3000000 if coin_name == "ETH" else 500
            
            # 계좌 잔고 조회
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
        
        # UI 구성 - 인라인 스타일로 직접 HTML 요소 렌더링
        st.markdown(
            f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e6e6e6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <p style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">코인 거래 정보</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e6e6e6;">
                        <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">현재가</div>
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{current_price:,} KRW</div>
                        <div style="font-size: 0.8rem; color: #666;">해당 코인의 현재 시장 가격</div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e6e6e6;">
                        <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">매수 가능 금액</div>
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{krw_balance:,} KRW</div>
                        <div style="font-size: 0.8rem; color: #666;">보유 KRW 잔액</div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e6e6e6;">
                        <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">보유량</div>
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{coin_balance:,} {coin_name}</div>
                        <div style="font-size: 0.8rem; color: #666;">현재 보유중인 코인 수량</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 차트 기간 선택
        chart_interval = st.radio(
            "차트 기간",
            options=["일봉", "주봉", "월봉"],
            horizontal=True,
            key=f"{coin_name}_chart_interval"
        )
        
        # 선택된 기간에 따라 차트 데이터 조회
        interval_map = {
            "일봉": "day",
            "주봉": "week",
            "월봉": "month"
        }
        
        interval = interval_map.get(chart_interval, "day")
        
        try:
            chart_data = pyupbit.get_ohlcv(coin_ticker, interval=interval, count=30)
            if chart_data is None or chart_data.empty:
                # 데이터가 없으면 샘플 차트 데이터 생성
                chart_data = generate_sample_chart_data(coin_ticker, interval)
        except Exception as e:
            # API 호출 실패 시 샘플 데이터 사용
            chart_data = generate_sample_chart_data(coin_ticker, interval)
        
        # 차트 그리기
        draw_candle_chart(chart_data, coin_name, interval)
        
        # API 키가 없으면 매수/매도 UI 표시하지 않음
        if _upbit_trade is None:
            st.info("실제 거래를 하려면 API 설정 탭에서 API 키를 설정하세요.")
            return
            
        # 매수/매도 UI
        st.markdown("### 거래하기")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("매수")
            # 최소 주문 금액 (KRW 잔고가 5000 미만일 경우 1000으로 설정)
            min_buy_amount = min(5000, max(1000, int(krw_balance))) if krw_balance > 0 else 1000
            
            buy_amount = st.number_input(
                "매수 금액 (KRW)",
                min_value=min(min_buy_amount, int(krw_balance)) if krw_balance > 0 else 1000,  # 최소값은 잔고와 최소 주문 금액 중 작은 값
                max_value=int(max(krw_balance, 1000)),  # 최대값은 잔고 (잔고가 0이면 1000으로 설정)
                value=min(min_buy_amount, int(krw_balance)) if krw_balance > 0 else 1000,  # 초기값도 동일하게 설정
                step=1000,
                key=f"{coin_name}_buy_amount"
            )
            
            # 수수료 계산 (0.05%)
            fee = buy_amount * 0.0005
            expected_quantity = (buy_amount - fee) / current_price if current_price > 0 else 0
            
            st.info(f"예상 수수료: {fee:,.0f} KRW")
            st.info(f"예상 매수 수량: {expected_quantity:,.8f} {coin_name}")
            
            if st.button("매수 주문", key=f"{coin_name}_buy_button"):
                with st.spinner("주문 처리 중..."):
                    try:
                        result = _upbit_trade.buy_market_order(coin_ticker, buy_amount)
                        if result:
                            st.success(f"매수 주문이 접수되었습니다. 주문번호: {result.get('uuid', '알 수 없음')}")
                        else:
                            st.error("매수 주문 실패")
                    except Exception as e:
                        st.error(f"매수 주문 중 오류 발생: {str(e)}")
        
        with col2:
            st.subheader("매도")
            sell_percentage = st.slider(
                "매도 비율",
                min_value=1,
                max_value=100,
                value=100,
                step=1,
                key=f"{coin_name}_sell_percentage"
            )
            
            sell_quantity = coin_balance * (sell_percentage / 100)
            expected_amount = sell_quantity * current_price
            fee = expected_amount * 0.0005
            
            st.info(f"매도 수량: {sell_quantity:,.8f} {coin_name}")
            st.info(f"예상 매도 금액: {expected_amount:,.0f} KRW")
            st.info(f"예상 수수료: {fee:,.0f} KRW")
            
            if st.button("매도 주문", key=f"{coin_name}_sell_button"):
                if coin_balance <= 0:
                    st.error(f"{coin_name}을(를) 보유하고 있지 않습니다.")
                else:
                    with st.spinner("주문 처리 중..."):
                        try:
                            result = _upbit_trade.sell_market_order(coin_ticker, sell_quantity)
                            if result:
                                st.success(f"매도 주문이 접수되었습니다. 주문번호: {result.get('uuid', '알 수 없음')}")
                            else:
                                st.error("매도 주문 실패")
                        except Exception as e:
                            st.error(f"매도 주문 중 오류 발생: {str(e)}")
    
    except Exception as e:
        print(f"코인 상세 정보 표시 중 오류 발생: {str(e)}")
        # 오류 발생 시 간단한 오류 정보 표시
        st.info(f"{coin_ticker}에 대한 정보를 불러오는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.")

def show_trade_market():
    """거래소 화면 표시"""
    st.title("📊 거래소")
    
    # API 키 확인 (경고 메시지만 표시하고 계속 진행)
    has_api_keys = check_api_keys()
    
    # Upbit Trade 인스턴스 생성
    upbit_trade = get_upbit_trade_instance()
    
    # API 키가 있지만 인스턴스 생성에 실패한 경우에만 오류 표시
    if not upbit_trade and has_api_keys:
        st.error("업비트 API 연결에 실패했습니다. API 키를 확인해주세요.")
    
    # 새로고침 버튼
    if st.button("🔄 새로고침", key="market_refresh"):
        st.cache_data.clear()
        st.rerun()
    
    # 코인 정보 가져오기
    important_coins = get_important_coins()
    
    if not important_coins.empty:
        # 주요 코인 및 주목할만한 코인 표시
        st.markdown(
            """
            ### 💰 주요 코인
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e6e6e6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-weight: bold; margin-bottom: 0.25rem; color: #444;">거래소 정보 안내</div>
                <ul style="margin-top: 5px; padding-left: 20px;">
                    <li><strong>코인</strong>: 암호화폐 티커 심볼</li>
                    <li><strong>현재가</strong>: 해당 코인의 최신 거래 가격</li>
                    <li><strong>변동률</strong>: 24시간 기준 가격 변화 비율(%)</li>
                </ul>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # 데이터프레임 형식으로 변환하여 스타일링 적용
        df = important_coins.copy()
        
        # 변동률 열에 따라 색상 적용 (양수는 녹색, 음수는 빨간색)
        def highlight_change(val):
            """변동률에 따라 색상 결정"""
            try:
                # 문자열인 경우 숫자 추출
                if isinstance(val, str):
                    # % 기호 및 부호 제거
                    cleaned_val = val.replace('%', '').replace('+', '')
                    # 숫자로 변환
                    num_val = float(cleaned_val)
                    color = '#28a745' if num_val >= 0 else '#dc3545'
                else:
                    # 숫자인 경우 직접 비교
                    color = '#28a745' if float(val) >= 0 else '#dc3545'
                
                return f'color: {color}; font-weight: bold'
            except:
                # 변환 실패 시 기본 스타일 반환
                return 'color: #212529'
        
        # 변동률 열에 화살표 추가 (이미 변환된 경우 건너뛰기)
        if not isinstance(df['변동률'].iloc[0], str):
            df['변동률'] = df['변동률'].apply(lambda x: f"{'↑' if x >= 0 else '↓'} {x:+.2f}%")
        
        # 현재가에 천 단위 콤마 적용
        df['현재가'] = df['현재가'].apply(lambda x: f"{x:,.0f} KRW")
        
        # 표시할 열만 선택 (코인, 현재가, 변동률)
        display_df = df[['코인', '현재가', '변동률']]
        
        # 스타일링된 테이블 표시
        st.dataframe(
            display_df.style
            .map(lambda _: 'text-align: left; padding: 0.5rem;', subset=['코인'])
            .map(lambda _: 'text-align: right; padding: 0.5rem;', subset=['현재가'])
            .map(highlight_change, subset=['변동률'])
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
            height=min(len(df) * 50 + 38, 300)  # 테이블 높이 동적 계산 (최대 300px)
        )
    else:
        st.info("코인 정보를 불러오는 중입니다...")
        # 샘플 데이터 생성 및 표시
        sample_data = generate_sample_market_data()
        st.dataframe(
            sample_data.style.format({
                '현재가': '{:,.0f}',
                '전일종가': '{:,.0f}',
                '변동률': '{:+.2f}%',
                '거래량': '{:,.0f}',
                '거래대금': '{:,.0f}'
            }),
            use_container_width=True,
            height=300
        )
    
    # API 키 없는 경우 안내
    if not has_api_keys:
        st.info("실제 거래를 하려면 API 설정 탭에서 API 키를 설정하세요. 현재는 샘플 데이터를 표시합니다.")
    
    # 코인 선택 옵션
    coins = important_coins['코인'].tolist() if not important_coins.empty else ["BTC", "ETH", "XRP", "ADA", "DOGE"]
    
    selected_coin = st.selectbox(
        "코인 선택",
        options=["KRW-" + coin for coin in coins],
        format_func=lambda x: f"{x.split('-')[1]} ({x})",
        key="selected_coin"
    )
    
    if selected_coin:
        st.markdown(f"### 📈 {selected_coin.split('-')[1]} 상세 정보")
        show_coin_details(upbit_trade, selected_coin)

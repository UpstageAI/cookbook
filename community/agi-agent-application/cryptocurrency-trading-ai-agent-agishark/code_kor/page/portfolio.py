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
    """숫자 포맷팅"""
    return f"{number:,.2f}"

@st.cache_data(ttl=300)  # 5분 캐시로 증가
def get_portfolio_info():
    try:
        upbit = get_upbit_instance()
        if not upbit:
            return None, pd.DataFrame()
            
        # 보유 자산 조회
        balances = upbit.get_balances()
        if not balances:
            return None, pd.DataFrame()
            
        # KRW 잔고
        krw_balance = float(next((b['balance'] for b in balances if b['currency'] == 'KRW'), 0))
        
        # 코인 보유 내역
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
                        '코인': balance['currency'],
                        '수량': quantity,
                        '평균매수가': avg_buy_price,
                        '현재가': current_price,
                        '평가금액': current_value,
                        '투자금액': investment,
                        '평가손익': current_value - investment,
                        '수익률': ((current_price - avg_buy_price) / avg_buy_price) * 100
                    })
                    
                    total_investment += investment
                    total_current_value += current_value
        
        # 포트폴리오 요약 정보
        portfolio_summary = {
            '총보유자산': total_current_value + krw_balance,
            '총투자금액': total_investment,
            '총평가손익': total_current_value - total_investment,
            '총수익률': ((total_current_value - total_investment) / total_investment * 100) if total_investment > 0 else 0,
            '보유현금': krw_balance
        }
        
        # 데이터프레임 생성
        df = pd.DataFrame(coin_balances)
        if not df.empty:
            df = df.sort_values('평가금액', ascending=False)
        
        return portfolio_summary, df
        
    except Exception as e:
        st.error(f"포트폴리오 정보 조회 중 오류 발생: {str(e)}")
        return None, pd.DataFrame()

def generate_sample_portfolio_data():
    """샘플 포트폴리오 데이터 생성 (API 호출 실패 시 대체용)"""
    # 포트폴리오 요약 정보
    portfolio_summary = {
        '총보유자산': 10000000,
        '총투자금액': 8000000,
        '총평가손익': 2000000,
        '총수익률': 25.0,
        '보유현금': 2000000,
        '일평가수익률': 1.5
    }
    
    # 코인 보유 내역
    sample_coins = [
        {'코인': 'BTC', '수량': 0.01, '평균매수가': 48000000, '현재가': 50000000, 
         '평가금액': 500000, '투자금액': 480000, '평가손익': 20000, '수익률': 4.17},
        {'코인': 'ETH', '수량': 0.5, '평균매수가': 2800000, '현재가': 3000000, 
         '평가금액': 1500000, '투자금액': 1400000, '평가손익': 100000, '수익률': 7.14},
        {'코인': 'XRP', '수량': 10000, '평균매수가': 450, '현재가': 500, 
         '평가금액': 5000000, '투자금액': 4500000, '평가손익': 500000, '수익률': 11.11},
        {'코인': 'SOL', '수량': 10, '평균매수가': 100000, '현재가': 120000, 
         '평가금액': 1200000, '투자금액': 1000000, '평가손익': 200000, '수익률': 20.0},
    ]
    
    return portfolio_summary, pd.DataFrame(sample_coins)

def calculate_daily_profit_rate(_upbit_trade):
    """일일 수익률 계산"""
    try:
        # 주요 코인 리스트 (모든 코인을 조회하지 않고 주요 코인만 확인하여 속도 개선)
        major_tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA"]
        
        # 24시간 전 가격 정보와 현재 가격 비교
        today_total = 0
        yesterday_total = 0
        
        # 모든 가격 한 번에 조회 (여러 API 호출 대신 한 번의 API 호출)
        current_prices = pyupbit.get_current_price(major_tickers)
        
        for ticker in major_tickers:
            coin_name = ticker.split('-')[1]
            balance = _upbit_trade.get_balance(coin_name)
            
            if balance > 0:
                # 현재 가격
                current_price = current_prices.get(ticker, 0)
                
                if current_price > 0:
                    # 24시간 전 가격
                    today_value = balance * current_price
                    
                    # 일봉 데이터에서 전일 종가 가져오기
                    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
                    if df is not None and not df.empty:
                        yesterday_price = df.iloc[0]['close']
                        yesterday_value = balance * yesterday_price
                        
                        today_total += today_value
                        yesterday_total += yesterday_value
        
        # 현금 포함
        krw_balance = _upbit_trade.get_balance("KRW")
        today_total += krw_balance
        yesterday_total += krw_balance
        
        # 일일 수익률 계산
        if yesterday_total > 0:
            daily_profit_rate = ((today_total - yesterday_total) / yesterday_total) * 100
            return daily_profit_rate
        else:
            return 0
            
    except Exception as e:
        return 0  # 오류 발생 시 기본값 반환 (UI에 0%로 표시)

@st.cache_data(ttl=300)  # 5분 캐시로 증가
def get_portfolio_info_from_trade(_upbit_trade):
    """Trade 클래스를 사용하여 포트폴리오 정보 조회"""
    try:
        if not _upbit_trade:
            # API 키가 없거나 인스턴스 생성 실패 시 샘플 데이터 반환
            return generate_sample_portfolio_data()
        
        # API 키가 설정되어 있고 인스턴스가 생성되었다면 실제 데이터로 로드 시도
        try:
            # KRW 잔고
            krw_balance = _upbit_trade.get_balance("KRW")
            
            # 코인 보유 내역
            coin_balances = []
            total_investment = 0
            total_current_value = 0
            
            # 실제 잔고 조회 시도
            upbit_balances = _upbit_trade.upbit.get_balances()
            
            if upbit_balances and len(upbit_balances) > 0:
                # 모든 KRW 마켓 티커와 현재가 조회
                tickers = pyupbit.get_tickers(fiat="KRW")
                current_prices = pyupbit.get_current_price(tickers)
                
                # 잔고 정보 처리
                for balance in upbit_balances:
                    if balance['currency'] == 'KRW':
                        continue  # KRW는 건너뜀
                    
                    coin_name = balance['currency']
                    ticker = f"KRW-{coin_name}"
                    
                    if ticker in tickers:
                        # 수량
                        quantity = float(balance['balance'])
                        
                        if quantity > 0:
                            # 평균 매수가
                            avg_buy_price = float(balance['avg_buy_price'])
                            
                            # 현재가
                            current_price = current_prices.get(ticker, 0)
                            if current_price <= 0:
                                current_price = _upbit_trade.get_current_price(ticker) or 0
                            
                            # 평가금액 및 손익 계산
                            current_value = quantity * current_price
                            investment = quantity * avg_buy_price
                            
                            # 수익률 계산
                            profit_rate = 0
                            if avg_buy_price > 0:
                                profit_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100
                            
                            # 코인 정보 추가
                            coin_balances.append({
                                '코인': coin_name,
                                '수량': quantity,
                                '평균매수가': avg_buy_price,
                                '현재가': current_price,
                                '평가금액': current_value,
                                '투자금액': investment,
                                '평가손익': current_value - investment,
                                '수익률': profit_rate
                            })
                            
                            # 총액 업데이트
                            total_investment += investment
                            total_current_value += current_value
            
            # 실제 보유 코인이 있을 경우만 계속 진행
            if coin_balances:
                # 일일 수익률 계산
                daily_profit_rate = calculate_daily_profit_rate(_upbit_trade)
                
                # 포트폴리오 요약 정보
                portfolio_summary = {
                    '총보유자산': total_current_value + krw_balance,
                    '총투자금액': total_investment,
                    '총평가손익': total_current_value - total_investment,
                    '총수익률': ((total_current_value - total_investment) / total_investment * 100) if total_investment > 0 else 0,
                    '보유현금': krw_balance,
                    '일평가수익률': daily_profit_rate,
                    '코인평가금액': total_current_value  # 코인 평가금액 추가
                }
                
                # 데이터프레임 생성
                df = pd.DataFrame(coin_balances)
                if not df.empty:
                    df = df.sort_values('평가금액', ascending=False)
                
                # 실제 데이터 반환
                return portfolio_summary, df
            
            # 실제 보유 코인이 없으면 샘플 데이터 반환
            st.info("업비트 계정에 보유한 코인이 없습니다. 샘플 데이터를 표시합니다.")
            return generate_sample_portfolio_data()
            
        except Exception as e:
            # API 호출 중 오류 발생 시 샘플 데이터로 대체
            st.error(f"Upbit API에서 포트폴리오 정보를 가져오는 중 오류가 발생했습니다: {str(e)}")
            return generate_sample_portfolio_data()
        
    except Exception as e:
        st.error(f"포트폴리오 정보 조회 오류: {str(e)}")
        # 오류 발생 시 샘플 데이터 반환
        return generate_sample_portfolio_data()

def show_portfolio():
    """포트폴리오 표시"""
    st.title("📂 포트폴리오")
    
    # API 키 확인
    has_api_keys = check_api_keys()
    
    # Upbit Trade 인스턴스 생성
    upbit_trade = get_upbit_trade_instance()
    
    # 새로고침 버튼
    if st.button("🔄 새로고침", key="portfolio_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # 포트폴리오 정보 조회
    portfolio_summary, coin_balances = get_portfolio_info_from_trade(upbit_trade)
    
    # 포트폴리오 요약 정보 설명 추가
    with st.expander("포트폴리오 지표 설명"):
        portfolio_summary_html = """
        <div class="data-container">
            <ul style="margin-top: 5px; padding-left: 20px;">
                <li><strong>총 보유자산</strong>: 현금과 코인 평가금액을 합한 총 자산</li>
                <li><strong>총 평가손익</strong>: 코인 투자로 인한 현재 수익/손실 금액</li>
                <li><strong>일평가수익률</strong>: 24시간 동안의 포트폴리오 수익률</li>
                <li><strong>보유 현금</strong>: 투자에 사용 가능한 현금 잔액</li>
                <li><strong>코인 평가금액</strong>: 보유 중인 모든 코인의 현재 가치</li>
                <li><strong>총 투자금액</strong>: 코인 구매에 사용한 총 금액</li>
            </ul>
        </div>
        """
    st.write(portfolio_summary_html, unsafe_allow_html=True)
    
    if not has_api_keys:
        st.info("현재 샘플 데이터가 표시되고 있습니다. 실제 데이터를 보려면 API 설정 탭에서 API 키를 설정하세요.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 총 보유자산
        total_assets = portfolio_summary['총보유자산']
        formatted_total_assets = f"{total_assets:,.0f}"
        st.metric("총 보유자산", f"{formatted_total_assets} KRW")
    
    with col2:
        # 총 평가손익 및 수익률
        total_profit = portfolio_summary['총평가손익']
        total_profit_rate = portfolio_summary['총수익률']
        
        formatted_total_profit = f"{total_profit:,.0f}"
        profit_delta = f"{total_profit_rate:+.2f}%"
        
        st.metric("총 평가손익", f"{formatted_total_profit} KRW", 
                 delta=profit_delta, 
                 delta_color="normal")
    
    with col3:
        # 일평가수익률 표시
        daily_profit_rate = portfolio_summary.get('일평가수익률', 0)
        daily_profit = f"{daily_profit_rate:+.2f}%" if daily_profit_rate != 0 else "0.00%"
        st.metric("일평가수익률", daily_profit,
                 delta_color="normal")
    
    # 두 번째 행에 추가 지표
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 보유 현금
        cash = portfolio_summary['보유현금']
        formatted_cash = f"{cash:,.0f}"
        st.metric("보유 현금", f"{formatted_cash} KRW")
    
    with col2:
        # 코인 평가금액
        coin_value = portfolio_summary.get('코인평가금액', 0)
        formatted_coin_value = f"{coin_value:,.0f}"
        st.metric("코인 평가금액", f"{formatted_coin_value} KRW")
    
    with col3:
        # 총 투자금액
        total_investment = portfolio_summary['총투자금액']
        formatted_investment = f"{total_investment:,.0f}"
        st.metric("총 투자금액", f"{formatted_investment} KRW")
    
    # 코인별 보유 현황 표시
    st.markdown("### 💰 코인별 보유 현황")
    
    # 페이지네이션 처리
    page_size = 5  # 한 페이지당 표시할 코인 수
    if 'portfolio_page' not in st.session_state:
        st.session_state.portfolio_page = 0
    
    total_pages = (len(coin_balances) + page_size - 1) // page_size if not coin_balances.empty else 1
    start_idx = st.session_state.portfolio_page * page_size
    end_idx = min(start_idx + page_size, len(coin_balances))
    
    # 페이지 선택
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            if st.button("이전", key="prev_page", disabled=st.session_state.portfolio_page <= 0):
                st.session_state.portfolio_page -= 1
                st.rerun()
        with col2:
            pagination_info = f"<div style='text-align: center'>페이지 {st.session_state.portfolio_page + 1}/{total_pages}</div>"
            st.write(pagination_info, unsafe_allow_html=True)
        with col3:
            if st.button("다음", key="next_page", disabled=st.session_state.portfolio_page >= total_pages - 1):
                st.session_state.portfolio_page += 1
                st.rerun()
    
    # 현재 페이지의 코인 목록 표시
    if not coin_balances.empty:
        # 현재 페이지에 해당하는 데이터만 표시
        page_data = coin_balances.iloc[start_idx:end_idx]
        
        # 데이터프레임 형식으로 변환하여 스타일링 적용
        df = page_data.copy()
        
        # 수익률에 따라 색상 적용 (양수는 녹색, 음수는 빨간색)
        def style_change(val):
            try:
                # 문자열인 경우 숫자 추출
                if isinstance(val, str):
                    # 화살표와 공백 제거
                    num_str = val.replace('↑', '').replace('↓', '').strip()
                    # % 기호와 KRW 제거
                    num_str = num_str.replace('%', '').replace('KRW', '')
                    # + 기호 제거
                    num_str = num_str.replace('+', '')
                    # 콤마 제거
                    num_str = num_str.replace(',', '')
                    # 숫자로 변환
                    num_val = float(num_str)
                    # 색상 결정
                    color = '#28a745' if num_val >= 0 else '#dc3545'
                else:
                    # 숫자 타입인 경우 직접 비교
                    color = '#28a745' if float(val) >= 0 else '#dc3545'
                
                return f'color: {color}; font-weight: bold'
            except:
                # 변환 불가능한 경우 기본값 반환
                return 'color: #212529'
        
        # 수익률 열에 화살표 추가 (이미 변환된 경우 건너뛰기)
        if not isinstance(df['수익률'].iloc[0], str):
            df['수익률 표시'] = df['수익률'].apply(lambda x: f"{'↑' if x >= 0 else '↓'} {x:+.2f}%")
        
        # 평가손익에 색상 및 부호 추가
        if '평가손익 표시' not in df.columns:
            df['평가손익 표시'] = df['평가손익'].apply(lambda x: f"{'+' if x >= 0 else ''}{x:,.0f} KRW")
        
        # 숫자 형식 지정
        df['현재가 표시'] = df['현재가'].apply(lambda x: f"{x:,.0f} KRW")
        df['평균매수가 표시'] = df['평균매수가'].apply(lambda x: f"{x:,.0f} KRW")
        df['평가금액 표시'] = df['평가금액'].apply(lambda x: f"{x:,.0f} KRW")
        df['투자금액 표시'] = df['투자금액'].apply(lambda x: f"{x:,.0f} KRW")
        
        # 표시할 열만 선택
        display_columns = ['코인', '수량', '현재가 표시', '평균매수가 표시', '평가금액 표시', '평가손익 표시', '수익률 표시']
        display_df = df[display_columns].rename(columns={
            '현재가 표시': '현재가',
            '평균매수가 표시': '평균매수가',
            '평가금액 표시': '평가금액',
            '평가손익 표시': '평가손익',
            '수익률 표시': '수익률'
        })
        
        # 스타일링된 테이블 표시
        st.dataframe(
            display_df.style
            .map(lambda _: 'text-align: left; font-weight: bold; padding: 0.5rem;', subset=['코인'])
            .map(lambda _: 'text-align: right; padding: 0.5rem;', subset=['수량', '현재가', '평균매수가', '평가금액'])
            .map(style_change, subset=['수익률'])
            .map(lambda x: style_change(x), subset=['평가손익'])
            .set_properties(**{
                'background-color': '#ffffff',
                'border': '1px solid #e6e6e6',
                'border-collapse': 'collapse',
                'font-size': '14px',
                'padding': '0.5rem'
            })
            .hide(axis='index'),
            use_container_width=True,
            height=min(len(df) * 55 + 38, 350)  # 테이블 높이 동적 계산 (최대 350px)
        )
        
        # 상세 정보 표시 (필요한 경우 접을 수 있는 섹션으로 제공)
        with st.expander("코인 상세 정보 보기"):
            for idx, row in page_data.iterrows():
                # 코인 상세 정보를 카드 형태로 표시
                profit_rate = row['수익률']
                profit_color = "#28a745" if profit_rate >= 0 else "#dc3545"
                profit_sign = "+" if profit_rate >= 0 else ""
                
                # 프로그레스 바 값 계산 (수익률에 따른 막대 길이)
                progress_value = min(max((profit_rate + 20) * 2, 0), 100) / 100.0
                
                st.markdown(f"### {row['코인']} 상세 정보")
                
                # 주요 정보를 2열 그리드로 표시
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("수량", f"{row['수량']:.8f}")
                    st.metric("현재가", f"{row['현재가']:,.0f} KRW")
                    st.metric("평균매수가", f"{row['평균매수가']:,.0f} KRW")
                with col2:
                    st.metric("평가금액", f"{row['평가금액']:,.0f} KRW")
                    st.metric("투자금액", f"{row['투자금액']:,.0f} KRW")
                    st.metric("평가손익", f"{row['평가손익']:,.0f} KRW", 
                             delta=f"{profit_sign}{profit_rate:.2f}%",
                             delta_color="normal")
                
                st.markdown("---")
    else:
        st.info("보유 중인 코인이 없습니다.")

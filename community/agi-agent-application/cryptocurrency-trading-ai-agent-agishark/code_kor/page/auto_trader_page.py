import streamlit as st
import pandas as pd
import json
import time
import asyncio
from datetime import datetime, timedelta

from tools.auto_trader.auto_trader import AutoTrader

# 세션 상태 초기화
if 'auto_trader' not in st.session_state:
    st.session_state.auto_trader = None
    
if 'auto_trader_settings' not in st.session_state:
    st.session_state.auto_trader_settings = {
        'interval_minutes': 5,
        'max_investment': 100000,
        'max_trading_count': 3,
        'target_coins': ["BTC", "ETH", "XRP", "SOL", "ADA"],
        'risk_level': "중립적",
        'model_options': "gpt-4o-mini"
    }

def show_page():
    st.title("🤖 자동 거래 에이전트")
    
    # 에이전트 시작/중지/재시작 버튼을 상단으로 이동
    control_col1, control_col2, control_col3 = st.columns(3)
    
    with control_col1:
        if st.button("에이전트 시작", use_container_width=True, type="primary", 
                    disabled=(st.session_state.auto_trader is not None and st.session_state.auto_trader.is_running)):
            
            if not st.session_state.get('upbit_access_key', '') or not st.session_state.get('upbit_secret_key', ''):
                st.error("Upbit API 키가 설정되지 않았습니다. API 설정 탭에서 설정해주세요.")
            elif not st.session_state.get('openai_key', ''):
                st.error("OpenAI API 키가 설정되지 않았습니다. API 설정 탭에서 설정해주세요.")
            else:
                # 에이전트 생성 또는 재사용
                if not st.session_state.auto_trader:
                    st.session_state.auto_trader = create_auto_trader()
                
                # 에이전트 시작
                success = st.session_state.auto_trader.start()
                if success:
                    st.success("에이전트가 시작되었습니다!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("에이전트 시작에 실패했습니다.")
    
    with control_col2:
        if st.button("에이전트 중지", use_container_width=True, 
                    disabled=(st.session_state.auto_trader is None or not st.session_state.auto_trader.is_running)):
            if st.session_state.auto_trader:
                success = st.session_state.auto_trader.stop()
                if success:
                    st.success("에이전트가 중지되었습니다!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("에이전트 중지에 실패했습니다.")
    
    with control_col3:
        if st.button("에이전트 재시작", use_container_width=True, 
                    disabled=(st.session_state.auto_trader is None)):
            if st.session_state.auto_trader:
                # 먼저 중지
                if st.session_state.auto_trader.is_running:
                    st.session_state.auto_trader.stop()
                
                # 재생성 및 시작
                st.session_state.auto_trader = create_auto_trader()
                success = st.session_state.auto_trader.start()
                
                if success:
                    st.success("에이전트가 재시작되었습니다!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("에이전트 재시작에 실패했습니다.")
    
    # 메인 컨텐츠
    # 에이전트 상태 및 컨트롤
    st.header("에이전트 상태")
    
    if st.session_state.auto_trader:
        status_info = st.session_state.auto_trader.get_status()
        
        # 상태 및 타이머 표시
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            st.metric(
                "현재 상태", 
                status_info["status"], 
                delta="실행 중" if status_info["is_running"] else "중지됨",
                delta_color="normal" if status_info["is_running"] else "off"
            )
        
        with status_col2:
            next_check = "준비 중..." 
            time_until = ""
            if status_info["next_check"]:
                next_check = status_info["next_check"]
                # n분 후 표시 추가
                try:
                    next_time = datetime.strptime(status_info["next_check"], "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    if next_time > now:
                        minutes_left = (next_time - now).total_seconds() // 60
                        time_until = f"{int(minutes_left)}분 후"
                except:
                    pass
            st.metric("다음 분석 시간", next_check, delta=time_until if time_until else None)
        
        with status_col3:
            st.metric(
                "일일 거래 횟수", 
                f"{status_info['daily_trading_count']} / {status_info['max_trading_count']}"
            )
        
        # 진행 상태 텍스트 표시
        st.text(f"마지막 분석: {status_info['last_check'] or '없음'}")
        
        # 진행 바 (다음 분석까지 남은 시간)
        if status_info["is_running"] and status_info["next_check"]:
            try:
                next_time = datetime.strptime(status_info["next_check"], "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                
                if next_time > now:
                    total_seconds = status_info["interval_minutes"] * 60
                    elapsed = total_seconds - (next_time - now).total_seconds()
                    progress = min(1.0, max(0.0, elapsed / total_seconds))
                    
                    st.progress(progress)
                else:
                    st.progress(1.0)
            except:
                st.progress(0.0)
        else:
            st.progress(0.0)
    else:
        st.info("에이전트가 초기화되지 않았습니다. 시작 버튼을 눌러주세요.")
    
    # 작동 설정 - 간소화된 입력
    st.header("작동 설정")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        interval_minutes = st.text_input(
            "분석 간격 (분)", 
            value=str(st.session_state.auto_trader_settings['interval_minutes']),
            key="interval_minutes_setting"
        )
    
    with col2:
        max_trading_count = st.text_input(
            "일일 최대 거래 횟수", 
            value=str(st.session_state.auto_trader_settings['max_trading_count']),
            key="max_trading_count_setting"
        )
        
    with col3:
        max_investment = st.text_input(
            "최대 투자 금액 (원)", 
            value=str(st.session_state.auto_trader_settings['max_investment']),
            key="max_investment_setting"
        )
    
    # 설정 적용 버튼
    if st.button("설정 적용", key="apply_all_settings", type="primary"):
        try:
            # 입력값 검증 및 변환
            interval_minutes_val = int(interval_minutes)
            max_investment_val = int(max_investment)
            max_trading_count_val = int(max_trading_count)
            
            # 사이드바에서 위험 성향 가져오기
            risk_level = st.session_state.get('risk_style', '중립적')
            
            if st.session_state.auto_trader:
                # 작동 설정 업데이트
                st.session_state.auto_trader.update_operation_settings(
                    interval_minutes=interval_minutes_val,
                    max_investment=max_investment_val,
                    max_trading_count=max_trading_count_val
                )
                
                # 투자 설정 업데이트
                new_settings = {
                    'interval_minutes': interval_minutes_val,
                    'max_investment': max_investment_val,
                    'max_trading_count': max_trading_count_val,
                    'risk_level': risk_level,
                    'model_options': st.session_state.get('model_options', 'gpt-4o-mini')
                }
                
                # 설정 변경 사항 저장
                st.session_state.auto_trader_settings.update(new_settings)
                
                # 에이전트 업데이트
                restart_required = st.session_state.auto_trader.update_settings(new_settings)
                
                if restart_required and st.session_state.auto_trader.is_running:
                    st.warning("일부 설정 변경은 에이전트 재시작이 필요합니다. 중지 후 시작해주세요.")
                else:
                    st.success("설정이 적용되었습니다!")
            else:
                # 세션 상태의 설정만 업데이트
                st.session_state.auto_trader_settings.update({
                    'interval_minutes': interval_minutes_val,
                    'max_investment': max_investment_val,
                    'max_trading_count': max_trading_count_val,
                    'risk_level': risk_level,
                    'model_options': st.session_state.get('model_options', 'gpt-4o-mini')
                })
                
                st.success("설정이 저장되었습니다. 에이전트를 시작하면 적용됩니다.")
        except ValueError:
            st.error("입력값이 올바르지 않습니다. 숫자만 입력해주세요.")
    
    # 거래 기록
    st.header("거래 기록")
    
    if st.session_state.auto_trader and st.session_state.auto_trader.trading_history:
        # 데이터프레임 생성
        history_data = []
        for trade in st.session_state.auto_trader.trading_history:
            history_data.append({
                "시간": trade.get("timestamp", ""),
                "행동": "매수" if trade.get("action") == "buy" else "매도",
                "코인": trade.get("ticker", ""),
                "금액/수량": trade.get("amount", ""),
                "이유": trade.get("reason", "")[:50] + "..." if trade.get("reason") and len(trade.get("reason")) > 50 else trade.get("reason", "")
            })
        
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True, height=300)
    else:
        st.info("아직 거래 내역이 없습니다.")
    
    # 시장 정보
    st.header("시장 정보")
    
    market_container = st.container(height=300, border=True)
    
    with market_container:
        if st.session_state.auto_trader:
            market_info = st.session_state.auto_trader.get_market_info()
            
            if market_info:
                market_col1, market_col2, market_col3 = st.columns(3)
                cols = [market_col1, market_col2, market_col3]
                col_idx = 0
                
                for coin, info in market_info.items():
                    price = info["current_price"]
                    change_rate = info["change_rate"]
                    
                    with cols[col_idx % 3]:
                        st.metric(
                            f"{coin}", 
                            f"{int(price):,}원", 
                            f"{change_rate:.2f}%",
                            delta_color="normal" if change_rate >= 0 else "inverse"
                        )
                    col_idx += 1
            else:
                st.info("시장 정보를 가져올 수 없습니다.")
        else:
            st.info("에이전트가 초기화되지 않았습니다.")
    
    # 로그 정보
    st.header("실행 로그")
    
    log_container = st.container(height=300, border=True)
    
    with log_container:
        if st.session_state.auto_trader and st.session_state.auto_trader.logs:
            logs = st.session_state.auto_trader.logs[-10:]  # 최근 10개 로그만 표시
            
            for log in reversed(logs):
                level = log.get("level", "INFO")
                timestamp = log.get("timestamp", "")
                message = log.get("message", "")
                
                if level == "ERROR":
                    st.error(f"{timestamp}: {message}")
                elif level == "WARNING":
                    st.warning(f"{timestamp}: {message}")
                else:
                    st.info(f"{timestamp}: {message}")
        else:
            st.info("로그 정보가 없습니다.")

def create_auto_trader():
    """설정 정보를 기반으로 AutoTrader 객체 생성"""
    settings = st.session_state.auto_trader_settings
    
    trader = AutoTrader(
        access_key=st.session_state.upbit_access_key,
        secret_key=st.session_state.upbit_secret_key,
        model_options=settings['model_options'],
        interval_minutes=settings['interval_minutes'],
        max_investment=settings['max_investment'],
        max_trading_count=settings['max_trading_count']
    )
    
    # 추가 설정 적용
    trader.target_coins = settings['target_coins']
    trader.risk_level = settings['risk_level']
    
    return trader
    
if __name__ == "__main__":
    show_page() 
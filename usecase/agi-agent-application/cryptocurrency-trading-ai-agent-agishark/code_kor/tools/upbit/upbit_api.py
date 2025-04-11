import streamlit as st
import asyncio
import json
import logging
import os
import traceback
from typing import Dict, List, Optional, Any, Union
import datetime
from agents import Agent, FunctionTool, function_tool, RunContextWrapper

# 로깅 설정 (필요한 경우)
logger = logging.getLogger("crypto_agent")





# UpbitTrader를 직접 가져옵니다
try:
    from upbit.upbit_trader import UpbitTrader
except ImportError:
    # upbit_trader 모듈이 없는 경우 대체 구현
    class UpbitTrader:
        def __init__(self, access_key, secret_key):
            self.access_key = access_key
            self.secret_key = secret_key
            self.is_valid = False
            
        def get_balance(self, ticker):
            log_error(None, f"UpbitTrader 모듈이 로드되지 않았습니다.")
            return 0

# 로깅 설정
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"crypto_agent_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 로거 설정
logger = logging.getLogger("crypto_agent")
logger.setLevel(logging.DEBUG)

# 파일 핸들러
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 스트림 핸들러 (콘솔 출력)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# 포맷 설정
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# 핸들러 추가
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# 디버그 모드 설정
def set_debug_mode(enable=True):
    """디버그 모드 설정"""
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = enable
    else:
        st.session_state.debug_mode = enable
    logger.info(f"디버그 모드: {enable}")

# 오류 로깅 및 디버그 정보 표시 함수
def log_error(error, context=None, show_tb=True):
    """오류 로깅 및 디버그 정보 표시"""
    error_msg = f"오류: {str(error)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    
    logger.error(error_msg)
    if show_tb:
        tb = traceback.format_exc()
        logger.error(f"Traceback:\n{tb}")
    
    if st.session_state.get('debug_mode', False):
        st.error(error_msg)
        if show_tb:
            with st.expander("상세 오류 정보"):
                st.code(tb)
    else:
        st.error("오류가 발생했습니다. 자세한 내용은 로그를 확인하세요.")

# 디버그 정보 로깅 함수
def log_info(message, data=None):
    """디버그 정보 로깅"""
    logger.info(message)
    if data:
        logger.debug(f"{message} - 데이터: {json.dumps(data, ensure_ascii=False)}")
    
    if st.session_state.get('debug_mode', False) and data:
        with st.expander(f"디버그 정보: {message}"):
            st.json(data)


# 업비트 인스턴스를 가져오는 함수
def get_upbit_instance() -> Any:
    """업비트 API 인스턴스를 반환합니다."""
    upbit_access = st.session_state.get('upbit_access_key', '')
    upbit_secret = st.session_state.get('upbit_secret_key', '')
    
    if upbit_access and upbit_secret:
        try:
            import pyupbit
            upbit = pyupbit.Upbit(upbit_access, upbit_secret)
            return upbit
        except Exception as e:
            log_error(e, "업비트 인스턴스 생성 중 오류")
    
    return None

# 업비트 트레이더 인스턴스를 가져오는 함수
def get_upbit_trade_instance() -> Any:
    """업비트 트레이더 인스턴스를 반환합니다."""
    upbit_access = st.session_state.get('upbit_access_key', '')
    upbit_secret = st.session_state.get('upbit_secret_key', '')
    
    if upbit_access and upbit_secret:
        try:
            trader = UpbitTrader(upbit_access, upbit_secret)
            return trader
        except Exception as e:
            log_error(e, "업비트 트레이더 인스턴스 생성 중 오류")
    
    return None



# 도구 함수 구현
@function_tool
async def get_available_coins_func(action_type: Optional[str] = None) -> str:
    """
    거래 가능한 코인 목록과 현재 보유 중인 코인 목록을 반환합니다.
    사용자가 매도하려는 경우에는 보유 중인 코인만 표시합니다.
    
    Args:
        action_type: 거래 유형 (buy 또는 sell)
    """
    log_info("get_available_coins 함수 호출")
    
    try:
        upbit = get_upbit_instance()
        
        if upbit:
            log_info("get_available_coins: 유효한 Upbit 인스턴스로 실제 데이터 조회 시도")
            
            # 사용자의 보유 코인 목록 조회
            portfolio_coins = []
            try:
                balances = upbit.get_balances()
                for balance in balances:
                    if balance['currency'] != 'KRW' and float(balance['balance']) > 0:
                        portfolio_coins.append({
                            'ticker': f"KRW-{balance['currency']}",
                            'korean_name': balance['currency'],  # API에서 한글 이름을 따로 제공하지 않음
                            'balance': float(balance['balance']),
                            'avg_buy_price': float(balance['avg_buy_price'])
                        })
            except Exception as e:
                log_error(e, "보유 코인 목록 조회 중 오류 발생")
                # 오류 발생해도 계속 진행
            
            # 매도 목적인 경우, 보유 코인만 반환
            if action_type == "sell":
                log_info("get_available_coins: 매도용 코인 목록 필터링 (보유 코인만)")
                if not portfolio_coins:
                    return json.dumps({
                        "success": True,
                        "message": "현재 보유 중인 코인이 없습니다.",
                        "coins": []
                    }, ensure_ascii=False)
                
                return json.dumps({
                    "success": True,
                    "message": f"보유 중인 코인 {len(portfolio_coins)}개를 찾았습니다.",
                    "coins": portfolio_coins
                }, ensure_ascii=False)
            
            # KRW 마켓 코인 조회
            try:
                import pyupbit
                markets = pyupbit.get_tickers(fiat="KRW")
                market_info = []
                
                # 시장 정보 가져오기
                for market in markets[:20]:  # 상위 20개만 처리 (속도 향상)
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
                log_error(e, "KRW 마켓 코인 조회 중 오류 발생")
                market_info = []
            
            krw_markets = market_info
            log_info(f"get_available_coins: {len(krw_markets)}개의 KRW 마켓 코인 조회됨")
            
            # 위험 성향에 기반해 추천 코인 필터링 (예시)
            risk_style = st.session_state.get('risk_style', '중립적')
            risk_filters = {
                '보수적': lambda m: m['market'] in ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOGE'],
                '중립적': lambda m: True,  # 모든 코인 허용
                '공격적': lambda m: True   # 모든 코인 허용
            }
            
            filtered_markets = [m for m in krw_markets if risk_filters.get(risk_style, lambda x: True)(m)]
            
            # 결과 제한 (최대 10개)
            result_markets = filtered_markets[:10] if len(filtered_markets) > 10 else filtered_markets
            
            # 결과 형식 변환
            coins = []
            for market in result_markets:
                coins.append({
                    'ticker': market['market'],
                    'korean_name': market['korean_name']
                })
            
            log_info("get_available_coins: 성공")
            return json.dumps({
                "success": True,
                "message": f"거래 가능한 코인 {len(coins)}개를 찾았습니다.",
                "coins": coins,
                "portfolio": portfolio_coins  # 보유 코인 정보 추가
            }, ensure_ascii=False)
            
        else:  # upbit API 인스턴스 없음
            # 데모 데이터 - 연결할 API 키가 없을 때
            log_info("get_available_coins: API 연결 없이 데모 데이터 반환")
            
            # 데모용 보유 코인 목록
            demo_portfolio = [
                {'ticker': 'KRW-BTC', 'korean_name': '비트코인', 'balance': 0.001, 'avg_buy_price': 65000000},
                {'ticker': 'KRW-ETH', 'korean_name': '이더리움', 'balance': 0.05, 'avg_buy_price': 3500000}
            ]
            
            # 매도 목적인 경우, 데모 보유 코인만 반환
            if action_type == "sell":
                return json.dumps({
                    "success": True,
                    "message": "보유 중인 코인 2개를 찾았습니다. (데모 모드)",
                    "coins": demo_portfolio,
                    "is_demo": True
                }, ensure_ascii=False)
            
            # 데모용 거래 가능 코인 목록
            demo_coins = [
                {'ticker': 'KRW-BTC', 'korean_name': '비트코인'},
                {'ticker': 'KRW-ETH', 'korean_name': '이더리움'},
                {'ticker': 'KRW-XRP', 'korean_name': '리플'},
                {'ticker': 'KRW-ADA', 'korean_name': '에이다'},
                {'ticker': 'KRW-DOGE', 'korean_name': '도지코인'},
                {'ticker': 'KRW-SOL', 'korean_name': '솔라나'},
                {'ticker': 'KRW-DOT', 'korean_name': '폴카닷'},
                {'ticker': 'KRW-AVAX', 'korean_name': '아발란체'}
            ]
            
            return json.dumps({
                "success": True, 
                "message": "거래 가능한 코인 8개를 찾았습니다. (데모 모드)",
                "coins": demo_coins,
                "portfolio": demo_portfolio,
                "is_demo": True
            }, ensure_ascii=False)
            
    except Exception as e:
        log_error(e, "get_available_coins 함수 실행 중 오류")
        return json.dumps({
            "success": False,
            "message": f"코인 목록 조회 중 오류 발생: {str(e)}",
            "coins": []
        }, ensure_ascii=False)


@function_tool
async def get_coin_price_info_func(ticker: str) -> str:
    """
    코인 가격 정보를 조회합니다.
    
    Args:
        ticker: 코인 티커 (예: 'BTC')
    """
    log_info("get_coin_price_info 함수 호출")
    
    # 티커 처리
    ticker = ticker.upper()
    
    # 티커가 없으면 오류
    if not ticker:
        error_msg = "티커(ticker) 값이 필요합니다."
        log_error(None, error_msg, show_tb=False)
        return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
    
    # KRW 프리픽스 추가
    if not ticker.startswith("KRW-"):
        ticker = f"KRW-{ticker}"
    
    log_info("get_coin_price_info: 티커 파싱 완료", {"ticker": ticker})
    
    try:
        # pyupbit 사용하여 데이터 조회
        try:
            import pyupbit
            
            # 현재가 조회
            current_price = pyupbit.get_current_price(ticker)
            log_info("get_coin_price_info: 현재가 조회 결과", {"price": current_price})
            
            # 보유량 조회
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
            
            log_info("get_coin_price_info: 잔고 조회 결과", balance_info)
            
            # 일봉 데이터 조회
            df = pyupbit.get_ohlcv(ticker, interval="day", count=7)
            log_info("get_coin_price_info: OHLCV 데이터 조회 성공")
            
            # 데이터 포맷팅
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
            
            # 데이터 조합
            result = {
                "success": True,
                "ticker": ticker,
                "current_price": current_price,
                "balance_info": balance_info,
                "ohlcv_data": ohlcv_data
            }
            
            log_info("get_coin_price_info: 성공")
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            error_msg = f"코인 가격 정보 조회 중 오류 발생: {str(e)}"
            log_error(e, error_msg)
            return json.dumps({"success": False, "message": error_msg, "ticker": ticker}, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"코인 가격 정보 조회 중 예상치 못한 오류: {str(e)}"
        log_error(e, error_msg)
        return json.dumps({"success": False, "message": error_msg, "ticker": ticker}, ensure_ascii=False)


@function_tool
async def buy_coin_func(ticker: str, price_type: str, amount: float, limit_price: Optional[float]) -> str:
    """
    코인 매수 함수
    
    Args:
        ticker: 코인 티커 (예: 'BTC')
        price_type: 'market' 또는 'limit'
        amount: 매수량 (원화)
        limit_price: 지정가 주문 시 가격
    """
    try:
        # 로깅 시작
        log_info("buy_coin 함수 호출", {"ticker": ticker, "price_type": price_type, "amount": amount, "limit_price": limit_price})
        print(f"매수 함수 호출: {ticker}, {price_type}, {amount}, {limit_price}")
        
        # 티커 처리
        ticker = ticker.upper()
        
        # 티커 검증
        if not ticker:
            error_msg = "티커(ticker)가 지정되지 않았습니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # KRW 마켓 프리픽스가 없으면 추가
        if not ticker.startswith("KRW-"):
            ticker = f"KRW-{ticker}"
        log_info(f"buy_coin: 코인명 추출", {"ticker": ticker})
        
        # upbit 인스턴스 가져오기
        upbit = get_upbit_instance()
        if not upbit:
            error_msg = "Upbit API 인스턴스를 생성할 수 없습니다. API 키 설정을 확인하세요."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        log_info(f"buy_coin: 유효한 Upbit 인스턴스 확인")
        
        # 주문 유형 확인
        price_type = price_type.lower()
        if price_type not in ["market", "limit"]:
            error_msg = f"지원하지 않는 주문 유형: {price_type}. 'market' 또는 'limit'만 사용할 수 있습니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 금액 검증
        if amount <= 0:
            error_msg = f"유효하지 않은 매수 금액: {amount}. 양수여야 합니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 전량 매수 여부 확인 (계좌의 원화 잔고와 동일한 경우)
        krw_balance = 0
        try:
            balances = upbit.get_balances()
            for balance in balances:
                if balance['currency'] == 'KRW':
                    krw_balance = float(balance['balance'])
                    break
            
            # 전량 매수로 판단되는 경우 (원화 잔고의 99% 이상 사용)
            if amount >= krw_balance * 0.99:
                # 수수료를 고려하여 99.95%만 사용
                amount = krw_balance * 0.9995
                log_info(f"buy_coin: 전량 매수로 판단됨. 수수료 고려하여 금액 조정", {"original": krw_balance, "adjusted": amount})
        except Exception as e:
            log_error(e, "buy_coin: 원화 잔고 확인 중 오류")
            # 오류가 발생해도 계속 진행 (조정 없이)
        
        order_type = None
        order_result = None
        
        # 마켓 주문과 리밋 주문의 분리 처리
        if price_type == "market":
            log_info(f"buy_coin: 시장가 매수 시도", {"ticker": ticker, "amount": amount})
            print(f"시장가 매수 주문: {ticker}, {amount}KRW")
            order_type = "시장가"
            try:
                order_result = upbit.buy_market_order(ticker, amount)
                log_info(f"buy_coin: 주문 결과", {"result": order_result})
            except Exception as e:
                error_msg = f"시장가 매수 중 오류 발생: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
                
        else:  # limit order
            if not limit_price or limit_price <= 0:
                error_msg = "지정가 주문에는 유효한 'limit_price'가 필요합니다."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
            # 수량 계산 (금액 / 지정가)
            volume = amount / limit_price
            
            log_info(f"buy_coin: 지정가 매수 시도", {"ticker": ticker, "price": limit_price, "volume": volume})
            print(f"지정가 매수 주문: {ticker}, 가격: {limit_price}KRW, 수량: {volume}")
            order_type = "지정가"
            try:
                order_result = upbit.buy_limit_order(ticker, limit_price, volume)
                log_info(f"buy_coin: 주문 결과", {"result": order_result})
            except Exception as e:
                error_msg = f"지정가 매수 중 오류 발생: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 주문 결과 반환
        if order_result and 'uuid' in order_result:
            result = {
                'success': True,
                'message': f"{ticker} {order_type} 매수 주문이 접수되었습니다. 주문 ID: {order_result['uuid']}\n주문 체결 결과는 '거래내역' 탭에서 확인하실 수 있습니다.",
                'order_id': order_result['uuid'],
                'order_info': order_result
            }
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"주문은 성공했으나 주문 ID를 받지 못했습니다.: {order_result}"
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"매수 주문 중 예기치 않은 오류 발생: {str(e)}"
        log_error(e, error_msg)
        return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)


@function_tool
async def sell_coin_func(ticker: str, price_type: str, amount: Union[str, float], limit_price: Optional[float]) -> str:
    """
    코인 매도 함수
    
    Args:
        ticker: 코인 티커 (예: 'BTC')
        price_type: 'market' 또는 'limit'
        amount: 매도량 (코인 수량 또는 'all'/'전체'/'전량')
        limit_price: 지정가 주문 시 가격
    """
    try:
        # 로깅 시작
        log_info("sell_coin 함수 호출", {"ticker": ticker, "price_type": price_type, "amount": amount, "limit_price": limit_price})
        print(f"매도 함수 호출: {ticker}, {price_type}, {amount}, {limit_price}")
        
        # 티커 처리
        ticker = ticker.upper()
        
        # 티커 검증
        if not ticker:
            error_msg = "티커(ticker)가 지정되지 않았습니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # KRW 마켓 프리픽스가 없으면 추가
        if not ticker.startswith("KRW-"):
            ticker = f"KRW-{ticker}"
        log_info(f"sell_coin: 코인명 추출", {"ticker": ticker})
        
        # upbit 인스턴스 가져오기
        upbit = get_upbit_instance()
        if not upbit:
            error_msg = "Upbit API 인스턴스를 생성할 수 없습니다. API 키 설정을 확인하세요."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        log_info(f"sell_coin: 유효한 Upbit 인스턴스 확인")
        
        # 주문 유형 확인
        price_type = price_type.lower()
        if price_type not in ["market", "limit"]:
            error_msg = f"지원하지 않는 주문 유형: {price_type}. 'market' 또는 'limit'만 사용할 수 있습니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 보유량 확인 - 포트폴리오 기준으로 확인
        coin_currency = ticker.replace("KRW-", "")
        coin_balance = 0
        try:
            balances = upbit.get_balances()
            for balance in balances:
                if balance['currency'] == coin_currency:
                    coin_balance = float(balance['balance'])
                    break
            
            log_info(f"sell_coin: 코인 잔고 조회", {"ticker": ticker, "balance": coin_balance})
            
            if coin_balance <= 0:
                error_msg = f"{coin_currency} 코인을 보유하고 있지 않습니다. 매도할 수 없습니다."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        except Exception as e:
            error_msg = f"코인 잔고 조회 중 오류 발생: {str(e)}"
            log_error(e, error_msg)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 수량 파싱
        amount_value = None
        
        # 전체 수량 매도인 경우
        if isinstance(amount, str) and amount.lower() in ["all", "전체", "전량"]:
            amount_value = coin_balance
            log_info(f"sell_coin: 전체 매도 요청", {"coin_balance": coin_balance})
        else:
            try:
                amount_value = float(amount)
                # 보유량보다 많은 경우 오류
                if amount_value > coin_balance:
                    error_msg = f"매도 수량({amount_value})이 보유량({coin_balance})보다 많습니다."
                    log_error(None, error_msg, show_tb=False)
                    return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            except ValueError:
                error_msg = f"유효하지 않은 매도 수량: {amount}. 숫자 또는 'all'/'전체'/'전량'으로 지정해주세요."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 유효한 수량인지 확인
        if amount_value <= 0:
            error_msg = f"유효하지 않은 매도 수량: {amount_value}. 양수여야 합니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        order_type = None
        order_result = None
        
        # 마켓 주문과 리밋 주문의 분리 처리
        if price_type == "market":
            log_info(f"sell_coin: 시장가 매도 시도", {"ticker": ticker, "amount": amount_value})
            print(f"시장가 매도 주문: {ticker}, {amount_value}개")
            order_type = "시장가"
            try:
                order_result = upbit.sell_market_order(ticker, amount_value)
                log_info(f"sell_coin: 주문 결과", {"result": order_result})
            except Exception as e:
                error_msg = f"시장가 매도 중 오류 발생: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
                
        else:  # limit order
            if not limit_price or limit_price <= 0:
                error_msg = "지정가 주문에는 유효한 'limit_price'가 필요합니다."
                log_error(None, error_msg, show_tb=False)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
            log_info(f"sell_coin: 지정가 매도 시도", {"ticker": ticker, "price": limit_price, "amount": amount_value})
            print(f"지정가 매도 주문: {ticker}, 가격: {limit_price}KRW, 수량: {amount_value}개")
            order_type = "지정가"
            try:
                order_result = upbit.sell_limit_order(ticker, limit_price, amount_value)
                log_info(f"sell_coin: 주문 결과", {"result": order_result})
            except Exception as e:
                error_msg = f"지정가 매도 중 오류 발생: {str(e)}"
                log_error(e, error_msg)
                return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        # 주문 결과 반환
        if order_result and 'uuid' in order_result:
            result = {
                'success': True,
                'message': f"{ticker} {order_type} 매도 주문이 접수되었습니다. 주문 ID: {order_result['uuid']}\n주문 체결 결과는 '거래내역' 탭에서 확인하실 수 있습니다.",
                'order_id': order_result['uuid'],
                'order_info': order_result
            }
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"주문은 성공했으나 주문 ID를 받지 못했습니다.: {order_result}"
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
            
    except Exception as e:
        error_msg = f"매도 주문 중 예기치 않은 오류 발생: {str(e)}"
        log_error(e, error_msg)
        return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)

@function_tool
async def check_order_status_func(order_id: str) -> str:
    """
    주문 상태를 확인합니다.
    
    Args:
        order_id: 확인할 주문의 ID (UUID)
    """
    function_name = "check_order_status"
    log_info(f"{function_name} 함수 호출", {"order_id": order_id})
    
    try:
        # 주문 ID 검증
        if not order_id:
            error_msg = "주문 ID가 지정되지 않았습니다."
            log_error(None, error_msg, show_tb=False)
            return json.dumps({"success": False, "message": error_msg}, ensure_ascii=False)
        
        log_info(f"{function_name}: 파라미터 확인 완료", {"order_id": order_id})
        
        st.write(f"주문 상태를 확인하는 중...")
        upbit_trade = get_upbit_trade_instance()
        
        if upbit_trade and upbit_trade.is_valid:
            log_info(f"{function_name}: 유효한 Upbit 인스턴스 확인")
            # 주문 상태 조회
            order_result = upbit_trade.get_order(order_id)
            log_info(f"{function_name}: 주문 조회 결과", {"result": order_result})
            
            if order_result and 'uuid' in order_result:
                # 주문 정보 가공
                order_info = {
                    'order_id': order_result['uuid'],
                    'status': order_result['state'],
                    'side': '매수' if order_result['side'] == 'bid' else '매도',
                    'price': float(order_result['price']) if order_result['price'] else None,
                    'volume': float(order_result['volume']) if order_result['volume'] else None,
                    'executed_volume': float(order_result['executed_volume']) if order_result['executed_volume'] else 0,
                    'remaining_volume': float(order_result['remaining_volume']) if order_result['remaining_volume'] else 0,
                    'created_at': order_result['created_at'],
                    'market': order_result['market'],
                    'order_type': order_result['ord_type']
                }
                
                # 주문 상태 한글화
                status_map = {
                    'wait': '대기',
                    'watch': '예약',
                    'done': '완료',
                    'cancel': '취소'
                }
                order_info['status_korean'] = status_map.get(order_result['state'], order_result['state'])
                
                # 체결 여부 및 체결률 계산
                if order_info['executed_volume'] > 0:
                    order_info['is_executed'] = True
                    if order_info['volume'] > 0:
                        order_info['execution_rate'] = (order_info['executed_volume'] / order_info['volume']) * 100
                    else:
                        order_info['execution_rate'] = 0
                else:
                    order_info['is_executed'] = False
                    order_info['execution_rate'] = 0
                
                log_info(f"{function_name}: 주문 정보 가공 완료", {"processed_info": order_info})
                
                result = {
                    'success': True,
                    'message': f"주문 조회 성공: {order_info['status_korean']}",
                    'order_info': order_info
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                log_info(f"{function_name}: 주문 조회 실패", {"order_id": order_id})
                result = {
                    'success': False,
                    'message': f"주문 조회 실패: {order_result}",
                    'order_info': None
                }
                return json.dumps(result, ensure_ascii=False)
        
        # API 키가 없거나 유효하지 않은 경우
        log_info(f"{function_name}: API 키 없음 또는 유효하지 않음")
        result = {
            'success': False,
            'message': "API 키가 설정되지 않았거나 유효하지 않습니다. API 설정 페이지에서 키를 확인해주세요.",
            'order_info': None,
            'is_demo': True
        }
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        log_error(e, f"{function_name} 함수 실행 중 오류 발생")
        result = {
            'success': False,
            'message': f"주문 상태 확인 중 오류 발생: {str(e)}",
            'order_info': None
        }
        return json.dumps(result, ensure_ascii=False)

# 도구 스키마 정의
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
            "description": "조회할 코인의 티커 (예: 'KRW-BTC' 또는 'BTC')"
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
            "description": "구매할 코인의 티커 (예: 'KRW-BTC' 또는 'BTC')"
        },
        "price": {
            "type": ["number", "null"],
            "description": "지정가 매수 시 주문 가격. null이면 시장가 주문."
        },
        "amount": {
            "type": ["number", "null"],
            "description": "구매할 금액(KRW) 또는 수량. 시장가 주문은 KRW 금액, 지정가 주문은 코인 수량."
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
            "description": "판매할 코인의 티커 (예: 'KRW-BTC' 또는 'BTC')"
        },
        "price": {
            "type": ["number", "null"],
            "description": "지정가 매도 시 주문 가격. null이면 시장가 주문."
        },
        "amount": {
            "type": ["number", "null"],
            "description": "판매할 코인 수량. null이면 전체 보유량 매도."
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
            "description": "확인할 주문의 ID (UUID)"
        }
    },
    "required": ["order_id"],
    "additionalProperties": False
}

# 도구 함수에 대한 래퍼
async def tool_wrapper(func, ctx, args, retries=2):
    """
    도구 함수 호출에 대한 래퍼 - 오류 처리 및 재시도를 제공
    """
    function_name = func.__name__
    attempt = 0
    last_error = None
    
    while attempt <= retries:
        try:
            if attempt > 0:
                log_info(f"{function_name}: 재시도 {attempt}/{retries}")
                
            return await func(ctx, args)
        except Exception as e:
            last_error = e
            log_error(e, f"{function_name} 함수 실행 중 오류 발생 (시도 {attempt+1}/{retries+1})")
            attempt += 1
            
            # 마지막 시도가 아니면 잠시 대기 후 재시도
            if attempt <= retries:
                await asyncio.sleep(1)  # 1초 대기
    
    # 모든 재시도 실패 시
    log_error(last_error, f"{function_name} 함수 실행 실패 - 최대 재시도 횟수 초과")
    
    # 기본 오류 응답
    error_response = {
        'success': False,
        'message': f"함수 실행 실패: {str(last_error)} (최대 재시도 횟수 초과)",
        'error': str(last_error)
    }
    return json.dumps(error_response, ensure_ascii=False)


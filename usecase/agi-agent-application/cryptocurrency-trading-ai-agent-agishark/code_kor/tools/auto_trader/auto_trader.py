import streamlit as st
import os
import time
import json
import threading
import asyncio
import schedule
from datetime import datetime, timedelta
import pandas as pd

# 필요한 모듈 임포트
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
        자동 매수/매도 에이전트 초기화
        
        Args:
            access_key: 업비트 액세스 키
            secret_key: 업비트 시크릿 키
            model_options: 사용할 모델
            interval_minutes: 매수/매도 결정을 내릴 간격(분)
            max_investment: 최대 투자 금액
            max_trading_count: 최대 거래 횟수(하루)
        """
        # 업비트 API 키 설정
        self.access_key = access_key or st.session_state.get('upbit_access_key', '')
        self.secret_key = secret_key or st.session_state.get('upbit_secret_key', '')
        
        # OpenAI API 키 설정
        self.openai_key = st.session_state.get('openai_key', '')
        
        # 거래 인스턴스 생성
        self.trade = Trade(access_key=self.access_key, secret_key=self.secret_key)
        
        # 설정값 저장
        self.model_options = model_options
        self.interval_minutes = interval_minutes
        self.max_investment = max_investment
        self.max_trading_count = max_trading_count
        
        # 거래 기록 저장소
        self.trading_history = []
        self.daily_trading_count = 0
        self.last_trading_date = None
        
        # 스레드 및 실행 제어
        self.is_running = False
        self.thread = None
        
        # 상태 정보
        self.status = "준비됨"
        self.last_check_time = None
        self.next_check_time = None
        
        # 매수/매도 전략 설정
        self.target_coins = ["BTC", "ETH", "XRP", "SOL", "ADA"]  # 기본 관심 코인
        self.risk_level = "중립적"  # 기본 위험 성향
        
        # 로그 저장소
        self.logs = []
        
        # 작동 설정
        self.daily_trade_volume = 100000  # 기본 일일 거래량 (원)
        
        # 스레드 관련
        self.trading_thread = None
        self.stop_event = threading.Event()
        
        # 콜백 함수
        self.trade_callback = None
        
    def log(self, message, level="INFO"):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {"timestamp": timestamp, "level": level, "message": message}
        self.logs.append(log_entry)
        print(f"[{level}] {timestamp}: {message}")
        
        # 로그가 너무 많아지면 오래된 것부터 삭제
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]

    @function_tool
    def buy_coin(self, ticker: str, price_type: str, amount: float, limit_price: float = None):
        """
        에이전트가 코인을 매수하는 도구
        
        Args:
            ticker: 코인 티커 (예: 'BTC')
            price_type: 'market' 또는 'limit'
            amount: 매수량 (원화)
            limit_price: 지정가 주문 시 가격
        """
        self.log(f"LLM 에이전트 매수 요청: {ticker} {amount}원 ({price_type})", "INFO")
        
        try:
            # 일일 거래 횟수 제한 확인
            current_date = datetime.now().date()
            if self.last_trading_date != current_date:
                self.last_trading_date = current_date
                self.daily_trading_count = 0
            
            if self.daily_trading_count >= self.max_trading_count:
                return {
                    "success": False,
                    "message": f"일일 최대 거래 횟수({self.max_trading_count}회)를 초과하여 거래를 건너뜁니다."
                }
            
            # KRW 프리픽스 추가
            if not ticker.startswith("KRW-"):
                ticker = f"KRW-{ticker}"
            
            # 금액 제한
            amount = min(amount, self.max_investment)
            
            # 현재 원화 잔고 확인
            krw_balance = self.trade.get_balance("KRW")
            if krw_balance < amount:
                self.log(f"원화 잔고({krw_balance}원)가 부족하여 거래 금액을 조정합니다.", "WARNING")
                amount = krw_balance * 0.95  # 수수료 고려하여 95%만 사용
            
            # 최소 주문 금액 확인
            if amount < 5000:
                return {
                    "success": False,
                    "message": f"최소 주문 금액(5,000원)보다 작아 거래를 건너뜁니다: {amount}원"
                }
            
            # 주문 유형에 따른 처리
            if price_type == "market":
                self.log(f"{ticker} {amount}원 시장가 매수 주문 시작", "INFO")
                result = self.trade.buy_market_order(ticker, amount)
            else:  # limit
                if not limit_price or limit_price <= 0:
                    return {
                        "success": False,
                        "message": "지정가 주문에는 유효한 가격이 필요합니다."
                    }
                
                volume = amount / limit_price
                self.log(f"{ticker} {volume}개 지정가({limit_price}원) 매수 주문 시작", "INFO")
                result = self.trade.buy_limit_order(ticker, limit_price, volume)
            
            if result and 'uuid' in result:
                # 거래 기록 저장
                trade_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "buy",
                    "ticker": ticker,
                    "amount": amount,
                    "price_type": price_type,
                    "limit_price": limit_price if price_type == "limit" else None,
                    "result": result,
                    "reason": "LLM 에이전트 매수 결정"
                }
                self.trading_history.append(trade_record)
                self.daily_trading_count += 1
                
                self.log(f"매수 주문 완료: {ticker}, 주문ID: {result['uuid']}", "INFO")
                
                # 거래 알림 전송
                self.notify_trade(trade_record)
                
                return {
                    "success": True,
                    "message": f"{ticker} 매수 주문이 접수되었습니다.",
                    "order_id": result['uuid']
                }
            else:
                self.log(f"매수 주문 실패: {ticker}", "ERROR")
                return {
                    "success": False,
                    "message": f"매수 주문 실패: {result}"
                }
        except Exception as e:
            self.log(f"매수 주문 중 오류 발생: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"매수 주문 중 오류 발생: {str(e)}"
            }

    @function_tool
    def sell_coin(self, ticker: str, price_type: str, amount: str = "all", limit_price: float = None):
        """
        에이전트가 코인을 매도하는 도구
        
        Args:
            ticker: 코인 티커 (예: 'BTC')
            price_type: 'market' 또는 'limit'
            amount: 매도량 (코인 수량 또는 'all'/'전량')
            limit_price: 지정가 주문 시 가격
        """
        self.log(f"LLM 에이전트 매도 요청: {ticker} {amount} ({price_type})", "INFO")
        
        try:
            # 일일 거래 횟수 제한 확인
            current_date = datetime.now().date()
            if self.last_trading_date != current_date:
                self.last_trading_date = current_date
                self.daily_trading_count = 0
            
            if self.daily_trading_count >= self.max_trading_count:
                return {
                    "success": False,
                    "message": f"일일 최대 거래 횟수({self.max_trading_count}회)를 초과하여 거래를 건너뜁니다."
                }
            
            # KRW 프리픽스 추가
            if not ticker.startswith("KRW-"):
                ticker = f"KRW-{ticker}"
            
            # 보유량 확인
            coin_balance = self.trade.get_balance(ticker)
            if not coin_balance or coin_balance <= 0:
                return {
                    "success": False,
                    "message": f"{ticker} 보유량이 없어 매도를 건너뜁니다."
                }
            
            # 매도 수량 결정
            volume = None  # 기본적으로 전량 매도
            if amount not in ["all", "전량"]:
                try:
                    volume = float(amount)
                    if volume > coin_balance:
                        self.log(f"매도 수량({volume})이 보유량({coin_balance})보다 많습니다.", "WARNING")
                        volume = coin_balance
                except ValueError:
                    return {
                        "success": False,
                        "message": f"유효하지 않은 매도 수량: {amount}. 숫자 또는 'all'로 지정해주세요."
                    }
            
            # 주문 유형에 따른 처리
            if price_type == "market":
                self.log(f"{ticker} {volume if volume else '전량'} 시장가 매도 주문 시작", "INFO")
                result = self.trade.sell_market_order(ticker, volume)
            else:  # limit
                if not limit_price or limit_price <= 0:
                    return {
                        "success": False,
                        "message": "지정가 주문에는 유효한 가격이 필요합니다."
                    }
                
                sell_volume = volume if volume else coin_balance
                self.log(f"{ticker} {sell_volume}개 지정가({limit_price}원) 매도 주문 시작", "INFO")
                result = self.trade.sell_limit_order(ticker, limit_price, sell_volume)
            
            if result and 'uuid' in result:
                # 거래 기록 저장
                trade_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "sell",
                    "ticker": ticker,
                    "amount": volume if volume else "전량",
                    "price_type": price_type,
                    "limit_price": limit_price if price_type == "limit" else None,
                    "result": result,
                    "reason": "LLM 에이전트 매도 결정"
                }
                self.trading_history.append(trade_record)
                self.daily_trading_count += 1
                
                self.log(f"매도 주문 완료: {ticker}, 주문ID: {result['uuid']}", "INFO")
                
                # 거래 알림 전송
                self.notify_trade(trade_record)
                
                result = {
                    'success': True,
                    'message': f"{ticker} {volume if volume else '전량'} 매도 주문이 접수되었습니다. 주문 ID: {result['uuid']}\n주문 체결 결과는 '거래내역' 탭에서 확인하실 수 있습니다.",
                    'order_id': result['uuid'],
                    'order_info': result
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                self.log(f"매도 주문 실패: {ticker}", "ERROR")
                return {
                    "success": False,
                    "message": f"매도 주문 실패: {result}"
                }
        except Exception as e:
            self.log(f"매도 주문 중 오류 발생: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"매도 주문 중 오류 발생: {str(e)}"
            }
    
    def create_agent(self):
        """LLM 에이전트 생성"""
        if not self.openai_key:
            self.log("OpenAI API 키가 설정되지 않았습니다", "ERROR")
            return None
            
        set_default_openai_key(self.openai_key)
        
        # 최근 거래 내역 가져오기
        recent_trades = self.trading_history[-5:] if self.trading_history else []
        recent_trades_str = "\n".join([
            f"- {trade['timestamp']}: {trade['action']} {trade['ticker']} ({trade['reason']})"
            for trade in recent_trades
        ])
        
        # 현재 포트폴리오 정보 가져오기
        portfolio = self.get_portfolio()
        portfolio_str = "\n".join([
            f"- {item['ticker']}: {item['amount']} ({item['value']}원)"
            for item in portfolio
        ])
        
        # 현재 시장 상황 정보 가져오기
        market_info = self.get_market_info()
        market_info_str = "\n".join([
            f"- {coin}: 현재가 {info['current_price']}원, 24시간 변동률 {info['change_rate']}%"
            for coin, info in market_info.items()
        ])
        
        # 에이전트 생성
        agent = Agent(
            name="Auto Trading Agent",
            instructions=f"""
            당신은 암호화폐 자동 거래 에이전트입니다. 현재 시장 상황과 포트폴리오를 분석하여 매수/매도 결정을 내려야 합니다.
            
            # 설정 정보
            - 최대 투자 금액: {self.max_investment}원
            - 매수/매도 결정 간격: {self.interval_minutes}분
            - 일일 최대 거래 횟수: {self.max_trading_count}회 (현재 {self.daily_trading_count}회 사용)
            - 위험 성향: {self.risk_level}
            - 관심 코인: {', '.join(self.target_coins)}
            
            # 현재 포트폴리오
            {portfolio_str}
            
            # 현재 시장 상황
            {market_info_str}
            
            # 최근 거래 내역
            {recent_trades_str}
            
            # 거래 지침
            1. 현재 시장 상황을 분석하여 매수 또는 매도 결정을 내리세요.
            2. 각 결정에 대한 이유를 명확히 설명하세요.
            3. 매수/매도할 코인과 금액을 구체적으로 지정하세요.
            4. 위험 성향에 맞는 결정을 내리세요 (중립적: 균형있는 투자, 공격적: 고위험 고수익, 보수적: 안정성 중시)
            
            # 거래 도구 사용법
            - 매수하려면 buy_coin 도구를 사용하세요. 티커, 주문 유형(market 또는 limit), 금액, 지정가 가격을 지정해야 합니다.
            - 매도하려면 sell_coin 도구를 사용하세요. 티커, 주문 유형(market 또는 limit), 수량(또는 "all"), 지정가 가격을 지정해야 합니다.
            
            # 중요 사항
            - 일일 최대 거래 횟수가 제한되어 있으므로, 확실한 기회에만 거래하세요.
            - 매수 주문은 자금의 100%를 사용하지 말고 일부만 사용하는 것이 좋습니다.
            - 매도할 코인이 있는 경우에만 매도하세요.
            
            분석 결과에 따라 거래 도구를 직접 호출하여 거래를 실행하세요. 거래를 하지 않기로 판단하는 경우 그 이유를 설명해주세요.
            """,
            model=get_model_name(self.model_options),
            tools=[self.buy_coin, self.sell_coin]
        )
        return agent
    
    def get_portfolio(self):
        """현재 포트폴리오 정보 가져오기"""
        try:
            portfolio = []
            
            # KRW 잔고 확인
            krw_balance = self.trade.get_balance("KRW")
            if krw_balance:
                portfolio.append({
                    "ticker": "KRW",
                    "amount": krw_balance,
                    "value": krw_balance
                })
            
            # 코인별 잔고 확인
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
            self.log(f"포트폴리오 정보 가져오기 실패: {str(e)}", "ERROR")
            return []
    
    def get_market_info(self):
        """현재 시장 정보 가져오기"""
        try:
            market_info = {}
            
            for coin in self.target_coins:
                ticker = f"KRW-{coin}"
                
                # 현재가 확인
                current_price = self.trade.get_current_price(ticker)
                
                # 24시간 캔들 데이터
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
            self.log(f"시장 정보 가져오기 실패: {str(e)}", "ERROR")
            return {}
    
    async def get_trading_decision(self):
        """LLM에게 거래 결정 요청"""
        try:
            agent = self.create_agent()
            if not agent:
                return None
            
            prompt = "현재 시장 상황과 포트폴리오를 분석하여 매수 또는 매도 결정을 내리고, 필요하다면 거래 도구를 직접 사용하여 거래를 실행해주세요."
            
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
            self.log(f"거래 결정 요청 실패: {str(e)}", "ERROR")
            return None
    
    async def check_and_trade(self):
        """시장 분석 및 거래 실행"""
        try:
            self.status = "분석 중..."
            self.last_check_time = datetime.now()
            self.next_check_time = self.last_check_time + timedelta(minutes=self.interval_minutes)
            
            self.log("시장 분석 및 거래 결정 시작", "INFO")
            
            # LLM에게 거래 결정 요청
            decision_text = await self.get_trading_decision()
            
            if not decision_text:
                self.log("거래 결정을 가져오지 못했습니다.", "WARNING")
                self.status = "분석 실패"
                return
            
            # 거래 실행 결과 저장
            self.log(f"거래 결정 결과: {decision_text[:100]}...", "INFO")
            self.status = "대기 중"
            
            self.log(f"거래 사이클 완료", "INFO")
            
        except Exception as e:
            self.log(f"거래 사이클 중 오류 발생: {str(e)}", "ERROR")
            self.status = "오류 발생"
    
    async def run_loop(self):
        """주기적으로 거래 결정을 내리는 메인 루프"""
        self.log("자동 거래 루프 시작", "INFO")
        
        while self.is_running:
            try:
                await self.check_and_trade()
                
                # 다음 체크 시간까지 대기
                wait_seconds = self.interval_minutes * 60
                self.log(f"{wait_seconds}초 후 다음 분석 예정", "INFO")
                
                # 비동기 대기 (작은 간격으로 나누어 취소 가능하게)
                wait_chunk = 5  # 5초 단위로 체크
                for _ in range(wait_seconds // wait_chunk):
                    if not self.is_running:
                        break
                    await asyncio.sleep(wait_chunk)
                
                # 남은 시간 대기
                if self.is_running and wait_seconds % wait_chunk > 0:
                    await asyncio.sleep(wait_seconds % wait_chunk)
                    
            except Exception as e:
                self.log(f"자동 거래 루프 오류: {str(e)}", "ERROR")
                await asyncio.sleep(60)  # 오류 발생 시 1분 대기 후 재시도
    
    def start(self):
        """자동 거래 시작"""
        if self.is_running:
            return False
        
        if not self.access_key or not self.secret_key:
            self.log("Upbit API 키가 설정되지 않았습니다.", "ERROR")
            return False
        
        if not self.openai_key:
            self.log("OpenAI API 키가 설정되지 않았습니다.", "ERROR")
            return False
        
        # 전체 시장 상태 확인
        market_all = self.trade.get_market_all()
        if not market_all:
            self.log("시장 정보를 가져오지 못했습니다. API 키를 확인하세요.", "ERROR")
            return False
        
        self.is_running = True
        self.status = "시작됨"
        self.log("자동 거래 시작", "INFO")
        
        # 비동기 루프 실행
        async def start_loop():
            await self.run_loop()
        
        # 새 스레드에서 이벤트 루프 실행
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_loop())
        
        self.thread = threading.Thread(target=run_async_loop)
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def stop(self):
        """자동 거래 중지"""
        if not self.is_running:
            return False
        
        self.is_running = False
        self.status = "중지됨"
        self.log("자동 거래 중지", "INFO")
        
        if self.thread and self.thread.is_alive():
            # 스레드 종료 대기 (최대 10초)
            self.thread.join(timeout=10)
        
        self.thread = None
        return True
    
    def get_status(self):
        """현재 상태 정보 반환"""
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
        """설정 업데이트"""
        restart_required = False
        
        # 설정 변경
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
        """거래 설정 업데이트"""
        if interval_minutes is not None:
            self.interval_minutes = interval_minutes
            self.log(f"분석 간격이 {interval_minutes}분으로 설정되었습니다.", "INFO")
            
        if max_investment is not None:
            self.max_investment = max_investment
            self.log(f"최대 투자 금액이 {max_investment:,}원으로 설정되었습니다.", "INFO")
            
        if max_trading_count is not None:
            self.max_trading_count = max_trading_count
            self.log(f"일일 최대 거래 횟수가 {max_trading_count}회로 설정되었습니다.", "INFO")
            
        return True

    def set_trade_callback(self, callback_func):
        """거래 발생 시 호출할 콜백 함수 설정"""
        self.trade_callback = callback_func
        self.log(f"거래 콜백 함수가 설정되었습니다.", "INFO")
        
    def notify_trade(self, trade_info):
        """거래 발생 시 콜백 함수 호출"""
        if self.trade_callback:
            try:
                self.trade_callback(trade_info)
                self.log(f"거래 알림이 전송되었습니다: {trade_info.get('timestamp')} {trade_info.get('action')} {trade_info.get('ticker')}", "INFO")
            except Exception as e:
                self.log(f"거래 알림 전송 중 오류 발생: {str(e)}", "ERROR") 
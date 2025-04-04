import streamlit as st
import asyncio
import uuid
import threading
import time
import json
import os
from datetime import datetime, timedelta

from model.open_ai_agent import stream_openai_response
from tools.auto_trader.auto_trader import AutoTrader

def perform_periodic_task(work_freq, time_str):
    """주기적으로 자동 대화를 생성하는 함수"""
    # 자동 생성할 메시지 (시간에 따라 다양한 메시지 생성 가능)
    auto_messages = f"""
    Based on user's request, auto think is called. ({time_str} has passed, period of {work_freq} seconds)

    1. Evaluate current Bitcoin price trends and market sentiment
    2. For any Bitcoin holdings in our portfolio, determine if we should HOLD or SELL
    3. Identify potential buying opportunities for Bitcoin if market conditions are favorable
    4. Scan for other promising cryptocurrencies that match our risk profile
    5. Execute optimal buy/sell decisions to maximize returns

    Please provide a comprehensive analysis with clear recommendations and execute trades if appropriate.
    """
    
    
    return auto_messages


def show_sidebar():
    st.title("암호화폐 거래 AI Agent")
    chat_tab, chat_settings_tab = st.tabs(["채팅", "Agent 설정"])

    # 세션 상태에 Agent 상태 변수 초기화
    if 'agent_run_count' not in st.session_state:
        st.session_state.agent_run_count = 0

    # Agent 활성화 상태 추가
    if 'agent_active' not in st.session_state:
        st.session_state.agent_active = False
        
    # agent_start_time 세션 상태 초기화 추가
    if 'agent_start_time' not in st.session_state:
        st.session_state.agent_start_time = None
        
    # 마지막 작업 실행 시간 세션 상태 추가
    if 'last_work_time' not in st.session_state:
        st.session_state.last_work_time = 0
        
    # 세션 상태 초기화 부분에 conversation_id 추가
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"
    
    # 세션 상태에 Agent 상태 변수 초기화 부분에 다음 추가
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 투자에 관해 무엇을 도와드릴까요?"}]

        # 세션 상태에 reboot_frequency 값 추가
    if 'reboot_frequency' not in st.session_state:
        st.session_state.reboot_frequency = "50"  # 기본값
    
    # Agent 작업 시간 파일 경로
    agent_time_file = "data/agent_work_time.json"
    
    # 디렉토리 확인 및 생성
    os.makedirs("data", exist_ok=True)
    
    # 토글 버튼 클릭 핸들러 함수
    def toggle_agent_state():
        # 현재 상태 반전
        new_active_state = not st.session_state.agent_active
        st.session_state.agent_active = new_active_state
        
        if new_active_state:
            # Agent 시작
            st.session_state.agent_start_time = time.time()
            st.session_state.last_work_time = 0
        else:
            # Agent 종료
            st.session_state.agent_start_time = None
            st.session_state.agent_run_count = 0
            st.session_state.last_work_time = 0
            st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 투자에 관해 무엇을 도와드릴까요?"}]
            st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"

    with chat_tab:
        agent_status_col1, agent_status_col2 = st.columns(2)
        with agent_status_col1:
            st.markdown(
            f"""
                Agent 작동 횟수 :primary-background[**{st.session_state.agent_run_count}회**]
                
            """
            )
        with agent_status_col2:
            # 실시간으로 업데이트되는 시간 표시
            runtime_placeholder = st.empty()
            if st.session_state.agent_start_time:
                elapsed_seconds = int(time.time() - st.session_state.agent_start_time)
                minutes, seconds = divmod(elapsed_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                
                # 필요한 단위만 표시
                time_parts = []
                if days > 0:
                    time_parts.append(f"{days}일")
                if hours > 0 or days > 0:  # 일이 있으면 시간도 표시
                    time_parts.append(f"{hours}시간")
                if minutes > 0 or hours > 0 or days > 0:  # 시간이 있으면 분도 표시
                    time_parts.append(f"{minutes}분")
                if seconds > 0 or not time_parts:  # 항상 초는 표시 (다른 단위가 없으면)
                    time_parts.append(f"{seconds}초")
                    
                time_str = " ".join(time_parts)
            else:
                time_str = "0초"
                
            runtime_placeholder.markdown(
            f"""
                자동 거래 작동 시간 :primary-background[**{time_str}**]
            """
            )
        chat_container = st.container(height=650, border=True)
        
        # 사용자 입력 처리 (채팅 컨테이너 아래에 배치)
        user_prompt = st.chat_input(
            placeholder="어떻게 투자할까요?",
            accept_file=False,
            file_type=None
        )

        # 채팅 기록 채우기 
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
            if user_prompt:
                st.session_state.agent_run_count += 1
                
                # 카운트 증가 후 바로 재부팅 조건 검사
                try:
                    reboot_freq = int(st.session_state.reboot_frequency)
                    if st.session_state.agent_run_count >= reboot_freq and st.session_state.agent_active:
                        st.session_state.agent_run_count = 0
                        st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 투자에 관해 무엇을 도와드릴까요?"}]
                        st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"
                        st.success(f"Agent가 {reboot_freq}회 작동 후 자동으로 재부팅되었습니다.")
                        st.rerun()
                except ValueError:
                    pass
                
                user_prompt_text = user_prompt
                st.session_state.messages.append({"role": "user", "content": user_prompt_text})
                
                # 스트리밍 방식으로 응답 생성 및 표시
                with chat_container:
                    with st.chat_message("user"):
                        st.write(user_prompt_text)
                        
                    with st.chat_message("assistant"):
                        response_placeholder = st.empty()
                        # 스트리밍 응답 처리
                        # 이벤트 루프 생성 및 관리 방식 변경
                        full_response = ""
                        sent_data = f"입력: {user_prompt_text[:50]}..., 모델: {st.session_state.model_options}"
                        print(f"요청 데이터: {sent_data}")

                        try:
                            # 기존 이벤트 루프 가져오기 시도
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                # 이벤트 루프가 없으면 새로 생성
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            # 비동기 코루틴 함수
                            async def process_chunks():
                                nonlocal full_response
                                full_response = ""
                                try:
                                    async for chunk in stream_openai_response(
                                        user_prompt_text,
                                        st.session_state.model_options,
                                        st.session_state.conversation_id
                                    ):
                                        print(f"청크 수신: {len(chunk)} 바이트")
                                        full_response += chunk
                                        response_placeholder.markdown(full_response + "▌")
                                    
                                    response_placeholder.markdown(full_response)
                                    return full_response
                                except Exception as e:
                                    error_msg = f"응답 생성 중 오류: {str(e)}"
                                    print(error_msg)
                                    response_placeholder.markdown(error_msg)
                                    return error_msg
                            
                            # 기존 루프에서 실행하거나 새 루프에서 실행
                            if loop.is_running():
                                print("기존 이벤트 루프 사용 중")
                                task = asyncio.create_task(process_chunks())
                                full_response = st.session_state.get("_temp_response", "")
                                st.session_state["_temp_task"] = task
                            else:
                                print("새 이벤트 루프 실행")
                                full_response = loop.run_until_complete(
                                    asyncio.wait_for(process_chunks(), timeout=60)
                                )
                            
                            print(f"응답 완료: {len(full_response)} 자")
                            
                        except asyncio.TimeoutError:
                            full_response = "응답 생성 시간이 초과되었습니다. 다시 시도해주세요."
                            response_placeholder.markdown(full_response)
                            print("타임아웃 발생")
                        except Exception as e:
                            full_response = f"오류 발생: {str(e)}"
                            response_placeholder.markdown(full_response)
                            print(f"예외 발생: {str(e)}")

                        # 응답 기록에 저장
                        st.session_state.messages.append({"role": "assistant", "content": full_response})

    with chat_settings_tab:
            
        with st.expander("Agent 설정", expanded=True):

            

            # 토글 버튼 텍스트 설정
            button_text = "자동 거래 Agent 종료 및 초기화" if st.session_state.agent_active else "자동 거래 Agent 시작"
            
            # 콜백 방식으로 버튼 생성 
            toggle_button = st.button(
                button_text, 
                on_click=toggle_agent_state,
                use_container_width=True
            )
            
            # 버튼 클릭 후 성공 메시지 표시
            if toggle_button:
                message = "자동 거래 Agent가 종료되었습니다." if not st.session_state.agent_active else "자동 거래 Agent가 시작되었습니다."
                st.success(message)
                st.rerun()
            
            agent_settings_col1, agent_settings_col2 = st.columns(2)
            with agent_settings_col1:
                reboot_frequency = st.text_input("Agent 재부팅 주기 (작동 횟수)", value=st.session_state.reboot_frequency)
            with agent_settings_col2:
                work_frequency = st.text_input("Agent 작동 주기 (초)", value="60")

            # 재부팅 주기 체크 및 LLM 초기화
            try:
                reboot_freq = int(reboot_frequency)
                if st.session_state.agent_run_count >= reboot_freq and st.session_state.agent_active:
                    st.session_state.agent_run_count = 0  # 카운터 초기화
                    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 투자에 관해 무엇을 도와드릴까요?"}]  # 채팅 기록 초기화
                    st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"  # 대화 ID 초기화
                    st.success(f"Agent가 {reboot_freq}회 작동 후 자동으로 재부팅되었습니다.")
                    st.rerun()
            except ValueError:
                st.error("재부팅 주기는 숫자로 입력해주세요.")

            # 주기적 작업 실행 (Agent가 활성화된 경우)
            if st.session_state.agent_active:
                try:
                    # 작업 주기 가져오기
                    work_freq = int(work_frequency)
                    current_time = time.time()
                    elapsed_time = int(current_time - st.session_state.agent_start_time)
                    
                    # 디버깅을 위한 시간 출력
                    print(f"현재 시간: {datetime.now()}, 경과 시간: {elapsed_time}초, 마지막 작업: {st.session_state.last_work_time}초")
                    
                    # 주기적 실행 부분에서:
                    if elapsed_time > 0 and elapsed_time % work_freq == 0 and st.session_state.last_work_time != elapsed_time:
                        print(f"주기 실행 시작: {elapsed_time}초")
                        # 풍선 효과 표시
                        st.balloons()  
                        
                        # 자동 대화 생성
                        auto_message = perform_periodic_task(work_freq, time_str)
                        st.success(f"자동 거래 Agent가 작동된지 {time_str}가 되어 자동으로 질문합니다.")
                        
                        # 에이전트 실행 횟수 증가
                        st.session_state.agent_run_count += 1
                        
                        # 카운트 증가 후 바로 재부팅 조건 검사
                        try:
                            reboot_freq = int(reboot_frequency)
                            if st.session_state.agent_run_count >= reboot_freq and st.session_state.agent_active:
                                st.session_state.agent_run_count = 0  # 카운터 초기화
                                st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 투자에 관해 무엇을 도와드릴까요?"}]  # 채팅 기록 초기화
                                st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"  # 대화 ID 초기화
                                st.success(f"Agent가 {reboot_freq}회 작동 후 자동으로 재부팅되었습니다.")
                                st.rerun()
                        except ValueError:
                            pass
                        
                        # 채팅 기록에 사용자 메시지 추가 (올바른 역할로 수정)
                        st.session_state.messages.append({"role": "user", "content": auto_message})
                        
                        # 채팅창에 바로 표시
                        with chat_container:
                            with st.chat_message("user"):
                                st.write(auto_message)
                            
                            with st.chat_message("assistant"):
                                progress_placeholder = st.empty()
                                progress_placeholder.markdown("응답 생성 중...")
                                
                                try:
                                    # AI 응답 생성
                                    print("AI 응답 생성 시작")
                                    
                                    full_response = ""
                                    
                                    # 메인 스레드에서 완전히 처리 (스레드 사용 안 함)
                                    try:
                                        loop = asyncio.get_event_loop()
                                    except RuntimeError:
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                    
                                    async def get_full_response():
                                        nonlocal full_response
                                        try:
                                            async for chunk in stream_openai_response(
                                                auto_message,
                                                st.session_state.model_options,
                                                st.session_state.conversation_id
                                            ):
                                                full_response += chunk
                                                progress_placeholder.markdown(full_response + "▌")
                                            
                                            progress_placeholder.markdown(full_response)
                                            return full_response
                                        except Exception as e:
                                            error_msg = f"응답 생성 중 오류: {str(e)}"
                                            print(error_msg)
                                            progress_placeholder.markdown(error_msg)
                                            return error_msg
                                    
                                    # 동기적으로 비동기 함수 실행
                                    if loop.is_running():
                                        print("기존 이벤트 루프 사용 중")
                                        task = asyncio.create_task(get_full_response())
                                        st.session_state["_temp_task"] = task
                                    else:
                                        print("새 이벤트 루프 실행")
                                        full_response = loop.run_until_complete(
                                            asyncio.wait_for(get_full_response(), timeout=60)
                                        )
                                    
                                    print(f"응답 완료: {len(full_response)} 자")
                                    
                                    # 채팅 기록에 AI 응답 추가
                                    if full_response:
                                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                                    
                                except Exception as e:
                                    error_msg = f"자동 응답 생성 중 오류 발생: {str(e)}"
                                    print(f"오류 발생: {error_msg}")
                                    progress_placeholder.markdown(error_msg)
                                    st.error(error_msg)
                        
                        # 마지막 실행 시간 업데이트
                        st.session_state.last_work_time = elapsed_time
                        print(f"주기 실행 완료: 마지막 작업 시간 = {st.session_state.last_work_time}초")
                        
                        # 짧은 대기 시간 추가 (UI 표시를 위해)
                        time.sleep(0.5)
                except (ValueError, TypeError) as e:
                    print(f"작업 주기 처리 오류: {str(e)}")

            st.session_state.model_options = st.selectbox("LLM 모델 선택", ("gpt 4o", "gpt 4o mini"))


        with st.expander("사용자 요구사항", expanded=True):
            user_requirement = st.text_area("사용자 맞춤 지시", value="최대한 짧은 시간 안에 큰 수익을 얻고 싶어. 가만히 있지 말고 공격적으로 가능하다면 매번 매수, 매도를 해줘.")
            st.session_state['user_requirement'] = user_requirement

            # 위험 성향 선택 시 세션 상태에 저장
            risk_style = st.select_slider(
                "위험 성향",
                options=["보수적", "중립적", "공격적"],
                value="공격적",
                key="sidebar_risk_style"
            )
            st.session_state['risk_style'] = risk_style

            # 위험 성향 선택 시 세션 상태에 저장
            period_style = st.select_slider(
                "기간 성향",
                options=["단기", "스윙", "장기"],
                value="단기",
                key="sidebar_period_style"
            )
            st.session_state['period_style'] = period_style

        # 설정 적용 버튼
        if st.button("설정 적용하기", use_container_width=True, type="primary", key="apply_settings"):
            st.success("설정이 적용되었습니다.")

    # 자동 갱신
    if st.session_state.agent_active:
        time.sleep(1)
        st.rerun()
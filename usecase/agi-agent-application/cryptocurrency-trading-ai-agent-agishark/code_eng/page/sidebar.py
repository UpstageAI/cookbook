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
    """Function that periodically generates automated dialogue"""
    # Automated messages (can generate various messages depending on time)
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
    st.title("Cryptocurrency Trading AI Agent")
    chat_tab, chat_settings_tab = st.tabs(["Chat", "Agent Settings"])

    # Initialize Agent status variables in session state
    if 'agent_run_count' not in st.session_state:
        st.session_state.agent_run_count = 0

    # Add Agent activation status
    if 'agent_active' not in st.session_state:
        st.session_state.agent_active = False
        
    # Initialize agent_start_time session state
    if 'agent_start_time' not in st.session_state:
        st.session_state.agent_start_time = None
        
    # Add last work execution time session state
    if 'last_work_time' not in st.session_state:
        st.session_state.last_work_time = 0
        
    # Add conversation_id to session state initialization
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"
    
    # Initialize Agent status variables in session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your investment?"}]

    # Add reboot_frequency value to session state
    if 'reboot_frequency' not in st.session_state:
        st.session_state.reboot_frequency = "50"  # Default value
    
    # Agent work time file path
    agent_time_file = "data/agent_work_time.json"
    
    # Check and create directory
    os.makedirs("data", exist_ok=True)
    
    # Toggle button click handler function
    def toggle_agent_state():
        # Invert current state
        new_active_state = not st.session_state.agent_active
        st.session_state.agent_active = new_active_state
        
        if new_active_state:
            # Start Agent
            st.session_state.agent_start_time = time.time()
            st.session_state.last_work_time = 0
        else:
            # Stop Agent
            st.session_state.agent_start_time = None
            st.session_state.agent_run_count = 0
            st.session_state.last_work_time = 0
            st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your investment?"}]
            st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"

    with chat_tab:
        agent_status_col1, agent_status_col2 = st.columns(2)
        with agent_status_col1:
            st.markdown(
            f"""
                Agent Operation Count: :primary-background[**{st.session_state.agent_run_count} times**]
                
            """
            )
        with agent_status_col2:
            # Real-time updated time display
            runtime_placeholder = st.empty()
            if st.session_state.agent_start_time:
                elapsed_seconds = int(time.time() - st.session_state.agent_start_time)
                minutes, seconds = divmod(elapsed_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                
                # Show only necessary units
                time_parts = []
                if days > 0:
                    time_parts.append(f"{days} days")
                if hours > 0 or days > 0:  # If there are days, show hours too
                    time_parts.append(f"{hours} hours")
                if minutes > 0 or hours > 0 or days > 0:  # If there are hours, show minutes too
                    time_parts.append(f"{minutes} minutes")
                if seconds > 0 or not time_parts:  # Always show seconds (if no other units)
                    time_parts.append(f"{seconds} seconds")
                    
                time_str = " ".join(time_parts)
            else:
                time_str = "0 seconds"
                
            runtime_placeholder.markdown(
            f"""
                Auto Trading Runtime: :primary-background[**{time_str}**]
            """
            )
        chat_container = st.container(height=650, border=True)
        
        # Process user input (placed below chat container)
        user_prompt = st.chat_input(
            placeholder="How should I invest?",
            accept_file=False,
            file_type=None
        )

        # Fill chat history
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
            if user_prompt:
                st.session_state.agent_run_count += 1
                
                # Check reboot condition immediately after count increase
                try:
                    reboot_freq = int(st.session_state.reboot_frequency)
                    if st.session_state.agent_run_count >= reboot_freq and st.session_state.agent_active:
                        st.session_state.agent_run_count = 0
                        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your investment?"}]
                        st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"
                        st.success(f"Agent has been automatically rebooted after {reboot_freq} operations.")
                        st.rerun()
                except ValueError:
                    pass
                
                user_prompt_text = user_prompt
                st.session_state.messages.append({"role": "user", "content": user_prompt_text})
                
                # Generate and display response in streaming mode
                with chat_container:
                    with st.chat_message("user"):
                        st.write(user_prompt_text)
                        
                    with st.chat_message("assistant"):
                        response_placeholder = st.empty()
                        # Process streaming response
                        # Changed event loop creation and management method
                        full_response = ""
                        sent_data = f"Input: {user_prompt_text[:50]}..., Model: {st.session_state.model_options}"
                        print(f"Request data: {sent_data}")

                        try:
                            # Try to get existing event loop
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                # Create new loop if none exists
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            # Async coroutine function
                            async def process_chunks():
                                nonlocal full_response
                                full_response = ""
                                try:
                                    async for chunk in stream_openai_response(
                                        user_prompt_text,
                                        st.session_state.model_options,
                                        st.session_state.conversation_id
                                    ):
                                        print(f"Chunk received: {len(chunk)} bytes")
                                        full_response += chunk
                                        response_placeholder.markdown(full_response + "▌")
                                    
                                    response_placeholder.markdown(full_response)
                                    return full_response
                                except Exception as e:
                                    error_msg = f"Error during response generation: {str(e)}"
                                    print(error_msg)
                                    response_placeholder.markdown(error_msg)
                                    return error_msg
                            
                            # Run in existing loop or new loop
                            if loop.is_running():
                                print("Using existing event loop")
                                task = asyncio.create_task(process_chunks())
                                full_response = st.session_state.get("_temp_response", "")
                                st.session_state["_temp_task"] = task
                            else:
                                print("Running new event loop")
                                full_response = loop.run_until_complete(
                                    asyncio.wait_for(process_chunks(), timeout=60)
                                )
                            
                            print(f"Response complete: {len(full_response)} characters")
                            
                        except asyncio.TimeoutError:
                            full_response = "Response generation timed out. Please try again."
                            response_placeholder.markdown(full_response)
                            print("Timeout occurred")
                        except Exception as e:
                            full_response = f"Error occurred: {str(e)}"
                            response_placeholder.markdown(full_response)
                            print(f"Exception occurred: {str(e)}")

                        # Save response to history
                        st.session_state.messages.append({"role": "assistant", "content": full_response})

    with chat_settings_tab:
            
        with st.expander("Agent Settings", expanded=True):

            

            # Set toggle button text
            button_text = "Stop Auto Trading Agent and Reset" if st.session_state.agent_active else "Start Auto Trading Agent"
            
            # Create button with callback
            toggle_button = st.button(
                button_text, 
                on_click=toggle_agent_state,
                use_container_width=True
            )
            
            # Display success message after button click
            if toggle_button:
                message = "Auto Trading Agent has been stopped." if not st.session_state.agent_active else "Auto Trading Agent has been started."
                st.success(message)
                st.rerun()
            
            agent_settings_col1, agent_settings_col2 = st.columns(2)
            with agent_settings_col1:
                reboot_frequency = st.text_input("Agent Reboot Frequency (count)", value=st.session_state.reboot_frequency)
            with agent_settings_col2:
                work_frequency = st.text_input("Agent Operation Interval (seconds)", value="60")

            # Check reboot frequency and initialize LLM
            try:
                reboot_freq = int(reboot_frequency)
                if st.session_state.agent_run_count >= reboot_freq and st.session_state.agent_active:
                    st.session_state.agent_run_count = 0  # Reset counter
                    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your investment?"}]  # Reset chat history
                    st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"  # Reset conversation ID
                    st.success(f"Agent has been automatically rebooted after {reboot_freq} operations.")
                    st.rerun()
            except ValueError:
                st.error("Please enter a numeric value for reboot frequency.")

            # Execute periodic tasks (if Agent is active)
            if st.session_state.agent_active:
                try:
                    # Get work interval
                    work_freq = int(work_frequency)
                    current_time = time.time()
                    elapsed_time = int(current_time - st.session_state.agent_start_time)
                    
                    # Output time for debugging
                    print(f"Current time: {datetime.now()}, Elapsed time: {elapsed_time} seconds, Last task: {st.session_state.last_work_time} seconds")
                    
                    # In periodic execution part:
                    if elapsed_time > 0 and elapsed_time % work_freq == 0 and st.session_state.last_work_time != elapsed_time:
                        print(f"Interval execution started: {elapsed_time} seconds")
                        # Show balloon effect
                        st.balloons()  
                        
                        # Generate automatic dialogue
                        auto_message = perform_periodic_task(work_freq, time_str)
                        st.success(f"Auto Trading Agent has been running for {time_str} and automatically asks a question.")
                        
                        # Increase agent execution count
                        st.session_state.agent_run_count += 1
                        
                        # Check reboot condition immediately after count increase
                        try:
                            reboot_freq = int(reboot_frequency)
                            if st.session_state.agent_run_count >= reboot_freq and st.session_state.agent_active:
                                st.session_state.agent_run_count = 0  # Reset counter
                                st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your investment?"}]  # Reset chat history
                                st.session_state.conversation_id = f"conversation_{uuid.uuid4()}"  # Reset conversation ID
                                st.success(f"Agent has been automatically rebooted after {reboot_freq} operations.")
                                st.rerun()
                        except ValueError:
                            pass
                        
                        # Add user message to chat history (correct role)
                        st.session_state.messages.append({"role": "user", "content": auto_message})
                        
                        # Display directly in chat window
                        with chat_container:
                            with st.chat_message("user"):
                                st.write(auto_message)
                            
                            with st.chat_message("assistant"):
                                progress_placeholder = st.empty()
                                progress_placeholder.markdown("Generating response...")
                                
                                try:
                                    # Generate AI response
                                    print("Starting AI response generation")
                                    
                                    full_response = ""
                                    
                                    # Process completely in main thread (don't use threads)
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
                                            error_msg = f"Error during response generation: {str(e)}"
                                            print(error_msg)
                                            progress_placeholder.markdown(error_msg)
                                            return error_msg
                                    
                                    # Execute async function synchronously
                                    if loop.is_running():
                                        print("Using existing event loop")
                                        task = asyncio.create_task(get_full_response())
                                        st.session_state["_temp_task"] = task
                                    else:
                                        print("Running new event loop")
                                        full_response = loop.run_until_complete(
                                            asyncio.wait_for(get_full_response(), timeout=60)
                                        )
                                    
                                    print(f"Response complete: {len(full_response)} characters")
                                    
                                    # Add AI response to chat history
                                    if full_response:
                                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                                    
                                except Exception as e:
                                    error_msg = f"Error during automatic response generation: {str(e)}"
                                    print(f"Error occurred: {error_msg}")
                                    progress_placeholder.markdown(error_msg)
                                    st.error(error_msg)
                        
                        # Update last execution time
                        st.session_state.last_work_time = elapsed_time
                        print(f"Interval execution completed: Last task time = {st.session_state.last_work_time} seconds")
                        
                        # Add short wait time (for UI display)
                        time.sleep(0.5)
                except (ValueError, TypeError) as e:
                    print(f"Error processing work interval: {str(e)}")

            st.session_state.model_options = st.selectbox("LLM Model Selection", ("gpt 4o", "gpt 4o mini"))


        with st.expander("User Requirements", expanded=True):
            user_requirement = st.text_area("Custom Instructions", value="I want to maximize profits in the shortest time possible. Don't stay idle, be aggressive and make buy/sell trades whenever possible.")
            st.session_state['user_requirement'] = user_requirement

            # Save risk preference to session state
            risk_style = st.select_slider(
                "Risk Preference",
                options=["Conservative", "Balanced", "Aggressive"],
                value="Aggressive",
                key="sidebar_risk_style"
            )
            st.session_state['risk_style'] = risk_style

            # Save time preference to session state
            period_style = st.select_slider(
                "Time Horizon",
                options=["Short-term", "Swing", "Long-term"],
                value="Short-term",
                key="sidebar_period_style"
            )
            st.session_state['period_style'] = period_style

        # Apply settings button
        if st.button("Apply Settings", use_container_width=True, type="primary", key="apply_settings"):
            st.success("Settings have been applied.")

    # Auto refresh
    if st.session_state.agent_active:
        time.sleep(1)
        st.rerun()
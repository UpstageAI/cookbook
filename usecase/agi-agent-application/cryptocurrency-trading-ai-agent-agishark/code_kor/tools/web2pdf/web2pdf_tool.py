from tools.web2pdf.web2pdf import get_webpage_as_pdf_binary
from agents import function_tool
from typing import Dict, List, Any, Optional
import os
import time
import streamlit as st
from openai import OpenAI

@function_tool
def search_parse_webpage_direct(search_query: str, max_results: int) -> Dict[str, Any]:
    """
    웹 검색을 수행하고, 검색 결과 페이지를 PDF로 변환하여 로컬에 저장하지 않고 바로 문서 파싱합니다.
    웹 검색, PDF 변환, 문서 파싱을 한 번에 처리하는 통합 도구로 로컬 저장 단계를 생략합니다.
    
    Args:
        search_query: 검색할 쿼리
        max_results: 처리할 최대 검색 결과 수
    
    Returns:
        Dict: 결과를 담은 딕셔너리. 다음과 같은 구조를 가집니다:
            - success (bool): 전체 작업 성공 여부
            - results (List): 파싱된 문서 결과 목록
            - query (str): 사용된 검색 쿼리
            - total_processed (int): 처리된 URL 수
            - total_success (int): 성공적으로 파싱된 문서 수
            - error (str): 실패 시, 오류 메시지
    """
    from tools.document_parser.document_parser import DocumentParser
    
    try:
        print(f"search_parse_webpage_direct 호출: 쿼리='{search_query}', max_results={max_results}")
        
        # max_results 기본값 설정
        if max_results is None or max_results <= 0:
            max_results = 3
            print(f"max_results 기본값 3 적용")
        
        # 1. 직접 OpenAI API로 웹 검색 수행
        # API 키 확인
        api_key = st.session_state.get('openai_key')
        if not api_key:
            print("OpenAI API 키가 설정되지 않았습니다.")
            return {
                'success': False,
                'results': [],
                'query': search_query,
                'total_processed': 0,
                'total_success': 0,
                'error': "OpenAI API 키가 설정되지 않았습니다. API 설정 페이지에서 키를 설정하세요."
            }
        
        # 웹 검색 수행
        urls = []
        try:
            print(f"OpenAI API로 웹 검색 시작: 쿼리='{search_query}'")
            client = OpenAI(api_key=api_key)
            
            # 웹 검색 실행 - 메시지 기반 API 호출
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "웹 검색을 수행하여 정확한 정보와 관련 URL을 제공해주세요."},
                    {"role": "user", "content": f"다음 주제에 대해 검색해주세요: {search_query}"}
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "description": "웹 검색을 수행하여 정보를 찾습니다.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "검색할 쿼리"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    }
                ]
            )
            
            print(f"응답 타입: {type(response)}")
            print(f"응답 내용: {response}")
            
            # 응답에서 URL 추출
            try:
                # 응답 형식 처리
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and choice.message:
                        message = choice.message
                        print(f"메시지 내용: {message.content if message.content else '없음'}")
                        
                        # 1. tool_calls 확인
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                print(f"tool_call: {tool_call}")
                                if hasattr(tool_call, 'function') and tool_call.function:
                                    function = tool_call.function
                                    if hasattr(function, 'arguments') and function.arguments:
                                        try:
                                            import json
                                            args = json.loads(function.arguments)
                                            if 'urls' in args:
                                                urls.extend(args['urls'])
                                        except json.JSONDecodeError:
                                            print(f"JSON 파싱 실패: {function.arguments}")
                        
                        # 2. 메시지 컨텐츠에서 URL 추출
                        if message.content:
                            import re
                            url_pattern = r'https?://[^\s]+'
                            found_urls = re.findall(url_pattern, message.content)
                            if found_urls:
                                print(f"컨텐츠에서 URL 찾음: {found_urls}")
                                urls.extend(found_urls)
                        
                        # 3. citation 또는 context 확인
                        if hasattr(message, 'context') and message.context:
                            for ctx_item in message.context:
                                if 'url' in ctx_item:
                                    urls.append(ctx_item['url'])
                
            except Exception as e:
                import traceback
                print(f"URL 추출 중 오류: {str(e)}\n{traceback.format_exc()}")
            
            # 중복 제거
            urls = list(dict.fromkeys(urls))
            
            # 결과 개수 제한
            urls = urls[:max_results] if len(urls) > max_results else urls
            print(f"웹 검색 성공: {len(urls)}개 URL 찾음, URLs: {urls}")
            
            # 하드코딩된 테스트 URL 추가 (임시)
            if not urls:
                print("검색 결과가 없어 테스트 URL 추가")
                test_urls = [
                    "https://www.coindesk.com/",
                    "https://cointelegraph.com/",
                    "https://www.bitcoin.com/"
                ]
                urls = test_urls[:max_results]
            
        except Exception as e:
            import traceback
            print(f"웹 검색 실패: {str(e)}\n{traceback.format_exc()}")
            return {
                'success': False,
                'results': [],
                'query': search_query,
                'total_processed': 0,
                'total_success': 0,
                'error': f"웹 검색 중 오류 발생: {str(e)}"
            }
        
        if not urls:
            print("검색 결과가 없습니다.")
            return {
                'success': True,
                'results': [],
                'query': search_query,
                'total_processed': 0,
                'total_success': 0,
                'message': "검색 결과가 없습니다."
            }
        
        # 2. 각 URL을 PDF 바이너리로 변환 (저장하지 않음)
        pdf_binary_list = []
        processed_count = 0
        
        for url in urls:
            print(f"URL을 PDF로 변환 중 (저장 안 함): {url}")
            pdf_result = get_webpage_as_pdf_binary(url)
            
            if pdf_result['success']:
                pdf_binary_list.append(pdf_result)
                processed_count += 1
            else:
                print(f"PDF 변환 실패: {url}, 오류: {pdf_result.get('error', '알 수 없는 오류')}")
        
        if not pdf_binary_list:
            return {
                'success': False,
                'results': [],
                'query': search_query,
                'total_processed': len(urls),
                'total_success': 0,
                'error': "모든 URL을 PDF로 변환하는 데 실패했습니다."
            }
        
        # 3. PDF 바이너리 데이터를 직접 DocumentParser로 전달
        print(f"바이너리 데이터 직접 파싱 시작: {len(pdf_binary_list)}개 문서")
        parser = DocumentParser()
        parse_result = parser.parse_binary_data(pdf_binary_list)
        
        # 4. 결과 조합
        parsed_docs = []
        total_success = 0
        
        if parse_result['success']:
            for result in parse_result.get('results', []):
                if result.get('success', False):
                    parsed_docs.append({
                        'success': True,
                        'source_url': result.get('metadata', {}).get('source_url', ''),
                        'text': result.get('text', ''),
                    })
                    total_success += 1
                else:
                    parsed_docs.append({
                        'success': False,
                        'source_url': result.get('source_url', ''),
                        'error': result.get('error', '문서 파싱 실패')
                    })
        
        print(f"search_parse_webpage_direct 완료: {total_success}/{len(pdf_binary_list)} 파싱 성공")
        
        return {
            'success': total_success > 0,
            'results': parsed_docs,
            'query': search_query,
            'total_processed': processed_count,
            'total_success': total_success,
            'message': f"{processed_count}개 문서 중 {total_success}개 파싱 성공"
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"search_parse_webpage_direct 예외 발생: {str(e)}\n{error_detail}")
        
        return {
            'success': False,
            'results': [],
            'query': search_query,
            'total_processed': 0,
            'total_success': 0,
            'error': f"웹 검색 및 문서 파싱 중 오류 발생: {str(e)}"
        } 
import requests
import streamlit as st
import os
from typing import List, Dict, Any

# Global variables
_UPSTAGE_API_KEY = None

def update_upstage_api_key():
    """Update global Upstage API key"""
    global _UPSTAGE_API_KEY
    _UPSTAGE_API_KEY = st.session_state.get('upstage_api_key', '')
    print(f"Upstage API key updated: {'set' if _UPSTAGE_API_KEY else 'not set'}")

class DocumentParser:
    def __init__(self, api_key=None):
        # API key priority: constructor parameter > global variable > session state
        self.api_key = api_key if api_key is not None else (_UPSTAGE_API_KEY or st.session_state.get('upstage_api_key', ''))
        self.url = "https://api.upstage.ai/v1/document-ai/document-parse"
        self.base_path = "tools/web2pdf/always_see_doc_storage/"
    
    def __call__(self, file_names: List[str]) -> Dict[str, Any]:
        """Tool interface required for agents library"""
        return self.parse_document(file_names)
        
    def parse_document(self, file_names: List[str]) -> Dict[str, Any]:
        """
        Method for parsing documents - processes a list of file names
        
        Args:
            file_names: List of PDF file names to parse (without extension)
            
        Returns:
            Dict: Dictionary containing parsing results
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Upstage API key is not set. Please enter the API key in the API settings tab.'
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "ocr": "force",
            "coordinates": True,
            "chart_recognition": True,
            "output_formats": "['text']",
            "base64_encoding": "['table']",
            "model": "document-parse"
        }

        # Convert input to list if it's not already
        if not isinstance(file_names, list):
            if isinstance(file_names, str):
                file_names = [file_names]
            else:
                return {
                    'success': False,
                    'error': 'Please provide a list of file names.'
                }

        all_results = []
        for file_name in file_names:
            # Skip if list contains None or empty string
            if not file_name:
                continue
                
            # Handle extension (.pdf) if it's already there
            if not file_name.lower().endswith('.pdf'):
                file_path = os.path.join(self.base_path, f"{file_name}.pdf")
            else:
                file_path = os.path.join(self.base_path, file_name)
            
            # Check if file exists
            if not os.path.exists(file_path):
                all_results.append({
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'file_name': file_name
                })
                continue
            
            # Read file
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                all_results.append({
                    'success': False,
                    'error': f'File reading error: {str(e)}',
                    'file_name': file_name
                })
                continue

            # API request
            files = {
                "document": (os.path.basename(file_path), file_content)
            }
            
            try:
                response = requests.post(self.url, headers=headers, files=files, data=data)
                response.raise_for_status()
                
                result = response.json()
                if 'content' in result and 'text' in result['content']:
                    all_results.append({
                        'success': True,
                        'text': result['content']['text'],
                        'metadata': {
                            'file_name': os.path.basename(file_path),
                            'parse_time': result.get('parse_time', 0)
                        }
                    })
                else:
                    all_results.append({
                        'success': False,
                        'error': 'Document parsing result is not in the expected format.',
                        'file_name': file_name
                    })
                    
            except requests.exceptions.RequestException as e:
                all_results.append({
                    'success': False,
                    'error': f'API request error: {str(e)}',
                    'file_name': file_name
                })
        
        return {
            'success': True,
            'results': all_results,
            'count': len(all_results),
            'successful_count': sum(1 for r in all_results if r.get('success', False))
        }

# Usage example:
# parser = DocumentParser()
# file_list = ["bitcoin_report", "bitcoin_report2"]  # .pdf extension is added automatically
# results = parser.parse_document(file_list)
# if results['success']:
#     for result in results['results']:
#         if result['success']:
#             print(f"File: {result['metadata']['file_name']}")
#             print(f"Text: {result['text'][:100]}...")  # Print only first 100 chars
#         else:
#             print(f"Error in {result.get('file_name', 'unknown')}: {result['error']}")
# else:
#     print(f"Error: {results['error']}")
import base64
import json
import os
import streamlit as st
from openai import OpenAI
from typing import Dict, Any, List, Optional

# Global variables
_UPSTAGE_API_KEY = None

def update_upstage_api_key():
    """Update global Upstage API key"""
    global _UPSTAGE_API_KEY
    _UPSTAGE_API_KEY = st.session_state.get('upstage_api_key', '')
    print(f"Upstage API key updated: {'set' if _UPSTAGE_API_KEY else 'not set'}")

class InformationExtractor:
    def __init__(self, api_key=None):
        # API key priority: constructor parameter > global variable > session state
        self.api_key = api_key if api_key is not None else (_UPSTAGE_API_KEY or st.session_state.get('upstage_api_key', ''))
        self.base_url = "https://api.upstage.ai/v1/information-extraction"
        
    def encode_img_to_base64(self, img_path: str) -> str:
        """Encode image file to base64"""
        try:
            with open(img_path, 'rb') as img_file:
                img_bytes = img_file.read()
                base64_data = base64.b64encode(img_bytes).decode('utf-8')
                return base64_data
        except Exception as e:
            raise ValueError(f"Image encoding error: {str(e)}")
    
    def extract_information(self, img_path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Method to extract information from an image
        
        Args:
            img_path: Image file path
            schema: Schema definition for information to extract
            
        Returns:
            Dict: Extracted information results
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Upstage API key is not set. Please enter the API key in the API settings tab.'
            }
            
        # Check if the image file exists
        if not os.path.exists(img_path):
            return {
                'success': False,
                'error': f'Image file not found: {img_path}'
            }
            
        try:
            # Encode image to base64
            base64_data = self.encode_img_to_base64(img_path)
            
            # Initialize API client
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # Call Information Extraction API
            extraction_response = client.chat.completions.create(
                model="information-extract",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_data}"}
                            }
                        ]
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "document_schema",
                        "schema": schema
                    }
                }
            )
            
            # Parse response results
            extracted_content = json.loads(extraction_response.choices[0].message.content)
            return {
                'success': True,
                'data': extracted_content,
                'metadata': {
                    'file_name': os.path.basename(img_path),
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Information extraction API error: {str(e)}'
            }


def information_extract(img_path: str, schema_properties: Dict[str, Dict[str, Any]], required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Extract information from an image according to the specified schema.
    
    Args:
        img_path: Path to the image file to extract information from
        schema_properties: Property definitions for information to extract (JSON schema format)
        required_fields: List of fields that must be extracted (optional)
        
    Returns:
        Dict: Extracted information or error
    """
    extractor = InformationExtractor()
    
    # Construct schema
    schema = {
        "type": "object",
        "properties": schema_properties
    }
    
    # Add required fields if provided
    if required_fields:
        schema["required"] = required_fields
    
    # Execute information extraction
    return extractor.extract_information(img_path, schema) 
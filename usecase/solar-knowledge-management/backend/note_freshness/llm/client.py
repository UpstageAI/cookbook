"""LLM client for Upstage API interaction including Information Extraction."""

import base64
import json
import httpx
from openai import OpenAI
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..config import Config


class UpstageClient:
    """Client for interacting with Upstage Solar API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or Config.UPSTAGE_API_KEY
        self.api_base = api_base or Config.UPSTAGE_API_BASE
        self.model = model or Config.MODEL_NAME

        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is required")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _encode_file_to_base64(self, file_path: Path) -> str:
        """Encode file to base64 string."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def make_request_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
    ) -> Optional[str]:
        """Make a synchronous request to the Upstage API."""
        temperature = temperature or Config.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or Config.DEFAULT_MAX_TOKENS

        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=Config.HTTP_TIMEOUT_SYNC) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error making request: {e}")
            return None

    def extract_information(
        self, document_path: Path, schema: str
    ) -> Optional[Dict[str, Any]]:
        """Extract information from a document using Upstage Information Extraction API.

        Args:
            document_path: Path to the document file (docx)
            schema: JSON schema string defining what to extract

        Returns:
            Extracted information as dictionary or None on error
        """
        try:
            # Encode document to base64
            base64_data = self._encode_file_to_base64(document_path)

            # Create OpenAI client for Information Extraction
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.upstage.ai/v1/information-extraction",
            )

            # Parse schema string to dict
            try:
                schema_dict = json.loads(schema)
            except json.JSONDecodeError:
                print("Error: Invalid JSON schema")
                return None

            # Make extraction request
            extraction_response = client.chat.completions.create(
                model="information-extract",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:application/octet-stream;base64,{base64_data}"
                                },
                            }
                        ],
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "document_schema", "schema": schema_dict},
                },
            )

            # Parse result
            json_str = extraction_response.choices[0].message.content
            result = json.loads(json_str)
            return result

        except Exception as e:
            print(f"Error during information extraction: {e}")
            return None

    def generate_freshness_guide(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.3
    ) -> Optional[str]:
        """Generate freshness guide using Solar model.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt with context
            temperature: Lower temperature for more focused output

        Returns:
            Generated guide content or None on error
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.make_request_sync(messages, temperature=temperature)

"""LLM client for Upstage API interaction."""
import asyncio
from typing import List, Optional, Dict, Any
import httpx
from ..config import Config
from ..models import PromptTemplate


class UpstageClient:
    """Client for interacting with Upstage Solar API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the Upstage client.

        Args:
            api_key: Upstage API key (defaults to Config.UPSTAGE_API_KEY)
            api_base: API base URL (defaults to Config.UPSTAGE_API_BASE)
            model: Model name (defaults to Config.MODEL_NAME)
        """
        self.api_key = api_key or Config.UPSTAGE_API_KEY
        self.api_base = api_base or Config.UPSTAGE_API_BASE
        self.model = model or Config.MODEL_NAME

        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY is required")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float = Config.DEFAULT_TEMPERATURE,
        max_tokens: int = Config.DEFAULT_MAX_TOKENS
    ) -> Optional[str]:
        """Make an async request to the Upstage API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None on error
        """
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=Config.HTTP_TIMEOUT_ASYNC) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return data['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error making request: {e}")
            return None

    def make_request_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: float = Config.DEFAULT_TEMPERATURE,
        max_tokens: int = Config.DEFAULT_MAX_TOKENS
    ) -> Optional[str]:
        """Make a synchronous request to the Upstage API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None on error
        """
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            with httpx.Client(timeout=Config.HTTP_TIMEOUT_SYNC) as client:
                response = client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return data['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"Error making request: {e}")
            return None

    async def generate_with_template(
        self,
        template: PromptTemplate,
        user_vars: Dict[str, Any],
        temperature: float = Config.DEFAULT_TEMPERATURE,
        max_tokens: int = Config.DEFAULT_MAX_TOKENS
    ) -> Optional[str]:
        """Generate text using a prompt template.

        Args:
            template: PromptTemplate object
            user_vars: Variables to format the user prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None on error
        """
        messages = [
            {"role": "system", "content": template.system_prompt},
            {"role": "user", "content": template.format_user_prompt(**user_vars)}
        ]

        return await self._make_request(messages, temperature, max_tokens)

    def generate_with_template_sync(
        self,
        template: PromptTemplate,
        user_vars: Dict[str, Any],
        temperature: float = Config.DEFAULT_TEMPERATURE,
        max_tokens: int = Config.DEFAULT_MAX_TOKENS
    ) -> Optional[str]:
        """Generate text using a prompt template (synchronous).

        Args:
            template: PromptTemplate object
            user_vars: Variables to format the user prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None on error
        """
        messages = [
            {"role": "system", "content": template.system_prompt},
            {"role": "user", "content": template.format_user_prompt(**user_vars)}
        ]

        return self.make_request_sync(messages, temperature, max_tokens)

    async def generate_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """Generate multiple responses in parallel.

        Args:
            requests: List of request dictionaries, each containing:
                - messages: List of message dicts
                - temperature (optional): Sampling temperature
                - max_tokens (optional): Maximum tokens to generate

        Returns:
            List of generated texts (or None for failed requests)
        """
        tasks = []
        for req in requests:
            messages = req['messages']
            temperature = req.get('temperature', Config.DEFAULT_TEMPERATURE)
            max_tokens = req.get('max_tokens', Config.DEFAULT_MAX_TOKENS)

            task = self._make_request(messages, temperature, max_tokens)
            tasks.append(task)

        return await asyncio.gather(*tasks)


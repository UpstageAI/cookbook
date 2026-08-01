"""Parsers for LLM responses."""
import json
import re
from typing import List, Optional, Dict, Any
from ..models import Topic


class ResponseParser:
    """Parser for LLM responses."""

    @staticmethod
    def parse_topics_from_json(response: str) -> List[Topic]:
        """Parse topics from JSON response.

        Expected JSON format:
        {
            "topics": [
                {
                    "topic": "Topic Name",
                    "coverage": "Brief overview",
                    "line_numbers": [1, 2, 3],
                    "keywords": ["keyword1", "keyword2"]
                }
            ]
        }

        Args:
            response: JSON string response from LLM

        Returns:
            List of Topic objects
        """
        try:
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)

            data = json.loads(response)
            topics_data = data.get('topics', [])

            topics = []
            for topic_data in topics_data:
                topic = Topic(
                    topic=topic_data.get('topic', ''),
                    coverage=topic_data.get('coverage', ''),
                    line_numbers=topic_data.get('line_numbers', []),
                    keywords=topic_data.get('keywords', [])
                )
                topics.append(topic)

            return topics
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            print(f"Error processing topics: {e}")
            return []

    @staticmethod
    def parse_line_numbers_from_json(response: str) -> List[int]:
        """Parse line numbers from JSON response.

        Expected JSON format:
        {
            "line_numbers": [1, 2, 3, 5, 7]
        }

        Args:
            response: JSON string response from LLM

        Returns:
            List of line numbers
        """
        try:
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)

            data = json.loads(response)
            return data.get('line_numbers', [])
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            print(f"Error processing line numbers: {e}")
            return []

    @staticmethod
    def parse_atomic_note_content(response: str) -> str:
        """Parse atomic note content from LLM response.

        The response should contain markdown content for the atomic note.

        Args:
            response: Markdown content from LLM

        Returns:
            Cleaned atomic note content
        """
        # Remove any markdown code blocks if the entire response is wrapped
        if response.strip().startswith('```') and response.strip().endswith('```'):
            # Remove the first and last line (markdown fences)
            lines = response.strip().split('\n')
            if len(lines) > 2:
                # Remove first line and last line
                response = '\n'.join(lines[1:-1])

        return response.strip()

    @staticmethod
    def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from a response that may contain other text.

        Args:
            response: Response text that may contain JSON

        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        # Try to find JSON in code blocks first
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing the entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None


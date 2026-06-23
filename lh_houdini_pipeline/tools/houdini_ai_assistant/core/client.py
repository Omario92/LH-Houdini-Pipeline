"""
lh_houdini_pipeline.tools.houdini_ai_assistant.core.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure Python LLM Client abstractions. Does not depend on 'hou' or 'PySide6'.
Uses 'requests' to execute raw HTTP queries, bypassing the need for external SDK packages.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional

import requests

_log = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised for any API call failure, authorization error, or malformed response."""


class LLMClient(ABC):
    """Abstract base class for all LLM clients."""

    def __init__(self, api_key: str, url: str, model: str, temperature: float = 0.2, max_tokens: int = 4096) -> None:
        self.api_key = api_key
        self.url = url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """Synchronously query the LLM and return the full text response.

        Args:
            messages: List of message dicts (e.g. [{"role": "user", "content": "..."}]).
            system_prompt: Optional system prompt to instruct the model.

        Returns:
            The complete response string.

        Raises:
            LLMError: If the request fails or is rejected.
        """
        pass

    @abstractmethod
    def chat_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        """Perform a streaming chat completion, yielding content chunks as they arrive.

        Args:
            messages: List of message dicts.
            system_prompt: Optional system prompt.

        Yields:
            Text chunks (str).

        Raises:
            LLMError: If the connection fails.
        """
        pass


class AnthropicClient(LLMClient):
    """Client wrapper for the Anthropic Messages API (Claude)."""

    def _build_request(self, messages: List[Dict[str, str]], system_prompt: Optional[str], stream: bool) -> tuple[Dict[str, str], Dict[str, Any]]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        # Clean and format messages (Anthropic doesn't allow "system" role in messages list)
        cleaned_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                # If system role is passed in messages, use it as system prompt if none is explicitly provided
                if not system_prompt:
                    system_prompt = msg.get("content", "")
                continue
            
            content = msg.get("content", "")
            image_b64 = msg.get("image_b64")
            
            if image_b64:
                content_payload: Any = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": content
                    }
                ]
            else:
                content_payload = content

            cleaned_messages.append({
                "role": role if role in ("user", "assistant") else "user",
                "content": content_payload
            })

        body: Dict[str, Any] = {
            "model": self.model,
            "messages": cleaned_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": stream
        }
        if system_prompt:
            body["system"] = system_prompt

        return headers, body

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        headers, body = self._build_request(messages, system_prompt, stream=False)
        try:
            response = requests.post(self.url, headers=headers, json=body, timeout=60)
            if response.status_code != 200:
                raise LLMError(f"Anthropic API error ({response.status_code}): {response.text}")
            
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"Anthropic request failed: {e}") from e
            raise

    def chat_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        headers, body = self._build_request(messages, system_prompt, stream=True)
        try:
            response = requests.post(self.url, headers=headers, json=body, stream=True, timeout=60)
            if response.status_code != 200:
                raise LLMError(f"Anthropic API error ({response.status_code}): {response.text}")
            
            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data:"):
                    data_payload = line_str[5:].strip()
                    if data_payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_payload)
                        chunk_type = chunk.get("type")
                        if chunk_type == "content_block_delta":
                            delta = chunk.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"Anthropic streaming failed: {e}") from e
            raise


class OpenAICompatibleClient(LLMClient):
    """Base client wrapper for OpenAI-compatible APIs (OpenAI, xAI, Ollama, LM Studio)."""

    def _build_request(self, messages: List[Dict[str, str]], system_prompt: Optional[str], stream: bool) -> tuple[Dict[str, str], Dict[str, Any]]:
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            role = msg.get("role", "user")
            # Skip duplicate system prompt if already processed
            if role == "system" and system_prompt:
                continue
            
            content = msg.get("content", "")
            image_b64 = msg.get("image_b64")
            
            if image_b64:
                content_payload: Any = [
                    {
                        "type": "text",
                        "text": content
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            else:
                content_payload = content

            formatted_messages.append({
                "role": role,
                "content": content_payload
            })

        body = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }
        return headers, body

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        headers, body = self._build_request(messages, system_prompt, stream=False)
        try:
            response = requests.post(self.url, headers=headers, json=body, timeout=60)
            if response.status_code != 200:
                raise LLMError(f"API error ({response.status_code}): {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"API request failed: {e}") from e
            raise

    def chat_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        headers, body = self._build_request(messages, system_prompt, stream=True)
        try:
            response = requests.post(self.url, headers=headers, json=body, stream=True, timeout=60)
            if response.status_code != 200:
                raise LLMError(f"API error ({response.status_code}): {response.text}")
            
            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data:"):
                    data_payload = line_str[5:].strip()
                    if data_payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_payload)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"API streaming failed: {e}") from e
            raise


class OpenAIClient(OpenAICompatibleClient):
    """Client wrapper for OpenAI API (GPT-4/GPT-5)."""
    pass


class xAIClient(OpenAICompatibleClient):
    """Client wrapper for xAI API (Grok)."""
    pass


class OllamaClient(OpenAICompatibleClient):
    """Client wrapper for Local Ollama API using OpenAI-compatibility endpoint."""
    pass


class LMStudioClient(OpenAICompatibleClient):
    """Client wrapper for Local LM Studio API using OpenAI-compatibility endpoint."""
    pass


class GeminiClient(LLMClient):
    """Client wrapper for Google Gemini API."""

    def _build_url(self, stream: bool) -> str:
        # Standard endpoint requires key as query parameter
        mode = "streamGenerateContent" if stream else "generateContent"
        # The base URL should contain {model} placeholder and be modified
        resolved_url = self.url.replace("{model}", self.model)
        if mode not in resolved_url:
            # Reconstruct model method
            resolved_url = resolved_url.replace("generateContent", mode)
        
        # Check if key is already in query param, if not append it
        if "key=" not in resolved_url:
            sep = "&" if "?" in resolved_url else "?"
            resolved_url = f"{resolved_url}{sep}key={self.api_key}"
        
        return resolved_url

    def _build_request(self, messages: List[Dict[str, str]], system_prompt: Optional[str]) -> tuple[Dict[str, str], Dict[str, Any]]:
        headers = {
            "Content-Type": "application/json"
        }

        # Convert roles: user -> user, assistant -> model
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                if not system_prompt:
                    system_prompt = msg.get("content", "")
                continue
            
            gemini_role = "user" if role == "user" else "model"
            
            parts: List[Dict[str, Any]] = [{"text": msg.get("content", "")}]
            image_b64 = msg.get("image_b64")
            if image_b64:
                parts.append({
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": image_b64
                    }
                })

            contents.append({
                "role": gemini_role,
                "parts": parts
            })

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }

        if system_prompt:
            body["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        return headers, body

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        url = self._build_url(stream=False)
        headers, body = self._build_request(messages, system_prompt)
        try:
            response = requests.post(url, headers=headers, json=body, timeout=60)
            if response.status_code != 200:
                raise LLMError(f"Gemini API error ({response.status_code}): {response.text}")
            
            data = response.json()
            # Extract text from first candidate
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return parts[0].get("text", "")
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"Gemini request failed: {e}") from e
            raise

    def chat_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        url = self._build_url(stream=True)
        headers, body = self._build_request(messages, system_prompt)
        try:
            response = requests.post(url, headers=headers, json=body, stream=True, timeout=60)
            if response.status_code != 200:
                raise LLMError(f"Gemini API error ({response.status_code}): {response.text}")
            
            # Gemini stream returns line-by-line SSE-like JSON or plain JSON array chunks
            # In streamGenerateContent, the server sends JSON blocks starting with [ and separated by commas, or plain objects
            # Let's read line by line and try parsing as JSON fragments.
            buffer = ""
            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                
                # Strip leading/trailing JSON array syntax if present (Gemini sends blocks)
                if line_str.startswith("["):
                    line_str = line_str[1:]
                if line_str.endswith("]"):
                    line_str = line_str[:-1]
                if line_str.startswith(","):
                    line_str = line_str[1:]
                
                line_str = line_str.strip()
                if not line_str:
                    continue
                
                try:
                    chunk = json.loads(line_str)
                    candidates = chunk.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            yield parts[0].get("text", "")
                except json.JSONDecodeError:
                    # Let's accumulate buffer just in case lines are split (rare but possible)
                    buffer += line_str
                    try:
                        chunk = json.loads(buffer)
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                yield parts[0].get("text", "")
                        buffer = ""  # Reset buffer on success
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"Gemini streaming failed: {e}") from e
            raise


def create_client(provider: str, api_key: str, url: str, model: str, temperature: float = 0.2, max_tokens: int = 4096) -> LLMClient:
    """Factory function to instantiate concrete client implementations based on the *provider*."""
    provider_lower = provider.lower()
    
    if provider_lower == "anthropic":
        return AnthropicClient(api_key, url, model, temperature, max_tokens)
    elif provider_lower == "openai":
        return OpenAIClient(api_key, url, model, temperature, max_tokens)
    elif provider_lower == "xai":
        return xAIClient(api_key, url, model, temperature, max_tokens)
    elif provider_lower == "gemini":
        return GeminiClient(api_key, url, model, temperature, max_tokens)
    elif provider_lower == "ollama":
        return OllamaClient(api_key, url, model, temperature, max_tokens)
    elif provider_lower == "lm_studio":
        return LMStudioClient(api_key, url, model, temperature, max_tokens)
    else:
        # Fallback to OpenAICompatible
        _log.warning(f"Unknown provider '{provider}', falling back to OpenAICompatibleClient")
        return OpenAICompatibleClient(api_key, url, model, temperature, max_tokens)

"""
lh_houdini_pipeline.tools.houdini_ai_assistant.core.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure Python LLM Client abstractions. Does not depend on 'hou' or 'PySide6'.
Uses 'requests' to execute raw HTTP queries, bypassing the need for external SDK packages.
"""

from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

import requests

_log = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised for any API call failure, authorization error, or malformed response."""


@dataclass
class ToolCall:
    """A single native function/tool call requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class AgentResponse:
    """Result of a native function-calling turn: free text and/or tool calls."""
    text: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


# ---------------------------------------------------------------------------
# Tool-schema formatters (AITool -> provider-native tool definition)
# ---------------------------------------------------------------------------

def _tools_anthropic(tools: List[Any]) -> List[Dict[str, Any]]:
    return [{"name": t.name, "description": t.description, "input_schema": t.schema} for t in tools]


def _tools_openai(tools: List[Any]) -> List[Dict[str, Any]]:
    return [{"type": "function",
             "function": {"name": t.name, "description": t.description, "parameters": t.schema}}
            for t in tools]


def _tools_gemini(tools: List[Any]) -> List[Dict[str, Any]]:
    return [{"functionDeclarations": [
        {"name": t.name, "description": t.description, "parameters": t.schema} for t in tools]}]


# ---------------------------------------------------------------------------
# Internal history -> provider message lists
# Internal roles: "user" | "assistant"(+optional tool_calls) | "tool"(result)
# ---------------------------------------------------------------------------

def _user_content_anthropic(msg: Dict[str, Any]) -> Any:
    img = msg.get("image_b64")
    text = msg.get("content", "")
    if img:
        return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
                {"type": "text", "text": text}]
    return text


def _internal_to_anthropic(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role == "user":
            out.append({"role": "user", "content": _user_content_anthropic(m)})
        elif role == "assistant":
            tcs = m.get("tool_calls")
            if tcs:
                blocks: List[Dict[str, Any]] = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in tcs:
                    blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"],
                                   "input": tc.get("arguments", {})})
                out.append({"role": "assistant", "content": blocks})
            else:
                out.append({"role": "assistant", "content": m.get("content", "")})
        elif role == "tool":
            out.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": m.get("tool_call_id", ""),
                 "content": m.get("content", "")}]})
    return out


def _internal_to_openai(messages: List[Dict[str, Any]], system_prompt: Optional[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role == "user":
            img = m.get("image_b64")
            if img:
                out.append({"role": "user", "content": [
                    {"type": "text", "text": m.get("content", "")},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64," + img}}]})
            else:
                out.append({"role": "user", "content": m.get("content", "")})
        elif role == "assistant":
            tcs = m.get("tool_calls")
            if tcs:
                out.append({"role": "assistant", "content": m.get("content") or None,
                            "tool_calls": [
                                {"id": tc["id"], "type": "function",
                                 "function": {"name": tc["name"],
                                              "arguments": json.dumps(tc.get("arguments", {}))}}
                                for tc in tcs]})
            else:
                out.append({"role": "assistant", "content": m.get("content", "")})
        elif role == "tool":
            out.append({"role": "tool", "tool_call_id": m.get("tool_call_id", ""),
                        "content": m.get("content", "")})
    return out


def _internal_to_gemini(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        if role == "user":
            parts: List[Dict[str, Any]] = [{"text": m.get("content", "")}]
            if m.get("image_b64"):
                parts.append({"inlineData": {"mimeType": "image/png", "data": m["image_b64"]}})
            out.append({"role": "user", "parts": parts})
        elif role == "assistant":
            tcs = m.get("tool_calls")
            if tcs:
                parts = []
                if m.get("content"):
                    parts.append({"text": m["content"]})
                for tc in tcs:
                    parts.append({"functionCall": {"name": tc["name"], "args": tc.get("arguments", {})}})
                out.append({"role": "model", "parts": parts})
            else:
                out.append({"role": "model", "parts": [{"text": m.get("content", "")}]})
        elif role == "tool":
            out.append({"role": "user", "parts": [
                {"functionResponse": {"name": m.get("name", ""),
                                      "response": {"result": m.get("content", "")}}}]})
    return out


class LLMClient(ABC):
    """Abstract base class for all LLM clients."""

    def __init__(self, api_key: str, url: str, model: str, temperature: float = 0.2, max_tokens: int = 4096) -> None:
        self.api_key = api_key
        self.url = url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Holds the in-flight streaming response so a cancel can close it and
        # unblock a stuck read (e.g. a model that hangs without emitting tokens).
        self._active_response = None

    def abort(self) -> None:
        """Best-effort: close any in-flight streaming response.

        Closing the socket makes the blocking ``iter_lines()`` in the worker
        thread raise immediately, so a stuck/"thinking-forever" request can be
        cancelled instantly instead of waiting for the 60s timeout.
        """
        resp = getattr(self, "_active_response", None)
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass
            self._active_response = None

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

    def chat_agentic(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None,
                     tools: Optional[List[Any]] = None) -> "AgentResponse":
        """Native function-calling turn (non-streaming).

        Returns an :class:`AgentResponse` carrying assistant text and/or a list
        of :class:`ToolCall`. Default implementation: no tool support (text only).
        """
        return AgentResponse(text=self.chat(messages, system_prompt), tool_calls=[])


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
            self._active_response = response
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

    def chat_agentic(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None,
                     tools: Optional[List[Any]] = None) -> "AgentResponse":
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": _internal_to_anthropic(messages),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if system_prompt:
            body["system"] = system_prompt
        if tools:
            body["tools"] = _tools_anthropic(tools)
        try:
            response = requests.post(self.url, headers=headers, json=body, timeout=120)
            if response.status_code != 200:
                raise LLMError(f"Anthropic API error ({response.status_code}): {response.text}")
            data = response.json()
            text_parts: List[str] = []
            calls: List[ToolCall] = []
            for block in data.get("content", []):
                btype = block.get("type")
                if btype == "text":
                    text_parts.append(block.get("text", ""))
                elif btype == "tool_use":
                    calls.append(ToolCall(id=block.get("id", uuid.uuid4().hex),
                                          name=block.get("name", ""),
                                          arguments=block.get("input", {}) or {}))
            return AgentResponse(text="".join(text_parts), tool_calls=calls)
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"Anthropic agentic request failed: {e}") from e
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
            self._active_response = response
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

    def chat_agentic(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None,
                     tools: Optional[List[Any]] = None) -> "AgentResponse":
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": _internal_to_openai(messages, system_prompt),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            body["tools"] = _tools_openai(tools)
        try:
            response = requests.post(self.url, headers=headers, json=body, timeout=120)
            if response.status_code != 200:
                raise LLMError(f"API error ({response.status_code}): {response.text}")
            data = response.json()
            message = data["choices"][0]["message"]
            calls: List[ToolCall] = []
            for tc in message.get("tool_calls") or []:
                fn = tc.get("function", {})
                raw_args = fn.get("arguments", "{}")
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except Exception:
                    args = {}
                calls.append(ToolCall(id=tc.get("id", uuid.uuid4().hex),
                                      name=fn.get("name", ""), arguments=args))
            return AgentResponse(text=message.get("content") or "", tool_calls=calls)
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"API agentic request failed: {e}") from e
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


class OpenRouterClient(OpenAICompatibleClient):
    """Client for OpenRouter (https://openrouter.ai) -- an OpenAI-compatible
    aggregator giving access to 400+ models via 'provider/model' slugs.

    Adds OpenRouter's optional ranking headers (HTTP-Referer / X-Title) on top
    of the standard Bearer auth; everything else is OpenAI-compatible.
    """

    def _build_request(self, messages, system_prompt, stream):
        headers, body = super()._build_request(messages, system_prompt, stream)
        # Optional attribution headers (recommended, not required by OpenRouter).
        headers.setdefault("HTTP-Referer", "https://github.com/lh-houdini-pipeline")
        headers.setdefault("X-Title", "LH Houdini AI Assistant")
        return headers, body


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
            self._active_response = response
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

    def chat_agentic(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None,
                     tools: Optional[List[Any]] = None) -> "AgentResponse":
        url = self._build_url(stream=False)
        headers = {"Content-Type": "application/json"}
        body: Dict[str, Any] = {
            "contents": _internal_to_gemini(messages),
            "generationConfig": {"temperature": self.temperature, "maxOutputTokens": self.max_tokens},
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if tools:
            body["tools"] = _tools_gemini(tools)
        try:
            response = requests.post(url, headers=headers, json=body, timeout=120)
            if response.status_code != 200:
                raise LLMError(f"Gemini API error ({response.status_code}): {response.text}")
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return AgentResponse(text="", tool_calls=[])
            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts: List[str] = []
            calls: List[ToolCall] = []
            for i, part in enumerate(parts):
                if "text" in part:
                    text_parts.append(part.get("text", ""))
                if "functionCall" in part:
                    fc = part["functionCall"]
                    calls.append(ToolCall(id=f"gemini-{i}-{uuid.uuid4().hex[:6]}",
                                          name=fc.get("name", ""), arguments=fc.get("args", {}) or {}))
            return AgentResponse(text="".join(text_parts), tool_calls=calls)
        except Exception as e:
            if not isinstance(e, LLMError):
                raise LLMError(f"Gemini agentic request failed: {e}") from e
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
    elif provider_lower == "openrouter":
        return OpenRouterClient(api_key, url, model, temperature, max_tokens)
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

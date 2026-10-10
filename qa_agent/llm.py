"""One bounded JSON calling layer for both SQL and document QA."""
from __future__ import annotations

import json
from contextlib import nullcontext
from time import sleep
from typing import TypeVar

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
from pydantic import BaseModel, ValidationError

from qa_agent.config import Settings, get_settings, sanitize_error
from qa_agent.trace import TraceRecorder

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    def __init__(self, message: str, code: str = "llm_error", retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class MissingCredentialError(LLMError):
    def __init__(self):
        super().__init__("请在项目本地 .env 配置 LLM_API_KEY，然后重启 API 服务。", "missing_llm_key")


class JsonLLM:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def _client(self) -> OpenAI:
        if not self.settings.llm_configured:
            raise MissingCredentialError()
        return OpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            timeout=self.settings.llm_timeout_seconds,
            max_retries=0,
        )

    def list_models(self) -> list[str]:
        try:
            with self._client() as client:
                return sorted(model.id for model in client.models.list().data)
        except LLMError:
            raise
        except Exception as exc:
            raise self._error(exc) from exc

    def _error(self, exc: Exception) -> LLMError:
        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return LLMError("模型接口连接失败或超时，请检查网络与 LLM_BASE_URL。", "llm_connection", True)
        if isinstance(exc, APIStatusError):
            code = exc.status_code
            if code in (401, 403):
                return LLMError("模型接口认证失败，请检查本地 API key 与账户权限。", "llm_auth")
            if code == 402:
                return LLMError("模型接口账户余额不足。", "llm_balance")
            if code == 429:
                return LLMError("模型接口请求限流，请稍后重试。", "llm_rate_limit", True)
            return LLMError(f"模型接口返回 HTTP {code}。", "llm_provider", code >= 500)
        return LLMError(sanitize_error(exc, self.settings), "llm_error")

    def complete_json(
        self, system_prompt: str, user_prompt: str, response_model: type[T],
        trace: TraceRecorder | None = None,
    ) -> T:
        if not self.settings.llm_configured:
            raise MissingCredentialError()
        schema_text = json.dumps(response_model.model_json_schema(), ensure_ascii=False)
        messages = [
            {"role": "system", "content": system_prompt +
             "\n只输出一个 JSON 对象，不输出 Markdown。字段遵守以下 JSON Schema：\n" + schema_text},
            {"role": "user", "content": user_prompt},
        ]
        last_error: LLMError | None = None
        # The SDK performs no hidden retry; this loop owns the total attempt budget.
        with self._client() as client:
            for attempt in range(1, self.settings.llm_max_attempts + 1):
                if trace is not None:
                    if trace.llm_attempts >= self.settings.llm_max_attempts:
                        raise LLMError("本次请求已达到模型调用次数上限。", "llm_attempt_budget")
                    trace.llm_attempts += 1
                context = trace.step("llm", {"attempt": attempt, "model": self.settings.llm_model}) if trace else nullcontext()
                try:
                    with context as step:
                        kwargs = {
                            "model": self.settings.llm_model,
                            "messages": messages,
                            "response_format": {"type": "json_object"},
                            "max_tokens": self.settings.llm_max_tokens,
                        }
                        if "deepseek.com" in self.settings.llm_base_url:
                            kwargs["extra_body"] = {"thinking": {"type": "enabled" if self.settings.llm_thinking else "disabled"}}
                        response = client.chat.completions.create(**kwargs)
                        if step is not None:
                            step.output_summary = {
                                "model": response.model,
                                "usage": response.usage.model_dump() if response.usage else {},
                            }
                        if not response.choices:
                            raise ValueError("模型返回为空")
                        choice = response.choices[0]
                        if choice.finish_reason == "length":
                            raise ValueError("模型 JSON 被截断，请调整 LLM_MAX_TOKENS")
                        if choice.message.refusal:
                            raise LLMError("模型未提供所需输出。", "llm_refused")
                        content = choice.message.content or ""
                        parsed = json.loads(content)
                        result = response_model.model_validate(parsed)
                        if step is not None:
                            step.output_summary["json_valid"] = True
                        return result
                except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                    last_error = LLMError("模型返回 JSON 格式或字段不符合协议。", "llm_format")
                    messages.append({"role": "user", "content":
                                     "上次结果未通过 JSON/字段校验。请重读原始任务，保持用户条件不变，只返回符合 Schema 的 JSON 对象。"})
                except Exception as exc:
                    last_error = exc if isinstance(exc, LLMError) else self._error(exc)
                    if not last_error.retryable:
                        raise last_error from exc
                    if attempt < self.settings.llm_max_attempts:
                        sleep(min(0.4 * attempt, 1.0))
        raise last_error or LLMError("模型调用未成功。")

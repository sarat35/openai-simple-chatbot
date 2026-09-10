import time
import random
import boto3
from botocore.exceptions import ClientError


class BedrockClient:
    RETRYABLE = {
        "ThrottlingException",
        "ServiceUnavailableException",
        "InternalServerException",
    }

    NO_RETRY = {
        "ValidationException",
        "AccessDeniedException",
    }

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "us-east-1",
        max_retries: int = 5,
        base_delay: float = 1.0,
        _client=None,
    ):
        self.model_id = model_id
        self.region = region
        self.max_retries = max_retries
        self.base_delay = base_delay

        self._client = (
            _client
            if _client is not None
            else boto3.client("bedrock-runtime", region_name=region)
        )

        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _backoff(self, attempt: int) -> None:
        """
        Sleep using exponential backoff + jitter.
        """
        delay = min(
            60,
            self.base_delay * (2 ** attempt)
        ) + random.uniform(0, 1)
        print("delay time:",delay)

        time.sleep(delay)

    def _request_args(self, messages, system=None):
        args = {
            "modelId": self.model_id,
            "messages": messages,
        }

        if system is not None:
            args["system"] = [{"text": system}]

        return args

    def _non_streaming(self, messages, system=None):
        args = self._request_args(messages, system)

        attempt = 0

        while True:
            try:
                response = self._client.converse(**args)

                text = response["output"]["message"]["content"][0]["text"]

                usage = response.get("usage", {})
                self.total_input_tokens += usage.get("inputTokens", 0)
                self.total_output_tokens += usage.get("outputTokens", 0)

                return text

            except ClientError as e:
                error_code = e.response["Error"]["Code"]

                # Fail immediately
                if error_code in self.NO_RETRY:
                    raise

                # Unknown/non-transient errors should also fail immediately
                if error_code not in self.RETRYABLE:
                    raise

                # No retries remaining
                if attempt >= self.max_retries:
                    raise

                self._backoff(attempt)
                attempt += 1

    def _streaming(self, messages, system=None):
        args = self._request_args(messages, system)

        attempt = 0

        while True:
            try:
                response = self._client.converse_stream(**args)

                for event in response["stream"]:

                    # Text arriving from the model
                    if "contentBlockDelta" in event:
                        chunk = (
                            event["contentBlockDelta"]
                            .get("delta", {})
                            .get("text", "")
                        )

                        if chunk:
                            yield chunk

                    # Usage normally appears near end of stream
                    if "metadata" in event:
                        usage = event["metadata"].get("usage", {})

                        self.total_input_tokens += usage.get(
                            "inputTokens", 0
                        )

                        self.total_output_tokens += usage.get(
                            "outputTokens", 0
                        )

                return

            except ClientError as e:
                error_code = e.response["Error"]["Code"]

                if error_code in self.NO_RETRY:
                    raise

                if error_code not in self.RETRYABLE:
                    raise

                if attempt >= self.max_retries:
                    raise

                self._backoff(attempt)
                attempt += 1

    def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        stream: bool = False,
    ):
        """
        Send a chat request to Bedrock with retry logic.

        Args:
            messages: list of {"role": "user"/"assistant",
                               "content": [{"text": "..."}]}
            system: optional system prompt string
            stream: if True, return a generator yielding text chunks

        Returns:
            str if stream=False
            Generator[str] if stream=True
        """

        if stream:
            return self._streaming(messages, system)

        return self._non_streaming(messages, system)

    @property
    def token_usage(self) -> dict:
        """Return cumulative token usage."""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens":
                self.total_input_tokens + self.total_output_tokens,
        }

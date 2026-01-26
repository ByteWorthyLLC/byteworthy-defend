"""
Claude-powered threat analyzer for scripts, network behavior, and incidents.
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic, APIError, APITimeoutError
from pydantic import BaseModel, Field

from hifzdefend.ai.cache import ResponseCache, CacheError
from hifzdefend.utils.exceptions import HifzDefendError

logger = logging.getLogger(__name__)


class AnalyzerError(HifzDefendError):
    """Analyzer operation error."""

    pass


class AnalysisResult(BaseModel):
    """Result from Claude analysis."""

    threat_level: str = Field(
        description="Threat level: safe, suspicious, malicious, critical"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    summary: str = Field(description="Plain language summary")
    details: dict[str, Any] = Field(default_factory=dict, description="Analysis details")
    recommendations: list[str] = Field(
        default_factory=list, description="Recommended actions"
    )
    indicators: list[str] = Field(
        default_factory=list, description="Threat indicators found"
    )


class CostTracker:
    """Track Claude API usage and costs."""

    def __init__(self, log_costs: bool = True):
        """Initialize cost tracker."""
        self.log_costs = log_costs
        self.request_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.hourly_requests: list[float] = []

    def track_request(
        self, input_tokens: int, output_tokens: int, timestamp: Optional[float] = None
    ) -> None:
        """Track a single API request."""
        self.request_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        if timestamp is None:
            timestamp = time.time()
        self.hourly_requests.append(timestamp)

        # Clean up old requests (older than 1 hour)
        cutoff = timestamp - 3600
        self.hourly_requests = [t for t in self.hourly_requests if t > cutoff]

        if self.log_costs:
            logger.info(
                f"API request tracked: {input_tokens} input tokens, "
                f"{output_tokens} output tokens, "
                f"{len(self.hourly_requests)} requests in last hour"
            )

    def get_hourly_requests(self) -> int:
        """Get number of requests in the last hour."""
        cutoff = time.time() - 3600
        self.hourly_requests = [t for t in self.hourly_requests if t > cutoff]
        return len(self.hourly_requests)

    def estimate_cost(self) -> dict[str, float]:
        """
        Estimate cost based on token usage.

        Uses Claude Sonnet 4 pricing:
        - Input: $3 per million tokens
        - Output: $15 per million tokens
        """
        input_cost = (self.total_input_tokens / 1_000_000) * 3.0
        output_cost = (self.total_output_tokens / 1_000_000) * 15.0
        total_cost = input_cost + output_cost

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": total_cost,
        }


class ClaudeAnalyzer:
    """
    Claude-powered threat analyzer.

    Features:
    - Script analysis (PowerShell, Batch, Python)
    - Network behavior analysis
    - Plain language explanations
    - Incident report generation
    - Response caching
    - Cost tracking
    - Rate limiting
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        timeout: int = 30,
        cache_enabled: bool = True,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 3600,
        max_requests_per_hour: int = 100,
        log_costs: bool = True,
        fallback_on_error: bool = True,
        retry_attempts: int = 3,
        retry_delay: int = 2,
    ):
        """
        Initialize Claude analyzer.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            timeout: API timeout in seconds
            cache_enabled: Enable response caching
            cache_dir: Cache directory path
            cache_ttl: Cache TTL in seconds
            max_requests_per_hour: Rate limit
            log_costs: Log API costs
            fallback_on_error: Gracefully degrade on errors
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.client = Anthropic(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_requests_per_hour = max_requests_per_hour
        self.fallback_on_error = fallback_on_error
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Initialize cache
        if cache_enabled and cache_dir:
            self.cache: Optional[ResponseCache] = ResponseCache(cache_dir, cache_ttl)
        else:
            self.cache = None

        # Initialize cost tracker
        self.cost_tracker = CostTracker(log_costs=log_costs)

    def _check_rate_limit(self) -> None:
        """Check if rate limit is exceeded."""
        if self.cost_tracker.get_hourly_requests() >= self.max_requests_per_hour:
            raise AnalyzerError(
                f"Rate limit exceeded: {self.max_requests_per_hour} requests/hour"
            )

    def _call_claude(self, prompt: str, use_cache: bool = True) -> dict[str, Any]:
        """
        Call Claude API with retry logic.

        Args:
            prompt: The prompt to send
            use_cache: Whether to use cache

        Returns:
            Response dict from Claude

        Raises:
            AnalyzerError: If API call fails after retries
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(prompt, self.model, self.temperature)
            if cached:
                logger.info("Using cached response")
                return cached["response"]

        # Check rate limit
        self._check_rate_limit()

        # Retry loop
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Track usage
                self.cost_tracker.track_request(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )

                # Extract text content
                result = {
                    "text": response.content[0].text,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                }

                # Cache response
                if use_cache and self.cache:
                    try:
                        self.cache.set(prompt, self.model, self.temperature, result)
                    except CacheError as e:
                        logger.warning(f"Failed to cache response: {e}")

                return result

            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    f"API timeout on attempt {attempt + 1}/{self.retry_attempts}"
                )
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)

            except APIError as e:
                last_error = e
                logger.error(f"API error on attempt {attempt + 1}/{self.retry_attempts}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)

            except Exception as e:
                # Catch all other exceptions
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}/{self.retry_attempts}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)

        # All retries failed
        if self.fallback_on_error:
            logger.error(f"All API attempts failed: {last_error}")
            return {
                "text": "Analysis unavailable (API error)",
                "model": self.model,
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "error": str(last_error),
            }
        else:
            raise AnalyzerError(f"API call failed after {self.retry_attempts} attempts: {last_error}")

    def analyze_script(
        self, script_path: Path, script_type: str = "auto"
    ) -> AnalysisResult:
        """
        Analyze a script file for threats.

        Args:
            script_path: Path to script file
            script_type: Script type (auto, powershell, batch, python)

        Returns:
            Analysis result with threat level and recommendations
        """
        # Read script content
        try:
            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                script_content = f.read()
        except OSError as e:
            raise AnalyzerError(f"Failed to read script: {e}")

        # Auto-detect script type
        if script_type == "auto":
            suffix = script_path.suffix.lower()
            if suffix in [".ps1", ".psm1"]:
                script_type = "powershell"
            elif suffix in [".bat", ".cmd"]:
                script_type = "batch"
            elif suffix == ".py":
                script_type = "python"
            else:
                script_type = "unknown"

        # Build prompt
        prompt = f"""Analyze this {script_type} script for security threats.

Script path: {script_path}

Script content:
```
{script_content[:5000]}  # Limit to 5000 chars
```

Provide analysis in this JSON format:
{{
  "threat_level": "safe|suspicious|malicious|critical",
  "confidence": 0.0-1.0,
  "summary": "Brief plain-language summary",
  "details": {{
    "suspicious_functions": [],
    "network_activity": [],
    "file_operations": [],
    "registry_modifications": [],
    "obfuscation_detected": false
  }},
  "recommendations": ["action 1", "action 2"],
  "indicators": ["indicator 1", "indicator 2"]
}}

Focus on:
- Obfuscation or encoding
- Network connections
- File system modifications
- Registry changes
- Process execution
- Privilege escalation
- Data exfiltration"""

        # Call Claude
        response = self._call_claude(prompt)

        # Parse response
        try:
            import json

            # Extract JSON from response
            text = response["text"]
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result_dict = json.loads(text.strip())
            return AnalysisResult(**result_dict)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse analysis result: {e}")
            # Return basic result
            return AnalysisResult(
                threat_level="unknown",
                confidence=0.0,
                summary=response["text"][:200],
                details={"raw_response": response["text"]},
                recommendations=["Manual review required"],
                indicators=[],
            )

    def analyze_network_behavior(
        self, network_data: dict[str, Any]
    ) -> AnalysisResult:
        """
        Analyze network behavior for threats.

        Args:
            network_data: Dict with network activity data

        Returns:
            Analysis result
        """
        prompt = f"""Analyze this network behavior for security threats.

Network data:
{network_data}

Provide analysis in this JSON format:
{{
  "threat_level": "safe|suspicious|malicious|critical",
  "confidence": 0.0-1.0,
  "summary": "Brief plain-language summary",
  "details": {{
    "c2_indicators": [],
    "data_exfiltration": false,
    "suspicious_ports": [],
    "unusual_destinations": []
  }},
  "recommendations": ["action 1", "action 2"],
  "indicators": ["indicator 1", "indicator 2"]
}}

Focus on:
- Command & control (C2) indicators
- Unusual destinations
- Data exfiltration patterns
- Port scanning
- DDoS activity
- Beaconing behavior"""

        response = self._call_claude(prompt)

        # Parse response (same as analyze_script)
        try:
            import json

            text = response["text"]
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result_dict = json.loads(text.strip())
            return AnalysisResult(**result_dict)
        except (json.JSONDecodeError, ValueError):
            return AnalysisResult(
                threat_level="unknown",
                confidence=0.0,
                summary=response["text"][:200],
                details={"raw_response": response["text"]},
                recommendations=["Manual review required"],
                indicators=[],
            )

    def generate_incident_report(
        self, incident_data: dict[str, Any]
    ) -> str:
        """
        Generate a plain English incident report.

        Args:
            incident_data: Dict with incident details

        Returns:
            Plain language incident report
        """
        prompt = f"""Generate a plain English incident report for this security event.

Incident data:
{incident_data}

Create a report that:
- Explains what happened in simple terms (grandma can understand)
- Describes the threat and why it's dangerous
- Lists what actions were taken
- Provides recommendations for prevention

Use clear, non-technical language."""

        response = self._call_claude(prompt, use_cache=False)
        return response["text"]

    def explain_threat(self, threat_id: str, threat_data: dict[str, Any]) -> str:
        """
        Explain a threat in plain language.

        Args:
            threat_id: Threat identifier
            threat_data: Threat details

        Returns:
            Plain language explanation
        """
        prompt = f"""Explain this security threat in plain language.

Threat ID: {threat_id}
Threat data:
{threat_data}

Provide:
1. What is this threat?
2. Why is it dangerous?
3. How did it get here?
4. What should I do?

Use simple, clear language that anyone can understand."""

        response = self._call_claude(prompt)
        return response["text"]

    def get_cost_stats(self) -> dict[str, Any]:
        """Get API usage and cost statistics."""
        return self.cost_tracker.estimate_cost()

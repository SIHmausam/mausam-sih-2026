from prometheus_client import (
    Counter,
    Histogram,
)

PROVIDER_REQUESTS = Counter(
    "mausam_provider_requests_total",
    "Actual HTTP attempts made to external providers.",
    [
        "provider",
        "outcome",
    ],
)


PROVIDER_RETRIES = Counter(
    "mausam_provider_retries_total",
    "External provider retries.",
    [
        "provider",
        "reason",
    ],
)


PROVIDER_RATE_LIMITS = Counter(
    "mausam_provider_rate_limits_total",
    "HTTP 429 responses received from providers.",
    [
        "provider",
    ],
)


PROVIDER_FAILURES = Counter(
    "mausam_provider_failures_total",
    "Provider requests that ultimately failed.",
    [
        "provider",
        "reason",
    ],
)


PROVIDER_REQUEST_DURATION = Histogram(
    "mausam_provider_request_duration_seconds",
    "Duration of individual external provider HTTP attempts.",
    [
        "provider",
    ],
)


CACHE_ACCESS = Counter(
    "mausam_cache_access_total",
    "Redis cache hits and misses.",
    [
        "cache",
        "result",
    ],
)
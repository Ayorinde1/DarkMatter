from dataclasses import dataclass
from typing import Optional

@dataclass
class ProxyConfig:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, socks5
    score: float = 0.0

    def to_curl_cffi_format(self) -> str:
        """Returns proxy string formatted for curl_cffi."""
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

@dataclass
class TrafficConfig:
    target_url: str
    max_threads: int
    total_visits: int
    min_duration: int  # Seconds
    max_duration: int  # Seconds
    headless: bool = True  # Not strictly used by curl_cffi but good for config completeness

@dataclass
class TrafficStats:
    success: int = 0
    failed: int = 0
    active_threads: int = 0
    total_requests: int = 0
    active_proxies: int = 0

@dataclass
class ProxyCheckResult:
    proxy: ProxyConfig
    status: str  # "Active" or "Dead"
    speed: int  # ms
    type: str  # HTTP, SOCKS5, etc.
    country: str
    country_code: str
    anonymity: str = "Unknown"
    score: float = 0.0


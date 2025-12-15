import os
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse


class Utils:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate that a URL has proper scheme and netloc."""
        if not url:
            return False
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def safe_int(value: Any, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Safely convert value to int with optional bounds clamping."""
        try:
            v = int(value)
            if min_val is not None:
                v = max(v, min_val)
            if max_val is not None:
                v = min(v, max_val)
            return v
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_flag(code: Optional[str]) -> str:
        """Convert a 2-letter country code to a flag emoji."""
        if not code or len(code) != 2:
            return "🏳️"
        try:
            return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)
        except (ValueError, TypeError):
            return "🏳️"

    @staticmethod
    def load_settings(filename: str = "resources/settings.json") -> Dict[str, Any]:
        """Load settings from JSON file, returning defaults if file doesn't exist."""
        defaults: Dict[str, Any] = {
            "target_url": "https://example.com",
            "threads": 5,
            "viewtime_min": 5,
            "viewtime_max": 10,
            "proxy_test_url": "https://httpbin.org/json",
            "proxy_timeout": 3000,
            "proxy_check_threads": 50,
            "proxy_scrape_threads": 20,
            "scraper_proxy": "",
            "scraper_proxy_protocol": "http",
            "use_scraper_proxy": False,
            "use_http": True,
            "use_socks4": True,
            "use_socks5": True,
            "hide_dead": True,
            "headless": True,
            "verify_ssl": True,
            "sources": "resources/sources.txt"
        }
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return {**defaults, **json.load(f)}
            except (json.JSONDecodeError, IOError, OSError):
                pass
        return defaults

    @staticmethod
    def save_settings(data: Dict[str, Any], filename: str = "resources/settings.json") -> None:
        """Save settings dictionary to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        except (IOError, OSError, TypeError) as e:
            logging.error(f"Failed to save settings: {e}")

    @staticmethod
    def deduplicate_proxies(proxy_strings: list) -> list:
        """
        Deduplicate proxy strings based on (host, port, protocol) tuple.
        Handles formats like 'http://1.2.3.4:80' and '1.2.3.4:80'.
        """
        seen: set = set()
        unique: list = []

        for p_str in proxy_strings:
            if not p_str:
                continue

            # Parse proxy string
            try:
                if "://" in p_str:
                    parts = p_str.split("://", 1)
                    protocol = parts[0].lower()
                    addr = parts[1]
                else:
                    protocol = "http"
                    addr = p_str

                # Handle auth in proxy (user:pass@host:port)
                if "@" in addr:
                    addr = addr.split("@", 1)[1]

                if ":" in addr:
                    host, port = addr.rsplit(":", 1)
                    key = (host.lower(), port, protocol)

                    if key not in seen:
                        seen.add(key)
                        unique.append(p_str)
            except (ValueError, IndexError):
                continue

        return unique

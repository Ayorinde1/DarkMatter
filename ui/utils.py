import os
import json

class Utils:
    @staticmethod
    def get_flag(code):
        if not code or len(code) != 2: return "🏳️"
        try:
            return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)
        except:
            return "🏳️"

    @staticmethod
    def load_settings(filename="resources/settings.json"):
        defaults = {
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
            "sources": "resources/sources.txt"
        }
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return {**defaults, **json.load(f)}
            except:
                pass
        return defaults

    @staticmethod
    def save_settings(data, filename="resources/settings.json"):
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        except:
            pass

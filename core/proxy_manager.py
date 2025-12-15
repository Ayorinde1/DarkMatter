import re
import time
import logging
import requests as std_requests
from typing import List, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests
from .header_manager import HeaderManager
from .models import ProxyConfig, ProxyCheckResult
from .constants import (
    SCRAPE_TIMEOUT_SECONDS,
    PROXY_CHECK_BATCH_SIZE,
    DEAD_PROXY_SPEED_MS,
)

class ThreadedProxyManager:
    def __init__(self):
        self.regex_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b")

    def scrape(self, sources: List[str], protocols: List[str], max_threads: int = 20, scraper_proxy: str = None, on_progress: Callable[[int], None] = None) -> List[ProxyConfig]:
        """Scrapes proxies from provided source URLs using threads."""
        found_proxies: Set[tuple] = set()
        
        def fetch_source(url: str):
            try:
                # Use standard requests for speed (scraping text/html usually doesn't need TLS fingerprinting)
                # But we use rotating headers to avoid 403s
                h = HeaderManager.get_random_headers()
                proxies = {"http": scraper_proxy, "https": scraper_proxy} if scraper_proxy else None
                
                response = std_requests.get(
                    url,
                    timeout=SCRAPE_TIMEOUT_SECONDS,
                    headers=h,
                    proxies=proxies
                )
                if response.status_code == 200:
                    if on_progress:
                        on_progress(len(response.content))
                    matches = self.regex_pattern.findall(response.text)
                    
                    # Smart Protocol Detection
                    u_lower = url.lower()
                    source_protos = []
                    
                    # Heuristics based on URL hints
                    if "socks5" in u_lower: source_protos.append("socks5")
                    if "socks4" in u_lower: source_protos.append("socks4")
                    if "http" in u_lower and "socks" not in u_lower: source_protos.append("http")
                    
                    # Intersect with user requests
                    valid_protos = [p for p in source_protos if p in protocols]
                    
                    # Fallback: If no specific protocol detected, try all requested
                    if not valid_protos:
                        valid_protos = protocols

                    for m in matches:
                        ip, port = m.split(":")
                        for proto in valid_protos:
                            found_proxies.add((ip, int(port), proto))
            except Exception as e:
                logging.debug(f"Error scraping {url}: {e}")

        with ThreadPoolExecutor(max_workers=max_threads) as ex:
             ex.map(fetch_source, [url for url in sources if url.strip() and not url.startswith("#")])

        results = []
        for ip, port, proto in found_proxies:
            results.append(ProxyConfig(host=ip, port=port, protocol=proto))
                
        return results

    def check_proxies(self, proxies: List[ProxyConfig], target_url: str, timeout_ms: int, real_ip: str, 
                          on_progress: Callable[[ProxyCheckResult, int, int], None], concurrency: int = 100,
                          pause_checker: Optional[Callable[[], bool]] = None) -> List[ProxyCheckResult]:
        """
        Checks a list of proxies concurrently using threads.
        """
        total = len(proxies)
        completed = 0
        valid_results = []
        lock = logging.threading.Lock() # Simple lock for counter

        def check_single(proxy: ProxyConfig):
            nonlocal completed
            
            # Pause logic
            if pause_checker:
                while pause_checker():
                    time.sleep(0.5)

            result = self._test_proxy(proxy, target_url, timeout_ms, real_ip)
            
            with lock:
                completed += 1
                current_completed = completed
            
            if on_progress:
                on_progress(result, current_completed, total)
            
            if result.status == "Active":
                # List append is thread-safe in Python (GIL), but explicit lock doesn't hurt.
                # Actually, standard list append IS atomic.
                return result
            return None

        valid_results_list = []
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = []
            
            # Staggered Launch to prevent UI freeze
            for i in range(0, len(proxies), PROXY_CHECK_BATCH_SIZE):
                batch = proxies[i:i + PROXY_CHECK_BATCH_SIZE]
                for p in batch:
                    futures.append(ex.submit(check_single, p))
                
                # Check pause during submission
                if pause_checker:
                    while pause_checker():
                        time.sleep(0.5)
                
                # Small sleep to yield CPU
                time.sleep(0.05)

            for f in futures:
                res = f.result()
                if res:
                    valid_results_list.append(res)
                    
        return valid_results_list

    def _test_proxy(self, proxy: ProxyConfig, target_url: str, timeout_ms: int, real_ip: str) -> ProxyCheckResult:
        result = ProxyCheckResult(
            proxy=proxy,
            status="Dead",
            speed=DEAD_PROXY_SPEED_MS,
            type=proxy.protocol.upper(),
            country="??",
            country_code="??"
        )

        proxy_url = proxy.to_curl_cffi_format()
        proxies_dict = {"http": proxy_url, "https": proxy_url}
        timeout_sec = max(timeout_ms / 1000, 1.0)  # Minimum 1 second timeout

        start_time = time.time()
        try:
            # Synchronous Session - don't pass proxies to constructor, pass to request
            with requests.Session(impersonate="chrome120") as session:
                resp = session.get(
                    target_url,
                    timeout=timeout_sec,
                    proxies=proxies_dict,
                    verify=False  # Many proxy test endpoints have cert issues
                )

                latency = int((time.time() - start_time) * 1000)
                result.speed = latency
                result.status = "Active"

                # If target was HTTPS and it worked, label as HTTPS proxy
                if target_url.lower().startswith("https://") and result.type == "HTTP":
                    result.type = "HTTPS"

                # Check Anonymity (only works with httpbin-like endpoints)
                try:
                    data = resp.json()
                    origin = data.get("origin", "")
                    if real_ip in origin:
                        result.anonymity = "Transparent"
                    else:
                        result.anonymity = "Elite"
                except (ValueError, KeyError, AttributeError):
                    pass  # Response wasn't JSON or missing expected fields

                # Score Calculation
                # Higher is better. 1000ms = 1.0. 100ms = 10.0.
                base_score = 1000.0 / max(latency, 1)
                if result.anonymity == "Elite":
                    base_score *= 1.5
                elif result.anonymity == "Transparent":
                    base_score *= 0.5

                result.score = round(base_score, 2)
                proxy.score = result.score  # Store on config for Engine use

        except Exception as e:
            # Log failed proxies at debug level for troubleshooting
            logging.debug(f"Proxy {proxy.host}:{proxy.port} failed: {type(e).__name__}: {e}")

        return result

# DarkMatter Traffic Bot (DM-Trafficbot)

**Version 3.1.2**

DM-Trafficbot is a sophisticated, high-performance traffic generation and proxy validation tool designed for advanced web analytics, load testing, and automation. It moves beyond simple request flooding by emulating human behavior and employing techniques to bypass advanced bot detection systems.

## Core Features

### 1. Verification Engine (Advanced Proxy Checker)
A quality checker that doesn't just ping an IP, but validates its usability against real-world targets.

- **Multi-Protocol Support**: Auto-detects and validates HTTP, HTTPS, SOCKS4, and SOCKS5 proxies.
- **Target-Specific Validation**: Checks if a proxy works on your specific target site, not just a generic endpoint like Google.
- **Anonymity Classification**: Categorizes proxies as Transparent, Anonymous, or Elite (High Anonymity) to assess their stealth level.
- **Deep Geolocation Data**: Provides City, ISP, and Timezone data, crucial for matching browser profiles to the proxy's location.
- **Blacklist & Spam Check**: Automatically queries databases (e.g., Spamhaus) to identify flagged IPs.

### 2. Traffic Engine (Human Emulation Logic)
The core of the bot, designed for quality traffic that mimics genuine users.

- **Advanced Fingerprint Spoofing**:
    - **User-Agent Rotation**: Cycles through modern browser user-agent strings.
    - **TLS/JA3 Fingerprinting**: Implements techniques to mimic genuine browser TLS handshakes, a critical step to avoid detection by providers like Cloudflare.
    - **Header Consistency**: Ensures headers like `Accept-Language` and `Sec-CH-UA` align with the User-Agent and proxy location.
- **High Concurrency**: Built on an `asyncio` architecture using `aiohttp` for massive scalability with low CPU overhead.
- **Referrer Injection**: Simulates traffic from various sources (Google Search, social media, direct) to appear organic.
- **Intelligent Session Management**: Manages cookies and sessions to simulate either new or returning visitors.

### 3. Workflow & Automation
Features that enable long-term, unattended operations.

- **Proxy Hot-Swapping**: Instantly rotates to a fresh proxy from the pool if one dies mid-operation, ensuring task continuity.
- **Macro/Script Support**: Allows for creating simple scripts to define user actions (e.g., Visit URL -> Wait -> Scroll -> Click Element).
- **Captcha Service Integration**: API hooks for services like 2Captcha or CapMonster to handle interruptions automatically.
- **Scheduler**: Plan and automate campaigns to run at specific times or for a set duration.

## Technical Deep Dive

Built with Python, DM-Trafficbot is architected to overcome the performance limitations of traditional threading models. By leveraging `asyncio` and `aiohttp`, it can efficiently handle thousands of concurrent connections on a single process. The primary focus is on defeating modern bot detection through advanced TLS/JA3 fingerprint spoofing, ensuring that the bot's traffic profile is indistinguishable from that of a standard web browser.

## Getting Started

### Prerequisites
- Python 3.10+
- A virtual environment is recommended.

### Installation & Running from Source
1.  **Set up Virtual Environment**:
    ```sh
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    source .venv/bin/activate # Linux/Mac
    ```
2.  **Install Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```
3.  **Run the Application**:
    ```sh
    python main.py
    ```

### Building the Executable
You can build a standalone `.exe` file for easy distribution. The build script automatically enforces the virtual environment and bundles all assets.

1.  **Run the Build Script**:
    ```sh
    python build.py
    ```
2.  **Locate the Output**:
    The build script will generate a zip file `DarkMatterBot_v3.1.2.zip` in the root directory, containing the standalone executable.

## Changelog

### v3.1.2
- Fixed dashboard stats glitching/reverting issue (thread-safety fix)
- Color-coded dashboard stats (green for success, red for failures)
- Color-coded proxy ping values (green/yellow/orange/red based on latency)
- Green network traffic indicator for better visibility
- Improved proxy sources with 60+ reliable endpoints
- Fixed proxy checker to find more live proxies

### v3.1.1
- Security: SSL verification now configurable
- Error handling improvements throughout codebase
- Input validation for URLs and numeric fields
- Thread-safe queue-based GUI updates
- Session pooling for better performance
- Centralized constants file

### v3.1.0
- Brand refresh with Dark Matter purple theme
- Single-file executable build system
- Hybrid concurrency model (asyncio + threading)

## Disclaimer

This tool is intended for educational and legitimate testing purposes **only**. The developers assume no liability and are not responsible for any misuse or damage caused by this program. Using this tool against websites without prior mutual consent may be illegal.
"""
Application-wide constants and configuration defaults.
"""

# Browser impersonation options for TLS fingerprinting
BROWSER_IMPERSONATIONS = ["chrome120", "chrome124", "safari15_5"]

# Proxy checking defaults
DEFAULT_PROXY_TIMEOUT_MS = 3000
MIN_PROXY_TIMEOUT_MS = 100
MAX_PROXY_TIMEOUT_MS = 30000

DEFAULT_CHECK_THREADS = 50
MIN_CHECK_THREADS = 1
MAX_CHECK_THREADS = 2000

DEFAULT_SCRAPE_THREADS = 20
MIN_SCRAPE_THREADS = 1
MAX_SCRAPE_THREADS = 100

# Traffic engine defaults
DEFAULT_ATTACK_THREADS = 5
MIN_ATTACK_THREADS = 1
MAX_ATTACK_THREADS = 500

DEFAULT_VIEW_TIME_MIN = 5
DEFAULT_VIEW_TIME_MAX = 10
MIN_VIEW_TIME = 1
MAX_VIEW_TIME = 300

# Request defaults
REQUEST_TIMEOUT_SECONDS = 30
SCRAPE_TIMEOUT_SECONDS = 15

# Proxy checker batch size (for staggered launch)
PROXY_CHECK_BATCH_SIZE = 50

# GUI update interval (ms)
GUI_UPDATE_INTERVAL_MS = 100

# Buffer drain limit per GUI update
BUFFER_DRAIN_LIMIT = 40

# Curl error codes indicating proxy failure
PROXY_ERROR_CODES = ["curl: (56)", "curl: (97)", "curl: (28)", "curl: (7)", "curl: (35)"]

# Success status codes
SUCCESS_STATUS_CODES = [200, 201, 301, 302]

# Dead proxy sentinel speed value
DEAD_PROXY_SPEED_MS = 9999

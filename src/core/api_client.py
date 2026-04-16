from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import logging

logger = logging.getLogger(__name__)


class GeoBlockError(Exception):
    """Raised when Binance returns 451 (geo/legal block)."""
    pass

class APIClient:
    def __init__(self, base_url: str, headers: dict, proxy: str = None):
        self.base_url = base_url
        self.headers = headers
        self.session = requests.Session()
        self.session.headers.update(headers)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError))
    )
    def post(self, endpoint: str, json_data: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.post(url, json=json_data, timeout=10)
            if response.status_code == 429:
                logger.warning(f"Rate limited on {endpoint}. Backing off.")
                raise requests.ConnectionError("Rate limited")
            if response.status_code == 451:
                raise GeoBlockError(
                    "Binance returned 451: this server's IP is geo-blocked by Binance (likely US region). "
                    "Run the app locally or on a non-US server."
                )
            response.raise_for_status()
            return response.json()
        except GeoBlockError:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {url} failed: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout))
    )
    def get(self, endpoint: str, params: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 429:
                logger.warning(f"Rate limited on {endpoint}. Backing off.")
                raise requests.ConnectionError("Rate limited")
            if response.status_code == 451:
                raise GeoBlockError(
                    "Binance returned 451: this server's IP is geo-blocked by Binance (likely US region). "
                    "Run the app locally or on a non-US server."
                )
            response.raise_for_status()
            return response.json()
        except GeoBlockError:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {url} failed: {e}")
            raise

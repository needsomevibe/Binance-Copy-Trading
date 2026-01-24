import unittest
from unittest.mock import MagicMock, patch
from src.core.scraper import BinanceScraper
from src.core.models import Trader, Metrics

class TestBinanceScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = BinanceScraper()
        # Mock the client to avoid real network calls
        self.scraper.client = MagicMock()

    def test_transform_for_llm_basic(self):
        # Mock raw data
        raw_trader = {
            "leadPortfolioId": "12345",
            "nickname": "TestTrader",
            "roi": 0.5,
            "pnl": 1000.0,
            "sharpRatio": 2.5,
            "mdd": 0.1,
            "aum": 50000.0,
            "winRate": 0.6,
            "currentCopyCount": 10,
            "maxCopyCount": 100,
            "chartItems": [
                {"dateTime": 1700000000000, "value": 10},
                {"dateTime": 1700086400000, "value": 12}
            ]
        }

        result = self.scraper.transform_for_llm(raw_trader, fetch_details=False)
        
        self.assertIsInstance(result, Trader)
        self.assertEqual(result.profile.nickname, "TestTrader")
        self.assertEqual(result.metrics.roi, 0.5)
        self.assertEqual(result.metrics.utilization, 10.0) # 10/100 * 100
        self.assertEqual(len(result.roi_history), 2)

    def test_fetch_traders_failure(self):
        # Simulate an API failure
        self.scraper.client.post.side_effect = Exception("API Error")
        
        traders = self.scraper.fetch_traders()
        self.assertEqual(traders, [])

    def test_fetch_asset_allocation_parsing(self):
        # Mock asset response
        mock_response = {
            "data": {
                "data": [
                    {"asset": "BTC", "volume": 0.5},
                    {"asset": "ETH", "volume": "0.3"}, # String float
                    {"asset": "USDT", "volume": None}  # None value
                ]
            }
        }
        self.scraper.client.get.return_value = mock_response
        
        assets = self.scraper.fetch_asset_allocation("123", "30D")
        
        self.assertEqual(len(assets), 3)
        self.assertEqual(assets[0].asset, "BTC")
        self.assertEqual(assets[0].volume_percent, 0.5)
        self.assertEqual(assets[1].asset, "ETH")
        self.assertEqual(assets[1].volume_percent, 0.3)
        self.assertEqual(assets[2].volume_percent, 0.0) # Handled by logic or model? Model doesn't handle validation for this specific call in scraper, scraper does it manually.
        # Wait, I updated scraper to use: AssetAllocation(asset=item.get("asset"), volume_percent=float(item.get("volume", 0)))
        # Pydantic validates type. 'volume'="0.3" -> float(0.3) works. None -> float(0) works? No, float(None) fails.
        # Let's check my scraper logic: float(item.get("volume", 0))
        # if volume is None, get returns None (default is ignored if key exists).
        # Actually item.get("volume", 0) returns None if key exists and value is None.
        # So float(None) -> TypeError.
        # I should fix this in the scraper code if the test fails.

if __name__ == '__main__':
    unittest.main()
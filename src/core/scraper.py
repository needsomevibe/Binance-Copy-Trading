from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from .api_client import APIClient
from .models import Trader, Metadata, Profile, Metrics, DeepDive, RoiHistoryItem, AssetAllocation, Position

logger = logging.getLogger(__name__)

class BinanceScraper:
    API_BASE = "https://www.binance.com/bapi/futures/v1"
    HEADERS = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "clienttype": "web"
    }

    def __init__(self, proxy: str = None):
        self.client = APIClient(self.API_BASE, self.HEADERS, proxy=proxy)

    def fetch_traders(self, page: int = 1, page_size: int = 20, time_range: str = "90D", data_type: str = "SHARP_RATIO") -> List[Dict]:
        endpoint = "friendly/future/copy-trade/home-page/query-list"
        payload = {
            "pageNumber": page,
            "pageSize": page_size,
            "timeRange": time_range,
            "dataType": data_type,
            "favoriteOnly": False,
            "hideFull": False,
            "nickname": "",
            "order": "DESC",
            "userAsset": 0,
            "portfolioType": "ALL",
            "useAiRecommended": True
        }
        try:
            data = self.client.post(endpoint, payload)
            if data.get("code") == "000000" and data.get("data"):
                return data["data"]["list"]
            return []
        except Exception:
            return []

    def fetch_details_concurrently(self, traders: List[Dict], time_range: str) -> List[Trader]:
        """
        Enhances a list of traders with deep-dive data using concurrency.
        """
        enhanced_traders = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_trader = {
                executor.submit(self._fetch_single_trader_details, trader, time_range): trader 
                for trader in traders
            }
            for future in as_completed(future_to_trader):
                try:
                    data = future.result()
                    enhanced_traders.append(data)
                except Exception as e:
                    logger.error(f"Failed to enhance trader: {e}")
                    # Return partial data if deep scan fails
                    enhanced_traders.append(self.transform_for_llm(future_to_trader[future], fetch_details=False))
        return enhanced_traders

    def _fetch_single_trader_details(self, trader: Dict, time_range: str) -> Trader:
        return self.transform_for_llm(trader, fetch_details=True, time_range=time_range)

    def fetch_portfolio_detail(self, portfolio_id: str) -> Dict:
        endpoint = "friendly/future/copy-trade/lead-portfolio/detail"
        try:
            res = self.client.get(endpoint, {"portfolioId": portfolio_id})
            return res.get("data", {})
        except Exception: return {}

    def fetch_asset_allocation(self, portfolio_id: str, time_range: str) -> List[AssetAllocation]:
        endpoint = "public/future/copy-trade/lead-portfolio/performance/coin"
        try:
            res = self.client.get(endpoint, {"portfolioId": portfolio_id, "timeRange": time_range})
            raw_data = (res.get("data") or {}).get("data") or []
            return [
                AssetAllocation(asset=item.get("asset"), volume_percent=float(item.get("volume") or 0)) 
                for item in raw_data
            ]
        except Exception as e:
            logger.warning(f"Error fetching assets for {portfolio_id}: {e}")
            return []

    def fetch_positions(self, portfolio_id: str) -> List[Position]:
        endpoint = "friendly/future/copy-trade/lead-data/positions"
        try:
            res = self.client.get(endpoint, {"portfolioId": portfolio_id})
            raw = res.get("data") or []
            valid = []
            for p in raw:
                try:
                    if float(p.get("positionAmount") or 0) != 0:
                        valid.append(Position(
                            symbol=p.get("symbol"),
                            side=p.get("positionSide"),
                            leverage=p.get("leverage"),
                            amount=p.get("positionAmount"),
                            entry_price=p.get("entryPrice"),
                            unrealized_pnl=p.get("unrealizedProfit"),
                            roe=p.get("unrealizedProfitRatio")
                        ))
                except (ValueError, TypeError):
                    continue
            return valid
        except Exception: return []

    def fetch_position_history(self, portfolio_id: str) -> List[Dict]:
        endpoint = "friendly/future/copy-trade/lead-portfolio/position-history"
        try:
            payload = {
                "pageNumber": 1,
                "pageSize": 10,
                "portfolioId": portfolio_id,
                "sort": "OPENING"
            }
            res = self.client.post(endpoint, payload)
            return (res.get("data") or {}).get("list") or []
        except Exception: return []

    def transform_for_llm(self, trader: Dict, fetch_details: bool = False, time_range: str = "90D") -> Trader:
        pid = trader.get("leadPortfolioId")
        chart_items = trader.get("chartItems", [])
        
        # Calculate Trend Logic
        trend = "stable"
        if len(chart_items) > 5:
            # Simple Moving Average comparison
            early = chart_items[:3]
            late = chart_items[-3:]
            avg_early = sum(i['value'] for i in early) / len(early) if early else 0
            avg_late = sum(i['value'] for i in late) / len(late) if late else 0
            
            threshold = 5.0 # percent
            if avg_late > avg_early + threshold: trend = "upward"
            elif avg_late < avg_early - threshold: trend = "downward"

        # Safe Metrics Extraction
        metrics = Metrics(
            roi=trader.get("roi"),
            pnl=trader.get("pnl"),
            sharpe=trader.get("sharpRatio"),
            mdd=trader.get("mdd"),
            aum=trader.get("aum"),
            win_rate=trader.get("winRate"),
            copiers=trader.get("currentCopyCount"),
            max_copiers=trader.get("maxCopyCount")
        )
        if metrics.max_copiers > 0:
            metrics.utilization = round((metrics.copiers / metrics.max_copiers) * 100, 2)

        deep_dive = None
        if fetch_details and pid:
            details = self.fetch_portfolio_detail(pid)
            deep_dive = DeepDive(
                bio=details.get("description") or "",
                trader_balance=float(details.get("marginBalance", 0) or 0),
                copier_pnl=float(details.get("copierPnl", 0) or 0),
                profit_share=float(details.get("profitSharingRate", 0) or 0),
                total_copiers=int(details.get("totalCopyCount", 0) or 0),
                min_copy_amount=float(details.get("fixedAmountMinCopyUsd", 0) or 0),
                risk_tags=details.get("tag", []) or [],
                assets=self.fetch_asset_allocation(pid, time_range),
                positions=self.fetch_positions(pid),
                history=self.fetch_position_history(pid)
            )

        return Trader(
            metadata=Metadata(
                profile_url=f"https://www.binance.com/en/copy-trading/lead-details/{pid}"
            ),
            profile=Profile(
                nickname=trader.get("nickname"),
                id=pid,
                tags=[trader.get("apiKeyTag")] if trader.get("apiKeyTag") else [],
                badges=[trader.get("badgeName")] if trader.get("badgeName") else []
            ),
            metrics=metrics,
            trend=trend,
            roi_history=[
                RoiHistoryItem(
                    d=datetime.fromtimestamp(i["dateTime"]/1000).strftime('%Y-%m-%d'), 
                    v=i["value"]
                ) for i in chart_items
            ],
            deep_dive=deep_dive
        )

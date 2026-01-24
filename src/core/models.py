from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime

class Metadata(BaseModel):
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    profile_url: str

class Profile(BaseModel):
    nickname: Optional[str] = "Unknown"
    id: str
    tags: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)

class Metrics(BaseModel):
    roi: float = 0.0
    pnl: float = 0.0
    sharpe: float = 0.0
    mdd: float = 0.0
    aum: float = 0.0
    win_rate: float = 0.0
    copiers: int = 0
    max_copiers: int = 0
    utilization: float = 0.0

    @field_validator('*', mode='before')
    def parse_float_or_int(cls, v):
        if v is None:
            return 0
        if isinstance(v, str):
            try:
                return float(v.replace(',', ''))
            except ValueError:
                return 0
        return v

class Position(BaseModel):
    symbol: str
    side: str
    leverage: int = 1
    amount: float
    entry_price: float
    unrealized_pnl: float
    roe: float

    @field_validator('amount', 'entry_price', 'unrealized_pnl', 'roe', mode='before')
    def parse_floats(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return 0.0
        return v or 0.0

class AssetAllocation(BaseModel):
    asset: str
    volume_percent: float

class DeepDive(BaseModel):
    bio: str = ""
    trader_balance: float = 0.0
    copier_pnl: float = 0.0
    profit_share: float = 0.0
    total_copiers: int = 0
    min_copy_amount: float = 0.0
    risk_tags: List[str] = Field(default_factory=list)
    assets: List[AssetAllocation] = Field(default_factory=list)
    positions: List[Position] = Field(default_factory=list)
    history: List[dict] = Field(default_factory=list) # Keeping history flexible for now

class RoiHistoryItem(BaseModel):
    d: str # Date string
    v: float # Value

class Trader(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    metadata: Metadata
    profile: Profile
    metrics: Metrics
    trend: str = "stable"
    roi_history: List[RoiHistoryItem] = Field(default_factory=list)
    deep_dive: Optional[DeepDive] = None

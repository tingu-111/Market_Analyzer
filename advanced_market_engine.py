
# ==============================================================================
# ADVANCED AI MARKET ANALYSIS & DECISION ENGINE
# Production-Grade Quantitative Architecture for PyCharm & Streamlit
# ==============================================================================

import os
import sys
import re
import math
import time
import json
import logging
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Dict, List, Tuple, Optional, Any, Union

import numpy as np
import pandas as pd
import requests
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Optional autorefresh & sentiment enhancements
try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH_AVAILABLE = True
except Exception:
    AUTO_REFRESH_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except Exception:
    VADER_AVAILABLE = False

# Suppress noisy logs
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

# ==============================================================================
# STREAMLIT CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Advanced AI Market Decision Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Financial Dashboard CSS
st.markdown("""
<style>
    /* Global Styles */
    .reportview-container {
        background: #0b0f19;
    }
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
    }
    .metric-card-title {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8b949e;
        margin-bottom: 6px;
    }
    .metric-card-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f0f6fc;
        line-height: 1.2;
    }
    .metric-card-subtitle {
        font-size: 0.78rem;
        color: #8b949e;
        margin-top: 4px;
    }
    /* Decision Box Styling */
    .decision-banner {
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 20px;
        border: 1px solid #30363d;
    }
    .decision-banner-long {
        background: linear-gradient(135deg, rgba(35, 134, 54, 0.2) 0%, rgba(22, 27, 34, 0.9) 100%);
        border-left: 6px solid #2ea043;
    }
    .decision-banner-short {
        background: linear-gradient(135deg, rgba(218, 54, 51, 0.2) 0%, rgba(22, 27, 34, 0.9) 100%);
        border-left: 6px solid #f85149;
    }
    .decision-banner-neutral {
        background: linear-gradient(135deg, rgba(139, 148, 158, 0.15) 0%, rgba(22, 27, 34, 0.9) 100%);
        border-left: 6px solid #8b949e;
    }
    .status-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .badge-live { background-color: #238636; color: #ffffff; }
    .badge-delayed { background-color: #9e6a03; color: #ffffff; }
    .badge-historical { background-color: #484f58; color: #c9d1d9; }
    .badge-stale { background-color: #da3633; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SECTION 1: ASSET UNIVERSE & DATA PROVIDER ARCHITECTURE
# ==============================================================================

POPULAR_INDIAN_STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Larsen & Toubro": "LT.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "NIFTY 50 Index": "^NSEI",
    "Bank NIFTY Index": "^NSEBANK"
}

POPULAR_US_STOCKS = {
    "Apple Inc.": "AAPL",
    "Microsoft Corp.": "MSFT",
    "NVIDIA Corp.": "NVDA",
    "Amazon.com Inc.": "AMZN",
    "Alphabet Inc. (Google)": "GOOGL",
    "Tesla Inc.": "TSLA",
    "Meta Platforms": "META",
    "S&P 500 ETF (SPY)": "SPY",
    "Invesco QQQ Trust": "QQQ"
}

POPULAR_CRYPTO = {
    "Bitcoin (USD)": "BTC-USD",
    "Ethereum (USD)": "ETH-USD",
    "Solana (USD)": "SOL-USD",
    "Binance Coin (USD)": "BNB-USD",
    "Ripple (USD)": "XRP-USD",
    "Cardano (USD)": "ADA-USD"
}

# Yahoo Finance spot-FX symbols use BASEQUOTE=X format.
POPULAR_FOREX = {
    "AUD/CAD": "AUDCAD=X",
    "AUD/JPY": "AUDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/CAD": "EURCAD=X",
    "EUR/CHF": "EURCHF=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "EUR/USD": "EURUSD=X",
    "GBP/AUD": "GBPAUD=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/JPY": "GBPJPY=X",
    "GBP/USD": "GBPUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CAD": "USDCAD=X",
    "USD/CHF": "USDCHF=X",
    "USD/CNH": "USDCNH=X",
    "USD/INR": "USDINR=X",
    "USD/JPY": "USDJPY=X",
}


def normalize_forex_symbol(value: str) -> str:
    """Normalize common user-entered forex pairs to Yahoo Finance BASEQUOTE=X format."""
    raw = (value or "").strip().upper().replace(" ", "")
    if not raw:
        return ""
    if raw.endswith("=X"):
        return raw
    pair = raw.replace("/", "").replace("-", "").replace("_", "")
    if len(pair) == 6 and pair.isalpha():
        return f"{pair}=X"
    return raw

TIMEFRAME_PRESETS = {
    "Scalping (1m primary)": {"primary": "1m", "higher": "5m", "major": "15m", "period": "1d"},
    "Intraday (5m primary)": {"primary": "5m", "higher": "15m", "major": "1h", "period": "5d"},
    "Intraday (15m primary)": {"primary": "15m", "higher": "1h", "major": "4h", "period": "1mo"},
    "Swing (1h primary)": {"primary": "1h", "higher": "1d", "major": "1w", "period": "3mo"},
    "Long-Term (1d primary)": {"primary": "1d", "higher": "1w", "major": "1mo", "period": "2y"},
    "Custom Timeframe": {"primary": "15m", "higher": "1h", "major": "1d", "period": "1mo"}
}

# Standardized OHLCV Schema: [Open, High, Low, Close, Volume] with DateTime index
REQUIRED_OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]

class BaseDataProvider:
    """Abstract base for data ingestion providers."""
    def fetch_ohlcv(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        raise NotImplementedError

class YahooFinanceProvider(BaseDataProvider):
    """Yahoo Finance API provider using yfinance."""
    def fetch_ohlcv(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval, auto_adjust=False, prepost=False)
            return self._clean_raw_df(df)
        except Exception as e:
            st.warning(f"Yahoo Finance data fetch error: {e}")
            return pd.DataFrame()

    @staticmethod
    def _clean_raw_df(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.copy()
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df.columns = df.columns.get_level_values(0)
            except Exception:
                df.columns = [str(c[0]) for c in df.columns]

        rename_map = {}
        for col in df.columns:
            c_low = str(col).lower().replace(" ", "").replace("_", "")
            if c_low in ["open", "o"]: rename_map[col] = "Open"
            elif c_low in ["high", "h"]: rename_map[col] = "High"
            elif c_low in ["low", "l"]: rename_map[col] = "Low"
            elif c_low in ["close", "c"]: rename_map[col] = "Close"
            elif c_low in ["volume", "v", "vol"]: rename_map[col] = "Volume"

        df = df.rename(columns=rename_map)
        missing = [c for c in REQUIRED_OHLCV_COLUMNS if c not in df.columns]
        if missing:
            return pd.DataFrame()

        df = df[REQUIRED_OHLCV_COLUMNS].copy()
        for c in REQUIRED_OHLCV_COLUMNS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna()
        df = df[~df.index.duplicated(keep="last")]
        df = df.sort_index()
        return df

class CustomCSVProvider(BaseDataProvider):
    """Custom CSV URL provider."""
    def __init__(self, url: str):
        self.url = url

    def fetch_ohlcv(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        if not self.url or not self.url.startswith("http"):
            return pd.DataFrame()
        try:
            resp = requests.get(self.url, timeout=12, headers={"User-Agent": "MarketAnalyzer/2.0"})
            resp.raise_for_status()
            df = pd.read_csv(StringIO(resp.text))
            return self._normalize_tabular(df)
        except Exception as e:
            st.warning(f"Custom CSV fetch failed: {e}")
            return pd.DataFrame()

    @staticmethod
    def _normalize_tabular(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return pd.DataFrame()
        # Look for datetime column
        dt_col = None
        for col in df.columns:
            if str(col).lower() in ["datetime", "date", "timestamp", "time"]:
                dt_col = col
                break
        if dt_col:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
            df = df.dropna(subset=[dt_col])
            df = df.set_index(dt_col)
        return YahooFinanceProvider._clean_raw_df(df)

class CustomJSONProvider(BaseDataProvider):
    """Custom JSON API provider."""
    def __init__(self, url: str):
        self.url = url

    def fetch_ohlcv(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        if not self.url or not self.url.startswith("http"):
            return pd.DataFrame()
        try:
            resp = requests.get(self.url, timeout=12, headers={"User-Agent": "MarketAnalyzer/2.0"})
            resp.raise_for_status()
            payload = resp.json()
            records = self._find_records(payload)
            if not records:
                return pd.DataFrame()
            df = pd.DataFrame(records)
            return CustomCSVProvider._normalize_tabular(df)
        except Exception as e:
            st.warning(f"Custom JSON fetch failed: {e}")
            return pd.DataFrame()

    def _find_records(self, obj: Any) -> Optional[List[Dict]]:
        if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
            return obj
        if isinstance(obj, dict):
            for k in ["data", "candles", "bars", "results", "prices", "records", "ohlcv"]:
                if k in obj and isinstance(obj[k], list):
                    return obj[k]
            for v in obj.values():
                res = self._find_records(v)
                if res: return res
        return None



class AngelOneProvider(BaseDataProvider):
    """Angel One SmartAPI candle provider. Credentials are read from environment variables."""

    INTERVAL_MAP = {
        "1m": "ONE_MINUTE",
        "3m": "THREE_MINUTE",
        "5m": "FIVE_MINUTE",
        "10m": "TEN_MINUTE",
        "15m": "FIFTEEN_MINUTE",
        "30m": "THIRTY_MINUTE",
        "1h": "ONE_HOUR",
        "1d": "ONE_DAY",
    }
    MAX_DAYS = {
        "1m": 30, "3m": 60, "5m": 100, "10m": 100,
        "15m": 200, "30m": 200, "1h": 400, "1d": 2000,
    }

    def __init__(self, exchange: str, symbol_token: str):
        self.exchange = exchange.strip().upper()
        self.symbol_token = symbol_token.strip()

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _login(api_key: str, client_code: str, pin: str, totp_secret: str):
        # Imported only when Angel One is selected, so other providers don't need these packages.
        import pyotp
        from SmartApi import SmartConnect

        client = SmartConnect(api_key=api_key)
        otp = pyotp.TOTP(totp_secret).now()
        session = client.generateSession(client_code, pin, otp)
        if not isinstance(session, dict) or not session.get("status"):
            message = session.get("message", "Login failed") if isinstance(session, dict) else "Login failed"
            raise RuntimeError(f"Angel One login failed: {message}")
        return client

    def fetch_ohlcv(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        required = {
            "ANGELONE_API_KEY": os.getenv("ANGELONE_API_KEY", "").strip(),
            "ANGELONE_CLIENT_CODE": os.getenv("ANGELONE_CLIENT_CODE", "").strip(),
            "ANGELONE_PIN": os.getenv("ANGELONE_PIN", "").strip(),
            "ANGELONE_TOTP_SECRET": os.getenv("ANGELONE_TOTP_SECRET", "").strip(),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            st.error("Angel One credentials are missing from environment variables: " + ", ".join(missing))
            return pd.DataFrame()

        if not self.symbol_token:
            st.error("Enter the Angel One symbol token for the selected instrument.")
            return pd.DataFrame()
        if interval not in self.INTERVAL_MAP:
            st.warning(f"Angel One does not support the selected candle interval ({interval}) in this app. Choose 1m, 3m, 5m, 10m, 15m, 30m, 1h, or 1d.")
            return pd.DataFrame()

        try:
            client = self._login(
                required["ANGELONE_API_KEY"],
                required["ANGELONE_CLIENT_CODE"],
                required["ANGELONE_PIN"],
                required["ANGELONE_TOTP_SECRET"],
            )
            now = datetime.now().astimezone()
            try:
                if period.endswith("mo"):
                    requested_days = int(period[:-2]) * 30
                elif period.endswith("y"):
                    requested_days = int(period[:-1]) * 365
                elif period.endswith("d"):
                    requested_days = int(period[:-1])
                else:
                    requested_days = 30
            except Exception:
                requested_days = 30
            days = max(1, min(requested_days, self.MAX_DAYS[interval]))
            start = now - timedelta(days=days)
            params = {
                "exchange": self.exchange,
                "symboltoken": self.symbol_token,
                "interval": self.INTERVAL_MAP[interval],
                "fromdate": start.strftime("%Y-%m-%d %H:%M"),
                "todate": now.strftime("%Y-%m-%d %H:%M"),
            }
            response = client.getCandleData(params)
            if not isinstance(response, dict) or not response.get("status"):
                message = response.get("message", "Unknown API response") if isinstance(response, dict) else "Invalid API response"
                st.warning(f"Angel One candle request failed: {message}")
                return pd.DataFrame()

            rows = response.get("data") or []
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows, columns=["Datetime", "Open", "High", "Low", "Close", "Volume"])
            df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
            df = df.dropna(subset=["Datetime"]).set_index("Datetime")
            return YahooFinanceProvider._clean_raw_df(df)
        except Exception as e:
            st.warning(f"Angel One data fetch failed: {type(e).__name__}: {e}")
            return pd.DataFrame()


# ==============================================================================
# SECTION 2: DATA QUALITY ENGINE
# ==============================================================================

class DataQualityEngine:
    """
    Validates incoming market data for integrity, gaps, logic inconsistencies,
    and stale candles before any analytical pipeline runs.
    """
    @staticmethod
    def audit_dataset(df: pd.DataFrame, interval: str, is_forex: bool = False) -> Dict[str, Any]:
        report = {
            "is_valid": True,
            "quality_grade": "HIGH",
            "score": 100,
            "issues": [],
            "metrics": {},
            "stale_status": "OK"
        }

        if df is None or df.empty or len(df) < 35:
            report["is_valid"] = False
            report["quality_grade"] = "LOW"
            report["score"] = 0
            report["issues"].append(f"Insufficient historical candles (found {0 if df is None else len(df)}, minimum required: 35).")
            return report

        total_rows = len(df)
        issues = []
        score_deductions = 0

        # 1. Monotonic timestamps & duplicates
        if not df.index.is_monotonic_increasing:
            issues.append("Timestamps are not in strict monotonic chronological order.")
            score_deductions += 15

        dupes = df.index.duplicated().sum()
        if dupes > 0:
            issues.append(f"Found {dupes} duplicate timestamp records.")
            score_deductions += min(20, dupes * 5)

        # 2. Logic violations: High < Low, Close outside [Low, High], Open outside [Low, High]
        invalid_hl = (df["High"] < df["Low"]).sum()
        if invalid_hl > 0:
            issues.append(f"Fatal: Found {invalid_hl} candles where High < Low.")
            score_deductions += 40

        invalid_close = ((df["Close"] > df["High"]) | (df["Close"] < df["Low"])).sum()
        if invalid_close > 0:
            issues.append(f"Found {invalid_close} candles where Close is outside [Low, High] bounds.")
            score_deductions += 25

        invalid_open = ((df["Open"] > df["High"]) | (df["Open"] < df["Low"])).sum()
        if invalid_open > 0:
            issues.append(f"Found {invalid_open} candles where Open is outside [Low, High] bounds.")
            score_deductions += 25

        # 3. Non-positive prices
        non_positive = ((df["Open"] <= 0) | (df["High"] <= 0) | (df["Low"] <= 0) | (df["Close"] <= 0)).sum()
        if non_positive > 0:
            issues.append(f"Found {non_positive} candles with non-positive prices.")
            score_deductions += 35

        # 4. Volume verification
        neg_vol = (df["Volume"] < 0).sum()
        if neg_vol > 0:
            issues.append(f"Found {neg_vol} negative volume values.")
            score_deductions += 20

        zero_vol_ratio = (df["Volume"] == 0).sum() / total_rows
        # Spot forex is decentralized; some feeds have no meaningful centralized volume.
        if not is_forex and zero_vol_ratio > 0.40:
            issues.append(f"Suspicious volume: {zero_vol_ratio * 100:.1f}% of candles report zero volume (possible illiquidity or synthetic quotes).")
            score_deductions += 15

        # 5. Outlier price shock / flash spikes
        returns = df["Close"].pct_change().abs()
        extreme_jumps = (returns > 0.30).sum() # >30% single-candle move
        if extreme_jumps > 0:
            issues.append(f"Detected {extreme_jumps} abnormal price jumps (>30% single-bar change). Inspect for split anomalies or bad ticks.")
            score_deductions += 20

        # Calculate final quality score
        final_score = max(0, 100 - score_deductions)
        report["score"] = final_score
        if final_score >= 80:
            report["quality_grade"] = "HIGH"
        elif final_score >= 55:
            report["quality_grade"] = "MODERATE"
        else:
            report["quality_grade"] = "LOW"
            report["is_valid"] = False

        report["issues"] = issues
        report["metrics"] = {
            "total_candles": total_rows,
            "zero_vol_pct": f"{zero_vol_ratio * 100:.1f}%",
            "start_time": str(df.index[0]),
            "end_time": str(df.index[-1]),
        }
        return report

# ==============================================================================
# SECTION 3: REAL-TIME DATA STATUS DETECTOR
# ==============================================================================

class RealTimeStatusEngine:
    """Analyzes timestamp freshness and market operating schedule."""
    @staticmethod
    def evaluate_freshness(df: pd.DataFrame, interval: str) -> Dict[str, Any]:
        if df.empty:
            return {"status": "NO DATA", "age_str": "N/A", "is_stale": True, "badge_class": "badge-stale"}

        latest_ts = df.index[-1]
        # Ensure UTC or localized comparison
        now_utc = datetime.now(timezone.utc)
        if latest_ts.tzinfo is None:
            # Assume local system timezone
            diff = datetime.now() - latest_ts
        else:
            diff = now_utc - latest_ts

        total_seconds = max(0, diff.total_seconds())
        minutes = total_seconds / 60
        hours = minutes / 60

        if hours < 1:
            age_str = f"{minutes:.1f} min ago"
        elif hours < 24:
            age_str = f"{hours:.1f} hours ago"
        else:
            days = hours / 24
            age_str = f"{days:.1f} days ago"

        # Freshness criteria depends on interval
        interval_mins = 15
        if interval.endswith("m"):
            interval_mins = int(interval[:-1])
        elif interval.endswith("h"):
            interval_mins = int(interval[:-1]) * 60
        elif interval.endswith("d"):
            interval_mins = 1440

        is_stale = False
        if minutes < max(10, interval_mins * 2.5):
            status = "LIVE DATA"
            badge_class = "badge-live"
        elif hours < 24:
            status = "DELAYED DATA"
            badge_class = "badge-delayed"
        else:
            status = "HISTORICAL DATA"
            badge_class = "badge-historical"
            if interval in ["1m", "5m", "15m"]:
                is_stale = True

        return {
            "status": status,
            "age_str": age_str,
            "latest_candle_time": str(latest_ts),
            "is_stale": is_stale,
            "badge_class": badge_class,
            "minutes_old": minutes
        }

# ==============================================================================
# SECTION 4: TECHNICAL INDICATORS & SESSION VWAP (NO LOOK-AHEAD)
# ==============================================================================

def calculate_session_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Computes strictly session-anchored VWAP for intraday data,
    resetting daily at the start of each trading session.
    """
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    tp_vol = typical_price * df["Volume"]

    # Check if index contains timestamps
    try:
        session_dates = df.index.date
        vwap_series = pd.Series(index=df.index, dtype=float)
        # Group cumulative values per session date
        for d in np.unique(session_dates):
            mask = session_dates == d
            sub_tp_vol = tp_vol[mask]
            sub_vol = df["Volume"][mask]
            cum_tpv = sub_tp_vol.cumsum()
            cum_vol = sub_vol.cumsum().replace(0, np.nan)
            vwap_series[mask] = cum_tpv / cum_vol
        return vwap_series.bfill().ffill()
    except Exception:
        # Fallback to rolling anchored VWAP if dates cannot be parsed
        cum_tpv = tp_vol.cumsum()
        cum_vol = df["Volume"].cumsum().replace(0, np.nan)
        return (cum_tpv / cum_vol).ffill()

def calculate_wilder_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's smoothed RSI implementation."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Computes ADX, DI+, DI- using Wilder's directional movement system."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_di = 100.0 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1.0 / period, adjust=False).mean() / atr.replace(0, np.nan))
    minus_di = 100.0 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1.0 / period, adjust=False).mean() / atr.replace(0, np.nan))

    dx = 100.0 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.ewm(alpha=1.0 / period, adjust=False).mean().fillna(20.0)
    return adx, plus_di.fillna(20.0), minus_di.fillna(20.0)

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates full technical indicator set without look-ahead bias."""
    if df.empty or len(df) < 10:
        return df

    d = df.copy()
    close, high, low, vol = d["Close"], d["High"], d["Low"], d["Volume"]

    # 1. Moving Averages
    d["EMA9"] = close.ewm(span=9, adjust=False).mean()
    d["EMA21"] = close.ewm(span=21, adjust=False).mean()
    d["SMA20"] = close.rolling(20, min_periods=5).mean()
    d["SMA50"] = close.rolling(50, min_periods=10).mean()
    d["SMA200"] = close.rolling(200, min_periods=20).mean()

    # Moving Average Slopes (percentage change over 3 bars)
    d["EMA9_Slope"] = (d["EMA9"] - d["EMA9"].shift(3)) / (d["EMA9"].shift(3).replace(0, np.nan)) * 100.0
    d["SMA50_Slope"] = (d["SMA50"] - d["SMA50"].shift(5)) / (d["SMA50"].shift(5).replace(0, np.nan)) * 100.0

    # 2. RSI (Wilder)
    d["RSI"] = calculate_wilder_rsi(close, 14)

    # 3. MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    d["MACD"] = ema12 - ema26
    d["MACD_Signal"] = d["MACD"].ewm(span=9, adjust=False).mean()
    d["MACD_Hist"] = d["MACD"] - d["MACD_Signal"]

    # 4. Bollinger Bands (20, 2)
    bb_mid = d["SMA20"]
    bb_std = close.rolling(20, min_periods=5).std().replace(0, np.nan)
    d["BB_Middle"] = bb_mid
    d["BB_Upper"] = bb_mid + (2.0 * bb_std)
    d["BB_Lower"] = bb_mid - (2.0 * bb_std)
    d["BB_Width"] = (d["BB_Upper"] - d["BB_Lower"]) / bb_mid.replace(0, np.nan)
    d["BB_PctB"] = (close - d["BB_Lower"]) / (d["BB_Upper"] - d["BB_Lower"]).replace(0, np.nan)

    # 5. ATR (14) & ATR Percentile (over 60 bars)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    d["ATR"] = tr.rolling(14, min_periods=5).mean().bfill()
    # Percentile rank over rolling 60 bars
    d["ATR_Percentile"] = d["ATR"].rolling(60, min_periods=15).apply(
        lambda s: (s.iloc[-1] <= s).mean() * 100.0 if len(s) > 0 else 50.0, raw=False
    ).fillna(50.0)

    # 6. Session-Anchored VWAP
    d["VWAP"] = calculate_session_vwap(d)

    # 7. ADX & Directional Movement
    adx, p_di, m_di = calculate_adx(d, 14)
    d["ADX"] = adx
    d["DI_Plus"] = p_di
    d["DI_Minus"] = m_di

    # 8. Volume Analytics
    d["Vol_SMA20"] = vol.rolling(20, min_periods=5).mean()
    d["Volume_Ratio"] = vol / d["Vol_SMA20"].replace(0, np.nan)

    # 9. Stochastic Oscillator (%K, %D)
    low14 = low.rolling(14, min_periods=5).min()
    high14 = high.rolling(14, min_periods=5).max()
    d["Stoch_K"] = 100.0 * ((close - low14) / (high14 - low14).replace(0, np.nan))
    d["Stoch_D"] = d["Stoch_K"].rolling(3, min_periods=1).mean().fillna(50.0)

    # 10. Rate of Change (ROC 12)
    d["ROC12"] = close.pct_change(12).fillna(0.0) * 100.0

    return d

# ==============================================================================
# SECTION 5: MARKET REGIME ENGINE (10 OBJECTIVE REGIMES)
# ==============================================================================

class MarketRegimeEngine:
    """
    Classifies market into 10 objective regimes without relying on a single indicator.
    Evaluates ADX, moving average alignment, volatility percentiles, and momentum.
    """
    REGIMES = [
        "Strong Bull Trend",
        "Weak Bull Trend",
        "Strong Bear Trend",
        "Weak Bear Trend",
        "Sideways / Range",
        "High Volatility",
        "Low Volatility / Squeeze",
        "Breakout Regime",
        "Mean-Reversion Regime",
        "Unstable / Unknown Regime"
    ]

    @staticmethod
    def identify_regime(df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or len(df) < 25:
            return {
                "regime": "Unstable / Unknown Regime",
                "description": "Insufficient candles to assess regime stability.",
                "adx": 0.0,
                "volatility_state": "Normal",
                "trend_bias": "Neutral"
            }

        last = df.iloc[-1]
        close = last["Close"]
        adx = last.get("ADX", 20.0)
        p_di = last.get("DI_Plus", 20.0)
        m_di = last.get("DI_Minus", 20.0)
        atr_pct = last.get("ATR_Percentile", 50.0)
        bb_width = last.get("BB_Width", 0.05)
        ema9 = last.get("EMA9", close)
        ema21 = last.get("EMA21", close)
        sma50 = last.get("SMA50", close)
        vol_ratio = last.get("Volume_Ratio", 1.0)
        rsi = last.get("RSI", 50.0)

        # Volatility assessment
        is_high_vol = atr_pct >= 80.0
        is_squeeze = atr_pct <= 20.0 or bb_width < 0.035

        # Trend conditions
        bull_ma_stack = (close > ema9) and (ema9 > ema21) and (pd.isna(sma50) or close > sma50)
        bear_ma_stack = (close < ema9) and (ema9 < ema21) and (pd.isna(sma50) or close < sma50)

        # Breakout condition (recent price exceeding 20-bar high/low with volume)
        recent_20_high = df["High"].iloc[-21:-1].max() if len(df) >= 22 else df["High"].max()
        recent_20_low = df["Low"].iloc[-21:-1].min() if len(df) >= 22 else df["Low"].min()
        is_breakout = (close > recent_20_high or close < recent_20_low) and (vol_ratio >= 1.4)

        # Classification Hierarchy
        if is_breakout:
            regime = "Breakout Regime"
            desc = "Price penetrating 20-bar extremes accompanied by expanding volume."
        elif is_high_vol:
            regime = "High Volatility"
            desc = f"ATR percentile is extreme ({atr_pct:.1f}%). Wide swings and elevated risk."
        elif is_squeeze:
            regime = "Low Volatility / Squeeze"
            desc = "Bollinger Bands compressed; volatility contraction preceding expansion."
        elif adx >= 25.0 and bull_ma_stack and (p_di > m_di):
            regime = "Strong Bull Trend"
            desc = f"ADX is robust ({adx:.1f}) with pristine bullish EMA/SMA stack and DI+ dominance."
        elif adx >= 25.0 and bear_ma_stack and (m_di > p_di):
            regime = "Strong Bear Trend"
            desc = f"ADX is robust ({adx:.1f}) with bearish EMA/SMA stack and DI- dominance."
        elif bull_ma_stack and close > ema21:
            regime = "Weak Bull Trend"
            desc = "Upward drift with moderate trend momentum (ADX < 25)."
        elif bear_ma_stack and close < ema21:
            regime = "Weak Bear Trend"
            desc = "Downward drift with moderate trend momentum (ADX < 25)."
        elif (rsi >= 75.0 or rsi <= 25.0) and (adx < 22.0):
            regime = "Mean-Reversion Regime"
            desc = f"RSI oscillator at extreme ({rsi:.1f}) in non-trending structure; reversion probable."
        elif adx < 20.0 and abs(ema9 - ema21) / close < 0.008:
            regime = "Sideways / Range"
            desc = f"ADX low ({adx:.1f}) and moving averages intertwined. Market in consolidation."
        else:
            regime = "Unstable / Unknown Regime"
            desc = "Conflicting indicators or transition phase without clear consensus."

        trend_bias = "Bullish" if "Bull" in regime else ("Bearish" if "Bear" in regime else "Neutral")

        return {
            "regime": regime,
            "description": desc,
            "adx": round(float(adx), 1),
            "atr_pct": round(float(atr_pct), 1),
            "volatility_state": "High" if is_high_vol else ("Squeeze" if is_squeeze else "Normal"),
            "trend_bias": trend_bias
        }

# ==============================================================================
# SECTION 6: SUPPORT & RESISTANCE ZONES & PIVOTS
# ==============================================================================

class SupportResistanceEngine:
    """Detects multi-touch support/resistance zones, swing fractals, and pivot levels."""
    @staticmethod
    def extract_zones(df: pd.DataFrame, window: int = 5) -> Dict[str, Any]:
        if df.empty or len(df) < (window * 2 + 5):
            return {"supports": [], "resistances": [], "nearest_support": None, "nearest_resistance": None}

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        atr = df["ATR"].iloc[-1] if "ATR" in df.columns else (highs[-1] - lows[-1])
        curr_price = closes[-1]

        swing_highs = []
        swing_lows = []

        # Find fractal swing points
        for i in range(window, len(df) - window):
            h_val = highs[i]
            l_val = lows[i]
            if all(h_val >= highs[i - k] for k in range(1, window + 1)) and all(h_val >= highs[i + k] for k in range(1, window + 1)):
                swing_highs.append(h_val)
            if all(l_val <= lows[i - k] for k in range(1, window + 1)) and all(l_val <= lows[i + k] for k in range(1, window + 1)):
                swing_lows.append(l_val)

        # Cluster levels into zones (tolerance = 0.35 * ATR)
        cluster_tol = max(0.01, float(atr) * 0.35)

        def cluster_levels(levels: List[float]) -> List[Dict[str, float]]:
            if not levels: return []
            levels = sorted(levels)
            clusters = []
            curr_cluster = [levels[0]]
            for lev in levels[1:]:
                if lev - curr_cluster[-1] <= cluster_tol:
                    curr_cluster.append(lev)
                else:
                    clusters.append(curr_cluster)
                    curr_cluster = [lev]
            clusters.append(curr_cluster)

            zones = []
            for c in clusters:
                avg_val = float(np.mean(c))
                zones.append({
                    "level": round(avg_val, 2),
                    "min": round(float(np.min(c)), 2),
                    "max": round(float(np.max(c)), 2),
                    "touches": len(c)
                })
            return sorted(zones, key=lambda z: z["touches"], reverse=True)

        res_clusters = cluster_levels([sh for sh in swing_highs if sh >= curr_price])
        sup_clusters = cluster_levels([sl for sl in swing_lows if sl <= curr_price])

        nearest_res = None
        if res_clusters:
            # find closest above price
            overhead = [r for r in res_clusters if r["level"] > curr_price]
            if overhead:
                nearest_res = min(overhead, key=lambda r: r["level"] - curr_price)

        nearest_sup = None
        if sup_clusters:
            under = [s for s in sup_clusters if s["level"] < curr_price]
            if under:
                nearest_sup = min(under, key=lambda s: curr_price - s["level"])

        return {
            "resistances": res_clusters[:4],
            "supports": sup_clusters[:4],
            "nearest_resistance": nearest_res,
            "nearest_support": nearest_sup,
            "cluster_tol": cluster_tol
        }

# ==============================================================================
# SECTION 7: PRICE ACTION & BREAKOUT VALIDATION ENGINE
# ==============================================================================

class PriceActionEngine:
    """Identifies candlestick structures, swing sequences, and validates breakouts."""
    @staticmethod
    def evaluate(df: pd.DataFrame, sr_data: Dict[str, Any]) -> Dict[str, Any]:
        if df.empty or len(df) < 5:
            return {"patterns": [], "breakout_status": "None", "structure": "Neutral", "score": 0}

        patterns = []
        score = 0
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        o, h, l, c = latest["Open"], latest["High"], latest["Low"], latest["Close"]
        po, ph, pl, pc = prev["Open"], prev["High"], prev["Low"], prev["Close"]
        body = abs(c - o)
        rng = max(0.0001, h - l)
        atr = latest.get("ATR", rng)
        vol_ratio = latest.get("Volume_Ratio", 1.0)

        # 1. Candlestick patterns
        # Pin Bar / Hammer (lower wick >= 60% of candle range, close in upper half)
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        if lower_wick / rng >= 0.55 and (c >= o or upper_wick / rng <= 0.25):
            patterns.append("Bullish Hammer / Pin Bar")
            score += 2
        elif upper_wick / rng >= 0.55 and (c <= o or lower_wick / rng <= 0.25):
            patterns.append("Bearish Shooting Star / Pin Bar")
            score -= 2

        # Engulfing
        if c > o and pc < po and c >= ph and o <= pc:
            patterns.append("Bullish Engulfing")
            score += 2
        elif c < o and pc > po and c <= pl and o >= pc:
            patterns.append("Bearish Engulfing")
            score -= 2

        # Inside Bar
        if h <= ph and l >= pl:
            patterns.append("Inside Bar (Compression)")

        # Momentum Bar (body > 75% of full range)
        if body / rng >= 0.75:
            if c > o:
                patterns.append("Bullish Momentum Marubozu")
                score += 1
            else:
                patterns.append("Bearish Momentum Marubozu")
                score -= 1

        # 2. Market Structure (HH/HL vs LH/LL)
        last_5_h = df["High"].iloc[-5:].values
        last_5_l = df["Low"].iloc[-5:].values
        if last_5_h[-1] > last_5_h[-3] and last_5_l[-1] > last_5_l[-3]:
            structure = "Higher Highs / Higher Lows (Bullish)"
            score += 1
        elif last_5_h[-1] < last_5_h[-3] and last_5_l[-1] < last_5_l[-3]:
            structure = "Lower Highs / Lower Lows (Bearish)"
            score -= 1
        else:
            structure = "Mixed / Consolidating"

        # 3. Breakout Validation
        breakout_status = "None"
        near_res = sr_data.get("nearest_resistance")
        near_sup = sr_data.get("nearest_support")

        if near_res and c > near_res["level"]:
            dist = c - near_res["level"]
            if dist >= 0.25 * atr and vol_ratio >= 1.3:
                breakout_status = "Confirmed Resistance Breakout"
                score += 3
                patterns.append("Confirmed Breakout (Vol + ATR Verified)")
            elif dist < 0.15 * atr or vol_ratio < 1.0:
                breakout_status = "Potential Breakout (Unconfirmed / Low Vol)"
                patterns.append("Unconfirmed Breakout (Lacks Volume Expansion)")
            else:
                breakout_status = "Breakout Attempt"
        elif near_sup and c < near_sup["level"]:
            dist = near_sup["level"] - c
            if dist >= 0.25 * atr and vol_ratio >= 1.3:
                breakout_status = "Confirmed Support Breakdown"
                score -= 3
                patterns.append("Confirmed Breakdown (Vol + ATR Verified)")
            elif dist < 0.15 * atr or vol_ratio < 1.0:
                breakout_status = "Potential Breakdown (Unconfirmed)"
                patterns.append("Unconfirmed Breakdown (Lacks Volume Expansion)")
            else:
                breakout_status = "Breakdown Attempt"

        return {
            "patterns": patterns,
            "breakout_status": breakout_status,
            "structure": structure,
            "score": score
        }

# ==============================================================================
# SECTION 8: NEWS SENTIMENT & EVENT RISK ENGINE
# ==============================================================================

class NewsEventEngine:
    """
    Fetches news, evaluates sentiment, detects critical financial events,
    and calculates a strictly bounded, non-dominating sentiment score.
    """
    EVENT_KEYWORDS = {
        "Earnings": ["earnings", "quarterly result", "revenue beat", "eps", "q1", "q2", "q3", "q4", "financial results"],
        "Guidance": ["guidance", "outlook", "forecast", "projection", "estimates"],
        "Analyst Action": ["upgrade", "downgrade", "price target", "rating", "outperform", "underperform"],
        "M&A / Acquisition": ["merger", "acquisition", "takeover", "buys", "deal", "stake"],
        "Regulatory / Legal": ["regulatory", "lawsuit", "sec", "doj", "investigation", "fine", "court", "probe"],
        "Macro / Policy": ["inflation", "cpi", "fed", "interest rate", "rbi", "central bank", "rate hike", "rate cut"]
    }

    @staticmethod
    def analyze_news(symbol: str, count: int = 10) -> Dict[str, Any]:
        result = {
            "articles": [],
            "mean_score": 0.0,
            "sentiment_label": "Neutral",
            "events_detected": [],
            "high_event_risk": False,
            "bounded_contribution": 0.0
        }

        try:
            ticker = yf.Ticker(symbol)
            raw = ticker.get_news(count=count)
            if not raw:
                return result

            rows = []
            events_found = set()

            for item in raw:
                content = item.get("content", item)
                title = content.get("title", "")
                summary = content.get("summary", "")
                provider = content.get("provider", {})
                p_name = provider.get("displayName", "") if isinstance(provider, dict) else str(provider)
                url = content.get("canonicalUrl", {}).get("url", "") if isinstance(content.get("canonicalUrl", {}), dict) else ""
                if not url and isinstance(content.get("clickThroughUrl", {}), dict):
                    url = content.get("clickThroughUrl", {}).get("url", "")

                full_text = f"{title} {summary}"

                # Calculate Sentiment
                if VADER_AVAILABLE and full_text.strip():
                    compound = vader_analyzer.polarity_scores(full_text)["compound"]
                else:
                    # Lexicon fallback
                    pos_words = ["gain", "beat", "profit", "surge", "growth", "record", "strong", "bullish", "jump", "success"]
                    neg_words = ["loss", "miss", "drop", "fall", "decline", "weak", "lawsuit", "debt", "crash", "bearish"]
                    t_low = full_text.lower()
                    p_c = sum(1 for w in pos_words if w in t_low)
                    n_c = sum(1 for w in neg_words if w in t_low)
                    tot = p_c + n_c
                    compound = (p_c - n_c) / tot if tot > 0 else 0.0

                # Detect events
                for evt, kws in NewsEventEngine.EVENT_KEYWORDS.items():
                    if any(kw in full_text.lower() for kw in kws):
                        events_found.add(evt)

                rows.append({
                    "title": title,
                    "publisher": p_name or "Financial Feed",
                    "score": round(compound, 3),
                    "url": url
                })

            if rows:
                scores = [r["score"] for r in rows]
                mean_sc = float(np.mean(scores))
                result["articles"] = rows
                result["mean_score"] = round(mean_sc, 3)
                if mean_sc > 0.15:
                    result["sentiment_label"] = "Positive"
                elif mean_sc < -0.15:
                    result["sentiment_label"] = "Negative"
                else:
                    result["sentiment_label"] = "Neutral"

                result["events_detected"] = list(events_found)
                if any(e in events_found for e in ["Earnings", "Regulatory / Legal"]):
                    result["high_event_risk"] = True

                # Capped contribution to overall engine: strictly within [-2.0, +2.0]
                result["bounded_contribution"] = float(np.clip(mean_sc * 2.0, -2.0, 2.0))

        except Exception as e:
            pass

        return result

# ==============================================================================
# SECTION 9: MULTI-TIMEFRAME ENGINE
# ==============================================================================

class MultiTimeframeEngine:
    """Downloads and aligns supporting higher timeframe (HTF) data."""
    @staticmethod
    def analyze_alignment(symbol: str, primary_interval: str, higher_interval: str, provider: BaseDataProvider) -> Dict[str, Any]:
        res = {
            "htf_interval": higher_interval,
            "htf_trend": "Unknown",
            "htf_adx": 0.0,
            "alignment_score": 50,  # 0 to 100
            "agrees_with_primary": True,
            "conflict_warning": None
        }

        # Select period for HTF
        htf_period = "1mo" if higher_interval in ["1h", "4h"] else ("1y" if higher_interval in ["1d", "1w"] else "5d")
        htf_df = provider.fetch_ohlcv(symbol, htf_period, higher_interval)

        if htf_df.empty or len(htf_df) < 20:
            res["htf_trend"] = "Data Insufficient"
            return res

        htf_df = compute_all_indicators(htf_df)
        last = htf_df.iloc[-1]
        c = last["Close"]
        ema9 = last.get("EMA9", c)
        ema21 = last.get("EMA21", c)
        sma50 = last.get("SMA50", c)
        adx = last.get("ADX", 20.0)

        res["htf_adx"] = round(float(adx), 1)

        if c > ema9 and ema9 > ema21:
            res["htf_trend"] = "Strong Bullish" if adx > 25 else "Moderate Bullish"
            res["alignment_score"] = 85
        elif c < ema9 and ema9 < ema21:
            res["htf_trend"] = "Strong Bearish" if adx > 25 else "Moderate Bearish"
            res["alignment_score"] = 15
        else:
            res["htf_trend"] = "Neutral / Sideways"
            res["alignment_score"] = 50

        return res

# ==============================================================================
# SECTION 10: INDEPENDENT MODELS & REGIME-AWARE ENSEMBLE
# ==============================================================================

class MultiModelEnsemble:
    """
    Evaluates 6 independent analytical models:
    A: Trend-Following
    B: Momentum
    C: Mean-Reversion
    D: Breakout
    E: Price Action
    F: Multi-Timeframe
    Applies regime-specific dynamic weighting to ensure models match market conditions.
    """
    @staticmethod
    def run_models(df: pd.DataFrame, htf_data: Dict[str, Any], regime: str, pa_data: Dict[str, Any]) -> Dict[str, Any]:
        latest = df.iloc[-1]
        close = latest["Close"]

        # --- MODEL A: Trend-Following ---
        ema9 = latest.get("EMA9", close)
        ema21 = latest.get("EMA21", close)
        sma50 = latest.get("SMA50", close)
        sma200 = latest.get("SMA200", close)
        adx = latest.get("ADX", 20.0)

        score_a = 0
        if close > ema9 > ema21: score_a += 1
        if pd.notna(sma50) and close > sma50: score_a += 1
        if pd.notna(sma200) and close > sma200: score_a += 1
        if close < ema9 < ema21: score_a -= 1
        if pd.notna(sma50) and close < sma50: score_a -= 1
        if pd.notna(sma200) and close < sma200: score_a -= 1

        stance_a = "LONG" if score_a >= 2 else ("SHORT" if score_a <= -2 else "NO TRADE")

        # --- MODEL B: Momentum ---
        rsi = latest.get("RSI", 50.0)
        macd = latest.get("MACD", 0.0)
        macd_sig = latest.get("MACD_Signal", 0.0)
        stoch_k = latest.get("Stoch_K", 50.0)

        score_b = 0
        if rsi > 52 and macd > macd_sig: score_b += 1
        if stoch_k > 50: score_b += 1
        if rsi < 48 and macd < macd_sig: score_b -= 1
        if stoch_k < 50: score_b -= 1

        stance_b = "LONG" if score_b >= 1 else ("SHORT" if score_b <= -1 else "NO TRADE")

        # --- MODEL C: Mean-Reversion ---
        bb_pctb = latest.get("BB_PctB", 0.5)
        vwap = latest.get("VWAP", close)
        score_c = 0
        # Reversion buys at lower band / oversold; sells at upper band / overbought
        if bb_pctb <= 0.08 or rsi <= 28: score_c += 1
        if bb_pctb >= 0.92 or rsi >= 72: score_c -= 1
        stance_c = "LONG" if score_c >= 1 else ("SHORT" if score_c <= -1 else "NO TRADE")

        # --- MODEL D: Breakout ---
        bo_status = pa_data.get("breakout_status", "None")
        if "Breakout" in bo_status: stance_d = "LONG"
        elif "Breakdown" in bo_status: stance_d = "SHORT"
        else: stance_d = "NO TRADE"

        # --- MODEL E: Price Action ---
        pa_score = pa_data.get("score", 0)
        stance_e = "LONG" if pa_score >= 2 else ("SHORT" if pa_score <= -2 else "NO TRADE")

        # --- MODEL F: Multi-Timeframe ---
        htf_trend = htf_data.get("htf_trend", "Neutral")
        if "Bullish" in htf_trend: stance_f = "LONG"
        elif "Bearish" in htf_trend: stance_f = "SHORT"
        else: stance_f = "NO TRADE"

        all_stances = [stance_a, stance_b, stance_c, stance_d, stance_e, stance_f]
        long_count = all_stances.count("LONG")
        short_count = all_stances.count("SHORT")
        neutral_count = all_stances.count("NO TRADE")

        # Dynamic Regime Weighting
        if "Strong Bull" in regime or "Strong Bear" in regime:
            w = {"A": 0.35, "B": 0.25, "C": 0.05, "D": 0.10, "E": 0.10, "F": 0.15}
        elif "Sideways" in regime or "Mean-Reversion" in regime:
            w = {"A": 0.10, "B": 0.15, "C": 0.40, "D": 0.05, "E": 0.20, "F": 0.10}
        elif "Breakout" in regime:
            w = {"A": 0.20, "B": 0.15, "C": 0.05, "D": 0.35, "E": 0.15, "F": 0.10}
        else:
            w = {"A": 0.20, "B": 0.20, "C": 0.15, "D": 0.15, "E": 0.15, "F": 0.15}

        def to_num(stc): return 1.0 if stc == "LONG" else (-1.0 if stc == "SHORT" else 0.0)

        weighted_consensus = (
            to_num(stance_a) * w["A"] +
            to_num(stance_b) * w["B"] +
            to_num(stance_c) * w["C"] +
            to_num(stance_d) * w["D"] +
            to_num(stance_e) * w["E"] +
            to_num(stance_f) * w["F"]
        )

        return {
            "model_stances": {
                "Model A (Trend)": stance_a,
                "Model B (Momentum)": stance_b,
                "Model C (Mean Reversion)": stance_c,
                "Model D (Breakout)": stance_d,
                "Model E (Price Action)": stance_e,
                "Model F (Multi-Timeframe)": stance_f
            },
            "consensus_ratio": f"{long_count} Bullish / {short_count} Bearish / {neutral_count} Neutral",
            "weighted_consensus": round(weighted_consensus, 3),
            "dominant_stance": "LONG" if weighted_consensus >= 0.30 else ("SHORT" if weighted_consensus <= -0.30 else "NO TRADE")
        }

# ==============================================================================
# SECTION 11: HISTORICAL ANALOG ENGINE & PROBABILITY CALIBRATION
# ==============================================================================

class HistoricalAnalogEngine:
    """
    Searches historical dataset for matching feature setups:
    [Regime, RSI Bucket, MACD Sign, Trend Alignment, Volume Ratio, VWAP Position]
    Calculates empirical outcomes, Wilson score confidence intervals, MFE, and MAE.
    Prevents synthetic confidence when sample size is insufficient.
    """
    @staticmethod
    def find_analogs(df: pd.DataFrame, current_features: Dict[str, Any], forward_bars: int = 5) -> Dict[str, Any]:
        if df.empty or len(df) < 50:
            return {"sample_size": 0, "status": "INSUFFICIENT SAMPLE SIZE", "calibrated_prob": None}

        # Build feature matrix across history (excluding the most recent forward_bars to prevent lookahead)
        closes = df["Close"].values
        highs = df["High"].values
        lows = df["Low"].values
        rsis = df["RSI"].values
        macds = df["MACD"].values
        vwaps = df["VWAP"].values
        ema9s = df["EMA9"].values
        ema21s = df["EMA21"].values

        c_rsi_bucket = 2 if current_features["rsi"] >= 60 else (0 if current_features["rsi"] <= 40 else 1)
        c_macd_pos = current_features["macd"] >= 0
        c_ema_bull = current_features["ema9"] >= current_features["ema21"]
        c_vwap_above = current_features["close"] >= current_features["vwap"]

        matches_fwd_ret = []
        mfes = []
        maes = []

        # Scan historical bars
        for i in range(30, len(df) - forward_bars - 1):
            h_rsi_bucket = 2 if rsis[i] >= 60 else (0 if rsis[i] <= 40 else 1)
            h_macd_pos = macds[i] >= 0
            h_ema_bull = ema9s[i] >= ema21s[i]
            h_vwap_above = closes[i] >= vwaps[i]

            # Match criteria: at least 3 of 4 core regime/momentum features match
            match_score = (
                (h_rsi_bucket == c_rsi_bucket) +
                (h_macd_pos == c_macd_pos) +
                (h_ema_bull == c_ema_bull) +
                (h_vwap_above == c_vwap_above)
            )

            if match_score >= 3:
                entry_p = closes[i]
                future_closes = closes[i + 1 : i + 1 + forward_bars]
                future_highs = highs[i + 1 : i + 1 + forward_bars]
                future_lows = lows[i + 1 : i + 1 + forward_bars]

                ret = (future_closes[-1] - entry_p) / entry_p * 100.0
                mfe = (np.max(future_highs) - entry_p) / entry_p * 100.0
                mae = (entry_p - np.min(future_lows)) / entry_p * 100.0

                matches_fwd_ret.append(ret)
                mfes.append(mfe)
                maes.append(mae)

        sample_size = len(matches_fwd_ret)

        # Statistical Safety Rule: Minimum 15 setups required
        if sample_size < 15:
            return {
                "sample_size": sample_size,
                "status": "INSUFFICIENT SAMPLE SIZE",
                "win_rate": None,
                "calibrated_prob": None,
                "wilson_ci": (None, None),
                "avg_mfe": None,
                "avg_mae": None
            }

        # Calculate empirical win rates
        bull_wins = sum(1 for r in matches_fwd_ret if r > 0.0)
        p_hat = bull_wins / sample_size

        # Wilson Score 95% Confidence Interval for sample proportion
        z = 1.96
        denom = 1.0 + (z**2 / sample_size)
        center = (p_hat + (z**2 / (2 * sample_size))) / denom
        margin = (z * math.sqrt((p_hat * (1 - p_hat) / sample_size) + (z**2 / (4 * sample_size**2)))) / denom
        ci_lower = max(0.0, center - margin) * 100.0
        ci_upper = min(1.0, center + margin) * 100.0

        # Empirical Shrinkage / Platt calibration: pull toward neutral 50% prior
        # P_calibrated = (wins + 10 * 0.5) / (N + 10)
        calibrated_prob = ((bull_wins + 5.0) / (sample_size + 10.0)) * 100.0

        return {
            "sample_size": sample_size,
            "status": "VALIDATED",
            "bull_win_rate": round(p_hat * 100.0, 1),
            "calibrated_prob": round(calibrated_prob, 1),
            "wilson_ci": (round(ci_lower, 1), round(ci_upper, 1)),
            "avg_mfe": round(float(np.mean(mfes)), 2),
            "avg_mae": round(float(np.mean(maes)), 2),
            "median_return": round(float(np.median(matches_fwd_ret)), 2)
        }

# ==============================================================================
# SECTION 12: TRADE PLAN ENGINE & LOGICAL INVALIDATION
# ==============================================================================

class TradePlanEngine:
    """Calculates Entry, multi-method Stop Loss, TP1, TP2, TP3, and Risk/Reward."""
    @staticmethod
    def generate_plan(
        df: pd.DataFrame,
        signal: str,
        sl_method: str,
        sl_atr_mult: float,
        tp1_r_mult: float,
        tp2_r_mult: float,
        min_rr_threshold: float,
        sr_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        latest = df.iloc[-1]
        entry = float(latest["Close"])
        atr = float(latest.get("ATR", entry * 0.01))

        if signal in ["NO TRADE", "NEUTRAL"]:
            return {
                "entry": entry, "stop_loss": None, "tp1": None, "tp2": None, "tp3": None,
                "risk_reward": None, "invalidation": "No active trade plan for neutral state.",
                "valid": False, "reason": "No directional setup."
            }

        is_long = "LONG" in signal

        # 1. Calculate Stop Loss based on selected methodology
        if sl_method == "ATR-based":
            sl = entry - (atr * sl_atr_mult) if is_long else entry + (atr * sl_atr_mult)
            inval_text = f"Close below ₹{sl:.2f} (ATR Invalidation)" if is_long else f"Close above ₹{sl:.2f} (ATR Invalidation)"
        elif sl_method == "Swing High/Low":
            if is_long:
                recent_low = float(df["Low"].iloc[-8:].min())
                sl = min(entry - (0.5 * atr), recent_low - (0.15 * atr))
                inval_text = f"Break of recent swing low at ₹{recent_low:.2f}"
            else:
                recent_high = float(df["High"].iloc[-8:].max())
                sl = max(entry + (0.5 * atr), recent_high + (0.15 * atr))
                inval_text = f"Break of recent swing high at ₹{recent_high:.2f}"
        elif sl_method == "Support/Resistance Zone":
            if is_long:
                near_s = sr_data.get("nearest_support")
                sl = (near_s["min"] - 0.2 * atr) if near_s else (entry - atr * sl_atr_mult)
                inval_text = f"S/R invalidation below zone ₹{sl:.2f}"
            else:
                near_r = sr_data.get("nearest_resistance")
                sl = (near_r["max"] + 0.2 * atr) if near_r else (entry + atr * sl_atr_mult)
                inval_text = f"S/R invalidation above zone ₹{sl:.2f}"
        else: # Hybrid
            if is_long:
                recent_low = float(df["Low"].iloc[-6:].min())
                sl = min(entry - (atr * sl_atr_mult), recent_low - (0.1 * atr))
                inval_text = f"Structural invalidation below ₹{sl:.2f}"
            else:
                recent_high = float(df["High"].iloc[-6:].max())
                sl = max(entry + (atr * sl_atr_mult), recent_high + (0.1 * atr))
                inval_text = f"Structural invalidation above ₹{sl:.2f}"

        risk_dist = abs(entry - sl)
        if risk_dist <= 0:
            risk_dist = atr * sl_atr_mult

        # 2. Take Profit Targets
        if is_long:
            tp1 = entry + (risk_dist * tp1_r_mult)
            tp2 = entry + (risk_dist * tp2_r_mult)
            tp3 = entry + (risk_dist * (tp2_r_mult + 1.0))
        else:
            tp1 = entry - (risk_dist * tp1_r_mult)
            tp2 = entry - (risk_dist * tp2_r_mult)
            tp3 = entry - (risk_dist * (tp2_r_mult + 1.0))

        rr = round(abs(tp1 - entry) / risk_dist, 2)
        valid = rr >= min_rr_threshold

        return {
            "entry": round(entry, 2),
            "stop_loss": round(sl, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "tp3": round(tp3, 2),
            "risk_dist": round(risk_dist, 2),
            "risk_reward": rr,
            "invalidation": inval_text,
            "valid": valid,
            "reason": "Risk/Reward passes threshold." if valid else f"R:R ({rr:.1f}) is below minimum requirement ({min_rr_threshold:.1f})."
        }

# ==============================================================================
# SECTION 13: COMPREHENSIVE DECISION & EXPLANATION ENGINE
# ==============================================================================

class DecisionEngine:
    """
    Combines evidence groups, model ensemble, uncertainty filters, and risk thresholds
    to generate calibrated signals with explainable reasons.
    """
    @staticmethod
    def decide(
        df: pd.DataFrame,
        weights: Dict[str, float],
        htf_data: Dict[str, Any],
        sr_data: Dict[str, Any],
        pa_data: Dict[str, Any],
        regime_data: Dict[str, Any],
        news_data: Dict[str, Any],
        analog_data: Dict[str, Any],
        data_quality: Dict[str, Any],
        min_rr: float,
        sl_method: str,
        sl_atr_mult: float,
        tp1_mult: float,
        tp2_mult: float
    ) -> Dict[str, Any]:
        latest = df.iloc[-1]
        close = latest["Close"]
        atr = latest.get("ATR", close * 0.01)

        why_reasons = []
        risk_warnings = []

        # 1. Evidence Group Scores (0 to 100 scale)
        # Group 1: Trend
        ema9 = latest.get("EMA9", close)
        ema21 = latest.get("EMA21", close)
        sma50 = latest.get("SMA50", close)
        trend_score = 50
        if close > ema9 > ema21:
            trend_score = 85
            why_reasons.append("EMA9 > EMA21 with price trading above short-term trend structure.")
        elif close < ema9 < ema21:
            trend_score = 15
            why_reasons.append("EMA9 < EMA21 with price trading below short-term trend structure.")
        if pd.notna(sma50):
            if close > sma50 and trend_score > 50: trend_score = min(100, trend_score + 10)
            elif close < sma50 and trend_score < 50: trend_score = max(0, trend_score - 10)

        # Group 2: Momentum
        rsi = latest.get("RSI", 50.0)
        macd_hist = latest.get("MACD_Hist", 0.0)
        mom_score = 50
        if rsi >= 55 and macd_hist > 0:
            mom_score = 80
            why_reasons.append(f"Positive momentum: RSI ({rsi:.1f}) in expansion zone and MACD Histogram positive.")
        elif rsi <= 45 and macd_hist < 0:
            mom_score = 20
            why_reasons.append(f"Bearish momentum: RSI ({rsi:.1f}) depressed and MACD Histogram negative.")
        if rsi >= 72:
            risk_warnings.append(f"RSI is elevated ({rsi:.1f}); prone to pullback.")
        elif rsi <= 28:
            risk_warnings.append(f"RSI is severely oversold ({rsi:.1f}); sharp short-covering possible.")

        # Group 3: Price Action
        pa_score = 50 + (pa_data.get("score", 0) * 10)
        pa_score = int(np.clip(pa_score, 0, 100))
        for pat in pa_data.get("patterns", []):
            why_reasons.append(f"Price action pattern: {pat}")

        # Group 4: Volume
        vol_ratio = latest.get("Volume_Ratio", 1.0)
        vol_score = 50
        if vol_ratio >= 1.4:
            if close > df["Close"].iloc[-2]:
                vol_score = 85
                why_reasons.append(f"High volume expansion ({vol_ratio:.1f}x) validating upward pressure.")
            else:
                vol_score = 15
                why_reasons.append(f"High volume expansion ({vol_ratio:.1f}x) validating downward selling.")
        elif vol_ratio < 0.65:
            vol_score = 40
            risk_warnings.append(f"Volume is thin ({vol_ratio:.2f}x of 20-SMA); reduced conviction.")

        # Group 5: Volatility
        atr_pct = latest.get("ATR_Percentile", 50.0)
        volatility_score = 50
        if atr_pct > 80:
            volatility_score = 30
            risk_warnings.append(f"High Volatility Regime (ATR at {atr_pct:.1f}% percentile). Slippage risk elevated.")
        elif atr_pct < 20:
            volatility_score = 65

        # Group 6: Multi-Timeframe Alignment
        mtf_score = htf_data.get("alignment_score", 50)
        htf_trend = htf_data.get("htf_trend", "Neutral")
        if "Bullish" in htf_trend:
            why_reasons.append(f"Higher timeframe ({htf_data['htf_interval']}) trend confirms bullish bias ({htf_trend}).")
        elif "Bearish" in htf_trend:
            why_reasons.append(f"Higher timeframe ({htf_data['htf_interval']}) trend confirms bearish bias ({htf_trend}).")

        # Group 7: Support / Resistance Proximity
        sr_score = 50
        near_res = sr_data.get("nearest_resistance")
        near_sup = sr_data.get("nearest_support")
        if near_res:
            res_dist_atr = (near_res["level"] - close) / atr
            if res_dist_atr < 0.7:
                sr_score -= 20
                risk_warnings.append(f"Major resistance overhead at ₹{near_res['level']} only {res_dist_atr:.1f} ATR away.")
        if near_sup:
            sup_dist_atr = (close - near_sup["level"]) / atr
            if sup_dist_atr < 0.7:
                sr_score += 20

        # Group 8: News Sentiment
        news_score = 50 + int(news_data.get("mean_score", 0.0) * 35)
        news_score = int(np.clip(news_score, 10, 90))
        if news_data.get("high_event_risk"):
            risk_warnings.append(f"HIGH EVENT RISK: {', '.join(news_data.get('events_detected', []))} detected in recent feeds.")

        # Data Quality Penalty
        if data_quality.get("quality_grade") == "LOW":
            risk_warnings.append("DATA QUALITY LOW: Dataset contains gaps or anomalies. High-conviction trades suppressed.")

        # Calculate Normalized Evidence Composite (-100 to +100)
        evidence_dict = {
            "Trend": (trend_score - 50) * 2,
            "Momentum": (mom_score - 50) * 2,
            "Price Action": (pa_score - 50) * 2,
            "Volume": (vol_score - 50) * 2,
            "Volatility": (volatility_score - 50) * 2,
            "Multi-Timeframe": (mtf_score - 50) * 2,
            "Support/Resistance": (sr_score - 50) * 2,
            "News": (news_score - 50) * 2
        }

        composite_score = sum(evidence_dict[k] * weights.get(k, 0.125) for k in evidence_dict)

        # Ensemble Model Consensus
        ensemble_res = MultiModelEnsemble.run_models(df, htf_data, regime_data["regime"], pa_data)
        weighted_consensus = ensemble_res["weighted_consensus"]

        # Blend Composite Score and Model Consensus
        final_signal_score = (composite_score * 0.6) + (weighted_consensus * 100.0 * 0.4)

        # Signal State Thresholds
        if final_signal_score >= 60: raw_signal = "HIGH-CONVICTION LONG"
        elif final_signal_score >= 35: raw_signal = "LONG"
        elif final_signal_score >= 20: raw_signal = "WEAK LONG"
        elif final_signal_score <= -60: raw_signal = "HIGH-CONVICTION SHORT"
        elif final_signal_score <= -35: raw_signal = "SHORT"
        elif final_signal_score <= -20: raw_signal = "WEAK SHORT"
        else: raw_signal = "NO TRADE"

        # Trade Plan & R:R Verification
        plan = TradePlanEngine.generate_plan(
            df, raw_signal, sl_method, sl_atr_mult, tp1_mult, tp2_mult, min_rr, sr_data
        )

        final_signal = raw_signal
        no_trade_reasons = []

        # Apply NO-TRADE Filters
        if not plan["valid"] and raw_signal not in ["NO TRADE"]:
            no_trade_reasons.append(f"Risk/Reward ratio ({plan['risk_reward']}) failed minimum required {min_rr}:1.")
            final_signal = "NO TRADE"

        if ("LONG" in raw_signal and "Bearish" in htf_trend) or ("SHORT" in raw_signal and "Bullish" in htf_trend):
            no_trade_reasons.append("Severe Multi-Timeframe conflict: lower timeframe opposing higher timeframe trend.")
            final_signal = "NO TRADE"

        if data_quality.get("quality_grade") == "LOW" and "HIGH-CONVICTION" in raw_signal:
            final_signal = "LONG" if "LONG" in raw_signal else "SHORT"

        if len(why_reasons) < 2 and final_signal != "NO TRADE":
            no_trade_reasons.append("Insufficient corroborating evidence across independent indicators.")
            final_signal = "NO TRADE"

        # Setup Quality (0 to 100)
        setup_quality = int(np.clip(abs(final_signal_score) * 0.6 + (mtf_score * 0.2) + (data_quality.get("score", 100) * 0.2), 10, 95))

        # Statistical Confidence Quality (HIGH / MODERATE / LOW / UNCERTAIN)
        sample_size = analog_data.get("sample_size", 0)
        if sample_size >= 40 and data_quality.get("quality_grade") == "HIGH" and len(risk_warnings) <= 1:
            confidence_quality = "HIGH"
        elif sample_size >= 15 and data_quality.get("quality_grade") != "LOW":
            confidence_quality = "MODERATE"
        else:
            confidence_quality = "LOW"

        return {
            "signal": final_signal,
            "raw_signal": raw_signal,
            "signal_score": round(final_signal_score, 1),
            "signal_strength": round(min(10.0, abs(final_signal_score) / 10.0), 1),
            "setup_quality": setup_quality,
            "confidence_quality": confidence_quality,
            "plan": plan,
            "why_reasons": why_reasons,
            "risk_warnings": risk_warnings,
            "no_trade_reasons": no_trade_reasons,
            "evidence_breakdown": evidence_dict,
            "ensemble": ensemble_res
        }

# ==============================================================================
# SECTION 14: REALISTIC BACKTESTING & WALK-FORWARD VALIDATION
# ==============================================================================

class WalkForwardBacktester:
    """
    Simulates realistic point-in-time trade outcomes using strict bar-by-bar progression,
    simulated slippage, transaction costs, and walk-forward out-of-sample evaluation.
    """
    @staticmethod
    def run_backtest(
        df: pd.DataFrame,
        sl_atr_mult: float = 1.5,
        tp1_mult: float = 1.5,
        tp2_mult: float = 3.0,
        slippage_pct: float = 0.05,
        fee_pct: float = 0.03,
        train_split: float = 0.65
    ) -> Dict[str, Any]:
        if df.empty or len(df) < 80:
            return {"error": "Insufficient bars for walk-forward validation (minimum 80 required)."}

        trades = []
        n = len(df)
        split_idx = int(n * train_split)

        closes = df["Close"].values
        highs = df["High"].values
        lows = df["Low"].values
        atrs = df["ATR"].values
        ema9s = df["EMA9"].values
        ema21s = df["EMA21"].values
        rsis = df["RSI"].values
        macds = df["MACD"].values
        macd_sigs = df["MACD_Signal"].values
        timestamps = df.index

        # Evaluate Out-Of-Sample partition strictly
        for i in range(split_idx, n - 10):
            atr_val = atrs[i]
            if np.isnan(atr_val) or atr_val <= 0: continue

            c = closes[i]
            is_bull = (ema9s[i] > ema21s[i]) and (rsis[i] > 52) and (macds[i] > macd_sigs[i])
            is_bear = (ema9s[i] < ema21s[i]) and (rsis[i] < 48) and (macds[i] < macd_sigs[i])

            if not is_bull and not is_bear:
                continue

            entry_price = c * (1.0 + (slippage_pct / 100.0 if is_bull else -slippage_pct / 100.0))
            risk_dist = atr_val * sl_atr_mult
            sl = entry_price - risk_dist if is_bull else entry_price + risk_dist
            tp1 = entry_price + (risk_dist * tp1_mult) if is_bull else entry_price - (risk_dist * tp1_mult)
            tp2 = entry_price + (risk_dist * tp2_mult) if is_bull else entry_price - (risk_dist * tp2_mult)

            # Bar-by-bar outcome tracking for up to 15 bars
            exit_price = None
            exit_reason = "Time Exit"
            holding_bars = 0
            mfe_p = entry_price
            mae_p = entry_price

            for f in range(1, 16):
                if i + f >= n: break
                holding_bars = f
                bar_h = highs[i + f]
                bar_l = lows[i + f]

                if is_bull:
                    mfe_p = max(mfe_p, bar_h)
                    mae_p = min(mae_p, bar_l)
                    if bar_l <= sl:
                        exit_price = sl * (1.0 - slippage_pct / 100.0)
                        exit_reason = "Stop Loss"
                        break
                    elif bar_h >= tp2:
                        exit_price = tp2 * (1.0 - slippage_pct / 100.0)
                        exit_reason = "Take Profit 2"
                        break
                    elif bar_h >= tp1 and exit_reason != "TP1 Hit":
                        exit_reason = "TP1 Hit"
                else:
                    mfe_p = min(mfe_p, bar_l)
                    mae_p = max(mae_p, bar_h)
                    if bar_h >= sl:
                        exit_price = sl * (1.0 + slippage_pct / 100.0)
                        exit_reason = "Stop Loss"
                        break
                    elif bar_l <= tp2:
                        exit_price = tp2 * (1.0 + slippage_pct / 100.0)
                        exit_reason = "Take Profit 2"
                        break
                    elif bar_l <= tp1 and exit_reason != "TP1 Hit":
                        exit_reason = "TP1 Hit"

            if exit_price is None:
                exit_price = closes[min(n - 1, i + 15)]

            # Deduct round-trip fees
            if is_bull:
                raw_ret = (exit_price - entry_price) / entry_price * 100.0
            else:
                raw_ret = (entry_price - exit_price) / entry_price * 100.0

            net_ret = raw_ret - (2.0 * fee_pct)
            r_multiple = net_ret / (risk_dist / entry_price * 100.0)

            trades.append({
                "entry_time": timestamps[i],
                "direction": "LONG" if is_bull else "SHORT",
                "entry": entry_price,
                "exit": exit_price,
                "exit_reason": exit_reason,
                "net_ret_pct": net_ret,
                "r_multiple": r_multiple,
                "bars": holding_bars
            })

        if not trades:
            return {"error": "No valid signals generated during out-of-sample testing window."}

        tdf = pd.DataFrame(trades)
        wins = tdf[tdf["net_ret_pct"] > 0]
        losses = tdf[tdf["net_ret_pct"] <= 0]

        total_trades = len(tdf)
        win_rate = (len(wins) / total_trades) * 100.0
        gross_profit = wins["net_ret_pct"].sum()
        gross_loss = abs(losses["net_ret_pct"].sum())
        profit_factor = round(gross_profit / max(0.001, gross_loss), 2)
        expectancy_r = round(tdf["r_multiple"].mean(), 2)
        avg_win = round(wins["net_ret_pct"].mean(), 2) if not wins.empty else 0.0
        avg_loss = round(losses["net_ret_pct"].mean(), 2) if not losses.empty else 0.0

        # Drawdown calculation
        cumulative_rets = (1.0 + tdf["net_ret_pct"] / 100.0).cumprod()
        peak = cumulative_rets.cummax()
        drawdown = (cumulative_rets - peak) / peak * 100.0
        max_drawdown = round(abs(drawdown.min()), 2)

        # Largest losing streak
        loss_seq = (tdf["net_ret_pct"] <= 0).astype(int)
        max_streak = 0
        curr_streak = 0
        for val in loss_seq:
            if val == 1:
                curr_streak += 1
                max_streak = max(max_streak, curr_streak)
            else:
                curr_streak = 0

        # Model Drift Check (compare last 25 trades vs earlier)
        drift_warning = None
        if len(tdf) >= 40:
            recent_wr = (tdf.iloc[-20:]["net_ret_pct"] > 0).mean() * 100.0
            prior_wr = (tdf.iloc[:-20]["net_ret_pct"] > 0).mean() * 100.0
            if prior_wr - recent_wr > 18.0:
                drift_warning = f"MODEL PERFORMANCE DEGRADING: Recent win rate ({recent_wr:.1f}%) dropped >18% below baseline ({prior_wr:.1f}%)."

        return {
            "total_signals": total_trades,
            "win_rate": round(win_rate, 1),
            "profit_factor": profit_factor,
            "expectancy_r": expectancy_r,
            "max_drawdown": max_drawdown,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_losing_streak": max_streak,
            "drift_warning": drift_warning,
            "trade_df": tdf
        }

# ==============================================================================
# SECTION 15: ADVANCED PLOTLY CHARTING
# ==============================================================================

def create_advanced_chart(
    df: pd.DataFrame,
    symbol: str,
    sr_data: Dict[str, Any],
    plan_data: Dict[str, Any],
    show_bb: bool = True,
    show_vwap: bool = True
) -> go.Figure:
    """Builds interactive financial chart with Candlesticks, Volume, RSI, and MACD."""
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=(f"{symbol} Price Action & Indicators", "Volume", "RSI (14)", "MACD (12, 26, 9)")
    )

    # 1. Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color="#2ea043",
            decreasing_line_color="#f85149"
        ),
        row=1, col=1
    )

    # Moving averages
    if "EMA9" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA9"], line=dict(color="#58a6ff", width=1.2), name="EMA 9"), row=1, col=1)
    if "EMA21" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA21"], line=dict(color="#f0883e", width=1.2), name="EMA 21"), row=1, col=1)
    if "SMA50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], line=dict(color="#d29922", width=1.5), name="SMA 50"), row=1, col=1)

    # Bollinger Bands
    if show_bb and "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], line=dict(color="rgba(110, 118, 129, 0.4)", width=1), name="BB Upper"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], line=dict(color="rgba(110, 118, 129, 0.4)", width=1), fill="tonexty", fillcolor="rgba(110, 118, 129, 0.08)", name="BB Lower"), row=1, col=1)

    # Session VWAP
    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], line=dict(color="#bc8cff", width=1.6, dash="dot"), name="Session VWAP"), row=1, col=1)

    # Support / Resistance Horizontal Levels
    for sup in sr_data.get("supports", [])[:2]:
        fig.add_hline(y=sup["level"], line_dash="dash", line_color="#2ea043", opacity=0.6, annotation_text=f"Sup ₹{sup['level']}", annotation_position="top left", row=1, col=1)
    for res in sr_data.get("resistances", [])[:2]:
        fig.add_hline(y=res["level"], line_dash="dash", line_color="#f85149", opacity=0.6, annotation_text=f"Res ₹{res['level']}", annotation_position="bottom left", row=1, col=1)

    # Plan Lines (Entry, SL, TP)
    if plan_data and plan_data.get("stop_loss"):
        fig.add_hline(y=plan_data["entry"], line_color="#ffffff", opacity=0.8, line_width=1.5, annotation_text=f"Entry ₹{plan_data['entry']}", row=1, col=1)
        fig.add_hline(y=plan_data["stop_loss"], line_color="#da3633", opacity=0.9, line_width=2, line_dash="dot", annotation_text=f"SL ₹{plan_data['stop_loss']}", row=1, col=1)
        fig.add_hline(y=plan_data["tp1"], line_color="#238636", opacity=0.9, line_width=2, line_dash="dot", annotation_text=f"TP1 ₹{plan_data['tp1']}", row=1, col=1)

    # 2. Volume
    colors = ["#2ea043" if c >= o else "#f85149" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume", opacity=0.7), row=2, col=1)
    if "Vol_SMA20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Vol_SMA20"], line=dict(color="#8b949e", width=1.2), name="Vol SMA20"), row=2, col=1)

    # 3. RSI
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], line=dict(color="#a371f7", width=1.5), name="RSI"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#f85149", opacity=0.6, row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#2ea043", opacity=0.6, row=3, col=1)
        fig.add_hline(y=50, line_dash="dash", line_color="#484f58", opacity=0.5, row=3, col=1)

    # 4. MACD
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], line=dict(color="#58a6ff", width=1.2), name="MACD"), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], line=dict(color="#f0883e", width=1.2), name="Signal"), row=4, col=1)
        hist_colors = ["#2ea043" if h >= 0 else "#f85149" for h in df["MACD_Hist"]]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], marker_color=hist_colors, name="Hist"), row=4, col=1)

    # Layout styling
    fig.update_layout(
        template="plotly_dark",
        height=1050,
        margin=dict(l=65, r=35, t=85, b=55),
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0, bgcolor="rgba(13,17,23,0.75)",
            font=dict(size=11)
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", size=12,
                  family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto"),
        title=dict(font=dict(size=17)),
        bargap=0.08
    )
    fig.update_xaxes(gridcolor="#30363d", showgrid=True, showspikes=True,
                     spikemode="across", spikesnap="cursor", showline=True,
                     linecolor="#484f58", rangeslider_visible=False)
    fig.update_yaxes(gridcolor="#30363d", showgrid=True, zeroline=False,
                     showline=True, linecolor="#484f58", automargin=True)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=4, col=1)
    return fig

# ==============================================================================
# SECTION 16: STREAMLIT USER INTERFACE & ORCHESTRATION
# ==============================================================================

def main():
    # Header Banner
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #30363d; padding-bottom: 12px; margin-bottom: 18px;">
        <div>
            <h2 style="margin: 0; color: #f0f6fc; font-weight: 700;">🧭 Advanced AI Market Decision Engine</h2>
            <div style="color: #8b949e; font-size: 0.85rem; margin-top: 4px;">
                Market analysis with multi-timeframe indicators, historical analog matching, and configurable market-data providers.
            </div>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 0.75rem; background: #21262d; border: 1px solid #30363d; padding: 4px 8px; border-radius: 4px; color: #8b949e;">PyCharm Quantitative Build v2.4</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Controls
    st.sidebar.markdown("### ⚙️ Market Configuration")

    asset_classes = sorted(
        ["Indian Stock", "US Stock", "Crypto", "Forex", "Custom Manual Entry"],
        key=str.casefold
    )
    asset_type = st.sidebar.selectbox("Asset Class", asset_classes)

    # Auto-Refresh. A 0.50-second interval is supported, but can trigger
    # frequent reruns and provider rate limits; use a longer interval for APIs.
    st.sidebar.markdown("### 🔄 Auto-Refresh")
    auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=False)
    refresh_secs = st.sidebar.slider(
        "Refresh interval (seconds)", min_value=5.0, max_value=120.0,
        value=10.0, step=5.0, disabled=not auto_refresh,
        help="Use 5–30 seconds or longer to reduce the chance of API rate limits."
    )
    if auto_refresh:
        if AUTO_REFRESH_AVAILABLE:
            st_autorefresh(interval=int(refresh_secs * 1000), key="amd_autorefresh")
            st.sidebar.success(f"Refreshing every {refresh_secs:.2f}s")
        else:
            st.sidebar.warning("Install streamlit-autorefresh for live refresh.")

    # Symbol Selection: sort labels alphabetically, case-insensitively.
    if asset_type == "Indian Stock":
        asset_options = sorted([*POPULAR_INDIAN_STOCKS.keys(), "Other"], key=str.casefold)
        sym_choice = st.sidebar.selectbox("Select Asset", asset_options)
        symbol = POPULAR_INDIAN_STOCKS[sym_choice] if sym_choice != "Other" else st.sidebar.text_input("Enter NSE/BSE Symbol", "RELIANCE.NS").strip().upper()
    elif asset_type == "US Stock":
        asset_options = sorted([*POPULAR_US_STOCKS.keys(), "Other"], key=str.casefold)
        sym_choice = st.sidebar.selectbox("Select Asset", asset_options)
        symbol = POPULAR_US_STOCKS[sym_choice] if sym_choice != "Other" else st.sidebar.text_input("Enter US Ticker", "AAPL").strip().upper()
    elif asset_type == "Crypto":
        asset_options = sorted([*POPULAR_CRYPTO.keys(), "Other"], key=str.casefold)
        sym_choice = st.sidebar.selectbox("Select Asset", asset_options)
        symbol = POPULAR_CRYPTO[sym_choice] if sym_choice != "Other" else st.sidebar.text_input("Enter Crypto Pair", "BTC-USD").strip().upper()
    elif asset_type == "Forex":
        forex_options = sorted([*POPULAR_FOREX.keys(), "Other"], key=str.casefold)
        sym_choice = st.sidebar.selectbox("Select Forex Pair", forex_options)
        if sym_choice == "Other":
            forex_input = st.sidebar.text_input(
                "Enter Forex Pair",
                "EUR/USD",
                help="Enter a six-letter pair such as EURUSD or a slash pair such as EUR/USD."
            )
            symbol = normalize_forex_symbol(forex_input)
        else:
            symbol = POPULAR_FOREX[sym_choice]
        st.sidebar.caption("Spot FX is decentralized; displayed volume may be unavailable or not representative.")
    else:
        symbol = st.sidebar.text_input("Enter Symbol", "RELIANCE.NS").strip().upper()

    # Data Provider Selection
    st.sidebar.markdown("### 📡 Data Source")
    if asset_type == "Forex":
        st.sidebar.info("Forex support uses Yahoo Finance FX symbols (for example EURUSD=X). Quotes can be delayed; refresh frequency does not guarantee provider updates.")
    provider_type = st.sidebar.selectbox(
        "Data Provider",
        ["Yahoo Finance", "Angel One SmartAPI", "Custom JSON API", "Custom CSV URL"]
    )
    custom_url = ""
    angel_exchange = "NSE"
    angel_symbol_token = ""
    if provider_type in ["Custom JSON API", "Custom CSV URL"]:
        custom_url = st.sidebar.text_input("Endpoint URL", placeholder="https://api.example.com/candles")
    elif provider_type == "Angel One SmartAPI":
        st.sidebar.caption("Uses your own Angel One SmartAPI account. Add credentials as environment variables; never paste API secrets into the app.")
        angel_exchange = st.sidebar.selectbox("Angel One Exchange", ["NSE", "BSE", "NFO", "BFO", "MCX"])
        angel_symbol_token = st.sidebar.text_input(
            "Angel One Symbol Token",
            value="",
            help="Use the token from Angel One's official instrument master for the exact exchange and instrument."
        ).strip()

    # News count is configurable; the provider may return fewer articles than requested.
    st.sidebar.markdown("### 📰 News Settings")
    news_article_count = st.sidebar.slider(
        "News articles to fetch",
        min_value=10,
        max_value=50,
        value=30,
        step=5,
        help="Requests up to 50 recent articles when supported by the news provider. The provider may return fewer."
    )

    # Timeframe Configuration
    st.sidebar.markdown("### ⏱️ Timeframe Architecture")
    tf_preset = st.sidebar.selectbox("Strategy Profile", list(TIMEFRAME_PRESETS.keys()), index=2)
    tf_config = TIMEFRAME_PRESETS[tf_preset]

    primary_interval = tf_config["primary"]
    higher_interval = tf_config["higher"]
    historical_period = tf_config["period"]

    with st.sidebar.expander("🛠️ Advanced Risk & Thresholds"):
        sl_method = st.selectbox("Stop-Loss Model", ["ATR-based", "Swing High/Low", "Support/Resistance Zone", "Hybrid"], index=0)
        sl_atr_mult = st.slider("SL ATR Multiplier", 0.8, 3.5, 1.5, 0.1)
        tp1_r_mult = st.slider("TP1 R-Multiple", 1.0, 3.0, 1.5, 0.1)
        tp2_r_mult = st.slider("TP2 R-Multiple", 2.0, 6.0, 3.0, 0.2)
        min_rr = st.slider("Min Acceptable R:R", 1.0, 3.0, 1.5, 0.1)

    with st.sidebar.expander("⚖️ Evidence Group Weights"):
        w_trend = st.slider("Trend Weight", 0.05, 0.40, 0.20, 0.05)
        w_mom = st.slider("Momentum Weight", 0.05, 0.30, 0.15, 0.05)
        w_pa = st.slider("Price Action Weight", 0.05, 0.30, 0.15, 0.05)
        w_vol = st.slider("Volume Weight", 0.05, 0.25, 0.10, 0.05)
        w_mtf = st.slider("Multi-Timeframe Weight", 0.05, 0.30, 0.15, 0.05)
        w_sr = st.slider("Support/Resistance Weight", 0.05, 0.25, 0.10, 0.05)
        w_news = st.slider("News Sentiment Weight", 0.00, 0.15, 0.05, 0.05)
        w_volat = st.slider("Volatility Weight", 0.00, 0.15, 0.05, 0.05)

        # Normalize weights
        raw_weights = {
            "Trend": w_trend, "Momentum": w_mom, "Price Action": w_pa, "Volume": w_vol,
            "Volatility": w_volat, "Multi-Timeframe": w_mtf, "Support/Resistance": w_sr, "News": w_news
        }
        total_w = sum(raw_weights.values())
        weights = {k: v / total_w for k, v in raw_weights.items()}

    # Sizing Calculator Inputs
    with st.sidebar.expander("💼 Position Sizing Calculator"):
        account_size = st.number_input("Account Capital (₹ / $)", value=100000.0, step=10000.0)
        risk_pct = st.slider("Risk Per Trade %", 0.25, 5.0, 1.0, 0.25)
        max_monetary_risk = account_size * (risk_pct / 100.0)

    # Initialize Provider
    if provider_type == "Yahoo Finance":
        provider = YahooFinanceProvider()
    elif provider_type == "Angel One SmartAPI":
        provider = AngelOneProvider(angel_exchange, angel_symbol_token)
    elif provider_type == "Custom JSON API":
        provider = CustomJSONProvider(custom_url)
    else:
        provider = CustomCSVProvider(custom_url)

    # Ingest Data
    with st.spinner(f"Ingesting {symbol} ({primary_interval})..."):
        raw_df = provider.fetch_ohlcv(symbol, historical_period, primary_interval)

    # Audit Data Quality
    dq_report = DataQualityEngine.audit_dataset(raw_df, primary_interval, is_forex=(asset_type == "Forex"))
    freshness = RealTimeStatusEngine.evaluate_freshness(raw_df, primary_interval)

    # Render Top Status Strip
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Data Status</div>
            <div class="metric-card-value" style="font-size: 1.15rem;">
                <span class="status-badge {freshness['badge_class']}">{freshness['status']}</span>
            </div>
            <div class="metric-card-subtitle">{freshness['age_str']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        dq_color = "#2ea043" if dq_report["quality_grade"] == "HIGH" else ("#d29922" if dq_report["quality_grade"] == "MODERATE" else "#da3633")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Data Quality</div>
            <div class="metric-card-value" style="color: {dq_color};">{dq_report['quality_grade']}</div>
            <div class="metric-card-subtitle">Score: {dq_report['score']}/100</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        last_price = raw_df["Close"].iloc[-1] if not raw_df.empty else 0.0
        price_change = (raw_df["Close"].iloc[-1] - raw_df["Close"].iloc[-2]) if len(raw_df) >= 2 else 0.0
        pct_change = (price_change / raw_df["Close"].iloc[-2] * 100.0) if len(raw_df) >= 2 else 0.0
        p_color = "#2ea043" if price_change >= 0 else "#da3633"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Latest Price</div>
            <div class="metric-card-value">{last_price:.2f}</div>
            <div class="metric-card-subtitle" style="color: {p_color};">{price_change:+.2f} ({pct_change:+.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Timeframe Matrix</div>
            <div class="metric-card-value" style="font-size: 1.25rem;">{primary_interval}</div>
            <div class="metric-card-subtitle">HTF: {higher_interval}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Candle Buffer</div>
            <div class="metric-card-value" style="font-size: 1.25rem;">{len(raw_df)} bars</div>
            <div class="metric-card-subtitle">{raw_df.index[0].strftime('%b %d') if not raw_df.empty else 'N/A'} - Now</div>
        </div>
        """, unsafe_allow_html=True)

    if not dq_report["is_valid"]:
        st.error(f"⚠️ Critical Data Ingestion Notice: Analysis halted due to compromised data quality.")
        for iss in dq_report["issues"]:
            st.markdown(f"- 🔴 {iss}")
        return

    # Initialize signal snapshot store in session state
    if "signal_log" not in st.session_state:
        st.session_state["signal_log"] = []

    # Pipeline Processing
    df = compute_all_indicators(raw_df)
    regime = MarketRegimeEngine.identify_regime(df)
    sr_zones = SupportResistanceEngine.extract_zones(df)
    pa_results = PriceActionEngine.evaluate(df, sr_zones)
    htf_analysis = MultiTimeframeEngine.analyze_alignment(symbol, primary_interval, higher_interval, provider)
    news_res = NewsEventEngine.analyze_news(symbol, count=news_article_count)

    # Historical Analog Matching
    latest_bar = df.iloc[-1]
    curr_feats = {
        "rsi": latest_bar["RSI"],
        "macd": latest_bar["MACD"],
        "ema9": latest_bar["EMA9"],
        "ema21": latest_bar["EMA21"],
        "close": latest_bar["Close"],
        "vwap": latest_bar["VWAP"]
    }
    analog_res = HistoricalAnalogEngine.find_analogs(df, curr_feats, forward_bars=5)

    # Master Decision Engine
    decision = DecisionEngine.decide(
        df=df,
        weights=weights,
        htf_data=htf_analysis,
        sr_data=sr_zones,
        pa_data=pa_results,
        regime_data=regime,
        news_data=news_res,
        analog_data=analog_res,
        data_quality=dq_report,
        min_rr=min_rr,
        sl_method=sl_method,
        sl_atr_mult=sl_atr_mult,
        tp1_mult=tp1_r_mult,
        tp2_mult=tp2_r_mult
    )

    plan = decision["plan"]

    # ── Signal Expiry Calculation ──────────────────────────────────────────────
    # A signal is valid for up to 3 primary candle durations.
    _interval_minutes = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60,
        "4h": 240, "1d": 1440, "1w": 10080
    }
    _pm = _interval_minutes.get(primary_interval, 15)
    signal_valid_until = datetime.now() + timedelta(minutes=_pm * 3)
    signal_expiry_str = signal_valid_until.strftime("%H:%M  (%d %b)")

    # ── Store signal snapshot in session log ───────────────────────────────────
    _snap = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "interval": primary_interval,
        "signal": decision["signal"],
        "setup_quality": decision["setup_quality"],
        "confidence": decision["confidence_quality"],
        "regime": regime["regime"],
        "entry": plan.get("entry"),
        "stop": plan.get("stop_loss"),
        "tp1": plan.get("tp1"),
        "rr": plan.get("risk_reward"),
        "analog_prob": analog_res.get("calibrated_prob"),
        "valid_until": signal_expiry_str
    }
    # Avoid duplicates within the same minute
    if not st.session_state["signal_log"] or st.session_state["signal_log"][-1]["timestamp"][:16] != _snap["timestamp"][:16]:
        st.session_state["signal_log"].append(_snap)
    # Keep only last 100 snapshots
    st.session_state["signal_log"] = st.session_state["signal_log"][-100:]

    # ==============================================================================
    # RENDER MASTER DECISION BANNER
    # ==============================================================================
    sig = decision["signal"]
    banner_class = "decision-banner-long" if "LONG" in sig else ("decision-banner-short" if "SHORT" in sig else "decision-banner-neutral")
    sig_icon = "🟢" if "LONG" in sig else ("🔴" if "SHORT" in sig else "⚪")

    st.markdown(f"""
    <div class="decision-banner {banner_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="font-size: 0.85rem; font-weight: 700; letter-spacing: 0.1em; color: #8b949e; text-transform: uppercase;">Final Analytical Market Decision</span>
                <h1 style="margin: 4px 0 8px 0; color: #f0f6fc; font-size: 2.2rem; font-weight: 800;">
                    {sig_icon} {sig}
                </h1>
                <div style="font-size: 0.95rem; color: #c9d1d9;">
                    Market Regime: <b style="color: #58a6ff;">{regime['regime']}</b> | HTF Alignment: <b style="color: #58a6ff;">{htf_analysis['htf_trend']}</b>
                </div>
            </div>
            <div style="text-align: right; background: rgba(13, 17, 23, 0.7); padding: 12px 18px; border-radius: 8px; border: 1px solid #30363d;">
                <div style="font-size: 0.75rem; color: #8b949e; text-transform: uppercase;">Confidence Quality</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: {'#2ea043' if decision['confidence_quality'] == 'HIGH' else ('#d29922' if decision['confidence_quality'] == 'MODERATE' else '#da3633')};">
                    {decision['confidence_quality']}
                </div>
                <div style="font-size: 0.75rem; color: #8b949e; margin-top: 4px;">Setup Quality: <b>{decision['setup_quality']}/100</b></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Master Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Interactive Chart",
        "🧭 Trade Scenario & Plan",
        "🔍 Probabilistic Analogs",
        "🧪 Walk-Forward Backtest",
        "📰 News & Market Events",
        "📈 Signal Log & Performance"
    ])

    with tab1:
        # Plotly Chart
        fig = create_advanced_chart(df, symbol, sr_zones, plan)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "responsive": True, "scrollZoom": True})

        # Reasons & Risks
        c_why, c_risk = st.columns(2)
        with c_why:
            st.markdown("#### ✅ Analytical Evidence")
            if decision["why_reasons"]:
                for r in decision["why_reasons"]:
                    st.markdown(f"- ✓ {r}")
            else:
                st.markdown("- *No affirmative directional signals validated.*")

            if decision["no_trade_reasons"]:
                st.markdown("##### 🚫 Trade Filter Invalidation Triggers:")
                for nr in decision["no_trade_reasons"]:
                    st.markdown(f"- ✗ **Filter Activated:** {nr}")

        with c_risk:
            st.markdown("#### ⚠️ Identified Hazards & Risks")
            if decision["risk_warnings"]:
                for rw in decision["risk_warnings"]:
                    st.markdown(f"- ⚠ {rw}")
            else:
                st.markdown("- *No extreme structural hazards flagged.*")

            # Signal expiry
            st.markdown("---")
            st.markdown(f"##### ⏱️ Signal Validity")
            st.info(f"Signal generated at **{datetime.now().strftime('%H:%M')}** — analytically valid until **{signal_expiry_str}** (3 primary candle durations). Reassess if price action invalidates the setup before that time.")

            st.markdown("##### 🛡️ Logical Invalidation:")
            st.info(f"**Structural Boundary:** {plan['invalidation']}")

    with tab2:
        st.subheader("🎯 Executable Trade Scenario Parameters")
        if plan["stop_loss"] is not None:
            tc1, tc2, tc3, tc4, tc5 = st.columns(5)
            tc1.metric("Analytical Entry", f"₹{plan['entry']:.2f}")
            tc2.metric("Logical Stop Loss", f"₹{plan['stop_loss']:.2f}", f"-₹{plan['risk_dist']:.2f}")
            tc3.metric("Take Profit 1 (1.5R)", f"₹{plan['tp1']:.2f}", f"+₹{abs(plan['tp1'] - plan['entry']):.2f}")
            tc4.metric("Take Profit 2 (3.0R)", f"₹{plan['tp2']:.2f}", f"+₹{abs(plan['tp2'] - plan['entry']):.2f}")
            tc5.metric("Reward-to-Risk", f"{plan['risk_reward']:.2f} : 1")

            st.divider()
            st.markdown("#### 💼 Quantitative Risk Sizing Matrix")
            # Calculate position sizing
            shares = int(max_monetary_risk / max(0.01, plan["risk_dist"]))
            capital_req = shares * plan["entry"]
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Recommended Share Size", f"{shares:,} units")
            sc2.metric("Allocated Capital Required", f"₹{capital_req:,.2f}", f"{(capital_req/account_size)*100:.1f}% of Account")
            sc3.metric("Max Monitored Risk", f"₹{max_monetary_risk:,.2f}", f"{risk_pct:.2f}% of Account")
        else:
            st.warning("⚠️ Market is in a NO-TRADE or NEUTRAL regime. No synthetic trade levels are manufactured.")
            if decision["no_trade_reasons"]:
                st.markdown("##### Explicit Invalidation Summary:")
                for r in decision["no_trade_reasons"]:
                    st.markdown(f"- 🚫 {r}")

        st.divider()
        st.markdown("#### 🤖 Model Ensemble Voting Consensus")
        m_cols = st.columns(6)
        idx = 0
        for m_name, m_stance in decision["ensemble"]["model_stances"].items():
            color = "#2ea043" if m_stance == "LONG" else ("#da3633" if m_stance == "SHORT" else "#8b949e")
            with m_cols[idx]:
                st.markdown(f"""
                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px; text-align: center;">
                    <div style="font-size: 0.72rem; color: #8b949e;">{m_name}</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: {color}; margin-top: 4px;">{m_stance}</div>
                </div>
                """, unsafe_allow_html=True)
            idx += 1

    with tab3:
        st.subheader("🔍 Statistical Historical Analog Profiling")
        st.caption("Matches current multi-dimensional indicator vectors across past history to measure empirical outcomes.")

        ac1, ac2, ac3, ac4 = st.columns(4)
        ac1.metric("Comparable Setups Found", f"{analog_res['sample_size']} historical bars")

        if analog_res["status"] == "VALIDATED":
            ac2.metric("Historical Analog Win Rate", f"{analog_res['bull_win_rate']}%")
            ac3.metric("Calibrated Probability (Empirical Shrinkage)", f"{analog_res['calibrated_prob']}%")
            ci = analog_res["wilson_ci"]
            ac4.metric("Wilson 95% Confidence Band", f"[{ci[0]}% - {ci[1]}%]")

            st.markdown(f"""
            - **Average Maximum Favorable Excursion (MFE):** `+{analog_res['avg_mfe']}%`
            - **Average Maximum Adverse Excursion (MAE):** `-{analog_res['avg_mae']}%`
            - **Median 5-Bar Outcome:** `{analog_res['median_return']:+.2f}%`
            """)
        else:
            ac2.metric("Historical Win Rate", "INSUFFICIENT SAMPLE")
            ac3.metric("Calibrated Probability", "N/A")
            ac4.metric("Sample Reliability", "LOW")
            st.warning("⚠️ Sample size is too small (< 15 historical analogs) to calculate a statistically grounded probability.")

        # Calibration Warning
        if analog_res["status"] == "VALIDATED":
            cal_prob = analog_res.get("calibrated_prob", 50.0)
            signal_log_df = pd.DataFrame(st.session_state.get("signal_log", []))
            if len(signal_log_df) >= 20 and "analog_prob" in signal_log_df.columns:
                signal_log_df["analog_prob"] = pd.to_numeric(signal_log_df["analog_prob"], errors="coerce")
                recent_probs = signal_log_df["analog_prob"].dropna().tail(20)
                if len(recent_probs) >= 10:
                    predicted_mean = float(recent_probs.mean())
                    if abs(predicted_mean - cal_prob) > 15.0:
                        st.warning(f"⚠️ **CALIBRATION WARNING**: The current calibrated probability ({cal_prob:.1f}%) differs significantly from recent session average ({predicted_mean:.1f}%). Model may be operating outside its validated range.")

    with tab4:
        st.subheader("🧪 Walk-Forward Out-Of-Sample Backtesting Engine")
        st.caption("Simulates point-in-time trade generation with strictly out-of-sample forward bar execution, slippage, and commissions.")

        with st.spinner("Executing walk-forward backtest..."):
            bt_res = WalkForwardBacktester.run_backtest(
                df,
                sl_atr_mult=sl_atr_mult,
                tp1_mult=tp1_r_mult,
                tp2_mult=tp2_r_mult,
                slippage_pct=0.05,
                fee_pct=0.03,
                train_split=0.60
            )

        if "error" not in bt_res:
            b1, b2, b3, b4, b5 = st.columns(5)
            b1.metric("OOS Signals Tested", bt_res["total_signals"])
            b2.metric("Realized Win Rate", f"{bt_res['win_rate']}%")
            b3.metric("Profit Factor", bt_res["profit_factor"])
            b4.metric("Expectancy (R/Trade)", f"{bt_res['expectancy_r']:+.2f}R")
            b5.metric("Max Drawdown", f"{bt_res['max_drawdown']}%")

            if bt_res.get("drift_warning"):
                st.warning(f"⚠️ {bt_res['drift_warning']}")

            with st.expander("📋 View Out-Of-Sample Trade Log"):
                st.dataframe(bt_res["trade_df"].tail(25), use_container_width=True)
        else:
            st.info(bt_res["error"])

    with tab5:
        st.subheader("📰 Market Intelligence & Event Risk Tracker")
        st.caption(f"Requested up to {news_article_count} recent articles. The provider may return fewer, and availability varies by ticker.")
        if news_res["articles"]:
            nc1, nc2 = st.columns([1, 2])
            with nc1:
                st.metric("Aggregate News Score", f"{news_res['mean_score']:+.2f}", news_res["sentiment_label"])
                st.metric("Bounded Engine Impact", f"{news_res['bounded_contribution']:+.2f} / 2.0")
                if news_res["high_event_risk"]:
                    st.error(f"🚨 High Event Risk Detected: {', '.join(news_res['events_detected'])}")
            with nc2:
                for a in news_res["articles"]:
                    st.markdown(f"**[{a['title']}]({a['url']})**")
                    st.caption(f"Source: {a['publisher']} | Sentiment Score: {a['score']}")
                    st.divider()
        else:
            st.info("No live news feed currently indexed for this ticker.")

    # ── TAB 6: Signal Log & Performance Monitoring ────────────────────────────
    with tab6:
        st.subheader("📈 Signal Log & Performance Monitoring")
        st.caption("Records every analytical signal generated this session. For live outcome tracking, manually mark trades after exit.")

        log_df = pd.DataFrame(st.session_state.get("signal_log", []))

        if log_df.empty:
            st.info("No signals recorded yet this session. Run the analysis on an asset to start logging.")
        else:
            # Summary Metrics
            total_sigs = len(log_df)
            long_sigs = (log_df["signal"].str.contains("LONG", na=False)).sum()
            short_sigs = (log_df["signal"].str.contains("SHORT", na=False)).sum()
            no_trade_sigs = (log_df["signal"] == "NO TRADE").sum()

            pm1, pm2, pm3, pm4 = st.columns(4)
            pm1.metric("Total Signals Logged", total_sigs)
            pm2.metric("Long Signals", long_sigs)
            pm3.metric("Short Signals", short_sigs)
            pm4.metric("NO TRADE Decisions", no_trade_sigs)

            st.divider()

            # Signal distribution by regime
            if "regime" in log_df.columns:
                regime_counts = log_df["regime"].value_counts()
                st.markdown("**Signals by Detected Market Regime:**")
                regime_cols = st.columns(min(len(regime_counts), 4))
                for i, (rg, cnt) in enumerate(regime_counts.items()):
                    if i < 4:
                        regime_cols[i].metric(rg, cnt)

            st.divider()

            # Signal breakdown by confidence
            if "confidence" in log_df.columns:
                st.markdown("**Confidence Quality Distribution:**")
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("HIGH Confidence", (log_df["confidence"] == "HIGH").sum())
                cc2.metric("MODERATE Confidence", (log_df["confidence"] == "MODERATE").sum())
                cc3.metric("LOW Confidence", (log_df["confidence"] == "LOW").sum())

            st.divider()
            st.markdown("**Full Signal Snapshot Log:**")
            display_df = log_df.copy()
            st.dataframe(display_df, use_container_width=True, height=350)

            # Export signal log
            log_csv = log_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Signal Log (CSV)",
                data=log_csv,
                file_name=f"signal_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

            if st.button("🗑️ Clear Signal Log"):
                st.session_state["signal_log"] = []
                st.rerun()

    # ── Market Data Export ─────────────────────────────────────────────────────
    st.divider()
    csv_bytes = df.to_csv().encode("utf-8")
    st.download_button(
        label="📥 Export Full Analyzed Dataset (CSV)",
        data=csv_bytes,
        file_name=f"{symbol}_{primary_interval}_analyzed.csv",
        mime="text/csv"
    )

    st.caption("Disclaimer: This software produces quantitative analytical scenarios and does not execute real-money orders. All calculations are non-predictive statistical estimates.")

# Programmatic entrypoint for PyCharm direct execution
if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[0].endswith(".py"):
        try:
            from streamlit.web import cli as stcli
            sys.argv = ["streamlit", "run", __file__]
            sys.exit(stcli.main())
        except Exception:
            main()
    else:
        main()


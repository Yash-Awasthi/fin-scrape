"""
ZAI Oracle — Whale Tracker
by Zawwar (github.com/Zawwarsami16)

Tracks where smart money is moving.
"Smart money moves first — retail follows."

Covers:
- Bitcoin top wallets (blockchain.com public API — no key needed)
- Ethereum whale wallets (Etherscan API)
- US Congress trading activity (public disclosure data)
- Known institutional addresses (MicroStrategy, Grayscale, etc.)

When whales move in the same direction as geopolitical signals,
that's when the pattern confidence goes to maximum.
"""

import os
import json
import time
import requests
from datetime import datetime
from config import DATA_PATH, ETHERSCAN_KEY, BTC_WHALE_ADDRESSES, ETH_WHALE_ADDRESSES


# ================================================================
# BITCOIN WHALE TRACKING
# The Bitcoin blockchain is fully public — no API key needed.
# We check balance changes on known large wallets.
# ================================================================
def fetch_btc_wallet(address, label):
    """
    Fetches current balance and recent transaction count
    for a known Bitcoin whale address.
    Uses blockchain.com public API — completely free.
    """
    try:
        r = requests.get(
            f"https://blockchain.info/rawaddr/{address}",
            params={"limit": 5},
            timeout=10
        )
        data = r.json()

        balance_btc = data.get("final_balance", 0) / 1e8  # satoshis to BTC
        n_tx        = data.get("n_tx", 0)
        total_recv  = data.get("total_received", 0) / 1e8
        total_sent  = data.get("total_sent", 0) / 1e8

        # Recent transactions (last 5)
        recent_txs = []
        for tx in data.get("txs", [])[:5]:
            # Determine if this wallet received or sent in this transaction
            received = sum(
                out["value"] for out in tx.get("out", [])
                if any(inp.get("addr") == address for inp in tx.get("inputs", []) or [])
                == False and out.get("addr") == address
            ) / 1e8

            recent_txs.append({
                "hash":   tx.get("hash", "")[:16] + "...",
                "time":   datetime.fromtimestamp(tx.get("time", 0)).strftime("%Y-%m-%d %H:%M"),
                "value_btc": round(received, 4),
            })

        return {
            "label":       label,
            "address":     address[:12] + "..." + address[-6:],
            "balance_btc": round(balance_btc, 2),
            "total_tx":    n_tx,
            "recent_txs":  recent_txs,
            "status":      "ok",
        }

    except Exception as e:
        return {"label": label, "status": "error", "error": str(e)}


def scan_btc_whales():
    """
    Scans all known BTC whale addresses.
    Returns summary of recent movement activity.
    """
    print("  Checking BTC whale wallets...")
    results = []
    total_btc_tracked = 0

    for label, address in BTC_WHALE_ADDRESSES.items():
        data = fetch_btc_wallet(address, label)
        if data["status"] == "ok":
            results.append(data)
            total_btc_tracked += data.get("balance_btc", 0)
        time.sleep(0.5)  # rate limit

    # Summarize movement signals
    active_wallets  = [r for r in results if r.get("recent_txs")]
    movement_signal = "ACCUMULATING" if len(active_wallets) > 2 else "HOLDING"

    return {
        "wallets_checked":  len(results),
        "total_btc_tracked": round(total_btc_tracked, 2),
        "active_wallets":   len(active_wallets),
        "movement_signal":  movement_signal,
        "wallets":          results,
    }


# ================================================================
# ETHEREUM WHALE TRACKING
# Uses Etherscan API — free tier is enough for this.
# ================================================================
def fetch_eth_wallet(address, label):
    """
    Fetches ETH balance and recent transactions for a known whale wallet.
    Requires Etherscan API key (free at etherscan.io/apis).
    """
    if not ETHERSCAN_KEY:
        return {"label": label, "status": "no_key"}

    try:
        # Get ETH balance
        balance_r = requests.get(
            "https://api.etherscan.io/api",
            params={
                "module":  "account",
                "action":  "balance",
                "address": address,
                "tag":     "latest",
                "apikey":  ETHERSCAN_KEY,
            },
            timeout=10
        )
        balance_data = balance_r.json()
        balance_eth  = int(balance_data.get("result", "0")) / 1e18

        # Get recent transactions (last 5)
        tx_r = requests.get(
            "https://api.etherscan.io/api",
            params={
                "module":     "account",
                "action":     "txlist",
                "address":    address,
                "startblock": 0,
                "endblock":   99999999,
                "page":       1,
                "offset":     5,
                "sort":       "desc",
                "apikey":     ETHERSCAN_KEY,
            },
            timeout=10
        )
        tx_data = tx_r.json()
        txs     = tx_data.get("result", [])

        recent_txs = []
        for tx in txs[:5]:
            value_eth = int(tx.get("value", "0")) / 1e18
            is_outgoing = tx.get("from", "").lower() == address.lower()
            recent_txs.append({
                "direction": "OUT" if is_outgoing else "IN",
                "value_eth": round(value_eth, 4),
                "time":      datetime.fromtimestamp(int(tx.get("timeStamp", 0))).strftime("%Y-%m-%d %H:%M"),
                "hash":      tx.get("hash", "")[:16] + "...",
            })

        # Detect recent large moves (>100 ETH)
        large_moves = [t for t in recent_txs if t["value_eth"] > 100]

        return {
            "label":       label,
            "address":     address[:8] + "..." + address[-6:],
            "balance_eth": round(balance_eth, 2),
            "recent_txs":  recent_txs,
            "large_moves": large_moves,
            "status":      "ok",
        }

    except Exception as e:
        return {"label": label, "status": "error", "error": str(e)}


def scan_eth_whales():
    """
    Scans known ETH whale addresses for significant movements.
    """
    if not ETHERSCAN_KEY:
        print("  ETH whale scan: no Etherscan key — skipping")
        return {"status": "no_key", "wallets": []}

    print("  Checking ETH whale wallets...")
    results = []
    large_move_count = 0

    for label, address in ETH_WHALE_ADDRESSES.items():
        data = fetch_eth_wallet(address, label)
        if data["status"] == "ok":
            results.append(data)
            large_move_count += len(data.get("large_moves", []))
        time.sleep(0.3)

    # Determine overall signal
    if large_move_count > 3:
        signal = "MAJOR MOVEMENT — multiple whales active"
    elif large_move_count > 0:
        signal = "SOME MOVEMENT — watch closely"
    else:
        signal = "QUIET — whales holding"

    return {
        "wallets_checked": len(results),
        "large_move_count": large_move_count,
        "signal":          signal,
        "wallets":         results,
    }


# ================================================================
# CONGRESS TRADING TRACKER
# US politicians must disclose trades — this is public data.
# "They always know before we do."
# ================================================================
def fetch_congress_trades():
    """
    Fetches recent US Congress member stock trades.
    Uses Capitol Trades public data (no API key needed).
    Politicians trading before major news = leading indicator.
    """
    print("  Checking Congress trading activity...")

    try:
        # Capitol Trades has a public feed
        r = requests.get(
            "https://www.capitoltrades.com/trades?pageSize=20&page=1",
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; research tool)",
                "Accept":     "application/json",
            },
            timeout=15
        )

        trades = []

        # Try JSON response
        if r.headers.get("content-type", "").startswith("application/json"):
            data = r.json()
            raw_trades = data.get("trades", data.get("data", []))

            for t in raw_trades[:15]:
                trades.append({
                    "politician": t.get("politician", {}).get("name", "Unknown"),
                    "party":      t.get("politician", {}).get("party", "?"),
                    "ticker":     t.get("asset", {}).get("ticker", "?"),
                    "asset_name": t.get("asset", {}).get("name", "?"),
                    "type":       t.get("type", "?"),  # BUY or SELL
                    "size":       t.get("size", "?"),
                    "date":       t.get("reportedAt", t.get("transactionDate", "?")),
                })

        # Analyze patterns
        buys  = [t for t in trades if "purchase" in t["type"].lower() or "buy" in t["type"].lower()]
        sells = [t for t in trades if "sale" in t["type"].lower() or "sell" in t["type"].lower()]

        # Sectors being bought/sold
        tickers_bought = [t["ticker"] for t in buys]
        tickers_sold   = [t["ticker"] for t in sells]

        # Detect if Congress is buying defensive assets (gold ETFs, bonds)
        defensive_buys = [t for t in buys if t["ticker"] in
                          ["GLD", "IAU", "TLT", "IEF", "SHY", "VXX", "UVXY"]]

        signal = "NEUTRAL"
        if len(defensive_buys) > 2:
            signal = "DEFENSIVE — Congress buying safe havens (bearish signal)"
        elif len(buys) > len(sells) * 2:
            signal = "BULLISH — Congress net buying"
        elif len(sells) > len(buys) * 2:
            signal = "BEARISH — Congress net selling"

        return {
            "total_trades":    len(trades),
            "buys":            len(buys),
            "sells":           len(sells),
            "signal":          signal,
            "defensive_buys":  len(defensive_buys),
            "recent_trades":   trades[:10],
            "tickers_bought":  list(set(tickers_bought))[:10],
            "tickers_sold":    list(set(tickers_sold))[:10],
            "status":          "ok",
        }

    except Exception as e:
        # Fallback: return neutral signal without crashing
        return {
            "status":  "limited",
            "signal":  "NEUTRAL",
            "message": f"Congress data limited: {str(e)[:50]}",
            "trades":  [],
        }


# ================================================================
# COMBINED WHALE SUMMARY
# Takes BTC + ETH + Congress and produces one unified signal
# ================================================================
def get_whale_summary(btc_data, eth_data, congress_data):
    """
    Synthesizes all whale data into one directional signal.
    When multiple whale categories agree → high confidence signal.
    """
    signals = []

    # BTC signal
    btc_signal = btc_data.get("movement_signal", "UNKNOWN")
    if btc_signal == "ACCUMULATING":
        signals.append("BULLISH")
    elif btc_signal == "DISTRIBUTING":
        signals.append("BEARISH")

    # ETH signal
    eth_signal = eth_data.get("signal", "")
    if "MAJOR MOVEMENT" in eth_signal:
        signals.append("ACTIVE")

    # Congress signal
    congress_signal = congress_data.get("signal", "NEUTRAL")
    if "BEARISH" in congress_signal or "DEFENSIVE" in congress_signal:
        signals.append("BEARISH")
    elif "BULLISH" in congress_signal:
        signals.append("BULLISH")

    # Overall
    bullish_count = signals.count("BULLISH")
    bearish_count = signals.count("BEARISH")

    if bearish_count > bullish_count:
        overall = "SMART MONEY EXITING — multiple whale categories bearish"
    elif bullish_count > bearish_count:
        overall = "SMART MONEY ACCUMULATING — whales buying"
    else:
        overall = "MIXED WHALE SIGNALS — no clear direction"

    return {
        "overall_signal": overall,
        "btc_signal":     btc_signal,
        "eth_signal":     eth_signal,
        "congress_signal": congress_signal,
        "confidence":     "HIGH" if len(signals) >= 2 else "LOW",
    }


# ================================================================
# MAIN SCAN FUNCTION
# ================================================================
def scan_all_whales():
    """
    Runs all whale tracking modules and returns a unified report.
    """
    print("\n  WHALE INTELLIGENCE SCAN")
    print("  " + "─" * 40)

    btc_data      = scan_btc_whales()
    eth_data      = scan_eth_whales()
    congress_data = fetch_congress_trades()
    summary       = get_whale_summary(btc_data, eth_data, congress_data)

    result = {
        "scanned_at": datetime.now().isoformat(),
        "summary":    summary,
        "btc":        btc_data,
        "eth":        eth_data,
        "congress":   congress_data,
    }

    # Save to disk
    os.makedirs(f"{DATA_PATH}/whales", exist_ok=True)
    with open(f"{DATA_PATH}/whales/latest.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"  Whale signal: {summary['overall_signal']}")
    return result


if __name__ == "__main__":
    result = scan_all_whales()
    print(json.dumps(result["summary"], indent=2))

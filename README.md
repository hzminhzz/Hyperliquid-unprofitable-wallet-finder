# Hyperliquid-unprofitable-wallet-finder

# Hyperliquid Bad Trader Tracker

This script identifies **consistently losing wallets** on [Hyperliquid](https://hyperliquid.xyz) in real time using their public SDK and API.

We monitor recent **liquidations**, check trading statistics for each wallet, and flag those with poor performance (low win rate, high leverage, negative PnL). These wallets are ideal candidates for **counter-trading**.

---

## 📁 Folder Structure

```
hyperliquid-bad-trader-tracker/
├── README.md
├── requirements.txt
└── tracker.py
```

---

## 🧪 Installation

```bash
git clone https://github.com/yourusername/hyperliquid-bad-trader-tracker.git
cd hyperliquid-bad-trader-tracker
pip install -r requirements.txt
```

---

## 🔧 Requirements (requirements.txt)

```
hyperliquid-sdk
```

---

## 🚀 Usage

```bash
python tracker.py
```

---

## 📜 Script Explanation (tracker.py)

```python
from hyperliquid.exchange import Exchange
import time

# 1. Initialize SDK client to interact with Hyperliquid
exchange = Exchange(url="https://api.hyperliquid.xyz")
checked_wallets = set()  # To avoid re-checking the same wallets

# 2. Define how to detect a "bad trader"
def analyze_wallet(wallet):
    try:
        user_state = exchange.user_state(wallet)
        perp_stats = user_state.get("perpStats")
        if not perp_stats:
            return None

        total_trades = perp_stats.get("numClosedPositions", 0)
        win_rate = perp_stats.get("winRate", 1.0)
        pnl = perp_stats.get("totalPnlUsd", 0.0)
        avg_leverage = perp_stats.get("avgLeverage", 1.0)

        # Criteria for "losing trader"
        if total_trades >= 10 and win_rate < 0.3 and pnl < 0 and avg_leverage > 8:
            return {
                "wallet": wallet,
                "win_rate": round(win_rate * 100, 2),
                "pnl": round(pnl, 2),
                "avg_leverage": round(avg_leverage, 2),
                "trades": total_trades
            }
    except Exception as e:
        print(f"Error checking wallet {wallet}: {e}")
    return None

# 3. Main loop to fetch recent liquidations and analyze wallets
def monitor_liquidations():
    print("🔍 Monitoring recent liquidations...")
    while True:
        try:
            liqs = exchange.all_liquidation_info()
            for liq in liqs:
                wallet = liq.get("user")
                if not wallet or wallet in checked_wallets:
                    continue
                result = analyze_wallet(wallet)
                if result:
                    print(f"\n🛑 BAD TRADER FOUND:\n{result}\n")
                checked_wallets.add(wallet)
        except Exception as e:
            print(f"Error in loop: {e}")
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    monitor_liquidations()
```

---

## 📌 Notes
- This is a **read-only script**: it doesn't interact with private keys or place trades.
- To extend: add **WebSocket stream**, **Telegram alerts**, or **live position tracking**.

---

## 📬 Contact
Created by @yourusername — inspired by on-chain alpha hunters.

Feel free to fork, improve, or request features!

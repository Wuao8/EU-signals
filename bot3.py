import os
import requests
import pandas as pd
import yfinance as yf

# ======================
# CONFIG
# ======================

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# ======================
# TELEGRAM
# ======================

def send_message(text):
    url = f"{BASE_URL}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}")


# ======================
# EUROPEAN STOCK UNIVERSE
# ======================

EU_STOCKS = [
    # Germania
    "SAP.DE", "SIE.DE", "BAS.DE", "BMW.DE", "VOW3.DE",

    # Francia
    "MC.PA", "OR.PA", "SAN.PA", "AIR.PA", "SU.PA",

    # Italia
    "ENEL.MI", "ENI.MI", "ISP.MI", "UCG.MI",

    # Olanda
    "ASML.AS", "UNA.AS", "INGA.AS",

    # Spagna
    "SAN.MC", "IBE.MC", "ITX.MC"
]


# ======================
# DATA
# ======================

def get_data(symbol, period="6mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)

        if df is None or df.empty:
            return None

        df = df.reset_index()
        df["Close"] = df["Close"].astype(float)

        return df

    except Exception as e:
        print(f"Data error {symbol}: {e}")
        return None


# ======================
# INDICATORS
# ======================

def calculate_ema(df, period=20):
    return df["Close"].ewm(span=period, adjust=False).mean()


def calculate_macd(df):
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    return macd, signal


# ======================
# SIGNAL LOGIC
# ======================

def check_signal(df):
    df["ema20"] = calculate_ema(df)

    macd, signal = calculate_macd(df)

    df["macd"] = macd
    df["signal"] = signal

    prev = df.iloc[-2]
    last = df.iloc[-1]

    price = last["Close"]

    # ======================
    # PRICE FILTER (18–26 EUR)
    # ======================
    price_filter = 18 <= price <= 26

    # ======================
    # EMA CROSS
    # ======================
    ema_cross = (
        prev["Close"] < prev["ema20"]
        and last["Close"] > last["ema20"]
    )

    # ======================
    # MACD CROSS
    # ======================
    macd_cross = (
        prev["macd"] < prev["signal"]
        and last["macd"] > last["signal"]
    )

    return price_filter and ema_cross and macd_cross


# ======================
# SCAN ENGINE
# ======================

def run_scan():
    signals = []

    for symbol in EU_STOCKS:
        try:
            df = get_data(symbol)

            if df is None or len(df) < 50:
                continue

            if check_signal(df):
                last_price = df.iloc[-1]["Close"]

                signals.append(f"{symbol} @ {round(last_price, 2)}")

        except Exception as e:
            print(f"Error {symbol}: {e}")

    return signals


# ======================
# MAIN
# ======================

if __name__ == "__main__":
    print("Starting Bot3 Scan...")

    results = run_scan()

    if results:
        message = "🚨 STOCK SIGNALS (EUROPE)\n\n" + "\n".join(results)
        send_message(message)

        print("Signals found:", results)
    else:
        print("No signals found")

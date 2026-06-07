import os
import requests
import pandas as pd
import yfinance as yf

# ======================
# CONFIG
# ======================

TOKEN = os.environ.get("TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))
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
            }
        )
    except Exception as e:
        print(f"Telegram error: {e}")


# ======================
# EUROPE STOCK UNIVERSE
# ======================
# Nota: qui partiamo con una base "liquida Europa"
# poi la espandiamo step by step

EU_STOCKS = [
    # Germania
    "SAP.DE", "SIE.DE", "BAS.DE", "BMW.DE", "VOW3.DE",

    # Francia
    "MC.PA", "OR.PA", "SAN.PA", "AIR.PA", "SU.PA",

    # Italia
    "ENEL.MI", "ENI.MI", "ISP.MI", "UCG.MI", "STM.MI",

    # Olanda
    "ASML.AS", "UNA.AS", "INGA.AS",

    # Spagna
    "SAN.MC", "IBE.MC", "ITX.MC"
]


# ======================
# DATA FETCH
# ======================

def get_data(symbol, period="6mo", interval="1d"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)

    if df is None or df.empty:
        return None

    df = df.reset_index()
    df["Close"] = df["Close"].astype(float)

    return df


# ======================
# MAIN
# ======================

def run_scan():
    results = []

    for symbol in EU_STOCKS:
        try:
            df = get_data(symbol)

            if df is None:
                continue

            # placeholder per prossimi step
            print(f"Checked {symbol}")

        except Exception as e:
            print(f"Error {symbol}: {e}")

    return results


if __name__ == "__main__":
    print("Scanning EU stocks...")
    run_scan()

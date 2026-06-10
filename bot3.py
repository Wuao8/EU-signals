import os
import requests
import pandas as pd
import yfinance as yf

# ======================
# CONFIG
# ======================

TOKEN = str(os.environ.get("TOKEN"))
CHAT_ID = str(os.environ.get("CHAT_ID"))
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# ======================
# TELEGRAM
# ======================

def send_message(text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except:
        pass


# ======================
# EUROPEAN STOCK UNIVERSE
# ======================

def get_eu_universe():
    return list(set([

        # 🇩🇪 Germania (DAX proxy)
"SAP.DE",
"SIE.DE",
"ALV.DE",
"BMW.DE",
"VOW3.DE",
"MBG.DE",
"BAS.DE",
"BAYN.DE",
"DBK.DE",
"ADS.DE",
"IFX.DE",
"RWE.DE",
"EOAN.DE",
"MRK.DE",
"MTX.DE",
"DTE.DE",     # Deutsche Telekom
"HEN3.DE",    # Henkel
"BEI.DE",     # Beiersdorf
"QIA.DE",     # Qiagen
"HEI.DE",     # Heidelberg Materials
"FRE.DE"     # Fresenius SE       

       # 🇫🇷 Francia (CAC 40 proxy)
"MC.PA",
"OR.PA",
"TTE.PA",
"SAN.PA",
"AIR.PA",
"SU.PA",
"BNP.PA",
"CS.PA",
"DG.PA",
"AI.PA",
"KER.PA",
"HO.PA",
"ML.PA",
"RI.PA",
"PUB.PA",
"DSY.PA",
"EL.PA",
"VIE.PA",
"CA.PA",
"ENGI.PA",
"ORA.PA",
"SGO.PA"        
        

        # 🇮🇹 Italia (FTSE MIB)
"ENEL.MI",
"ENI.MI",
"ISP.MI",
"UCG.MI",
"STLAM.MI",
"LDO.MI",
"PRY.MI",
"SRG.MI",
"TRN.MI",
"CNHI.MI",
"MB.MI",
"ATL.MI",
"REC.MI",
"PST.MI",
"BAMI.MI",
"MBG.MI",
"DIA.MI",
"TEN.MI",
"HER.MI",
"MONC.MI",
"BPE.MI"        
        

        # 🇳🇱 Olanda
"ASML.AS",
"AD.AS",
"INGA.AS",
"UNA.AS",
"PHIA.AS",
"HEIA.AS",
"PRX.AS",
"AKZA.AS",
"NN.AS",
"WKL.AS",
"MT.AS",
"IMCD.AS",
"AGN.AS",
"RAND.AS"        

        # 🇪🇸 Spagna (IBEX)
"SAN.MC",
"BBVA.MC",
"ITX.MC",
"IBE.MC",
"REP.MC",
"AMS.MC",
"ACS.MC",
"FER.MC",
"TEF.MC",
"ENG.MC",
"MRL.MC",
"MAP.MC",
"COL.MC",
"ROVI.MC",
"GRF.MC"

        
        # 🇨🇭 Svizzera
"NESN.SW",
"NOVN.SW",
"ROG.SW",
"UBSG.SW",
"CFR.SW",
"SREN.SW",
"ZURN.SW",
"ABBN.SW",
"LONN.SW",
"GIVN.SW",
"SGSN.SW",
"SIKA.SW",
"ALC.SW",
"PGHN.SW",
        

       # 🇬🇧 UK (FTSE)
"HSBA.L",
"BP.L",
"SHEL.L",
"GSK.L",
"ULVR.L",
"RIO.L",
"GLEN.L",
"AZN.L",
"LSEG.L",
"BA.L",
"RR.L",
"BARC.L",
"VOD.L",
"NG.L",
"SMIN.L",
"PRU.L",
"LLOY.L",
"AAL.L",
"BT-A.L"
    ]))


# ======================
# DATA
# ======================

def get_all_data(symbols, period="6mo", interval="1d"):
    try:
        data = yf.download(
            tickers=" ".join(symbols),
            period=period,
            interval=interval,
            group_by="ticker",
            threads=True,
            progress=False
        )
        return data
    except Exception:
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

    
    # ======================
    # EMA CROSS
    # ======================
    ema_cross = (
        prev["Close"] < prev["ema20"]
        and last["Close"] > last["ema20"]
    )

    # ======================
    # MACD ALREADY BULLISH
    # ======================
    macd_bullish = (
        last["macd"] > last["signal"]
    )

    return ema_cross and macd_bullish


# ======================
# SCAN ENGINE
# ======================

def run_scan():
    signals = []
    symbols = get_eu_universe()

    chunk_size = 15  # batch piccoli = stabile

    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i+chunk_size]

        try:
            data = yf.download(
                tickers=" ".join(chunk),
                period="6mo",
                interval="1d",
                group_by="ticker",
                threads=False,
                progress=False
            )
        except Exception:
            continue

        if data is None:
            continue

        for symbol in chunk:
            try:
                if symbol not in data.columns.levels[0]:
                    continue

                df = data[symbol][["Close"]].copy()
                df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
                df = df.dropna()

                if len(df) < 50:
                    continue

                if check_signal(df):
                    price = float(df.iloc[-1]["Close"])
                    signals.append(f"{symbol} @ {round(price, 2)}")

            except Exception:
                continue

    return signals


# ======================
# MAIN
# ======================

if __name__ == "__main__":
    print("Starting Bot3 Scan...")
    
    results = run_scan()

    if results:
        message = "STOCK SIGNALS (EUROPE)\n\n" + "\n".join(str(x) for x in results)
        send_message(message)

        print("Signals found:", results)
    else:
        print("No signals found")

import time
time.sleep(2)

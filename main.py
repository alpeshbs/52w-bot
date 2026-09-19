import io
import re
import requests
import pandas as pd
from datetime import datetime, timedelta

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
TARGET_CHAT_ID = "1051774043"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/"
}

def get_52w_data():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=15)
    except Exception:
        pass

    today = datetime.now()
    high_list, low_list = [], []
    trade_date_str = ""

    for i in range(5):
        target_date = today - timedelta(days=i)
        d_str = target_date.strftime("%d%m%Y")          # 18092026
        day_num = target_date.strftime("%d")            # 18
        mon_str = target_date.strftime("%b")            # Sep
        yr_full = target_date.strftime("%Y")            # 2026
        yr_short = target_date.strftime("%y")           # 26

        url = f"https://nsearchives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv"
        url_alt = f"https://archives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv"

        raw_csv = None
        for u in [url, url_alt]:
            try:
                r = session.get(u, headers=HEADERS, timeout=15)
                if r.status_code == 200 and len(r.text) > 1000:
                    raw_csv = r.text
                    trade_date_str = f"{day_num}-{mon_str}-{yr_full}"
                    break
            except Exception:
                continue

        if raw_csv:
            lines = raw_csv.splitlines()
            # હેડર લાઈન શોધો જ્યાં SYMBOL લખેલું હોય
            header_idx = -1
            for idx, line in enumerate(lines[:10]):
                if "SYMBOL" in line.upper():
                    header_idx = idx
                    break

            if header_idx != -1:
                # શુદ્ધ CSV ડેટા મેળવો
                clean_csv = "\n".join(lines[header_idx:])
                df = pd.read_csv(io.StringIO(clean_csv))
                
                # તારીખ સરખામણી માટે સંભવિત પેટર્ન: 18-sep-2026 અથવા 18-sep-26
                patt_full = f"{day_num}-{mon_str}-{yr_full}".lower()
                patt_short = f"{day_num}-{mon_str}-{yr_short}".lower()

                for _, row in df.iterrows():
                    try:
                        vals = [str(x).strip() for x in row.values]
                        sym = vals[0]
                        if not sym or sym.lower() in ['nan', '-', 'symbol']:
                            continue

                        # લાઈનમાં રહેલી તમામ કોલમ્સ તપાસો
                        # જો તારીખ મેચ થાય, તો તેની તરત પહેલાંની વેલ્યુ એ ભાવ હશે
                        for c_idx, cell_val in enumerate(vals):
                            cell_clean = cell_val.replace(" ", "").lower()
                            
                            # High ચેક
                            if cell_clean in [patt_full, patt_short]:
                                # કોલમ ૩ એ High Date છે
                                if c_idx == 3 or "high" in str(df.columns[c_idx]).lower():
                                    price = vals[c_idx - 1].replace(',', '').strip()
                                    if price != '-' and float(price) > 0:
                                        high_list.append({"stock": sym, "val": f"{float(price):.2f}"})
                                
                                # કોલમ ૫ એ Low Date છે
                                elif c_idx == 5 or "low" in str(df.columns[c_idx]).lower():
                                    price = vals[c_idx - 1].replace(',', '').strip()
                                    if price != '-' and float(price) > 0:
                                        low_list.append({"stock": sym, "val": f"{float(price):.2f}"})
                    except Exception:
                        continue

            break

    return high_list, low_list, trade_date_str

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TARGET_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("Telegram send error:", e)

def main():
    highs, lows, trade_date = get_52w_data()

    if not highs and not lows:
        send_telegram(f"ℹ️ <b>NSE અપડેટ ({trade_date}):</b> આજના સેશનમાં કોઈ સ્ટોક કે ETF એ નવો 52W High કે Low બનાવ્યો નથી.")
        return

    if highs:
        msg = f"🚀 <b>NSE 52-Week HIGH ({trade_date}) - {len(highs)}:</b>\n<pre>"
        msg += "Symbol     | 52W High Price\n---------------------------\n"
        for s in highs[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['val']:<12}\n"
        msg += "</pre>"
        send_telegram(msg)

    if lows:
        msg = f"🔻 <b>NSE 52-Week LOW ({trade_date}) - {len(lows)}:</b>\n<pre>"
        msg += "Symbol     | 52W Low Price \n---------------------------\n"
        for s in lows[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['val']:<12}\n"
        msg += "</pre>"
        send_telegram(msg)

if __name__ == "__main__":
    main()
    

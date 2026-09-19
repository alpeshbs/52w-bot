import io
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
    matched_date_str = ""

    # છેલ્લા 5 દિવસમાંથી ઉપલબ્ધ ફાઇલ શોધો
    for i in range(5):
        target_date = today - timedelta(days=i)
        d_str = target_date.strftime("%d%m%Y")          # 18092026
        check_date = target_date.strftime("%d-%b-%Y")   # 18-Sep-2026

        url = f"https://nsearchives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv"
        url_alt = f"https://archives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv"

        content = None
        for u in [url, url_alt]:
            try:
                r = session.get(u, headers=HEADERS, timeout=15)
                if r.status_code == 200 and len(r.text) > 1000:
                    content = r.text
                    matched_date_str = check_date
                    break
            except Exception:
                continue

        if content:
            # લાઇન 3 થી હેડર્સ શરૂ થાય છે (Skip initial 2 lines)
            df = pd.read_csv(io.StringIO(content), skiprows=2)
            df.columns = [str(c).strip().replace(' ', '_').upper() for c in df.columns]

            # કોલમ્સ: SYMBOL, SERIES, ADJUSTED_52_WEEK_HIGH, 52_WEEK_HIGH_DT, ADJUSTED_52_WEEK_LOW, 52_WEEK_LOW_DT
            sym_col = df.columns[0]
            series_col = df.columns[1]
            high_val_col = df.columns[2]
            high_dt_col = df.columns[3]
            low_val_col = df.columns[4]
            low_dt_col = df.columns[5]

            # શેર્સ અને ETFs (EQ, BE, SM, ST, E1, E2)
            allowed_series = ['EQ', 'BE', 'SM', 'ST', 'E1', 'E2']
            if series_col in df.columns:
                df = df[df[series_col].isin(allowed_series)]

            for _, row in df.iterrows():
                try:
                    sym = str(row[sym_col]).strip()
                    if not sym or sym.lower() in ['nan', '-']:
                        continue

                    # 52W High ચકાસણી: તારીખ આજના દિવસ સાથે મળવી જોઈએ
                    h_dt = str(row[high_dt_col]).strip()
                    if h_dt.lower() == check_date.lower():
                        h_val = float(str(row[high_val_col]).replace(',', ''))
                        high_list.append({"stock": sym, "val": f"{h_val:.2f}"})

                    # 52W Low ચકાસણી: તારીખ આજના દિવસ સાથે મળવી જોઈએ
                    l_dt = str(row[low_dt_col]).strip()
                    if l_dt.lower() == check_date.lower():
                        l_val = float(str(row[low_val_col]).replace(',', ''))
                        low_list.append({"stock": sym, "val": f"{l_val:.2f}"})
                except Exception:
                    continue

            # ડેટા મળતાં જ લૂપમાંથી બહાર નીકળો
            break

    return high_list, low_list, matched_date_str

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TARGET_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def main():
    highs, lows, trade_date = get_52w_data()

    if not highs and not lows:
        send_telegram(f"ℹ️ <b>NSE અપડેટ ({trade_date}):</b> આજના સેશનમાં કોઈ નવો 52W High કે Low સ્ટોક/ETF બન્યો નથી.")
        return

    # 52W High ટેબલ
    if highs:
        msg = f"🚀 <b>NSE 52-Week HIGH ({trade_date}) - {len(highs)} સ્ટોક્સ & ETFs:</b>\n<pre>"
        msg += "Symbol     | 52W High Price\n---------------------------\n"
        for s in highs[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['val']:<12}\n"
        msg += "</pre>"
        send_telegram(msg)

    # 52W Low ટેબલ
    if lows:
        msg = f"🔻 <b>NSE 52-Week LOW ({trade_date}) - {len(lows)} સ્ટોક્સ & ETFs:</b>\n<pre>"
        msg += "Symbol     | 52W Low Price \n---------------------------\n"
        for s in lows[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['val']:<12}\n"
        msg += "</pre>"
        send_telegram(msg)

if __name__ == "__main__":
    main()

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
    trade_date_str = ""

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
                    trade_date_str = check_date
                    break
            except Exception:
                continue

        if content:
            # 2 લાઈન ડિસ્ક્લેમર છોડીને ત્રીજી લાઈન હેડર તરીકે લો
            df = pd.read_csv(io.StringIO(content), skiprows=2)
            
            # કોલમના નામ કોઈપણ ફોર્મેટમાં હોય તો પણ ઈન્ડેક્સ નંબરથી પકડો
            # Col 0: SYMBOL | Col 1: SERIES | Col 2: High Price | Col 3: High Date | Col 4: Low Price | Col 5: Low Date
            sym_col = df.columns[0]
            series_col = df.columns[1]
            h_val_col = df.columns[2]
            h_dt_col = df.columns[3]
            l_val_col = df.columns[4]
            l_dt_col = df.columns[5]

            # તારીખ સરખામણી માટે ક્લીન ટેક્સ્ટ બનાવો (e.g. '18-sep-2026')
            target_dt_clean = check_date.replace(" ", "").strip().lower()

            for _, row in df.iterrows():
                try:
                    sym = str(row[sym_col]).strip()
                    if not sym or sym.lower() in ['nan', '-', 'symbol']:
                        continue

                    # High Date ચેક
                    h_dt = str(row[h_dt_col]).replace(" ", "").strip().lower()
                    if h_dt == target_dt_clean:
                        val = str(row[h_val_col]).replace(',', '').strip()
                        if val != '-':
                            high_list.append({"stock": sym, "val": f"{float(val):.2f}"})

                    # Low Date ચેક
                    l_dt = str(row[l_dt_col]).replace(" ", "").strip().lower()
                    if l_dt == target_dt_clean:
                        val = str(row[l_val_col]).replace(',', '').strip()
                        if val != '-':
                            low_list.append({"stock": sym, "val": f"{float(val):.2f}"})
                except Exception:
                    continue

            # ડેટા પ્રોસેસ થઈ ગયો એટલે લૂપ પૂરું કરો
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
        send_telegram(f"ℹ️ <b>NSE અપડેટ ({trade_date}):</b> આજના સેશનમાં કોઈ નવો 52W High કે Low સ્ટોક/ETF બન્યો નથી.")
        return

    # 52-Week High ટેબલ
    if highs:
        msg = f"🚀 <b>NSE 52-Week HIGH ({trade_date}) - {len(highs)} સ્ટોક્સ & ETFs:</b>\n<pre>"
        msg += "Symbol     | 52W High Price\n---------------------------\n"
        for s in highs[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['val']:<12}\n"
        msg += "</pre>"
        send_telegram(msg)

    # 52-Week Low ટેબલ
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
    

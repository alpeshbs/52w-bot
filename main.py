import io
import requests
import pandas as pd
from datetime import datetime, timedelta

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
TARGET_CHAT_ID = "1051774043"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TARGET_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=15)
    except Exception as e:
        print("Telegram error:", e)

def run_diagnostic():
    # UTC માંથી સીધો ભારતીય સમય (IST = UTC + 5:30)
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/all-reports"
    }

    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=15)
    except Exception:
        pass

    logs = []
    found_file = None
    file_content = ""
    used_date_str = ""

    # છેલ્લા 4 ટ્રેડિંગ દિવસ ચેક કરો
    for i in range(1, 5):
        t_date = now_ist - timedelta(days=i)
        d_str = t_date.strftime("%d%m%Y")          # 18092026
        dt_display = t_date.strftime("%d-%b-%Y")    # 18-Sep-2026

        candidate_urls = [
            f"https://nsearchives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv",
            f"https://archives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv",
            f"https://www.nseindia.com/api/reports-download?filename=CM_52_wk_High_low_{d_str}.csv&type=equities"
        ]

        for u in candidate_urls:
            try:
                res = session.get(u, headers=headers, timeout=12)
                short_u = u.split("/")[-1]
                logs.append(f"{short_u} ➔ {res.status_code}")
                if res.status_code == 200 and len(res.text) > 1000:
                    found_file = u
                    file_content = res.text
                    used_date_str = dt_display
                    break
            except Exception as ex:
                logs.append(f"Err: {str(ex)[:15]}")

        if found_file:
            break

    if not found_file:
        send_telegram("❌ <b>ફાઈલ ન મળી!</b>\n" + "\n".join(logs[:6]))
        return

    lines = file_content.splitlines()
    header_idx = -1
    for idx, l in enumerate(lines[:10]):
        if "SYMBOL" in l.upper():
            header_idx = idx
            break

    if header_idx == -1:
        send_telegram(f"⚠️ ફાઈલ મળી પણ SYMBOL હેડર ન મળ્યું: {lines[0][:40]}")
        return

    df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))

    sym_col = df.columns[0]
    high_val_col = df.columns[2]
    high_dt_col = df.columns[3]
    low_val_col = df.columns[4]
    low_dt_col = df.columns[5]

    # તારીખ સરખામણી માટે (દા.ત. '18-sep-2026' અથવા '18-sep-26')
    day = used_date_str[:2].lower()
    mon = used_date_str[3:6].lower()
    yr_full = used_date_str[-4:].lower()
    yr_short = used_date_str[-2:].lower()

    highs, lows = [], []
    for _, row in df.iterrows():
        try:
            s = str(row[sym_col]).strip()
            if not s or s.lower() in ['nan', '-', 'symbol']:
                continue

            h_dt = str(row[high_dt_col]).replace(" ", "").lower()
            if (f"{day}-{mon}-{yr_full}" in h_dt) or (f"{day}-{mon}-{yr_short}" in h_dt):
                h_p = str(row[high_val_col]).replace(',', '').strip()
                if h_p != '-':
                    highs.append({"stock": s, "val": h_p})

            l_dt = str(row[low_dt_col]).replace(" ", "").lower()
            if (f"{day}-{mon}-{yr_full}" in l_dt) or (f"{day}-{mon}-{yr_short}" in l_dt):
                l_p = str(row[low_val_col]).replace(',', '').strip()
                if l_p != '-':
                    lows.append({"stock": s, "val": l_p})
        except Exception:
            continue

    msg = f"✅ <b>NSE ડેટા રિપોર્ટ ({used_date_str})</b>\nકુલ લિસ્ટેડ સ્ટોક્સ: {len(df)}\n"
    msg += f"🚀 52W High: {len(highs)} | 🔻 52W Low: {len(lows)}\n\n"

    if highs:
        msg += "<b>52-Week High (ટોપ 20):</b>\n<pre>"
        msg += "Symbol     | 52W High\n----------------------\n"
        for item in highs[:20]:
            msg += f"{item['stock'][:10]:<10} | {item['val']:<10}\n"
        msg += "</pre>\n"

    if lows:
        msg += "<b>52-Week Low (ટોપ 20):</b>\n<pre>"
        msg += "Symbol     | 52W Low\n----------------------\n"
        for item in lows[:20]:
            msg += f"{item['stock'][:10]:<10} | {item['val']:<10}\n"
        msg += "</pre>"

    send_telegram(msg)

if __name__ == "__main__":
    run_diagnostic()
                

import io
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

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
    # ભારતીય સમય (IST) મુજબ તારીખ નક્કી કરો
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/all-reports"
    }

    # કૂકી મેળવો
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
        d_str = t_date.strftime("%d%m%Y")       # 18092026
        dt_display = t_date.strftime("%d-%b-%Y") # 18-Sep-2026

        # સંભવિત تمام URLs
        candidate_urls = [
            f"https://nsearchives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv",
            f"https://archives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv",
            f"https://www.nseindia.com/api/reports-download?filename=CM_52_wk_High_low_{d_str}.csv&type=equities",
            f"https://nsearchives.nseindia.com/archives/equities/bhavcopy/pr/CM_52_wk_High_low_{d_str}.csv"
        ]

        for u in candidate_urls:
            try:
                res = session.get(u, headers=headers, timeout=12)
                logs.append(f"URL: ...{u[-35:]} ➔ Status: {res.status_code}")
                if res.status_code == 200 and len(res.text) > 1500:
                    found_file = u
                    file_content = res.text
                    used_date_str = dt_display
                    break
            except Exception as ex:
                logs.append(f"Err: {str(ex)[:20]}")

        if found_file:
            break

    # જો ફાઈલ ન મળે તો લોગ મોકલી આપો
    if not found_file:
        send_telegram("❌ <b>ફાઈલ ડાઉનલોડ નિષ્ફળ!</b>\n\n<b>ટ્રાય કરેલા લિંક્સ:</b>\n" + "\n".join(logs[:6]))
        return

    # જો ફાઈલ મળી જાય તો તેની અંદરથી ડેટા પ્રોસેસ કરો
    lines = file_content.splitlines()
    header_idx = -1
    for idx, l in enumerate(lines[:10]):
        if "SYMBOL" in l.upper():
            header_idx = idx
            break

    if header_idx == -1:
        send_telegram(f"⚠️ ફાઈલ મળી પણ SYMBOL હેડર ન મળ્યું! પહેલી લાઈન: {lines[0][:50]}")
        return

    df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    
    # કોલમ્સ ઇન્ડેક્સ
    sym_col = df.columns[0]
    high_val_col = df.columns[2]
    high_dt_col = df.columns[3]
    low_val_col = df.columns[4]
    low_dt_col = df.columns[5]

    target_clean = used_date_str.replace(" ", "").lower()

    highs, lows = [], []
    for _, row in df.iterrows():
        try:
            s = str(row[sym_col]).strip()
            if not s or s.lower() in ['nan', '-', 'symbol']:
                continue

            h_dt = str(row[high_dt_col]).replace(" ", "").lower()
            if target_clean in h_dt:
                h_p = str(row[high_val_col]).replace(',', '').strip()
                highs.append({"stock": s, "val": h_p})

            l_dt = str(row[low_dt_col]).replace(" ", "").lower()
            if target_clean in l_dt:
                l_p = str(row[low_val_col]).replace(',', '').strip()
                lows.append({"stock": s, "val": l_p})
        except Exception:
            continue

    # રિપોર્ટ મોકલો
    msg = f"✅ <b>સફળ ડાઉનલોડ:</b> {used_date_str}\nકુલ રેકોર્ડ્સ: {len(df)}\n"
    msg += f"🚀 52W High મળ્યા: {len(highs)}\n🔻 52W Low મળ્યા: {len(lows)}\n\n"

    if highs:
        msg += "<b>52-Week High (ટોપ 15):</b>\n<pre>"
        for item in highs[:15]:
            msg += f"{item['stock'][:10]:<10} | {item['val']:<10}\n"
        msg += "</pre>\n"

    if lows:
        msg += "<b>52-Week Low (ટોપ 15):</b>\n<pre>"
        for item in lows[:15]:
            msg += f"{item['stock'][:10]:<10} | {item['val']:<10}\n"
        msg += "</pre>"

    send_telegram(msg)

if __name__ == "__main__":
    run_diagnostic()

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

def main():
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/all-reports"
    }

    found_file = None
    file_content = ""

    # આગળ-પાછળના દિવસોની ફાઈલો ચેક કરો
    check_offsets = [3, 2, 1, 0, -1, -2, -3]

    for offset in check_offsets:
        t_date = now_ist + timedelta(days=offset)
        d_str = t_date.strftime("%d%m%Y")

        urls = [
            f"https://nsearchives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv",
            f"https://archives.nseindia.com/content/CM_52_wk_High_low_{d_str}.csv"
        ]

        for u in urls:
            try:
                res = session.get(u, headers=headers, timeout=12)
                if res.status_code == 200 and len(res.text) > 2000:
                    found_file = u
                    file_content = res.text
                    break
            except Exception:
                continue

        if found_file:
            break

    if not found_file:
        send_telegram("❌ NSE 52W રિપોર્ટ ફાઈલ ડાઉનલોડ થઈ શકી નથી.")
        return

    lines = file_content.splitlines()
    header_idx = -1
    for idx, l in enumerate(lines[:10]):
        if "SYMBOL" in l.upper():
            header_idx = idx
            break

    df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))

    sym_col = df.columns[0]
    series_col = df.columns[1]
    h_val_col = df.columns[2]
    h_dt_col = df.columns[3]
    l_val_col = df.columns[4]
    l_dt_col = df.columns[5]

    all_dates = pd.concat([
        pd.to_datetime(df[h_dt_col].replace('-', None), format="%d-%b-%Y", errors='coerce'),
        pd.to_datetime(df[l_dt_col].replace('-', None), format="%d-%b-%Y", errors='coerce')
    ]).dropna()

    if all_dates.empty:
        send_telegram("⚠️ ફાઈલમાં કોઈ માન્ય તારીખ મળી નથી.")
        return

    latest_date_dt = all_dates.max()
    latest_date_str = latest_date_dt.strftime("%d-%b-%Y").upper()

    allowed_series = ['EQ', 'BE', 'SM', 'ST', 'BZ', 'E1', 'E2']
    df_filtered = df[df[series_col].isin(allowed_series)]

    high_list, low_list = [], []

    for _, row in df_filtered.iterrows():
        try:
            sym = str(row[sym_col]).strip()
            if not sym or sym in ['-', 'nan']:
                continue

            h_dt = str(row[h_dt_col]).strip().upper()
            if h_dt == latest_date_str:
                val = str(row[h_val_col]).replace(',', '').strip()
                if val != '-':
                    high_list.append({"stock": sym, "val": f"{float(val):.2f}"})

            l_dt = str(row[l_dt_col]).strip().upper()
            if l_dt == latest_date_str:
                val = str(row[l_val_col]).replace(',', '').strip()
                if val != '-':
                    low_list.append({"stock": sym, "val": f"{float(val):.2f}"})
        except Exception:
            continue

    # હેડર મેસેજ
    header_msg = (
        f"📊 <b>NSE 52-WEEK HIGH & LOW અપડેટ</b>\n"
        f"📅 સેશન તારીખ: <b>{latest_date_str}</b>\n\n"
        f"🚀 <b>52W High:</b> {len(high_list)} સ્ટોક્સ & ETFs\n"
        f"🔻 <b>52W Low:</b> {len(low_list)} સ્ટોક્સ & ETFs\n"
    )
    send_telegram(header_msg)

    # 52W High સ્ટોક્સ - મોટા અને બોલ્ડ અક્ષરો સાથે
    if high_list:
        chunk_size = 25
        for i in range(0, len(high_list), chunk_size):
            chunk = high_list[i:i + chunk_size]
            part = f" (ભાગ {i//chunk_size + 1})" if len(high_list) > chunk_size else ""
            msg = f"🚀 <b>52-Week HIGH સ્ટોક્સ & ETFs{part}:</b>\n\n"
            for s in chunk:
                msg += f"🔹 <b>{s['stock']}</b>  ➔  ₹<b>{s['val']}</b>\n"
            send_telegram(msg)

    # 52W Low સ્ટોક્સ - મોટા અને બોલ્ડ અક્ષરો સાથે
    if low_list:
        chunk_size = 25
        for i in range(0, len(low_list), chunk_size):
            chunk = low_list[i:i + chunk_size]
            part = f" (ભાગ {i//chunk_size + 1})" if len(low_list) > chunk_size else ""
            msg = f"🔻 <b>52-Week LOW સ્ટોક્સ & ETFs{part}:</b>\n\n"
            for s in chunk:
                msg += f"🔸 <b>{s['stock']}</b>  ➔  ₹<b>{s['val']}</b>\n"
            send_telegram(msg)

if __name__ == "__main__":
    main()

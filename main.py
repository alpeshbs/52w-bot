import io
import zipfile
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

def get_nse_bhavcopy():
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=15)
    except Exception:
        pass

    today = datetime.now()
    df = None

    # છેલ્લા 5 દિવસમાંથી છેલ્લી ઉપલબ્ધ સત્તાવાર ભાવકોપી
    for i in range(5):
        target_date = today - timedelta(days=i)
        d_str = target_date.strftime("%Y%m%d")
        url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d_str}_F_0000.csv.zip"
        try:
            r = session.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    csv_filename = z.namelist()[0]
                    with z.open(csv_filename) as f:
                        df = pd.read_csv(f)
                        print(f"Bhavcopy ડાઉનલોડ થઈ: {d_str}")
                        break
        except Exception:
            continue

    # જૂનો ફોર્મેટ બેકઅપ
    if df is None:
        for i in range(5):
            target_date = today - timedelta(days=i)
            day = target_date.strftime("%d")
            mon = target_date.strftime("%b").upper()
            yr = target_date.strftime("%Y")
            url = f"https://archives.nseindia.com/content/historical/EQUITIES/{yr}/{mon}/cm{day}{mon}{yr}bhav.csv.zip"
            try:
                r = session.get(url, headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        csv_filename = z.namelist()[0]
                        with z.open(csv_filename) as f:
                            df = pd.read_csv(f)
                            print(f"જૂની Bhavcopy મળી: {day}{mon}{yr}")
                            break
            except Exception:
                continue

    return df

def process_data(df):
    high_list, low_list = [], []
    if df is None or df.empty:
        return high_list, low_list

    df.columns = [str(c).strip().upper() for c in df.columns]

    series_col = 'SCTYSRS' if 'SCTYSRS' in df.columns else 'SERIES'
    symbol_col = 'TRADGSSYM' if 'TRADGSSYM' in df.columns else 'SYMBOL'
    close_col  = 'CLSPRC' if 'CLSPRC' in df.columns else 'CLOSE'
    high_col   = 'HGSTPRC' if 'HGSTPRC' in df.columns else 'HIGH'
    low_col    = 'LWSTPRC' if 'LWSTPRC' in df.columns else 'LOW'
    high52_col = 'HIGH52' if 'HIGH52' in df.columns else ('52W_HIGH' if '52W_HIGH' in df.columns else None)
    low52_col  = 'LOW52' if 'LOW52' in df.columns else ('52W_LOW' if '52W_LOW' in df.columns else None)

    # શેર્સ (EQ, BE, SM) ની સાથે ETFs (E1, E2) પણ સામેલ કર્યા
    if series_col in df.columns:
        df = df[df[series_col].isin(['EQ', 'BE', 'SM', 'ST', 'E1', 'E2'])]

    for _, row in df.iterrows():
        try:
            sym = str(row[symbol_col]).strip()
            close_p = float(row[close_col])
            high_p = float(row[high_col])
            low_p = float(row[low_col])

            # 52W High ચકાસણી
            if high52_col and high52_col in row:
                h52 = float(row[high52_col])
                if h52 > 0 and high_p >= h52:
                    high_list.append({"stock": sym, "cmp": f"{close_p:.2f}", "rec": f"{h52:.2f}"})

            # 52W Low ચકાસણી
            if low52_col and low52_col in row:
                l52 = float(row[low52_col])
                if l52 > 0 and low_p <= l52:
                    low_list.append({"stock": sym, "cmp": f"{close_p:.2f}", "rec": f"{l52:.2f}"})
        except Exception:
            continue

    return high_list, low_list

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
    df = get_nse_bhavcopy()
    if df is None:
        send_telegram("⚠️ <b>NSE અપડેટ:</b> NSE સર્વર પરથી ભાવકોપી ડાઉનલોડ થઈ શકી નથી.")
        return

    highs, lows = process_data(df)

    if not highs and not lows:
        send_telegram(f"ℹ️ <b>NSE અપડેટ:</b> {len(df)} સ્ટોક્સ/ETFs ની ભાવકોપી મળી છે, પરંતુ આજના સેશનમાં કોઈ નવો 52W High કે Low બન્યો નથી.")
        return

    if highs:
        msg = f"🚀 <b>NSE 52-Week HIGH (સ્ટોક્સ & ETFs - {len(highs)}):</b>\n<pre>"
        msg += "Symbol     | CMP      | 52W High\n--------------------------------\n"
        for s in highs[:30]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

    if lows:
        msg = f"🔻 <b>NSE 52-Week LOW (સ્ટોક્સ & ETFs - {len(lows)}):</b>\n<pre>"
        msg += "Symbol     | CMP      | 52W Low \n--------------------------------\n"
        for s in lows[:30]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

if __name__ == "__main__":
    main()

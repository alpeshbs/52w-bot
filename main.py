import io
import requests
import pandas as pd

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

def get_data():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    
    high_list, low_list = [], []
    
    # NSE 52W High CSV (તમામ જૂના અને નવા IPO સહિત)
    try:
        url_high = "https://archives.nseindia.com/content/CM_52_wk_High_low.csv"
        res = session.get(url_high, headers=headers, timeout=15)
        if res.status_code == 200:
            df = pd.read_csv(io.StringIO(res.text))
            # CSV કોલમ હેન્ડલિંગ
            df.columns = [c.strip().upper() for c in df.columns]
            for _, row in df.iterrows():
                sym = str(row.get('SYMBOL', ''))
                cmp_val = row.get('LTP', row.get('PREV_CLOSE', 0))
                h_val = row.get('NEW_52_HIGH', row.get('HIGH', 0))
                l_val = row.get('NEW_52_LOW', row.get('LOW', 0))
                
                if pd.notna(h_val) and float(h_val) > 0:
                    high_list.append({"stock": sym, "cmp": f"{float(cmp_val):.2f}", "rec": f"{float(h_val):.2f}"})
                if pd.notna(l_val) and float(l_val) > 0:
                    low_list.append({"stock": sym, "cmp": f"{float(cmp_val):.2f}", "rec": f"{float(l_val):.2f}"})
    except Exception as e:
        print("Archive CSV Error:", e)

    # જો આર્કાઇવ ખાલી હોય તો ડાયરેક્ટ API થી બેકઅપ ફેચ
    if not high_list and not low_list:
        try:
            session.get("https://www.nseindia.com", headers=headers, timeout=15)
            r_high = session.get("https://www.nseindia.com/api/live-analysis-52week-high-low?type=high", headers=headers, timeout=15).json()
            for r in r_high.get('data', []):
                high_list.append({"stock": str(r.get('symbol', '')), "cmp": f"{float(r.get('lastPrice', 0)):.2f}", "rec": f"{float(r.get('value', 0)):.2f}"})
                
            r_low = session.get("https://www.nseindia.com/api/live-analysis-52week-high-low?type=low", headers=headers, timeout=15).json()
            for r in r_low.get('data', []):
                low_list.append({"stock": str(r.get('symbol', '')), "cmp": f"{float(r.get('lastPrice', 0)):.2f}", "rec": f"{float(r.get('value', 0)):.2f}"})
        except Exception as e:
            print("API Error:", e)

    return high_list, low_list

def make_table(items, title, col):
    if not items:
        return [f"{title}\nઆજે કોઈ સ્ટોક મળ્યો નથી.\n"]
    msgs = []
    chunk_size = 25
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i+chunk_size]
        t = f"{title} (ભાગ {i//chunk_size + 1})\n" if len(items) > chunk_size else f"{title}\n"
        t += f"<pre>Stock      | CMP      | {col:<8}\n--------------------------------\n"
        for s in chunk:
            sym = s['stock'][:10]
            t += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        t += "</pre>\n"
        msgs.append(t)
    return msgs

def main():
    highs, lows = get_data()
    all_msgs = ["📊 <b>NSE 52-WEEK HIGH & LOW ડેઇલી અપડેટ</b>\n(નવા IPO અને તમામ લિસ્ટેડ સ્ટોક્સ)"]
    all_msgs += make_table(highs, "🚀 <b>આજના નવા 52-Week HIGH:</b>", "52W High")
    all_msgs += make_table(lows, "🔻 <b>આજના નવા 52-Week LOW:</b>", "52W Low")

    for cid in CHAT_IDS:
        for m in all_msgs:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": m, "parse_mode": "HTML"},
                    timeout=10
                )
            except Exception as e:
                print(f"Send error for {cid}: {e}")

if __name__ == "__main__":
    main()

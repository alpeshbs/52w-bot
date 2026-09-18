import io
import requests
import pandas as pd
from datetime import datetime, timedelta

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

def get_data_from_nse():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/all-reports"
    }
    
    # પહેલા NSE ની કૂકીઝ લો
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=15)
    except Exception as e:
        print("Home session error:", e)

    high_list, low_list = [], []

    # છેલ્લા 5 દિવસમાંથી જે છેલ્લો ટ્રેડિંગ દિવસ હોય તેની CSV શોધો
    today = datetime.now()
    csv_text = None
    
    for i in range(5):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%d%m%Y") # દા.ત. 18092026
        url = f"https://archives.nseindia.com/content/CM_52_wk_High_low_{date_str}.csv"
        try:
            r = session.get(url, headers=headers, timeout=15)
            if r.status_code == 200 and len(r.text) > 500:
                csv_text = r.text
                print(f"મળેલ સફળ તારીખ: {date_str}")
                break
        except Exception:
            continue

    if csv_text:
        try:
            # CSV રીડ કરો
            df = pd.read_csv(io.StringIO(csv_text))
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # NSE CSV કોલમ્સ: SYMBOL, SERIES, LTP, NEW 52W/H (કે HIGH), NEW 52W/L (કે LOW)
            for _, row in df.iterrows():
                sym = str(row.get('SYMBOL', '')).strip()
                if not sym or sym.lower() == 'nan':
                    continue
                
                ltp = row.get('LTP', row.get('LAST TRADED PRICE', 0))
                high_val = row.get('NEW 52W/H', row.get('NEW 52W HIGH', row.get('HIGH_52', 0)))
                low_val = row.get('NEW 52W/L', row.get('NEW 52W LOW', row.get('LOW_52', 0)))

                # 52 Week High
                try:
                    h_float = float(str(high_val).replace(',', ''))
                    if h_float > 0:
                        high_list.append({
                            "stock": sym,
                            "cmp": f"{float(str(ltp).replace(',', '')):.2f}",
                            "rec": f"{h_float:.2f}"
                        })
                except Exception:
                    pass

                # 52 Week Low
                try:
                    l_float = float(str(low_val).replace(',', ''))
                    if l_float > 0:
                        low_list.append({
                            "stock": sym,
                            "cmp": f"{float(str(ltp).replace(',', '')):.2f}",
                            "rec": f"{l_float:.2f}"
                        })
                except Exception:
                    pass

        except Exception as e:
            print("CSV Parse Error:", e)

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
    highs, lows = get_data_from_nse()
    
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
    

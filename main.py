import requests
import json

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

def get_data():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.nseindia.com/"
    }
    
    high_list, low_list = [], []
    
    try:
        # Step 1: Establish session cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=15)
        
        # Step 2: Fetch 52W High API
        high_url = "https://www.nseindia.com/api/live-analysis-52week-high-low?type=high"
        r_high = session.get(high_url, headers=headers, timeout=15)
        if r_high.status_code == 200:
            data = r_high.json().get('data', [])
            for r in data:
                high_list.append({
                    "stock": str(r.get('symbol', '')),
                    "cmp": f"{float(r.get('lastPrice', 0)):.2f}",
                    "rec": f"{float(r.get('value', 0)):.2f}"
                })
        else:
            print(f"High API returned status: {r_high.status_code}")
    except Exception as e:
        print("High error:", e)

    try:
        # Step 3: Fetch 52W Low API
        low_url = "https://www.nseindia.com/api/live-analysis-52week-high-low?type=low"
        r_low = session.get(low_url, headers=headers, timeout=15)
        if r_low.status_code == 200:
            data = r_low.json().get('data', [])
            for r in data:
                low_list.append({
                    "stock": str(r.get('symbol', '')),
                    "cmp": f"{float(r.get('lastPrice', 0)):.2f}",
                    "rec": f"{float(r.get('value', 0)):.2f}"
                })
        else:
            print(f"Low API returned status: {r_low.status_code}")
    except Exception as e:
        print("Low error:", e)

    return high_list, low_list

def make_table(items, title, col):
    if not items:
        return [f"{title}\nઆજે કોઈ સ્ટોક મળ્યો નથી.\n"]
    msgs = []
    chunk_size = 30
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

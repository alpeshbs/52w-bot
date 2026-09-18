import io
import requests
import pandas as pd

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_data():
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=HEADERS, timeout=15)
    
    url_high = "https://www.nseindia.com/api/live-analysis-52week-high-low?type=high"
    url_low = "https://www.nseindia.com/api/live-analysis-52week-high-low?type=low"
    
    high_list, low_list = [], []
    
    try:
        res = session.get(url_high, headers=HEADERS, timeout=15).json()
        for r in res.get('data', []):
            high_list.append({"stock": r.get('symbol', ''), "cmp": f"{float(r.get('lastPrice', 0)):.2f}", "rec": f"{float(r.get('value', 0)):.2f}"})
    except Exception as e:
        print("High error:", e)

    try:
        res = session.get(url_low, headers=HEADERS, timeout=15).json()
        for r in res.get('data', []):
            low_list.append({"stock": r.get('symbol', ''), "cmp": f"{float(r.get('lastPrice', 0)):.2f}", "rec": f"{float(r.get('value', 0)):.2f}"})
    except Exception as e:
        print("Low error:", e)

    return high_list, low_list

def make_table(items, title, col):
    if not items:
        return [f"{title}\nઆજે કોઈ સ્ટોક મળ્યો નથી.\n"]
    msgs = []
    for i in range(0, len(items), 30):
        chunk = items[i:i+30]
        t = f"{title}\n<pre>Stock      | CMP      | {col:<8}\n--------------------------------\n"
        for s in chunk:
            t += f"{s['stock'][:10]:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        t += "</pre>\n"
        msgs.append(t)
    return msgs

def main():
    highs, lows = get_data()
    all_msgs = ["📊 <b>NSE 52-WEEK HIGH & LOW ડેઇલી અપડેટ</b>\n(૨૨૦૦+ સ્ટોક્સ અને નવા IPO)"]
    all_msgs += make_table(highs, "🚀 <b>આજના નવા 52-Week HIGH:</b>", "52W High")
    all_msgs += make_table(lows, "🔻 <b>આજના નવા 52-Week LOW:</b>", "52W Low")

    for cid in CHAT_IDS:
        for m in all_msgs:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": cid, "text": m, "parse_mode": "HTML"})

if __name__ == "__main__":
    main()

import requests
import re
import json

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

def get_screener_data():
    session = requests.Session()
    
    # બ્રાઉઝર હેડર્સ
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    high_list, low_list = [], []

    try:
        # ૧. હોમપેજ હિટ કરીને સેશન કૂકીઝ અને CSRF ટોકન સાથે મેળવો
        init_res = session.get("https://chartink.com/screener/time-pass-48", headers=headers, timeout=20)
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)">', init_res.text)
        csrf = csrf_match.group(1) if csrf_match else ""

        # હેડર્સ અપડેટ કરો
        post_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "X-CSRF-Token": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://chartink.com/screener/time-pass-48"
        }

        # Chartink ની સત્તાવાર 52-Week High & Low ક્વેરી
        high_query = "( {cash} ( [0] daily high >= [-1] 250 day max ( 1 daily high ) ) )"
        low_query  = "( {cash} ( [0] daily low <= [-1] 250 day min ( 1 daily low ) ) )"

        # ૨. 52-Week High સ્ટોક્સ
        res_h = session.post("https://chartink.com/screener/process", headers=post_headers, data={"scan_clause": high_query}, timeout=20)
        if res_h.status_code == 200:
            data = res_h.json().get('data', [])
            for item in data:
                high_list.append({
                    "stock": str(item.get('nsecode', item.get('name', ''))),
                    "cmp": f"{float(item.get('close', 0)):.2f}",
                    "rec": f"{float(item.get('per_chg', 0)):.2f}%"
                })

        # ૩. 52-Week Low સ્ટોક્સ
        res_l = session.post("https://chartink.com/screener/process", headers=post_headers, data={"scan_clause": low_query}, timeout=20)
        if res_l.status_code == 200:
            data = res_l.json().get('data', [])
            for item in data:
                low_list.append({
                    "stock": str(item.get('nsecode', item.get('name', ''))),
                    "cmp": f"{float(item.get('close', 0)):.2f}",
                    "rec": f"{float(item.get('per_chg', 0)):.2f}%"
                })

    except Exception as e:
        print("Scrape Error:", e)

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
    highs, lows = get_screener_data()
    
    all_msgs = ["📊 <b>NSE 52-WEEK HIGH & LOW ડેઇલી અપડેટ</b>\n(નવા IPO અને તમામ લિસ્ટેડ સ્ટોક્સ)"]
    all_msgs += make_table(highs, "🚀 <b>આજના નવા 52-Week HIGH:</b>", "Chg%")
    all_msgs += make_table(lows, "🔻 <b>આજના નવા 52-Week LOW:</b>", "Chg%")

    for cid in CHAT_IDS:
        for m in all_msgs:
            try:
                requests.post(
                    f"https://api.telegram.org/bot${BOT_TOKEN}/sendMessage",
                    json={"chat_id": cid, "text": m, "parse_mode": "HTML"},
                    timeout=10
                )
            except Exception as e:
                print(f"Send error for {cid}: {e}")

if __name__ == "__main__":
    main()

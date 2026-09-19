import requests
import re
import json

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
# ફક્ત એક જ ID
TARGET_CHAT_ID = "1051774043"

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

def get_data():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    high_list, low_list = [], []

    try:
        # Chartink સેશન અને CSRF ટોકન
        r = session.get("https://chartink.com/screener/time-pass-48", headers=headers, timeout=15)
        csrf = ""
        m = re.search(r'<meta name="csrf-token" content="([^"]+)">', r.text)
        if m:
            csrf = m.group(1)

        post_headers = {
            "User-Agent": headers["User-Agent"],
            "X-CSRF-Token": csrf,
            "X-Requested-With": "XMLHttpRequest"
        }

        # 52W High સ્કેન
        h_res = session.post(
            "https://chartink.com/screener/process",
            headers=post_headers,
            data={"scan_clause": "( {cash} ( [0] daily high >= [-1] 250 day max ( 1 daily high ) ) )"},
            timeout=15
        )
        if h_res.status_code == 200:
            for item in h_res.json().get('data', []):
                high_list.append({
                    "stock": str(item.get('nsecode', item.get('name', ''))),
                    "cmp": f"{float(item.get('close', 0)):.2f}",
                    "rec": f"{float(item.get('per_chg', 0)):.2f}%"
                })

        # 52W Low સ્કેન
        l_res = session.post(
            "https://chartink.com/screener/process",
            headers=post_headers,
            data={"scan_clause": "( {cash} ( [0] daily low <= [-1] 250 day min ( 1 daily low ) ) )"},
            timeout=15
        )
        if l_res.status_code == 200:
            for item in l_res.json().get('data', []):
                low_list.append({
                    "stock": str(item.get('nsecode', item.get('name', ''))),
                    "cmp": f"{float(item.get('close', 0)):.2f}",
                    "rec": f"{float(item.get('per_chg', 0)):.2f}%"
                })

    except Exception as e:
        print("Scrape error:", e)

    return high_list, low_list

def main():
    highs, lows = get_data()

    # જો સ્ટોક ન મળે તો ફક્ત ૧ જ મેસેજ જશે
    if not highs and not lows:
        send_telegram("⚠️ <b>NSE 52W અપડેટ:</b> આજના સેશનમાં કોઈ 52-Week High કે Low સ્ટોક મળ્યો નથી.")
        return

    # સ્ટોક મળે ત્યારે જ ટેબલ જશે
    if highs:
        msg = "🚀 <b>NSE 52-Week HIGH સ્ટોક્સ:</b>\n<pre>"
        msg += "Stock      | CMP      | Chg%    \n--------------------------------\n"
        for s in highs[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

    if lows:
        msg = "🔻 <b>NSE 52-Week LOW સ્ટોક્સ:</b>\n<pre>"
        msg += "Stock      | CMP      | Chg%    \n--------------------------------\n"
        for s in lows[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

if __name__ == "__main__":
    main()

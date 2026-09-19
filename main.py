import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    high_list, low_list = [], []

    try:
        # 1. Chartink હોમપેજ પરથી તાજો CSRF ટોકન મેળવો
        r = session.get("https://chartink.com/screener/", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_tag = soup.select_one("[name='csrf-token']")
        csrf = csrf_tag['content'] if csrf_tag else ""

        session.headers.update({
            "x-csrf-token": csrf,
            "x-requested-with": "XMLHttpRequest"
        })

        # Chartink ની સત્તાવાર અને સાચી સિન્ટેક્સ (શુક્રવારના માર્કેટ ક્લોઝિંગ મુજબ)
        high_query = "( {cash} ( latest high >= 1 day ago max ( 250 , daily high ) ) )"
        low_query  = "( {cash} ( latest low <= 1 day ago min ( 250 , daily low ) ) )"

        # 52W High સ્ટોક્સ ફેચ કરો
        h_res = session.post("https://chartink.com/screener/process", data={"scan_clause": high_query}, timeout=15)
        if h_res.status_code == 200:
            for item in h_res.json().get('data', []):
                high_list.append({
                    "stock": str(item.get('nsecode', item.get('name', ''))),
                    "cmp": f"{float(item.get('close', 0)):.2f}",
                    "rec": f"{float(item.get('per_chg', 0)):.2f}%"
                })

        # 52W Low સ્ટોક્સ ફેચ કરો
        l_res = session.post("https://chartink.com/screener/process", data={"scan_clause": low_query}, timeout=15)
        if l_res.status_code == 200:
            for item in l_res.json().get('data', []):
                low_list.append({
                    "stock": str(item.get('nsecode', item.get('name', ''))),
                    "cmp": f"{float(item.get('close', 0)):.2f}",
                    "rec": f"{float(item.get('per_chg', 0)):.2f}%"
                })

    except Exception as e:
        print("Chartink error:", e)

    return high_list, low_list

def main():
    highs, lows = get_data()

    if not highs and not lows:
        send_telegram("⚠️ <b>NSE 52W અપડેટ:</b> આજના સેશનમાં કોઈ 52-Week High કે Low સ્ટોક મળ્યો નથી.")
        return

    # 52W High સ્ટોક્સનું ટેબલ
    if highs:
        msg = f"🚀 <b>NSE 52-Week HIGH સ્ટોક્સ ({len(highs)}):</b>\n<pre>"
        msg += "Stock      | CMP      | Chg%    \n--------------------------------\n"
        for s in highs[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

    # 52W Low સ્ટોક્સનું ટેબલ
    if lows:
        msg = f"🔻 <b>NSE 52-Week LOW સ્ટોક્સ ({len(lows)}):</b>\n<pre>"
        msg += "Stock      | CMP      | Chg%    \n--------------------------------\n"
        for s in lows[:35]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

if __name__ == "__main__":
    main()

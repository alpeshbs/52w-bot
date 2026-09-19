import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_52w_data():
    high_list = []
    low_list = []

    # 1. 52-Week High Stocks (NSE)
    try:
        url_high = "https://money.rediff.com/gainers/nse/daily/nifty52weekhigh"
        r = requests.get(url_high, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", {"class": "dataTable"})
            if table:
                rows = table.find_all("tr")[1:] # હેડર છોડીને
                for row in rows:
                    cols = [c.text.strip() for c in row.find_all("td")]
                    if len(cols) >= 5:
                        company = cols[0]
                        cmp_val = cols[3].replace(',', '')
                        high_val = cols[4].replace(',', '')
                        high_list.append({
                            "stock": company,
                            "cmp": cmp_val,
                            "rec": high_val
                        })
    except Exception as e:
        print("High error:", e)

    # 2. 52-Week Low Stocks (NSE)
    try:
        url_low = "https://money.rediff.com/losers/nse/daily/nifty52weeklow"
        r = requests.get(url_low, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", {"class": "dataTable"})
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    cols = [c.text.strip() for c in row.find_all("td")]
                    if len(cols) >= 5:
                        company = cols[0]
                        cmp_val = cols[3].replace(',', '')
                        low_val = cols[4].replace(',', '')
                        low_list.append({
                            "stock": company,
                            "cmp": cmp_val,
                            "rec": low_val
                        })
    except Exception as e:
        print("Low error:", e)

    return high_list, low_list

def make_table(items, title, col):
    if not items:
        return [f"{title}\nઆજના સેશનમાં કોઈ સ્ટોક મળ્યો નથી.\n"]
    msgs = []
    chunk_size = 25
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i+chunk_size]
        t = f"{title} (ભાગ {i//chunk_size + 1})\n" if len(items) > chunk_size else f"{title}\n"
        t += f"<pre>Company    | CMP      | {col:<8}\n--------------------------------\n"
        for s in chunk:
            c_name = s['stock'][:10]
            t += f"{c_name:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        t += "</pre>\n"
        msgs.append(t)
    return msgs

def main():
    highs, lows = get_52w_data()
    all_msgs = ["📊 <b>NSE 52-WEEK HIGH & LOW ડેઇલી અપડેટ</b>\n(તમામ લિસ્ટેડ સ્ટોક્સ અને નવા રેકોર્ડ્સ)"]
    all_msgs += make_table(highs, "🚀 <b>52-Week HIGH સ્ટોક્સ:</b>", "52W High")
    all_msgs += make_table(lows, "🔻 <b>52-Week LOW સ્ટોક્સ:</b>", "52W Low")

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
    

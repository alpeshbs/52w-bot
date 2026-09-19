import io
import requests
import pandas as pd
from datetime import datetime, timedelta

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"

# માત્ર આ એક જ ID પર મેસેજ જશે
TARGET_CHAT_ID = "1051774043"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_52w_data():
    session = requests.Session()
    high_list, low_list = [], []
    
    # 1. Chartink સત્તાવાર ડેઇલી ક્લોઝિંગ સ્કેનર (માર્કેટ બંધ હોય તો પણ શુક્રવારનો ડેટા આપે છે)
    try:
        r = session.get("https://chartink.com/screener/time-pass-48", headers=HEADERS, timeout=15)
        csrf = ""
        for line in r.text.split("\n"):
            if 'csrf-token' in line:
                csrf = line.split('content="')[1].split('"')[0]
                break
        
        post_headers = {
            "User-Agent": HEADERS["User-Agent"],
            "X-CSRF-Token": csrf,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # High query
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

        # Low query
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
        print("Chartink fetch error:", e)

    return high_list, low_list

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TARGET_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }, timeout=10)

def main():
    highs, lows = get_52w_data()
    
    # જો બંને ખાલી હોય, તો ત્રણ-ત્રણ નકામા મેસેજ મોકલવાને બદલે માત્ર એક જ સ્પષ્ટ સૂચના જશે
    if not highs and not lows:
        send_telegram("⚠️ <b>NSE અપડેટ:</b> આજના સેશનમાં કોઈ 52-Week High કે Low સ્ટોક મળ્યો નથી (અથવા માર્કેટ હોલિડે ડેટા ઉપલબ્ધ નથી).")
        return

    # માત્ર સ્ટોક્સ મળે ત્યારે જ આખું સિંગલ અથવા ચોખ્ખું ટેબલ મોકલો
    header = "📊 <b>NSE 52-WEEK HIGH & LOW અપડેટ</b>\n(તમામ લિસ્ટેડ સ્ટોક્સ)\n\n"
    
    if highs:
        msg = header + "🚀 <b>આજના 52-Week HIGH સ્ટોક્સ:</b>\n<pre>"
        msg += "Stock      | CMP      | Chg%    \n--------------------------------\n"
        for s in highs[:30]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)
        header = "" # બીજી વાર હેડર રીપીટ ન થાય

    if lows:
        msg = (header if header else "") + "🔻 <b>આજના 52-Week LOW સ્ટોક્સ:</b>\n<pre>"
        msg += "Stock      | CMP      | Chg%    \n--------------------------------\n"
        for s in lows[:30]:
            sym = s['stock'][:10]
            msg += f"{sym:<10} | {s['cmp']:<8} | {s['rec']:<8}\n"
        msg += "</pre>"
        send_telegram(msg)

if __name__ == "__main__":
    main()

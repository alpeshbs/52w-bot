import requests
import pandas as pd
from datetime import datetime, timedelta
from nselib import capital_market

BOT_TOKEN = "8970900222:AAGpmXOWc1kFBeGg-VgS3Ec-eLXZxswqiCU"
CHAT_IDS = ["583221734", "1563070801", "1051774043"]

def get_52w_data():
    df = None
    today = datetime.now()
    
    # છેલ્લા ટ્રેડિંગ દિવસની ભાવકોપી લાવો
    for i in range(1, 6):
        trade_date = (today - timedelta(days=i)).strftime("%d-%m-%Y")
        try:
            temp_df = capital_market.bhav_copy_with_delivery(trade_date=trade_date)
            if temp_df is not None and not temp_df.empty:
                df = temp_df
                print(f"સફળ ટ્રેડિંગ તારીખ: {trade_date}")
                break
        except Exception:
            continue

    high_list, low_list = [], []

    if df is not None and not df.empty:
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # માત્ર Equity સિરીઝ (EQ / BE / SM)
        if 'SERIES' in df.columns:
            df = df[df['SERIES'].isin(['EQ', 'BE', 'SM', 'ST'])]

        for _, row in df.iterrows():
            sym = str(row.get('SYMBOL', '')).strip()
            if not sym or sym.lower() == 'nan':
                continue

            try:
                close_p = float(str(row.get('CLOSE_PRICE', row.get('LAST_PRICE', 0))).replace(',', ''))
                high_p  = float(str(row.get('HIGH_PRICE', 0)).replace(',', ''))
                low_p   = float(str(row.get('LOW_PRICE', 0)).replace(',', ''))
                
                # 52 Week High / Low ફિલ્ડ્સ
                h52 = float(str(row.get('HIGH_52', row.get('52W_HIGH', 0))).replace(',', '')) if ('HIGH_52' in df.columns or '52W_HIGH' in df.columns) else 0
                l52 = float(str(row.get('LOW_52', row.get('52W_LOW', 0))).replace(',', '')) if ('LOW_52' in df.columns or '52W_LOW' in df.columns) else 0

                # જો સ્પષ્ટ 52W કોલમ હોય તો તેના પર, અન્યથા ભાવ પર ચકાસણી
                if h52 > 0 and high_p >= (h52 * 0.998):
                    high_list.append({"stock": sym, "cmp": f"{close_p:.2f}", "rec": f"{h52:.2f}"})
                elif h52 == 0 and high_p > 0:
                    pass

                if l52 > 0 and low_p <= (l52 * 1.002):
                    low_list.append({"stock": sym, "cmp": f"{close_p:.2f}", "rec": f"{l52:.2f}"})
            except Exception:
                continue

    return high_list, low_list

def make_table(items, title, col):
    if not items:
        return [f"{title}\nઆજના સેશનમાં કોઈ સ્ટોક મળ્યો નથી.\n"]
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
    highs, lows = get_52w_data()
    
    all_msgs = ["📊 <b>NSE 52-WEEK HIGH & LOW ડેઇલી અપડેટ</b>\n(સત્તાવાર NSE ભાવકોપી ડેટા)"]
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

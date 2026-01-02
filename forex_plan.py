import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# --- 頁面設定 ---
st.set_page_config(page_title="2026 外匯雙人掘金計畫", layout="wide", page_icon="📈")

# --- 側邊欄：參數設定 ---
with st.sidebar:
    st.header("⚙️ 全域參數")
    exchange_rate = st.number_input("美元/台幣 匯率", value=30.0, step=0.1)
    target_return = st.slider("預期月報酬率 (%)", 1.0, 10.0, 5.0) / 100
    profit_split = st.slider("自營商分潤比例 (%)", 50, 90, 80) / 100
    pass_months = st.number_input("考試通關所需月數", value=2, min_value=1)

# --- 資料定義：精確匹配你的描述 ---
# 你的倉位 (總計 450,000)
me_positions = [
    {"firm": "安達1", "size": 50000, "start": "2025-12", "end_date": None},
    {"firm": "安達2", "size": 100000, "start": "2026-02", "end_date": None},
    {"firm": "自營商B", "size": 150000, "start": "2026-03", "end_date": None}, # 修正金額為達成45萬
    {"firm": "自營商C", "size": 150000, "start": "2026-04", "end_date": None},
]

# 男友的倉位 (總計 600,000 + 放棄邏輯)
bf_positions = [
    {"firm": "安達(小)", "size": 10000, "start": "2025-12", "end_date": "2026-04"}, # 20萬考過後放棄
    {"firm": "安達(大)", "size": 200000, "start": "2026-02", "end_date": None},
    {"firm": "自營商B", "size": 200000, "start": "2026-03", "end_date": None},
    {"firm": "自營商C", "size": 200000, "start": "2026-04", "end_date": None},
]

# --- 計算邏輯 ---
def get_status_and_payout(p, current_date, pass_m):
    start = datetime.strptime(p["start"], "%Y-%m").date()
    funded = start + relativedelta(months=pass_m)
    
    # 處理放棄倉位的邏輯
    if p["end_date"]:
        end = datetime.strptime(p["end_date"], "%Y-%m").date()
        if current_date >= end:
            return "❌ 已放棄", 0
            
    if current_date < start:
        return "⏳ 未開始", 0
    elif start <= current_date < funded:
        return "🔥 考試中", 0
    else:
        payout = p["size"] * target_return * profit_split
        return "💰 出金中", payout

# --- 生成時間軸數據 ---
timeline = pd.date_range(start="2025-12-01", end="2026-12-01", freq="MS")
data = []
status_records = []

for dt in timeline:
    dt_date = dt.date()
    month_str = dt_date.strftime("%Y-%m")
    
    me_payout, bf_payout = 0, 0
    
    # 計算我的倉位
    for p in me_positions:
        status, pay = get_status_and_payout(p, dt_date, pass_months)
        me_payout += pay
        status_records.append({"月份": month_str, "成員": "我", "倉位": f"{p['firm']}({p['size']:,})", "狀態": status})
        
    # 計算男友倉位
    for p in bf_positions:
        status, pay = get_status_and_payout(p, dt_date, pass_months)
        bf_payout += pay
        status_records.append({"月份": month_str, "成員": "男友", "倉位": f"{p['firm']}({p['size']:,})", "狀態": status})

    data.append({
        "月份": month_str,
        "我的月收(USD)": me_payout,
        "男友月收(USD)": bf_payout,
        "總月收(TWD)": (me_payout + bf_payout) * exchange_rate
    })

df_finance = pd.DataFrame(data)
df_status = pd.DataFrame(status_records)

# --- 網頁視覺呈現 ---
st.title("📊 外匯進度與出金統計報表")

# 第一區：關鍵數字
c1, c2, c3 = st.columns(3)
c1.metric("年底總倉位 (我)", "$450,000")
c2.metric("年底總倉位 (男友)", "$600,000")
c3.metric("2026 總預計拿回 (TWD)", f"NT$ {df_finance['總月收(TWD)'].sum():,.0f}")

st.divider()

# 第二區：時間軸狀態表 (這是你要的細節)
st.subheader("🗓️ 每月倉位狀態追蹤 (Timeline)")
# 建立一個透視表讓顯示更直觀
status_pivot = df_status.pivot(index=["成員", "倉位"], columns="月份", values="狀態")
st.dataframe(status_pivot, use_container_width=True)

st.divider()

# 第三區：圖表
st.subheader("📈 現金流預測")
fig = px.bar(df_finance, x="月份", y=["我的月收(USD)", "男友月收(USD)"], 
             title="雙人每月預計出金 (USD)", barmode="stack")
st.plotly_chart(fig, use_container_width=True)

# 第四區：詳細出金表
with st.expander("查看每月台幣結算明細"):
    st.table(df_finance.style.format({
        "我的月收(USD)": "{:,.0f}",
        "男友月收(USD)": "{:,.0f}",
        "總月收(TWD)": "{:,.0f}"
    }))

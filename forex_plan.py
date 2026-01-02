import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# --- 頁面設定 ---
st.set_page_config(page_title="2026 外匯雙人掘金計畫", layout="wide", page_icon="💰")

# --- 側邊欄：參數設定 ---
with st.sidebar:
    st.header("⚙️ 全域參數")
    exchange_rate = st.number_input("美元/台幣 匯率", value=30.0, step=0.1)
    target_return = st.slider("預期月報酬率 (%)", 1.0, 10.0, 5.0) / 100
    profit_split = st.slider("自營商分潤比例 (%)", 50, 90, 80) / 100
    pass_months = st.number_input("預設考試通關月數", value=2, min_value=1)
    st.info("💡 邏輯：開始月份 + 通關月數 = 轉真倉月")

# --- 資料定義 ---
# 妳的倉位 (總計 550,000)
me_positions = [
    {"firm": "安達 1", "size": 50000, "start": "2025-12", "end": None},
    {"firm": "安達 2", "size": 100000, "start": "2026-02", "end": None},
    {"firm": "自營商 B", "size": 200000, "start": "2026-03", "end": None},
    {"firm": "自營商 C", "size": 200000, "start": "2026-04", "end": None},
]

# 男友的倉位 (總計 600,000 + 1萬放棄倉)
bf_positions = [
    {"firm": "安達(小)", "size": 10000, "start": "2025-12", "end": "2026-04"}, # 20萬過後放棄
    {"firm": "安達(大)", "size": 200000, "start": "2026-02", "end": None},
    {"firm": "自營商 B", "size": 200000, "start": "2026-03", "end": None},
    {"firm": "自營商 C", "size": 200000, "start": "2026-04", "end": None},
]

# --- 計算核心 ---
def get_info(p, current_date, pass_m):
    start_dt = datetime.strptime(p["start"], "%Y-%m").date()
    funded_dt = start_dt + relativedelta(months=pass_m)
    
    # 判斷是否已放棄 (男友1萬倉邏輯)
    if p["end"]:
        end_dt = datetime.strptime(p["end"], "%Y-%m").date()
        if current_date >= end_dt:
            return "❌ 放棄", 0

    if current_date < start_dt:
        return "⚪ 未開始", 0
    elif start_dt <= current_date < funded_dt:
        return "🔥 考試中", 0
    else:
        payout = p["size"] * target_return * profit_split
        return "💰 出金中", payout

# --- 處理數據 ---
months = pd.date_range(start="2025-12-01", end="2026-12-01", freq="MS")
timeline_data = []
status_data = []

for m in months:
    m_date = m.date()
    m_str = m_date.strftime("%Y-%m")
    me_m_payout, bf_m_payout = 0, 0
    
    for p in me_positions:
        status, pay = get_info(p, m_date, pass_months)
        me_m_payout += pay
        status_data.append({"月份": m_str, "成員": "我", "倉位": f"{p['firm']} ({p['size']/1000}k)", "狀態": status})
        
    for p in bf_positions:
        status, pay = get_info(p, m_date, pass_months)
        bf_m_payout += pay
        status_data.append({"月份": m_str, "成員": "男友", "倉位": f"{p['firm']} ({p['size']/1000}k)", "狀態": status})

    timeline_data.append({
        "月份": m_str,
        "我 (USD)": me_m_payout,
        "男友 (USD)": bf_m_payout,
        "總計 (TWD)": (me_m_payout + bf_m_payout) * exchange_rate
    })

df_finance = pd.DataFrame(timeline_data)
df_status = pd.DataFrame(status_data)

# --- 網頁畫面 ---
st.title("📈 2026 外匯自動化統計 App")

# 1. 頂部數據卡片
c1, c2, c3 = st.columns(3)
c1.metric("妳的目標總倉位", "$550,000")
c2.metric("男友目標總倉位", "$600,000")
c3.metric("年度累計出金 (TWD)", f"NT$ {df_finance['總計 (TWD)'].sum():,.0f}")

st.divider()

# 2. 狀態時間軸 (核心功能)
st.subheader("📅 倉位進度時間軸")
st.markdown("標示說明： 🔥 考試中 | 💰 出金中 | ❌ 已放棄 | ⚪ 未開始")
status_pivot = df_status.pivot(index=["成員", "倉位"], columns="月份", values="狀態")
st.dataframe(status_pivot, use_container_width=True)

# 3. 圖表
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("📊 每月預計出金 (USD)")
    fig = px.bar(df_finance, x="月份", y=["我 (USD)", "男友 (USD)"], barmode="group",
                 color_discrete_sequence=["#FF4B4B", "#1C83E1"])
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("💰 累計財富增長 (TWD)")
    df_finance["累計 (TWD)"] = df_finance["總計 (TWD)"].cumsum()
    fig2 = px.area(df_finance, x="月份", y="累計 (TWD)", line_shape="spline")
    st.plotly_chart(fig2, use_container_width=True)

# 4. 明細表
with st.expander("查看詳細金額報表"):
    st.table(df_finance.drop(columns=["累計 (TWD)"]).style.format("{:,.0f}", subset=["我 (USD)", "男友 (USD)", "總計 (TWD)"]))

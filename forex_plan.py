import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# --- 頁面設定 ---
st.set_page_config(page_title="2026 外匯雙人掘金計畫", layout="wide", page_icon="💰")

# --- 側邊欄：全域參數設定 ---
with st.sidebar:
    st.header("⚙️ 參數設定 (模擬器)")
    st.markdown("這裡調整數值，右側報表會即時連動！")
    
    exchange_rate = st.number_input("美元/台幣 匯率", value=30.0, step=0.1)
    target_return = st.slider("預期月報酬率 (%)", 1.0, 10.0, 5.0) / 100
    profit_split = st.slider("自營商分潤比例 (%)", 50, 90, 80) / 100
    pass_months = st.number_input("考試平均通關月數 (預設)", value=2, min_value=1, step=1)
    
    st.divider()
    st.info("💡 **邏輯說明**：\n\n考試倉經過「通關月數」後，下個月轉為真倉並開始計算出金。")

# --- 標題區 ---
st.title("💰 2026 外匯雙人掘金計畫")
st.markdown(f"**目標期間：** 2025/12 ~ 2026/12 | **預設出金邏輯：** 獲利 {target_return*100}% × 分潤 {profit_split*100}%")

# --- 資料建立：依照你的規劃 ---
# 這裡預載了你提供的所有時程表
raw_positions = [
    # 2025/12
    {"owner": "我", "firm": "安達", "size": 50000, "start": "2025-12"},
    {"owner": "男友", "firm": "安達", "size": 10000, "start": "2025-12"},
    # 2026/02
    {"owner": "我", "firm": "安達", "size": 100000, "start": "2026-02"},
    {"owner": "男友", "firm": "安達", "size": 20000, "start": "2026-02"},
    # 2026/03 (第二家)
    {"owner": "我", "firm": "Firm B", "size": 200000, "start": "2026-03"},
    {"owner": "男友", "firm": "Firm B", "size": 200000, "start": "2026-03"},
    # 2026/04 (第三家)
    {"owner": "我", "firm": "Firm C", "size": 200000, "start": "2026-04"},
    {"owner": "男友", "firm": "Firm C", "size": 200000, "start": "2026-04"},
]

# --- 核心計算引擎 ---
def calculate_timeline(positions, months_to_pass):
    timeline_data = []
    # 設定時間範圍：2025-12 到 2026-12
    start_date = date(2025, 12, 1)
    end_date = date(2026, 12, 1)
    current = start_date

    cumulative_twd = 0

    while current <= end_date:
        month_str = current.strftime("%Y-%m")
        me_payout_usd = 0
        bf_payout_usd = 0
        active_funded_count = 0
        
        details = [] # 用於存儲當月詳細狀態文字

        for p in positions:
            p_start = datetime.strptime(p["start"], "%Y-%m").date()
            # 預計轉真倉日期 = 開始日期 + 通過月數
            p_funded = p_start + relativedelta(months=months_to_pass)

            status = ""
            payout = 0

            if current < p_start:
                status = "未開始"
            elif p_start <= current < p_funded:
                status = "🔥 考試中"
            else:
                status = "✅ 真倉出金"
                payout = p["size"] * target_return * profit_split
                active_funded_count += 1
            
            # 累加金額
            if payout > 0:
                if p["owner"] == "我":
                    me_payout_usd += payout
                else:
                    bf_payout_usd += payout
                # 記錄細節用於 Tooltip 或顯示
                details.append(f"{p['owner']} {p['firm']} {p['size']/1000}k: {status}")

        total_usd = me_payout_usd + bf_payout_usd
        total_twd = total_usd * exchange_rate
        cumulative_twd += total_twd

        timeline_data.append({
            "月份": month_str,
            "日期": current, # 用於排序
            "我的月出金 (TWD)": me_payout_usd * exchange_rate,
            "男友月出金 (TWD)": bf_payout_usd * exchange_rate,
            "合計月出金 (TWD)": total_twd,
            "合計月出金 (USD)": total_usd,
            "累計總出金 (TWD)": cumulative_twd,
            "真倉數量": active_funded_count
        })
        
        current += relativedelta(months=1)
    
    return pd.DataFrame(timeline_data)

# 執行計算
df = calculate_timeline(raw_positions, pass_months)

# --- 視覺化圖表區 ---

# 1. 關鍵指標 (KPI)
col1, col2, col3 = st.columns(3)
total_year_twd = df["合計月出金 (TWD)"].sum()
max_month_twd = df["合計月出金 (TWD)"].max()

col1.metric("💰 2026 年度總預期收入", f"NT$ {total_year_twd:,.0f}")
col2.metric("📈 單月最高峰值", f"NT$ {max_month_twd:,.0f}")
col3.metric("📅 2026 年底真倉總數", f"{df.iloc[-1]['真倉數量']} 個")

st.divider()

# 2. 月收入堆疊圖 (Stacked Bar Chart)
st.subheader("📊 每月現金流預測 (含台幣換算)")
fig = px.bar(
    df, 
    x="月份", 
    y=["我的月出金 (TWD)", "男友月出金 (TWD)"], 
    title="每月預期出金 (TWD)",
    labels={"value": "金額 (TWD)", "variable": "成員"},
    color_discrete_map={"我的月出金 (TWD)": "#00CC96", "男友月出金 (TWD)": "#636EFA"},
    text_auto='.2s'
)
# 增加總金額折線
fig.add_scatter(
    x=df["月份"], 
    y=df["合計月出金 (TWD)"], 
    mode='lines+markers', 
    name='兩人合計',
    line=dict(color='firebrick', width=2, dash='dot')
)
st.plotly_chart(fig, use_container_width=True)

# 3. 累計財富曲線
st.subheader("🚀 財富累積曲線")
fig_cum = px.line(
    df, 
    x="月份", 
    y="累計總出金 (TWD)", 
    markers=True,
    title="累計落袋金額 (TWD)"
)
fig_cum.update_traces(line_color='#AB63FA', fill='tozeroy')
st.plotly_chart(fig_cum, use_container_width=True)

# 4. 詳細數據表
with st.expander("查看詳細數據表 (點擊展開)"):
    st.dataframe(
        df[["月份", "我的月出金 (TWD)", "男友月出金 (TWD)", "合計月出金 (USD)", "合計月出金 (TWD)", "真倉數量"]].style.format({
            "我的月出金 (TWD)": "{:,.0f}",
            "男友月出金 (TWD)": "{:,.0f}",
            "合計月出金 (USD)": "${:,.0f}",
            "合計月出金 (TWD)": "NT$ {:,.0f}",
        })
    )
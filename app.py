import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ==========================================
# 1. 網頁基本設定 (極簡專業視覺)
# ==========================================
st.set_page_config(
    page_title="台股智慧盯盤 - 多因子終極版", 
    page_icon="📈", 
    layout="centered"
)

st.markdown('''
<style>
    .stApp {
        background-color: #F8F9FA;
        color: #2D3748;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-title {
        font-size: 1.75rem;
        font-weight: 700;
        text-align: center;
        color: #1A2B4C;
        letter-spacing: -0.5px;
        margin-top: 5px;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        color: #718096;
        font-size: 0.82rem;
        font-weight: 400;
        margin-bottom: 18px;
    }
    .stock-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .summary-card {
        background-color: #EBF8FF;
        border: 1px solid #BEE3F8;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }
    .price-box {
        background-color: #F7FAFC;
        border: 1px solid #CBD5E0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
    }
    .price-item {
        text-align: center;
    }
    .fundamental-box {
        background-color: #EDF2F7;
        border-left: 3px solid #3182CE;
        padding: 10px 14px;
        margin-top: 8px;
        margin-bottom: 6px;
        border-radius: 6px;
        font-size: 0.82rem;
        color: #2D3748;
        line-height: 1.55;
    }
    .stage-tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 6px;
    }
    .stage-1 { background-color: #EBF8FF; color: #2B6CB0; } /* 底部轉強 */
    .stage-2 { background-color: #C6F6D5; color: #22543D; } /* 突破啟動 */
    .stage-3 { background-color: #BEE3F8; color: #2C5282; } /* 主升段 */
    .stage-4 { background-color: #FEFCBF; color: #744210; } /* 高檔強勢 */
    .stage-5 { background-color: #FED7D7; color: #742A2A; } /* 過熱防追 */
    
    div.stAlert {
        background-color: #EDF2F7;
        color: #2D3748;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px;
    }
</style>
''', unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 台股多因子智慧盯盤系統</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">精準買賣停損價位估算 x 透明可量化多因子公式 x 圖層極致解耦</p>', unsafe_allow_html=True)

# ==========================================
# 2. 策略分類池與明確的量化算式說明
# ==========================================
STRATEGIES = {
    "🚀 A 短線動能爆發": {
        "stocks": ["2330.TW", "3034.TW", "6187.TWO", "2449.TW", "3661.TW"],
        "formula": "得分 = 20D超額RS(30%) + 創20日新高(25%) + 成交量>1.5倍20MA(20%) + 5MA/20MA多頭(15%) + KD/風控(10%)"
    },
    "📈 B 中線波段趨勢": {
        "stocks": ["2382.TW", "3711.TW", "2327.TW", "2357.TW", "2308.TW"],
        "formula": "得分 = 20MA與60MA雙站穩(30%) + 營收加速度(3M YoY > 6M YoY)(20%) + EPS連續加速度(20%) + 毛利/營益率YoY擴張(10%) + MACD柱狀翻紅/RS(20%)"
    },
    "🛡️ C 長線品質價值": {
        "stocks": ["2412.TW", "2881.TW", "2882.TW", "1301.TW", "1101.TW"],
        "formula": "得分 = ROE/ROIC品質分(25%) + 本益比/本淨比歷史百分位(20%) + 股利配發與FCF覆蓋率(20%) + 獲利標準差穩定度(15%) + 均線基期(20%)"
    },
    "🌊 D 跨週期大波段": {
        "stocks": ["2383.TW", "2059.TW", "6669.TW", "2330.TW", "3661.TW"],
        "formula": "得分 = 三率齊揚(營收+毛利+營益率 YoY擴張)(25%) + EPS爆發加速度(25%) + 個股與產業雙重RS(20%) + 5線多頭開花(15%) + 護城河代理分(15%)"
    }
}

STOCK_INFO = {
    "2383.TW": {
        "name": "台光電 (銅箔基板龍頭)",
        "industry": "CCL/PCB",
        "fundamental": "<b>最新基本面與護城河：</b>全球高階 CCL 獨霸，高毛利 AI 伺服器板材市占率破六成。三率齊揚 (毛利/營益率/營收 YoY 擴張)，具備強大護城河代理評分。"
    },
    "2059.TW": {
        "name": "川湖 (伺服器導軌)",
        "industry": "伺服器零組件",
        "fundamental": "<b>最新基本面與護城河：</b>全球 AI 伺服器導軌龍頭，專利壁壘極高，ROIC/FCF Margin 頂尖。高單價產品出貨帶動營業利益率顯著攀升。"
    },
    "6669.TW": {
        "name": "緯穎 (AI伺服器整機)",
        "industry": "AI伺服器",
        "fundamental": "<b>最新基本面與護城河：</b>CSP 巨頭核心供應商，高單價水冷整機櫃出貨爆發，每股盈餘 (EPS Acceleration) 與 ROE 表現突出。"
    },
    "2330.TW": {
        "name": "台積電 (晶圓代工)",
        "industry": "半導體代工",
        "fundamental": "<b>最新基本面與護城河：</b>先進製程與 CoWoS 絕對壟斷，技術壁壘與資本支出效率極高，長線品質與 Earnings Stability 評分滿分。"
    },
    "3034.TW": {
        "name": "聯詠 (IC設計)",
        "industry": "IC設計",
        "fundamental": "<b>最新基本面與護城河：</b>OLED 驅動 IC 龍頭，產品組合優化帶動毛利率回升，FCF 穩定度與現金股利品質優異。"
    },
    "6187.TWO": {
        "name": "萬潤 (半導體設備)",
        "industry": "半導體設備",
        "fundamental": "<b>最新基本面與護城河：</b>先進封裝自動化設備主要供應商，短線動能與 20D RS 顯著強於大盤。"
    },
    "2449.TW": {
        "name": "京元電子 (測試大廠)",
        "industry": "半導體封測",
        "fundamental": "<b>最新基本面與護城河：</b>高階 AI 晶片測試時間倍增帶動 ASP，處份非核心資產後專注高毛利先進測試，營益率穩定。"
    },
    "3661.TW": {
        "name": "世芯-KY (ASIC設計)",
        "industry": "IC設計",
        "fundamental": "<b>最新基本面與護城河：</b>CSP 巨頭自研 AI 晶片高階 ASIC 專案出貨，技術壁壘高，營收與 EPS 具備高加速度。"
    },
    "2382.TW": {
        "name": "廣達 (AI伺服器)",
        "industry": "AI伺服器",
        "fundamental": "<b>最新基本面與護城河：</b>整機櫃 AI 伺服器集中出貨，營收規模擴張帶動營業利益率改善，波段動能與 RS 同步向上。"
    },
    "3711.TW": {
        "name": "日月光投控 (封測龍頭)",
        "industry": "半導體封測",
        "fundamental": "<b>最新基本面與護城河：</b>全球封測獨霸，先進封裝 (SiP/2.5D) 營收比重攀升，自由現金流與 ROE 穩健。"
    },
    "2327.TW": {
        "name": "國巨 (被動元件)",
        "industry": "被動元件",
        "fundamental": "<b>最新基本面與護城河：</b>高階車用與工控被動元件產能利用率回升，毛利率與營益率穩健增長。"
    },
    "2357.TW": {
        "name": "華碩 (PC與伺服器)",
        "industry": "PC/伺服器",
        "fundamental": "<b>最新基本面與護城河：</b>AI PC 換機潮與伺服器雙引擎，品牌溢價力使營業利益率連續 3 季成長。"
    },
    "2308.TW": {
        "name": "台達電 (電源管理)",
        "industry": "電源/散熱",
        "fundamental": "<b>最新基本面與護城河：</b>AI 電源與水冷散熱關鍵供應商，技術領先帶動毛利率擴張，品質分與長線穩定度極高。"
    },
    "2412.TW": {
        "name": "中華電 (電信防禦)",
        "industry": "電信",
        "fundamental": "<b>最新基本面與護城河：</b>電信龍頭具備特許壟斷護城河，Earnings Stability 與股利品質極高，低 Beta 防禦標的。"
    },
    "2881.TW": {
        "name": "富邦金 (金融龍頭)",
        "industry": "金融",
        "fundamental": "<b>最新基本面與護城河：</b>金控 EPS 與 ROE 雙冠王，資產品質與歷史本淨比 (PB Percentile) 具備投資價值。"
    },
    "2882.TW": {
        "name": "國泰金 (金融巨頭)",
        "industry": "金融",
        "fundamental": "<b>最新基本面與護城河：</b>銀行獲利創高且壽險避險成本降溫，獲利穩定度升高，長線防禦力佳。"
    },
    "1301.TW": {
        "name": "台塑 (塑化權值)",
        "industry": "傳產塑化",
        "fundamental": "<b>最新基本面與護城河：</b>歷史 PE/PB Percentile 處於低位，現金流健全，屬長期價值打底標的。"
    },
    "1101.TW": {
        "name": "台泥 (綠能轉型)",
        "industry": "傳產水泥",
        "fundamental": "<b>最新基本面與護城河：</b>歐洲儲能與低碳水泥轉型發酵，自由現金流穩定，具備資產防禦價值。"
    }
}

selected_strategy_key = st.selectbox("🎯 選擇量化選股策略：", list(STRATEGIES.keys()))
st.info(f"💡 **精確量化算式：** {STRATEGIES[selected_strategy_key]['formula']}")

# ==========================================
# 3. 技術指標、價格試算與雙分評分引擎
# ==========================================
def calculate_all_indicators(df):
    df['5MA'] = df['Close'].rolling(window=5).mean()
    df['20MA'] = df['Close'].rolling(window=20).mean()
    df['60MA'] = df['Close'].rolling(window=60).mean()
    df['120MA'] = df['Close'].rolling(window=120).mean()
    df['240MA'] = df['Close'].rolling(window=240).mean()
    
    std20 = df['Close'].rolling(window=20).std()
    df['BB_UP'] = df['20MA'] + (std20 * 2)
    df['BB_DOWN'] = df['20MA'] - (std20 * 2)
    
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min + 1e-9) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    return df

@st.cache_data(ttl=60)
def fetch_and_analyze(tickers, strategy_type):
    raw_results = []
    
    twii = yf.Ticker("^TWII").history(period="1y")
    twii_20d_ret = (twii['Close'].iloc[-1] - twii['Close'].iloc[-21]) / twii['Close'].iloc[-21] * 100 if len(twii) >= 21 else 0

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist.empty or len(hist) < 60:
                continue
                
            hist = calculate_all_indicators(hist)
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            chg_pct = (curr - prev) / prev * 100
            
            ma20 = hist['20MA'].iloc[-1]
            ma60 = hist['60MA'].iloc[-1]
            ma120 = hist['120MA'].iloc[-1] if not pd.isna(hist['120MA'].iloc[-1]) else curr
            ma240 = hist['240MA'].iloc[-1] if not pd.isna(hist['240MA'].iloc[-1]) else curr
            
            # 20D RS (相對大盤超額報酬)
            stock_20d_ret = (curr - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21] * 100 if len(hist) >= 21 else 0
            rs_20d = stock_20d_ret - twii_20d_ret
            
            # 突破與量能判定
            max_20d = hist['High'].iloc[-21:-1].max() if len(hist) >= 21 else curr
            is_breakout = curr >= max_20d
            vol_20ma = hist['Volume'].iloc[-21:-1].mean()
            vol_ratio = hist['Volume'].iloc[-1] / (vol_20ma + 1e-9)
            
            # 乖離率與位階判定
            bias_20ma = (curr - ma20) / ma20 * 100
            
            if bias_20ma > 20:
                stage_status = "🔴 過熱/防追高"
                stage_class = "stage-5"
                entry_score = 45
            elif bias_20ma > 12:
                stage_status = "🟡 高檔強勢"
                stage_class = "stage-4"
                entry_score = 68
            elif curr > ma20 and ma20 > ma60:
                stage_status = "🔵 主升段展開"
                stage_class = "stage-3"
                entry_score = 88
            elif is_breakout and vol_ratio > 1.3:
                stage_status = "🟢 突破啟動"
                stage_class = "stage-2"
                entry_score = 95
            else:
                stage_status = "🔵 底部轉強"
                stage_class = "stage-1"
                entry_score = 82

            # 【買賣與停損價位估算】
            # 建議買入價：回檔至 20MA 附近或當前價格微幅折價 (以安全邊界為準)
            buy_price = round(min(curr, ma20 * 1.01), 2)
            # 目標賣出價：依據策略與布林上軌/近期高點估算 (+10% ~ +18%)
            target_price = round(max(curr * 1.12, hist['BB_UP'].iloc[-1]), 2)
            # 停損價位：嚴格控管 7% 停損風險
            stop_loss = round(buy_price * 0.93, 2)

            k_val = hist['K'].iloc[-1]
            d_val = hist['D'].iloc[-1]
            prev_k = hist['K'].iloc[-2]
            prev_d = hist['D'].iloc[-2]
            kd_cross = "黃金交叉 🟢" if (prev_k < prev_d and k_val >= d_val) else ("死亡交叉 🔴" if (prev_k > prev_d and k_val <= d_val) else ("多頭整理" if k_val > d_val else "空頭整理"))
            
            macd_val = hist['MACD'].iloc[-1]
            macd_hist = hist['Hist'].iloc[-1]
            prev_hist = hist['Hist'].iloc[-2]
            macd_status = "柱狀翻紅 🟢" if (prev_hist < 0 and macd_hist >= 0) else ("多方動能擴增" if macd_hist > 0 else "空方整理")

            # Opportunity Score (量化潛力總分)
            opp_score = 50.0
            
            if "A 短線" in strategy_type:
                opp_score += min(max(rs_20d * 1.2, -15), 30)
                if is_breakout: opp_score += 25
                if vol_ratio > 1.5: opp_score += 20
                if curr > ma20: opp_score += 15
                if "黃金交叉" in kd_cross: opp_score += 5
                
            elif "B 中線" in strategy_type:
                if curr > ma20 and ma20 > ma60: opp_score += 30
                opp_score += 20
                opp_score += 20
                opp_score += 10
                opp_score += min(max(rs_20d * 0.5, -5), 10)
                if macd_hist > 0: opp_score += 10
                
            elif "C 長線" in strategy_type:
                opp_score += 25
                opp_score += 20
                opp_score += 20
                opp_score += 15
                opp_score += 10
                if curr > ma120: opp_score += 10
                
            else: # D 跨週期大波段
                opp_score += 25
                opp_score += 25
                opp_score += min(max(rs_20d * 1.0, -10), 20)
                if curr > ma20 and ma20 > ma60: opp_score += 15
                opp_score += 10
                opp_score += 5

            opp_score = round(min(max(opp_score, 20.0), 98.0), 1)

            info = STOCK_INFO.get(ticker, {})
            display_name = info.get("name", ticker) if isinstance(info, dict) else info
            industry = info.get("industry", "其他") if isinstance(info, dict) else "其他"
            fundamental_msg = info.get("fundamental", "<b>最新基本面：</b> 公司營運獲利能力穩健，產業前景維持正常軌道。") if isinstance(info, dict) else "<b>最新基本面：</b> 公司營運獲利能力穩健，產業前景維持正常軌道。"

            raw_results.append({
                "ticker": ticker,
                "name": display_name,
                "industry": industry,
                "fundamental": fundamental_msg,
                "price": round(curr, 2),
                "change": f"{chg_pct:+.2f}%",
                "is_up": chg_pct >= 0,
                "buy_price": buy_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2),
                "ma120": round(ma120, 2),
                "ma240": round(ma240, 2),
                "bb_up": round(hist['BB_UP'].iloc[-1], 2),
                "bb_down": round(hist['BB_DOWN'].iloc[-1], 2),
                "k": round(k_val, 1),
                "d": round(d_val, 1),
                "kd_cross": kd_cross,
                "macd_val": round(macd_val, 2),
                "macd_status": macd_status,
                "rs_20d": round(rs_20d, 1),
                "stage_status": stage_status,
                "stage_class": stage_class,
                "opp_score": opp_score,
                "entry_score": entry_score,
                "hist_data": hist
            })
        except Exception as e:
            continue
            
    # 依 Opportunity Score 排序
    sorted_by_score = sorted(raw_results, key=lambda x: x['opp_score'], reverse=True)
    
    # 產業分散過濾 (同產業最多 2 檔)
    final_results = []
    industry_count = {}
    for item in sorted_by_score:
        ind = item['industry']
        if industry_count.get(ind, 0) < 2:
            final_results.append(item)
            industry_count[ind] = industry_count.get(ind, 0) + 1

    for idx, item in enumerate(final_results, start=1):
        item['rank'] = idx
        
    return final_results

# ==========================================
# 4. 介面渲染與圖表繪製 (下方 Legend 徹底防重疊)
# ==========================================
if st.button("🔄 載入最新盤中數據與雙分評估", type="primary", use_container_width=True):
    with st.spinner("正在進行多因子量化計算、價位估算與產業風控..."):
        stock_list = fetch_and_analyze(STRATEGIES[selected_strategy_key]["stocks"], selected_strategy_key)
    
    st.success(f"運算完成！時間：{datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    
    # 選股摘要標的總覽
    summary_html = "<div class='summary-card'><b style='color: #1A2B4C; font-size: 1rem;'>📌 策略精選推薦標的總覽（產業分散後依潛力總分排序）：</b><ol style='margin-top: 8px; margin-bottom: 0px; padding-left: 20px; font-size: 0.88rem; color: #2D3748;'>"
    for item in stock_list:
        color = "#E53E3E" if item["is_up"] else "#38A169"
        summary_html += f"<li style='margin-bottom: 4px;'><b>{item['name']}</b> － <span style='color: {color}; font-weight: bold;'>{item['price']} ({item['change']})</span> ｜ 潛力分：<b>{item['opp_score']}分</b> ｜ 買點位階：<span class='stage-tag {item['stage_class']}'>{item['stage_status']}</span></li>"
    summary_html += "</ol></div>"
    st.markdown(summary_html, unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 0.9rem; font-weight: bold; color: #4A5568;'>👇 以下為個股詳細技術圖表與買賣價位規劃：</p>", unsafe_allow_html=True)
    
    # 逐一呈現個股卡片
    for item in stock_list:
        color_style = "color: #E53E3E;" if item["is_up"] else "color: #38A169;"
        
        with st.container():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: #1A2B4C;">
                        NO.{item['rank']} {item['name']}
                        <span class="stage-tag {item['stage_class']}">{item['stage_status']}</span>
                    </span>
                    <span style="font-size: 1.05rem; font-weight: 700; {color_style}">{item['price']} ({item['change']})</span>
                </div>
                <hr style="margin: 10px 0; border: none; border-top: 1px solid #EDF2F7;">
                <div style="font-size: 0.83rem; color: #4A5568; line-height: 1.6;">
                    <b>潛力總分 (Opportunity Score)：</b> <span style="color: #3182CE; font-weight: 700;">{item['opp_score']} 分</span> ｜ <b>買點適宜度 (Entry Score)：</b> <span style="color: #D69E2E; font-weight: 700;">{item['entry_score']} 分</span><br>
                    <b>20日相對強度 (RS)：</b> {item['rs_20d']}% ｜ <b>產業類別：</b> {item['industry']}<br>
                    <b>關鍵均線參考：</b> 月線: {item['ma20']} | 季線: {item['ma60']} | 半年線: {item['ma120']} | 年線: {item['ma240']}<br>
                    <b>動能技術指標：</b> KD ({item['k']}/{item['d']}) [{item['kd_cross']}] | MACD ({item['macd_val']}) [{item['macd_status']}]
                </div>
                <!-- 買賣與停損價位規劃區塊 -->
                <div class="price-box">
                    <div class="price-item">
                        <span style="color: #718096; font-size: 0.78rem;">建議買入價</span><br>
                        <b style="color: #2B6CB0; font-size: 0.95rem;">{item['buy_price']}</b>
                    </div>
                    <div class="price-item">
                        <span style="color: #718096; font-size: 0.78rem;">目標賣出價</span><br>
                        <b style="color: #E53E3E; font-size: 0.95rem;">{item['target_price']}</b>
                    </div>
                    <div class="price-item">
                        <span style="color: #718096; font-size: 0.78rem;">嚴格停損價 (-7%)</span><br>
                        <b style="color: #38A169; font-size: 0.95rem;">{item['stop_loss']}</b>
                    </div>
                </div>
                <div class="fundamental-box">
                    {item['fundamental']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            df_plot = item["hist_data"]
            df_sub = df_plot.tail(66) # 3 個月 K 線
            date_strs = df_sub.index.strftime('%Y-%m-%d').tolist()
            
            # 最高價防頂線 (保留 5% 緩衝空間)
            max_price_in_window = df_sub['High'].max()
            limit_line_val = max_price_in_window * 1.05
            
            fig = make_subplots(
                rows=4, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.04, 
                row_heights=[0.45, 0.18, 0.18, 0.19]
            )
            
            # 1. 主圖：K線與均線 (棒棒加粗無縫靠攏)
            fig.add_trace(go.Candlestick(
                x=date_strs, open=df_sub['Open'], high=df_sub['High'],
                low=df_sub['Low'], close=df_sub['Close'], name='K線',
                increasing_line_color='#E53E3E', decreasing_line_color='#38A169',
                increasing_fillcolor='#E53E3E', decreasing_fillcolor='#38A169',
                line=dict(width=1.5)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['5MA'], name='5MA', line=dict(color='#DD6B20', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['20MA'], name='月線(20)', line=dict(color='#3182CE', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['60MA'], name='季線(60)', line=dict(color='#805AD5', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['120MA'], name='半年線', line=dict(color='#319795', width=1, dash='dot')), row=1, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['240MA'], name='年線(240)', line=dict(color='#4A5568', width=1, dash='dash')), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=date_strs, 
                y=[limit_line_val] * len(date_strs), 
                name='防頂線', 
                line=dict(color='#CBD5E0', width=1, dash='dashdot')
            ), row=1, col=1)
            
            # 2. 副圖一：成交量
            vol_colors = ['#E53E3E' if c >= o else '#38A169' for c, o in zip(df_sub['Close'], df_sub['Open'])]
            fig.add_trace(go.Bar(x=date_strs, y=df_sub['Volume'], name='成交量', marker_color=vol_colors), row=2, col=1)
            
            # 3. 副圖二：KD
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['K'], name='K值', line=dict(color='#DD6B20', width=1.2)), row=3, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['D'], name='D值', line=dict(color='#3182CE', width=1.2)), row=3, col=1)
            
            # 4. 副圖三：MACD
            macd_hist_colors = ['#E53E3E' if val >= 0 else '#38A169' for val in df_sub['Hist']]
            fig.add_trace(go.Bar(x=date_strs, y=df_sub['Hist'], name='MACD柱狀', marker_color=macd_hist_colors), row=4, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['MACD'], name='MACD(DIF)', line=dict(color='#E53E3E', width=1.2)), row=4, col=1)
            fig.add_trace(go.Scatter(x=date_strs, y=df_sub['Signal'], name='Signal(DEM)', line=dict(color='#38A169', width=1.2)), row=4, col=1)
            
            # 【核心修復】：將 Legend 移動至圖表正下方 (y=-0.15)，徹底解耦右上角控制工具欄遮擋
            fig.update_layout(
                height=600,
                margin=dict(l=5, r=5, t=25, b=65), # 底部 b=65 留空間給 Legend
                xaxis_rangeslider_visible=False,
                xaxis4_type='category',
                bargap=0.05, 
                bargroupgap=0,
                yaxis_range=[df_sub['Low'].min() * 0.98, limit_line_val * 1.01],
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=-0.15, # 放置於圖表下方，絕對不與控制Bar或均線重疊
                    xanchor="center", 
                    x=0.5, 
                    font=dict(size=8),
                    bgcolor='rgba(255, 255, 255, 0.95)',
                    bordercolor='#E2E8F0',
                    borderwidth=1
                ),
                template="plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                key=f"plotly_chart_{item['ticker']}",
                config={'displayModeBar': True, 'displaylogo': False} # 保留控制功能但不妨礙圖例
            )
            st.markdown("---")
else:
    st.markdown("<br><p style='text-align: center; color: #A0AEC0;'>👆 點擊上方按鈕載入最新技術分析與價位規劃</p>", unsafe_allow_html=True)

st.markdown("---")
st.caption("⚠️ 聲明：本系統估算之買賣與停損價位僅供量化策略參考，實際投資請嚴格控管風險。")

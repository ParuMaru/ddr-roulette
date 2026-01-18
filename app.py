import streamlit as st
import pandas as pd
import random

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="DDR Lv18 Revenge",
    page_icon="🔥",
    layout="centered"
)

# --- 2. データの読み込み ---
@st.cache_data
def load_data():
    try:
        # さっき作ったCSVを読み込む
        df = pd.read_csv("lv18_revenge_list.csv")
        return df
    except FileNotFoundError:
        return None

df = load_data()

# --- 3. アプリの見た目（UI） ---
st.title("🔥 DDR Lv18 リベンジ・ルーレット")

if df is None:
    st.error("エラー: 'lv18_revenge_list.csv' が見つかりません。同じフォルダに置いてください！")
else:
    # 残り曲数の表示
    remain_count = len(df)
    st.markdown(f"**残りの課題曲数: :red[{remain_count} 曲]**")
    
    st.divider() # 仕切り線

    # --- 4. ルーレット機能 ---
    # 大きなボタンを配置
    if st.button("運命の課題曲を抽選する (SPIN!)", type="primary", use_container_width=True):
        
        # ランダムに1曲選ぶ
        target_song = df.sample(1).iloc[0]
        song_name = target_song['課題曲名']
        status = target_song['現状']
        
        # 結果をドーンと表示
        st.markdown("### 今日の挑戦曲は...")
        st.markdown(f"# 💿 {song_name}")
        st.caption(f"現在のステータス: {status}")
        
        # 盛り上げエフェクト（風船が飛ぶ）
        st.balloons()
        
    else:
        st.info("上のボタンを押して、今日の課題曲を決めましょう。")

    st.divider()

    # --- 5. リスト一覧（アコーディオン） ---
    with st.expander("📋 残りの課題曲リストを見る"):
        st.dataframe(df, use_container_width=True)

# --- 6. フッター ---
st.markdown("---")
st.caption("Created with Python & Streamlit for DDR Life")
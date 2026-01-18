import streamlit as st
import pandas as pd
import random

# --- ページ設定 ---
st.set_page_config(
    page_title="DDR Lv18 Manager",
    page_icon="👣",
    layout="centered"
)

st.title("👣 DDR Lv18 Manager")

# --- データ読み込み関数 ---
def load_csv(filename):
    try:
        return pd.read_csv(filename)
    except:
        return None

# 2つのファイルを読み込む
df_revenge = load_csv("lv18_revenge.csv")
df_unplayed = load_csv("lv18_unplayed.csv")

# --- サイドバー（アップロード機能） ---
st.sidebar.header("📂 データ更新")
st.sidebar.markdown("自分で抽出したCSVがあれば、ここでアップロードして上書きできます。")

up_revenge = st.sidebar.file_uploader("リベンジリスト (revenge)", type=["csv"], key="rev")
up_unplayed = st.sidebar.file_uploader("未プレイリスト (unplayed)", type=["csv"], key="unp")

if up_revenge: df_revenge = pd.read_csv(up_revenge)
if up_unplayed: df_unplayed = pd.read_csv(up_unplayed)

# --- メイン画面：タブ切り替え ---
tab1, tab2 = st.tabs(["🔥 リベンジ・ルーレット", "🆕 未プレイリスト"])

# === タブ1：未クリア曲のルーレット ===
with tab1:
    st.header("今こそ倒す時だ！")
    
    if df_revenge is not None and not df_revenge.empty:
        count = len(df_revenge)
        st.info(f"現在の未クリア残り: **{count}曲**")
        
        if st.button("運命の抽選 (SPIN!)", type="primary", use_container_width=True):
            target = df_revenge.sample(1).iloc[0]
            song_name = target[df_revenge.columns[0]] # 1列目を取得
            
            st.markdown("### 挑戦状")
            st.markdown(f"# 💿 {song_name}")
            st.balloons()
            
        with st.expander("全リベンジリストを見る"):
            st.dataframe(df_revenge, use_container_width=True, hide_index=True)
    else:
        st.success("リベンジリストが見つかりません（全クリア済みかも！？）")

# === タブ2：未プレイ曲の管理 ===
with tab2:
    st.header("未知の譜面たち")
    
    if df_unplayed is not None and not df_unplayed.empty:
        count = len(df_unplayed)
        st.write(f"まだ触っていないLv18が **{count}曲** あります。")
        
        # シンプルにリスト表示
        st.dataframe(df_unplayed, use_container_width=True, hide_index=True)
    else:
        st.success("未プレイ曲はありません！全曲解禁済みです。")

# --- フッター ---
st.markdown("---")
st.caption("DDR Lv18 Scorer | Created with Streamlit")
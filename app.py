import streamlit as st
import pandas as pd
import urllib.parse # URLを作るためのライブラリ

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

# --- ★新機能：YouTubeリンク列を追加する関数 ---
def add_youtube_link(df, col_name):
    if df is None or df.empty:
        return df
    
    # URLエンコード（日本語をURLで使える文字に変換）
    # 例: "月光乱舞" -> "%E6%9C%88..."
    def make_url(song_name):
        query = urllib.parse.quote(f"DDR {song_name} 譜面確認")
        return f"https://www.youtube.com/results?search_query={query}"

    # 新しい列「検索リンク」を作る
    df['検索リンク'] = df[col_name].apply(make_url)
    return df

# データを読み込み
df_revenge = load_csv("lv18_revenge.csv")
df_unplayed = load_csv("lv18_unplayed.csv")

# リンク情報を付与
df_revenge = add_youtube_link(df_revenge, "課題曲名")
df_unplayed = add_youtube_link(df_unplayed, "未プレイ曲名")


# --- サイドバー ---
st.sidebar.header("📂 データ更新")
up_revenge = st.sidebar.file_uploader("リベンジリスト (revenge)", type=["csv"], key="rev")
up_unplayed = st.sidebar.file_uploader("未プレイリスト (unplayed)", type=["csv"], key="unp")

if up_revenge: 
    df_revenge = pd.read_csv(up_revenge)
    df_revenge = add_youtube_link(df_revenge, "課題曲名") # アップロード時もリンク付与

if up_unplayed: 
    df_unplayed = pd.read_csv(up_unplayed)
    df_unplayed = add_youtube_link(df_unplayed, "未プレイ曲名")


# --- メイン画面 ---
tab1, tab2 = st.tabs(["🔥 リベンジ・ルーレット", "🆕 未プレイリスト"])

# === 設定：テーブルの見た目 ===
# これでURLを「▶動画」という文字に変える
column_config_settings = {
    "検索リンク": st.column_config.LinkColumn(
        "攻略",            # 列のヘッダー名
        display_text="▶動画", # 実際の表示文字
        help="クリックするとYouTube検索が開きます"
    )
}

# === タブ1：未クリア曲 ===
with tab1:
    st.header("今こそ倒す時だ！")
    
    if df_revenge is not None and not df_revenge.empty:
        count = len(df_revenge)
        st.info(f"現在の未クリア残り: **{count}曲**")
        
        if st.button("運命の抽選 (SPIN!)", type="primary", use_container_width=True):
            target = df_revenge.sample(1).iloc[0]
            song_name = target['課題曲名']
            link = target['検索リンク']
            
            st.markdown("### 挑戦状")
            st.markdown(f"# 💿 {song_name}")
            # 結果画面にもリンクを出す
            st.markdown(f"[YouTubeで譜面を確認する]({link})")
            st.toast('抽選しました！', icon='🎉')
            
        with st.expander("全リベンジリストを見る"):
            # column_configを使ってリンクを表示
            st.dataframe(
                df_revenge[['課題曲名', '検索リンク']], 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config_settings
            )
    else:
        st.success("リベンジリストが見つかりません")

# === タブ2：未プレイ曲 ===
with tab2:
    st.header("未知の譜面たち")
    
    if df_unplayed is not None and not df_unplayed.empty:
        count = len(df_unplayed)
        st.write(f"まだ触っていないLv18が **{count}曲** あります。")
        
        st.dataframe(
            df_unplayed[['未プレイ曲名', '検索リンク']], 
            use_container_width=True, 
            hide_index=True,
            column_config=column_config_settings
        )
    else:
        st.success("未プレイ曲はありません！")

# --- フッター ---
st.markdown("---")
st.caption("DDR Lv18 Scorer | Created with Streamlit")
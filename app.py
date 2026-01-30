import streamlit as st
import pandas as pd
import urllib.parse
import altair as alt
import data_manager
import time
import os

# --- ページ設定 ---
st.set_page_config(
    page_title="DDR Lv18 Manager",
    page_icon="👣",
    layout="centered"
)

st.title("👣 DDR Lv18 Manager")

# --- データ読み込み関数 ---
def load_csv(filename):
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename)
        except Exception:
            return None
    return None

# --- YouTubeリンク列を追加する関数 ---
def add_youtube_link(df, col_name):
    if df is None or df.empty or col_name not in df.columns:
        return df
    
    def make_url(song_name):
        query = urllib.parse.quote(f"DDR {song_name} 譜面確認")
        return f"https://www.youtube.com/results?search_query={query}"

    df['検索リンク'] = df[col_name].apply(make_url)
    return df

# データを読み込み
df_wiki = load_csv("DDR18_songs.csv")      # ★全曲数用
df_revenge = load_csv("lv18_revenge.csv")
df_unplayed = load_csv("lv18_unplayed.csv")
df_calories = load_csv("my_calorie_data.csv")

# リンク情報を付与
df_revenge = add_youtube_link(df_revenge, "曲名")
df_unplayed = add_youtube_link(df_unplayed, "未プレイ曲名")


# --- サイドバー ---
st.sidebar.header("📂 データ更新")

# ファイルアップローダー（キー重複注意ポイント）
up_revenge = st.sidebar.file_uploader("リベンジリスト (revenge)", type=["csv"], key="rev_uploader")
up_unplayed = st.sidebar.file_uploader("未プレイリスト (unplayed)", type=["csv"], key="unp_uploader")
up_calorie = st.sidebar.file_uploader("ワークアウト (calorie)", type=["csv"], key="cal_uploader")

if up_revenge: 
    df_revenge = pd.read_csv(up_revenge)
    df_revenge = add_youtube_link(df_revenge, "曲名")

if up_unplayed: 
    df_unplayed = pd.read_csv(up_unplayed)
    df_unplayed = add_youtube_link(df_unplayed, "未プレイ曲名")

if up_calorie:
    df_calories = pd.read_csv(up_calorie)

# 1. Wiki更新ボタン
if st.sidebar.button("1. Wikiリスト更新"):
    with st.spinner("Wikiを確認中..."):
        msg = data_manager.update_wiki_data()
        if "成功" in msg:
            st.success(msg)
            time.sleep(1)
            st.rerun() 
        else:
            st.error(msg)

# 2. 公式データ更新ボタン
if st.sidebar.button("2. 公式データ更新"):
    st.info("ブラウザが起動します。初回のみ手動でログインしてください。")
    with st.spinner("データ収集中... (ログイン状態を保存します)"):
        # 1. データを集める
        msg = data_manager.update_official_data()
        
        if "成功" in msg:
            st.success(msg)
            
            # 2. 分析もする
            res = data_manager.analyze_data()
            st.info(res)
            
            # 3. キャッシュをクリアしてリロード
            st.cache_data.clear()
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            st.error(msg)


# --- メインエリア：クリア率表示 ---
if df_wiki is not None and not df_wiki.empty:
    st.markdown("### 🏆 現在の攻略状況")
    
    total_songs = len(df_wiki) # 全曲数
    
    # データがない場合は0として扱う
    count_revenge = len(df_revenge) if df_revenge is not None else 0
    count_unplayed = len(df_unplayed) if df_unplayed is not None else 0
    
    # クリア数 = 全曲 - (未クリア + 未プレイ)
    cleared_count = total_songs - (count_revenge + count_unplayed)
    
    # 0除算防止
    playable_total = total_songs - count_unplayed
    if total_songs > 0 and playable_total > 0:
        clear_rate = cleared_count / playable_total
        all_clear_rate = cleared_count / total_songs
    else:
        clear_rate = 0
        all_clear_rate = 0
        
    # メトリクス表示
    col1, col2, col3 = st.columns(3)
    col1.metric("Lv18 クリア率", f"{clear_rate:.1%}")
    col2.metric("クリア済み", f"{cleared_count} / {total_songs-count_unplayed} 曲")
    col3.metric("未解禁含めたクリア率", f"{all_clear_rate:.1%}")
    
    st.progress(clear_rate)
    
else:
    st.warning("Wikiデータ (DDR18_songs.csv) がありません。サイドバーから「Wikiリスト更新」を行ってください。")

st.markdown("---")


# --- タブエリア ---
tab1, tab2, tab3 = st.tabs(["ルーレット", "未プレイリスト","ワークアウト"])

column_config_settings = {
    "検索リンク": st.column_config.LinkColumn(
        "攻略",
        display_text="▶動画",
        help="クリックするとYouTube検索が開く"
    )
}

# === タブ1：未クリア曲 ===
with tab1:
    st.header("めざせLv18制覇")
    
    if df_revenge is not None and not df_revenge.empty:
        count = len(df_revenge)
        st.info(f"現在のプレイ可能な未クリア残り: **{count}曲**")
        
        if st.button("抽選", type="primary", use_container_width=True):
            target = df_revenge.sample(1).iloc[0]
            song_name = target['曲名']
            link = target['検索リンク']
            
            st.markdown("### 挑戦状")
            st.markdown(f"# 💿 {song_name}")
            st.markdown(f"[YouTubeで譜面を確認する]({link})")
            st.toast('抽選しました！', icon='🎉')
            st.snow()
            
        with st.expander("未クリア一覧を見る"):
            st.dataframe(
                df_revenge[['曲名', '検索リンク']], 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config_settings
            )
    else:
        st.success("リストが見つかりません (または全曲クリア済みです！)")

# === タブ2：未プレイ曲 ===
with tab2:
    st.header("未解禁譜面たち")
    
    if df_unplayed is not None and not df_unplayed.empty:
        count = len(df_unplayed)
        st.write(f"まだ触ってないLv18が **{count}曲** あります。")
        
        st.dataframe(
            df_unplayed[['未プレイ曲名', '検索リンク']], 
            use_container_width=True, 
            hide_index=True,
            column_config=column_config_settings
        )
    else:
        st.success("未プレイ曲はありません！")


# === タブ3：カロリーグラフ ===
with tab3:
    st.header("ワークアウト")
    
    if df_calories is not None and not df_calories.empty:
        try:
            # データの前処理
            df_calories["日付"] = pd.to_datetime(df_calories["日付"]).dt.date
            df_calories["燃焼効率"] = df_calories["消費カロリー"] / df_calories["曲数"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                total_cal = df_calories["消費カロリー"].sum()
                st.metric("最新20日の総消費カロリー", f"{total_cal:,.0f} kcal")
            with col2:
                total_songs = df_calories["曲数"].sum()
                st.metric("総プレイ曲数", f"{total_songs} 曲")
            with col3:
                avg_cal = df_calories["消費カロリー"].mean()
                st.metric("1日平均", f"{avg_cal:,.0f} kcal")

            st.markdown("---")

            st.subheader("📅 日々の推移")
            chart_df = df_calories.copy()
            chart_df["日付"] = pd.to_datetime(chart_df["日付"])

            max_cal = chart_df["消費カロリー"].max()
            max_song = chart_df["曲数"].max()
            scale_cal = alt.Scale(domain=[0, max_cal])
            scale_song = alt.Scale(domain=[0, max_song * 1.3])

            base = alt.Chart(chart_df).encode(
                x=alt.X('日付:T', title='日付', axis=alt.Axis(format='%Y/%m/%d'))
            )
            bar = base.mark_bar(color='#FF4B4B', opacity=0.7).encode(
                y=alt.Y('消費カロリー:Q', title='消費カロリー (kcal)', scale=scale_cal),
                tooltip=[alt.Tooltip('日付:T', format='%Y/%m/%d'), '消費カロリー:Q', '曲数:Q']
            )
            line = base.mark_line(color='#2E86C1', point=True).encode(
                y=alt.Y('曲数:Q', title='曲数 (曲)', scale=scale_song),
                tooltip=['日付:T', '消費カロリー:Q', '曲数:Q']
            )
            combined_chart = alt.layer(bar, line).resolve_scale(y='independent')
            st.altair_chart(combined_chart, use_container_width=True)

            st.markdown("---")

            st.subheader("🔍 プレイ分析")
            bubble = alt.Chart(chart_df).mark_circle().encode(
                x=alt.X('曲数:Q', title='曲数 (曲)', scale=alt.Scale(zero=False)),
                y=alt.Y('消費カロリー:Q', title='消費カロリー (kcal)', scale=alt.Scale(zero=False)),
                size=alt.Size('消費カロリー:Q', legend=None, scale=alt.Scale(range=[100, 1000])),
                color=alt.Color('燃焼効率:Q', title='効率', scale=alt.Scale(scheme='reds')),
                tooltip=[alt.Tooltip('日付:T', format='%Y/%m/%d'), '曲数:Q', '消費カロリー:Q', '燃焼効率:Q']
            )
            trend = bubble.transform_regression('曲数', '消費カロリー').mark_line(
                color='gray', strokeDash=[5,5]
            )
            st.altair_chart((bubble + trend).interactive(), use_container_width=True)

            with st.expander("詳細データを見る"):
                st.dataframe(df_calories.sort_values("日付", ascending=False), use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.info("カロリーデータがありません。")

# --- フッター ---
st.markdown("---")
st.caption("DDR Lv18 Scorer | Created with Streamlit")

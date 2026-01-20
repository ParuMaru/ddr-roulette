import streamlit as st
import pandas as pd
import urllib.parse # URLを作るためのライブラリ
import altair as alt

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

# --- YouTubeリンク列を追加する関数 ---
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
df_calories = load_csv("my_calorie_data.csv")

# リンク情報を付与
df_revenge = add_youtube_link(df_revenge, "課題曲名")
df_unplayed = add_youtube_link(df_unplayed, "未プレイ曲名")


# --- サイドバー ---
st.sidebar.header("📂 データ更新")
up_revenge = st.sidebar.file_uploader("リベンジリスト (revenge)", type=["csv"], key="rev")
up_unplayed = st.sidebar.file_uploader("未プレイリスト (unplayed)", type=["csv"], key="unp")
up_calorie = st.sidebar.file_uploader("ワークアウト (calorie)", type=["csv"], key="cal")

if up_revenge: 
    df_revenge = pd.read_csv(up_revenge)
    df_revenge = add_youtube_link(df_revenge, "課題曲名") # アップロード時もリンク付与

if up_unplayed: 
    df_unplayed = pd.read_csv(up_unplayed)
    df_unplayed = add_youtube_link(df_unplayed, "未プレイ曲名")

if up_calorie:
    df_calorie = pd.read_csv(up_calorie)


# --- メイン画面 ---
tab1, tab2, tab3 = st.tabs(["ルーレット", "未プレイリスト","消費カロリー"])

# === 設定：テーブルの見た目 ===
# 　URLを「▶動画」という文字に変える
column_config_settings = {
    "検索リンク": st.column_config.LinkColumn(
        "攻略",            # 列のヘッダー名
        display_text="▶動画", # 実際の表示文字
        help="クリックするとYouTube検索が開く"
    )
}

# === タブ1：未クリア曲 ===
with tab1:
    st.header("めざせLv18制覇")
    
    if df_revenge is not None and not df_revenge.empty:
        count = len(df_revenge)
        st.info(f"現在の未クリア残り: **{count}曲**")
        
        if st.button("抽選", type="primary", use_container_width=True):
            target = df_revenge.sample(1).iloc[0]
            song_name = target['課題曲名']
            link = target['検索リンク']
            
            st.markdown("### 挑戦状")
            st.markdown(f"# 💿 {song_name}")
            # 結果画面にもリンクを出す
            st.markdown(f"[YouTubeで譜面を確認する]({link})")
            st.toast('抽選しました！', icon='🎉')
            st.snow()
            st.balloons()
            
        with st.expander("未クリア一覧を見る"):
            # column_configを使ってリンクを表示
            st.dataframe(
                df_revenge[['課題曲名', '検索リンク']], 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config_settings
            )
    else:
        st.success("リストが見つかりません")

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
            # 1. データの前処理
            df_calories["日付"] = pd.to_datetime(df_calories["日付"]).dt.date
            
            # 2. 概要データの表示
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

            # 3. グラフの描画（2軸グラフ）
            chart_df = df_calories.copy()
            chart_df["日付"] = pd.to_datetime(chart_df["日付"])

            # ベースとなる設定（X軸）
            base = alt.Chart(chart_df).encode(
                x=alt.X('日付:T', title='日付', axis=alt.Axis(format='%Y/%m/%d'))
            )

            # ① 棒グラフ：カロリー（左の軸）
            bar = base.mark_bar(color='#FF4B4B', opacity=0.7).encode(
                y=alt.Y('消費カロリー:Q', title='消費カロリー (kcal)'),
                tooltip=[
                    alt.Tooltip('日付:T', title='日付', format='%Y/%m/%d'),
                    alt.Tooltip('消費カロリー:Q', title='カロリー', format=','),
                    alt.Tooltip('曲数:Q', title='曲数')
                ]
            )

            # ② 折れ線グラフ：曲数（右の軸）
            line = base.mark_line(color='#2E86C1', point=True).encode(
                y=alt.Y('曲数:Q', title='曲数 (曲)'),
                tooltip=[
                    alt.Tooltip('日付:T', title='日付', format='%Y/%m/%d'),
                    alt.Tooltip('消費カロリー:Q', title='カロリー', format=','),
                    alt.Tooltip('曲数:Q', title='曲数')
                ]
            )

            # 2つを重ねて、左右の目盛りを独立させる（resolve_scale）
            combined_chart = alt.layer(bar, line).resolve_scale(
                y='independent'
            )
            
            st.altair_chart(combined_chart, use_container_width=True)
            
            # 4. 詳細データ（表）
            with st.expander("詳細データを見る"):
                st.dataframe(
                    df_calories.sort_values("日付", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.info("カロリーデータ（my_calorie_data.csv）をアップロードしてください。")

# --- フッター ---
st.markdown("---")
st.caption("DDR Lv18 Scorer | Created with Streamlit")
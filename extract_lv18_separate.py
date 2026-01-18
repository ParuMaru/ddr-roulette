import pandas as pd
import re
import os
import unicodedata

# ==========================================
# 設定エリア
# ==========================================
base_dir = os.path.dirname(os.path.abspath(__file__))

wiki_file = os.path.join(base_dir, "DDR18_songs.csv")
my_data_file = os.path.join(base_dir, "my_ddr_complete_data.csv")

revenge_file = os.path.join(base_dir, "lv18_revenge.csv")
unplayed_file = os.path.join(base_dir, "lv18_unplayed.csv")
# ==========================================

print(f"参照先: {base_dir}")
print("記号・空白を全て無視して照合します...")

# --- 強力な正規化関数 ---
def create_fingerprint(text):
    if pd.isna(text): return ""
    text = str(text)
    # 1. NFKC正規化（全角英数を半角になど）
    text = unicodedata.normalize('NFKC', text)
    # 2. 難易度表記 (鬼)(激) などを先に削除（これは曲名ではないので）
    #    ※ ただし (X-Special) や (2025 edit) みたいな曲名の一部は残したい
    #    → 難易度表記は末尾にあるはずなので、末尾の特定の文字だけ消す
    text = re.sub(r'\((鬼|激|踊|楽|習)\)$', '', text)
    
    # 3. 英数字と日本語（ひらがな・カタカナ・漢字）以外を全て削除
    #    記号（~, -, ", space）は全て消え去る
    text = re.sub(r'[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    
    # 4. 大文字小文字も無視（全て小文字へ）
    return text.lower()

try:
    # 1. データ読み込み
    df_wiki = pd.read_csv(wiki_file)
    df_my = pd.read_csv(my_data_file)
    
    wiki_col = df_wiki.columns[0]
    my_col = "曲名" if "曲名" in df_my.columns else df_my.columns[0]

    # 自分のデータの「照合用フィンガープリント」を作成
    df_my['fingerprint'] = df_my[my_col].apply(create_fingerprint)

    revenge_list = []
    unplayed_list = []

    # 2. 全曲チェック
    for index, row in df_wiki.iterrows():
        raw_name = str(row[wiki_col]).strip()
        
        # Wiki側の名前もフィンガープリント化
        search_key = create_fingerprint(raw_name)
        
        # 難易度判定
        target_mode = "BOTH"
        if "(鬼)" in raw_name: target_mode = "CHALLENGE判定"
        elif "(激)" in raw_name: target_mode = "EXPERT判定"

        # 照合！
        # 「完全に一致するもの」を探す
        # ※ 部分一致だと危ないので完全一致推奨だが、これで合わなければ前方一致も検討
        user_row = df_my[df_my['fingerprint'] == search_key]
        
        status = "未プレイ" # デフォルト
        
        if not user_row.empty:
            # データが見つかった！
            if target_mode == "BOTH":
                e = str(user_row.iloc[0].get("EXPERT判定", ""))
                c = str(user_row.iloc[0].get("CHALLENGE判定", ""))
                if "未クリア" in e or "未クリア" in c: 
                    status = "未クリア"
                elif "クリア済み" in e and "クリア済み" in c:
                    status = "クリア済み"
                else:
                    if "未クリア" in e: status = "未クリア"
            else:
                val = user_row.iloc[0].get(target_mode, "")
                if pd.notna(val):
                    status = str(val)

        # 3. 分別処理
        if "未クリア" in status:
            revenge_list.append(raw_name)
        elif "クリア済み" in status:
            continue
        else:
            unplayed_list.append(raw_name)

    # 4. 保存
    if revenge_list:
        pd.DataFrame(revenge_list, columns=["課題曲名"]).to_csv(revenge_file, index=False, encoding='utf-8_sig')
        print(f"🔥 リベンジリスト: {len(revenge_list)}曲")
    
    if unplayed_list:
        pd.DataFrame(unplayed_list, columns=["未プレイ曲名"]).to_csv(unplayed_file, index=False, encoding='utf-8_sig')
        print(f"🆕 未プレイリスト: {len(unplayed_list)}曲（ここに入っている曲を確認してください）")
        if len(unplayed_list) < 10:
             print("※ 残りわずかなので、具体的に表示します:")
             print(pd.DataFrame(unplayed_list))

except Exception as e:
    print(f"エラー: {e}")
import pandas as pd
import re
import os

# ==========================================
# 設定エリア
# ==========================================
base_dir = os.path.dirname(os.path.abspath(__file__))

wiki_file = os.path.join(base_dir, "DDR18_songs.csv")          # Wikiリスト
my_data_file = os.path.join(base_dir, "my_ddr_complete_data.csv") # 自分のデータ
output_file = os.path.join(base_dir, "lv18_revenge_list.csv")  # 結果出力先
# ==========================================

print(f"参照先: {base_dir}")
print("未クリア（E判定）のみを抽出します（曲名修正版）...")

try:
    # 1. データの読み込み
    df_wiki = pd.read_csv(wiki_file)
    df_my = pd.read_csv(my_data_file)
    
    # Wikiの列名を特定
    wiki_col_name = df_wiki.columns[0]
    # 自分のデータの列名を特定
    my_col_name = "曲名" if "曲名" in df_my.columns else df_my.columns[0]

    # 結果を格納するリスト
    targets = []

    # 2. Wikiリストを走査
    for index, row in df_wiki.iterrows():
        raw_name = str(row[wiki_col_name]).strip() # 例: "鳳 (Five Flares Mix)(鬼)"
        
        # 【修正ポイント】
        # 以前: re.sub(r'\s*\(.*\)$', '', raw_name) -> カッコを全部消していた
        # 今回: (鬼) や (激) だけをピンポイントで消す正規表現に変更
        clean_name = re.sub(r'\s*\((鬼|激|踊|楽|習)\)$', '', raw_name).strip()
        
        # 判定すべき難易度を特定
        target_col = ""
        if "(鬼)" in raw_name:
            target_col = "CHALLENGE判定"
        elif "(激)" in raw_name:
            target_col = "EXPERT判定"
        else:
            target_col = "BOTH"

        # 3. 自分のデータから検索
        user_row = df_my[df_my[my_col_name] == clean_name]
        
        status = "データなし" # デフォルト
        
        if not user_row.empty:
            if target_col == "BOTH":
                # 指定がない場合は両方見て、片方でも「未クリア」なら対象
                exp = str(user_row.iloc[0].get("EXPERT判定", ""))
                cha = str(user_row.iloc[0].get("CHALLENGE判定", ""))
                if "未クリア" in exp or "未クリア" in cha:
                    status = "未クリア"
            else:
                # 指定の難易度だけを見る
                val = user_row.iloc[0].get(target_col, "")
                if pd.notna(val):
                    status = str(val)

        # 4. フィルタリング
        # 「未クリア」が含まれる場合のみリストに入れる
        # 「データなし（未解禁）」は入れない
        if "未クリア" in status:
            targets.append({
                "課題曲名": raw_name,
                "現状": status
            })

    # 5. 保存
    if targets:
        df_result = pd.DataFrame(targets)
        df_result.to_csv(output_file, index=False, encoding='utf-8_sig')
        
        print(f"\n🔥 抽出完了！ リベンジすべき課題は {len(df_result)}曲 です。")
        print(f"保存ファイル: {output_file}")
        
        # 確認用表示
        print("\n--- リベンジ・リスト（一部） ---")
        print(df_result.head().to_string(index=False))
    else:
        print("\n未クリアの曲は見つかりませんでした。")

except Exception as e:
    print(f"\n【エラー】: {e}")
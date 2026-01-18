from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv

# ターゲットURL
url = "https://w.atwiki.jp/asigami/pages/19.html"

print("🚀 ブラウザを起動しています...")

# 1. Chromeを起動する準備（ここが最強のポイント）
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # これを有効にすると画面を出さずに裏で動く（今回は見たいのでコメントアウト）

# ドライバを自動インストールして起動
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print(f"アクセス中: {url}")
    driver.get(url)

    # 2. 【重要】ページが完全に表示されるまで待つ
    # AtWikiは表示に少しラグがあるのと、セキュリティチェックを通過する時間を待つ
    print("⏳ 読み込み待ち（5秒）...")
    time.sleep(5)

    # 3. 表示された状態の「生のHTML」を全部引っこ抜く
    html = driver.page_source
    
    print("データ取得成功！解析します。")

    # ここからは使い慣れたBeautifulSoupにバトンタッチ
    soup = BeautifulSoup(html, 'html.parser')
    
    # 保存準備
    filename = "DDR18_songs.csv"
    count = 0

    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["楽曲データ"])
        
        # テーブルの行(tr)を探す
        # AtWikiの本文エリアに絞る
        main_content = soup.find('div', id='wikibody')
        # テーブルの行(tr)をループ
        for row in main_content.find_all('tr'):
            
            # 1. 行の中にある「セル（td）」をリストとして全部取得
            cells = row.find_all('td')

            # セルがない行（ヘッダーなど）や、空っぽの行は無視して飛ばす
            if not cells:
                continue

            # 2. 画像の通り、曲名は「1つ目のセル（[0]）」にある
            target_cell = cells[0]

            # 3. そのセルの中に「リンク（aタグ）」があるか探す
            link_tag = target_cell.find('a')

            # リンクが見つかったら、そのテキスト（曲名）を取り出す
            if link_tag:
                song_name = link_tag.text.strip()
                
                # CSVに書き込み
                writer.writerow([song_name])
                count += 1
                
                # 画面確認用
                if count <= 5:
                    print(f"抽出成功: {song_name}")

    print(f"\n✅ 完了！ {count}件のデータを '{filename}' に保存しました。")

except Exception as e:
    print(f"エラー: {e}")

finally:
    # 最後はブラウザを閉じる
    print("ブラウザを終了します。")
    driver.quit()
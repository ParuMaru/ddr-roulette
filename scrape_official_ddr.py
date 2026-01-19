from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import time

# --- ステルス設定 ---
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # 1. ログインページへ
    driver.get("https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=rank")
    
    print("\n" + "="*60)
    print("【手順】")
    print("1. 手動ログインしてください。")
    print("2. 楽曲データ一覧の「1ページ目」を開いてください。")
    print("   (重要: 全曲表示させたいので、必要なら絞り込みを解除してください)")
    print("3. 準備ができたら Enter を押してください。")
    print("="*60 + "\n")
    
    input(">> 準備完了したら Enter <<")

    print("解析開始！全ページを巡回します...")

    filename = "my_ddr_data.csv"
    total_count = 0
    page_num = 1

    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"])

        # --- 無限ループ開始 ---
        while True:
            print(f"--- {page_num} ページ目を解析中 ---")
            
            # HTML解析
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all('tr', class_='data')

            if not rows:
                print("データが見つかりませんでした。終了します。")
                break

            # データ抽出ループ
            for row in rows:
                # 曲名取得
                title_div = row.find('div', class_='music_tit')
                if not title_div:
                    title_link = row.find('a')
                    song_name = title_link.text.strip() if title_link else "不明な曲"
                else:
                    song_name = title_div.text.strip()

                # 判定ロジック
                def check_status(diff_id):
                    td = row.find('td', id=diff_id)
                    if not td: return "データなし", ""
                    img = td.find('img')
                    if not img: return "未プレイ", "no_image"
                    src = img.get('src', '')
                    
                    if 'rank_s_e' in src:
                        return "未クリア(E)", src
                    else:
                        return "クリア済み", src

                exp_status, exp_src = check_status('expert')
                cha_status, cha_src = check_status('challenge')

                writer.writerow([song_name, exp_status, cha_status])
                total_count += 1

            # --- 次へボタン探索＆強制クリック処理 ---
            try:
                # 1. ID="next" を探す
                next_div = driver.find_element(By.ID, "next")
                
                # 2. その中のリンク(aタグ)を探す
                next_link = next_div.find_element(By.TAG_NAME, "a")

                # 3. リンクの飛び先(href)があるかチェック（最後のページだとhrefがない場合があるため）
                href = next_link.get_attribute("href")
                if not href or "javascript:void(0)" in href:
                    print("「次へ」ボタンはありますが、リンク先がありません。最終ページと判断します。")
                    break

                print("次のページへ強制移動します...")
                
                # Seleniumの標準クリックではなく、JavaScriptで直接クリックを実行させる
                driver.execute_script("arguments[0].click();", next_link)
                
                # 読み込み待ち（3秒）
                time.sleep(3)
                page_num += 1

            except Exception as e:
                # id="next" 自体が見つからない場合など
                print(f"次のページが見つかりませんでした（エラー: {e}）。全ページ完了です！")
                break

    print(f"\n✅ 全工程完了！ 合計 {total_count}曲のデータを保存しました。")

except Exception as e:
    print(f"エラー: {e}")

finally:
    print("確認用: ブラウザは残しておきます。")
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import time

# --- 設定エリア ---
score_filename = "my_ddr_data.csv"       # スコア保存用
calorie_filename = "my_calorie_data.csv" # カロリー保存用

# ユーザーから指定されたURL
URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
URL_WORKOUT = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/workout.html"

# --- ブラウザ起動 ---
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # ==========================================
    # Phase 0: ログイン（スコアページを開始地点にする）
    # ==========================================
    driver.get(URL_SCORE)
    
    print("\n" + "="*60)
    print("【手順1：ログイン】")
    print("ブラウザが開きました。KONAMI IDに手動でログインしてください。")
    print("ログイン後、スコア一覧が表示されたら準備完了です。")
    print("="*60 + "\n")
    
    input(">> ログイン完了したら Enter を押してください <<")

    driver.get(URL_SCORE)
    time.sleep(3)

    # ==========================================
    # Phase 1: スコア取得 (Lv18)
    # ==========================================
    print("\n" + "="*60)
    print("【手順2：スコア取得】")
    print("Lv18のデータ収集中...")
    
    total_songs = 0
    page_num = 1

    with open(score_filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"])

        while True:
            print(f"  - Page {page_num}...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all('tr', class_='data')

            if not rows:
                print("  データなし。スコア収集を終了します。")
                break

            for row in rows:
                # 曲名取得
                title_div = row.find('div', class_='music_tit')
                song_name = title_div.text.strip() if title_div else row.find('a').text.strip()

                # 判定取得ロジック
                def check_status(diff_id):
                    td = row.find('td', id=diff_id)
                    if not td: return "データなし"
                    img = td.find('img')
                    if not img: return "未プレイ"
                    src = img.get('src', '')
                    return "未クリア(E)" if 'rank_s_e' in src else "クリア済み"

                exp = check_status('expert')
                cha = check_status('challenge')
                
                writer.writerow([song_name, exp, cha])
                total_songs += 1

            # 「次へ」ボタン処理
            try:
                next_div = driver.find_element(By.ID, "next")
                next_link = next_div.find_element(By.TAG_NAME, "a")
                href = next_link.get_attribute("href")
                
                # JavaScriptのリンクか、空リンクなら終了
                if not href or "javascript:void(0)" in href:
                    break 

                driver.execute_script("arguments[0].click();", next_link)
                time.sleep(3) 
                page_num += 1
            except:
                break 
    
    print(f"✅ スコア保存完了: {total_songs}曲 -> {score_filename}")


    # ==========================================
    # Phase 2: カロリー取得 (ワークアウトページ)
    # ==========================================
    print("\n" + "="*60)
    print("【手順3：ワークアウトデータ取得】")
    print("ワークアウトページへ自動移動します...")
    
    driver.get(URL_WORKOUT)
    time.sleep(3) # 読み込み待ち

    print("解析中...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 画像で確認した id="work_out_left" のテーブルを探す
    table = soup.find('table', id='work_out_left')
    
    calorie_data = []

    if table:
        # ヘッダー以外の行(tr)を取得
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            # 画像の通り、tdが5つある行がデータ行 (No, 日付, 曲数, カロリー, 体重)
            if len(cells) >= 4:
                try:
                    # インデックス1: 日付 (2026-01-19)
                    date_text = cells[1].text.strip()
                    
                    # インデックス2: 曲数 (20 曲) -> " 曲"を消す
                    count_text = cells[2].text.strip().replace("曲", "").strip()
                    
                    # インデックス3: カロリー (791.389 kcal) -> " kcal"を消す
                    kcal_text = cells[3].text.strip().replace("kcal", "").strip()
                    
                    # リストに追加
                    if date_text and kcal_text:
                        calorie_data.append([date_text, count_text, kcal_text])
                        print(f"  取得: {date_text} / {count_text}曲 / {kcal_text}kcal")
                except Exception as e:
                    continue
    else:
        print("⚠️ テーブル(id=work_out_left)が見つかりませんでした。")

    # CSV保存
    if calorie_data:
        with open(calorie_filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["日付", "曲数", "消費カロリー"]) # ヘッダーに曲数を追加
            writer.writerows(calorie_data)
        print(f"✅ カロリー保存完了: {len(calorie_data)}件 -> {calorie_filename}")
    else:
        print("⚠️ データが取得できませんでした。")

    print("\n🎉 全工程終了！お疲れ様でした！")

except Exception as e:
    print(f"エラー: {e}")

finally:
    # driver.quit() # ブラウザを閉じたい場合はコメントアウトを外す
    pass
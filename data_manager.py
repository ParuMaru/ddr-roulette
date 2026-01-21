import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
import csv
import re
import unicodedata

# --- 設定：保存するファイル名 ---
# ファイル名は元のスクリプトの指定に合わせつつ、連携しやすいように定義
base_dir = os.path.dirname(os.path.abspath(__file__))
FILE_WIKI = os.path.join(base_dir, "DDR18_songs.csv")
FILE_SCORE = os.path.join(base_dir, "my_ddr_data.csv")
FILE_CALORIE = os.path.join(base_dir, "my_calorie_data.csv")
FILE_REVENGE = os.path.join(base_dir, "lv18_revenge.csv")
FILE_UNPLAYED = os.path.join(base_dir, "lv18_unplayed.csv")

# ==========================================
# 共通関数: 文字列正規化 (extract_lv18_separate.pyより)
# ==========================================
def create_fingerprint(text):
    if pd.isna(text): return ""
    text = str(text)
    # 1. NFKC正規化
    text = unicodedata.normalize('NFKC', text)
    # 2. 難易度表記 (鬼)(激) などを削除
    text = re.sub(r'\((鬼|激|踊|楽|習)\)$', '', text)
    # 3. 英数字と日本語以外を削除
    text = re.sub(r'[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    # 4. 小文字化
    return text.lower()


# ==========================================
# 機能1: Wikiデータの更新 (scrapping_wiki_data.pyベース)
# ==========================================
def update_wiki_data():
    """WikiからLv18の楽曲リストを取得して保存する"""
    print("🚀 Wikiデータの取得を開始します...")
    
    # 元ファイルに記載されていたURL
    url = "https://w.atwiki.jp/asigami/pages/19.html"

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # 画面を表示しない場合は有効化
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        print(f"アクセス中: {url}")
        driver.get(url)

        # 読み込み待ち（元コード通り5秒）
        print("⏳ 読み込み待ち（5秒）...")
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        with open(FILE_WIKI, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["楽曲データ"]) # 元コードのヘッダー
            
            # 本文エリア(wikibody)からテーブルを探す
            main_content = soup.find('div', id='wikibody')
            if not main_content:
                return "エラー: Wikiの本文が見つかりませんでした"

            count = 0
            for row in main_content.find_all('tr'):
                cells = row.find_all('td')
                if not cells: continue

                target_cell = cells[0]
                link_tag = target_cell.find('a')

                if link_tag:
                    song_name = link_tag.text.strip()
                    writer.writerow([song_name])
                    count += 1
        
        return f"成功: Wikiデータを更新しました ({count}曲)"

    except Exception as e:
        return f"Wiki更新エラー: {e}"

    finally:
        driver.quit()


# ==========================================
# 機能2: 公式データの更新 (scrape_official_ddr.pyベース)
# ==========================================
def update_official_data():
    """公式からスコアとカロリーを取得（ログイン維持・全ページ取得）"""
    print("🚀 公式データの取得を開始します...")
    
    # 元ファイルに記載されていたURL (display=score)
    URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
    URL_WORKOUT = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/workout.html"

    options = webdriver.ChromeOptions()
    
    # ★ログイン維持のためのプロファイル設定
    profile_path = os.path.join(os.getcwd(), "ddr_profile")
    options.add_argument(f'--user-data-dir={profile_path}')
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 1. スコアページへ移動 & ログイン待機処理
        driver.get(URL_SCORE)
        
        print("🔑 ログイン確認中...")
        # ログイン完了待ちループ
        for i in range(60):
            current_url = driver.current_url
            
            # ログイン後に別ページ（トップなど）に飛ばされた場合、スコアページに戻す
            if "login" not in current_url and "eagate.573.jp" in current_url:
                if "music_data_single" not in current_url:
                    print("🔄 スコアページへ再移動します...")
                    driver.get(URL_SCORE)
            
            # データテーブル(class="data")が見つかればOK
            try:
                WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
                print("✅ データを確認しました。収集を開始します。")
                break 
            except:
                time.sleep(1)
        else:
            return "タイムアウト: ログインまたはデータ表示を確認できませんでした。"

        # --- スコア収集 (scrape_official_ddr.pyのロジック) ---
        print("💿 スコア収集中...")
        
        with open(FILE_SCORE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"]) # 元コードのヘッダー

            total_songs = 0
            page_num = 1
            
            while True:
                print(f"  - Page {page_num}...")
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                rows = soup.find_all('tr', class_='data')

                if not rows:
                    print("  データなし。スコア収集を終了します。")
                    break

                for row in rows:
                    title_div = row.find('div', class_='music_tit')
                    song_name = title_div.text.strip() if title_div else row.find('a').text.strip()

                    def check_status(diff_id):
                        td = row.find('td', id=diff_id)
                        if not td: return "データなし"
                        img = td.find('img')
                        if not img: return "未プレイ"
                        src = img.get('src', '')
                        # display=scoreの場合は画像ファイル名で判定
                        return "未クリア(E)" if 'rank_s_e' in src else "クリア済み"

                    exp = check_status('expert')
                    cha = check_status('challenge')
                    
                    writer.writerow([song_name, exp, cha])
                    total_songs += 1

                # 次へボタン処理
                try:
                    next_div = driver.find_element(By.ID, "next")
                    next_link = next_div.find_element(By.TAG_NAME, "a")
                    href = next_link.get_attribute("href")
                    
                    if not href or "javascript:void(0)" in href:
                        break 

                    driver.execute_script("arguments[0].click();", next_link)
                    time.sleep(3) 
                    page_num += 1
                except:
                    break 
        
        print(f"✅ スコア取得完了: {total_songs}曲")


        # --- カロリー取得 (scrape_official_ddr.pyのロジック) ---
        print("🔥 カロリー収集中...")
        driver.get(URL_WORKOUT)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', id='work_out_left')
        
        calorie_data = []
        if table:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        date_t = cells[1].text.strip()
                        count_t = cells[2].text.strip().replace("曲", "").strip()
                        cal_t = cells[3].text.strip().replace("kcal", "").strip()
                        if date_t and cal_t:
                            calorie_data.append([date_t, count_t, cal_t])
                    except:
                        continue
        
        with open(FILE_CALORIE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["日付", "曲数", "消費カロリー"]) # 元コードのヘッダー
            writer.writerows(calorie_data)

        return f"成功: スコア({total_songs}件)とカロリーを更新しました！"

    except Exception as e:
        return f"公式更新エラー: {e}"
    finally:
        driver.quit()


# ==========================================
# 機能3: データ分析・抽出 (extract_lv18_separate.pyベース)
# ==========================================
def analyze_data():
    """Wikiと公式データを突き合わせてリストを作る"""
    try:
        if not os.path.exists(FILE_SCORE) or not os.path.exists(FILE_WIKI):
            return "エラー: データファイルが見つかりません。先にWikiと公式データを更新してください。"
            
        # データ読み込み
        df_wiki = pd.read_csv(FILE_WIKI)
        df_my = pd.read_csv(FILE_SCORE)
        
        # 列名特定（元コードのロジック）
        wiki_col = df_wiki.columns[0] # "楽曲データ"
        my_col = "曲名" if "曲名" in df_my.columns else df_my.columns[0] # "曲名"

        # 照合用フィンガープリント作成
        df_my['fingerprint'] = df_my[my_col].apply(create_fingerprint)

        revenge_list = []
        unplayed_list = []

        # 全曲チェックループ
        for index, row in df_wiki.iterrows():
            raw_name = str(row[wiki_col]).strip()
            search_key = create_fingerprint(raw_name)
            
            # 難易度判定 (鬼/激)
            target_mode = "BOTH"
            if "(鬼)" in raw_name: target_mode = "CHALLENGE判定"
            elif "(激)" in raw_name: target_mode = "EXPERT判定"

            # 照合
            user_row = df_my[df_my['fingerprint'] == search_key]
            
            status = "未プレイ"
            
            if not user_row.empty:
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

            # 分別
            if "未クリア" in status:
                revenge_list.append(raw_name)
            elif "クリア済み" in status:
                continue
            else:
                unplayed_list.append(raw_name)

        # 保存
        if revenge_list:
            pd.DataFrame(revenge_list, columns=["曲名"]).to_csv(FILE_REVENGE, index=False, encoding='utf-8_sig')
        
        if unplayed_list:
            pd.DataFrame(unplayed_list, columns=["未プレイ曲名"]).to_csv(FILE_UNPLAYED, index=False, encoding='utf-8_sig')
        
        return "成功: リベンジリストと未プレイリストを作成しました！"
        
    except Exception as e:
        return f"分析エラー: {e}"
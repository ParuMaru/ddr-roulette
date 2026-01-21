import os
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # 追加
from selenium.webdriver.support import expected_conditions as EC # 追加
from bs4 import BeautifulSoup
import time
import csv
import re
import unicodedata

# GitHub Secrets
COOKIES_JSON = os.environ.get("DDR_COOKIES")

# ファイル設定
FILE_WIKI = "DDR18_songs.csv"
FILE_SCORE = "my_ddr_data.csv"
FILE_CALORIE = "my_calorie_data.csv"
FILE_REVENGE = "lv18_revenge.csv"
FILE_UNPLAYED = "lv18_unplayed.csv"

def create_fingerprint(text):
    if pd.isna(text): return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\((鬼|激|踊|楽|習)\)$', '', text)
    text = re.sub(r'[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    return text.lower()

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def update_wiki():
    print("🚀 Wiki更新...")
    driver = get_driver()
    try:
        driver.set_page_load_timeout(60)
        driver.get("https://w.atwiki.jp/asigami/pages/19.html")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        with open(FILE_WIKI, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["楽曲データ"])
            main = soup.find('div', id='wikibody')
            if main:
                for row in main.find_all('tr'):
                    cells = row.find_all('td')
                    if not cells: continue
                    link = cells[0].find('a')
                    if link: writer.writerow([link.text.strip()])
        print("✅ Wiki完了")
    except Exception as e:
        print(f"⚠️ Wiki更新エラー: {e}")
    finally:
        driver.quit()

def update_official():
    print("🚀 公式更新...")
    driver = get_driver()
    URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
    URL_WORKOUT = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/workout.html"
    
    try:
        driver.set_page_load_timeout(60)
        
        # 1. Cookieセット
        driver.get("https://p.eagate.573.jp/")
        if COOKIES_JSON:
            cookies = json.loads(COOKIES_JSON)
            for cookie in cookies:
                if "p.eagate.573.jp" in cookie.get("domain", ""):
                    cd = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"]
                    }
                    if "sameSite" in cookie:
                        ss = cookie["sameSite"]
                        if ss in ["no_restriction", "None", "none"]: cd["sameSite"] = "None"
                        elif ss in ["lax", "Lax"]: cd["sameSite"] = "Lax"
                        elif ss in ["strict", "Strict"]: cd["sameSite"] = "Strict"
                    if "secure" in cookie: cd["secure"] = cookie["secure"]
                    driver.add_cookie(cd)
        else:
            print("❌ Cookieなし")
            return

        # 2. スコアページへ移動
        driver.get(URL_SCORE)
        
        # ★修正ポイント：URLチェックだけでなく、実際に「データが出るまで」待つ
        print("⏳ データの表示を待機中...")
        try:
            # class="data" が出るまで最大20秒待つ
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
            print("✅ データテーブル検出！")
        except:
            # タイムアウトした場合の調査ログ
            print("❌ タイムアウト：データが見つかりませんでした。")
            print(f"   現在のURL: {driver.current_url}")
            print(f"   ページタイトル: {driver.title}")
            # ログインページに飛ばされていないか確認
            if "login" in driver.current_url:
                print("   -> ログイン画面にリダイレクトされています。Cookieが無効です。")
            return

        # 3. データ収集開始
        score_data = []
        page = 1
        MAX_PAGES = 5

        while page <= MAX_PAGES:
            print(f"  Page {page} 読み込み...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all('tr', class_='data')
            
            if not rows:
                print("  データなし（終了）")
                break
            
            current_page_songs = 0
            for row in rows:
                title_div = row.find('div', class_='music_tit')
                name = title_div.text.strip() if title_div else row.find('a').text.strip()
                def check(did):
                    td = row.find('td', id=did)
                    if not td or not td.find('img'): return "未プレイ"
                    return "未クリア(E)" if 'rank_s_e' in td.find('img').get('src', '') else "クリア済み"
                score_data.append([name, check('expert'), check('challenge')])
                current_page_songs += 1
            
            print(f"  -> {current_page_songs}曲取得")

            try:
                # 次へボタン判定を強化（クリック可能になるまで待つ）
                next_div = driver.find_element(By.ID, "next")
                nxt = next_div.find_element(By.TAG_NAME, "a")
                href = nxt.get_attribute("href")
                
                if not href or "javascript:void(0)" in href:
                    print("  次へボタンなし（正常終了）")
                    break
                
                # クリックして、次のページのデータが出るまで待つ
                driver.execute_script("arguments[0].click();", nxt)
                time.sleep(3)
                WebDriverWait(driver, 10).until(EC.staleness_of(rows[0])) # 古いデータが消えるのを待つ
                page += 1
            except:
                print("  次へボタンが見つからない、または最終ページのため終了")
                break
        else:
            print("⚠️ ページ数が多すぎるため強制終了しました")

        with open(FILE_SCORE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"])
            writer.writerows(score_data)

        # カロリー
        print("🔥 カロリー取得...")
        driver.get(URL_WORKOUT)
        # カロリーテーブルが出るまで待つ
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "work_out_left")))
        except:
            print("⚠️ カロリーテーブルが見つかりませんでした")
            
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tbl = soup.find('table', id='work_out_left')
        cal_data = []
        if tbl:
            for row in tbl.find_all('tr'):
                c = row.find_all('td')
                if len(c) >= 4:
                    try:
                        cal_data.append([c[1].text.strip(), c[2].text.strip().replace("曲",""), c[3].text.strip().replace("kcal","")])
                    except: continue

        with open(FILE_CALORIE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["日付", "曲数", "消費カロリー"])
            writer.writerows(cal_data)
        
        print("✅ 公式完了")

    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

def analyze():
    print("🚀 分析...")
    if not os.path.exists(FILE_SCORE) or not os.path.exists(FILE_WIKI): return
    df_wiki = pd.read_csv(FILE_WIKI)
    df_my = pd.read_csv(FILE_SCORE)
    df_my['fp'] = df_my['曲名'].apply(create_fingerprint)
    
    rev, unp = [], []
    for _, row in df_wiki.iterrows():
        raw = str(row[0]).strip()
        key = create_fingerprint(raw)
        mode = "CHALLENGE判定" if "(鬼)" in raw else ("EXPERT判定" if "(激)" in raw else "BOTH")
        target = df_my[df_my['fp'] == key]
        status = "未プレイ"
        if not target.empty:
            r = target.iloc[0]
            if mode == "BOTH":
                e, c = str(r.get("EXPERT判定","")), str(r.get("CHALLENGE判定",""))
                if "未クリア" in e or "未クリア" in c: status = "未クリア"
                elif "クリア済み" in e and "クリア済み" in c: status = "クリア済み"
                elif "未クリア" in e: status = "未クリア"
            else: status = str(r.get(mode, ""))
        if "未クリア" in status: rev.append(raw)
        elif "クリア済み" not in status: unp.append(raw)
        
    if rev: pd.DataFrame(rev, columns=["曲名"]).to_csv(FILE_REVENGE, index=False)
    if unp: pd.DataFrame(unp, columns=["未プレイ曲名"]).to_csv(FILE_UNPLAYED, index=False)
    print("✅ 分析完了")

if __name__ == "__main__":
    update_wiki()
    update_official()
    analyze()
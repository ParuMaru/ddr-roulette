import os
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import re
import unicodedata

# GitHubに預けたCookieを読み込む
COOKIES_JSON = os.environ.get("DDR_COOKIES")

# ファイル名設定
FILE_WIKI = "DDR18_songs.csv"
FILE_SCORE = "my_ddr_data.csv"
FILE_CALORIE = "my_calorie_data.csv"
FILE_REVENGE = "lv18_revenge.csv"
FILE_UNPLAYED = "lv18_unplayed.csv"

# --- 共通関数 ---
def create_fingerprint(text):
    if pd.isna(text): return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\((鬼|激|踊|楽|習)\)$', '', text)
    text = re.sub(r'[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    return text.lower()

def get_driver():
    options = Options()
    options.add_argument('--headless') # 画面なしモード
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

# --- 1. Wiki更新 ---
def update_wiki():
    print("🚀 Wikiデータ更新開始...")
    driver = get_driver()
    try:
        driver.get("https://w.atwiki.jp/asigami/pages/19.html")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        with open(FILE_WIKI, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["楽曲データ"])
            main_content = soup.find('div', id='wikibody')
            if main_content:
                for row in main_content.find_all('tr'):
                    cells = row.find_all('td')
                    if not cells: continue
                    link = cells[0].find('a')
                    if link:
                        writer.writerow([link.text.strip()])
        print("✅ Wiki更新完了")
    finally:
        driver.quit()

# --- 2. 公式データ更新 (Cookie版) ---
def update_official():
    print("🚀 公式データ更新開始...")
    driver = get_driver()
    
    URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
    URL_WORKOUT = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/workout.html"
    
    try:
        # 1. ドメインにアクセスしてCookieをセット
        driver.get("https://p.eagate.573.jp/")
        
        if COOKIES_JSON:
            cookies = json.loads(COOKIES_JSON)
            for cookie in cookies:
                if "p.eagate.573.jp" in cookie.get("domain", ""):
                    cookie_dict = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"]
                    }
                    # セキュリティ関連のキーを除外
                    if "sameSite" in cookie: cookie_dict["sameSite"] = cookie["sameSite"]
                    driver.add_cookie(cookie_dict)
        else:
            print("❌ Cookieがありません！")
            return

        # 2. スコアページへ
        driver.get(URL_SCORE)
        time.sleep(3)
        
        if "login" in driver.current_url:
            print("💀 ログイン失敗（Cookie切れの可能性あり）")
            return
        
        print("✅ ログイン成功。収集開始...")

        # スコア収集
        score_data = []
        page = 1
        while True:
            print(f"  Page {page}...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all('tr', class_='data')
            if not rows: break
            
            for row in rows:
                title_div = row.find('div', class_='music_tit')
                name = title_div.text.strip() if title_div else row.find('a').text.strip()
                
                def check(did):
                    td = row.find('td', id=did)
                    if not td: return "データなし"
                    if not td.find('img'): return "未プレイ"
                    return "未クリア(E)" if 'rank_s_e' in td.find('img').get('src', '') else "クリア済み"
                
                score_data.append([name, check('expert'), check('challenge')])
            
            # 次へ
            try:
                nxt = driver.find_element(By.ID, "next").find_element(By.TAG_NAME, "a")
                if "javascript:void(0)" in nxt.get_attribute("href"): break
                driver.execute_script("arguments[0].click();", nxt)
                time.sleep(3)
                page += 1
            except:
                break

        with open(FILE_SCORE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"])
            writer.writerows(score_data)

        # カロリー収集
        driver.get(URL_WORKOUT)
        time.sleep(3)
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

        print("✅ 公式データ更新完了")

    finally:
        driver.quit()

# --- 3. 分析 ---
def analyze():
    print("🚀 データ分析開始...")
    if not os.path.exists(FILE_SCORE) or not os.path.exists(FILE_WIKI): return

    df_wiki = pd.read_csv(FILE_WIKI)
    df_my = pd.read_csv(FILE_SCORE)
    
    # 照合
    df_my['fp'] = df_my['曲名'].apply(create_fingerprint)
    
    rev, unp = [], []
    for _, row in df_wiki.iterrows():
        raw = str(row[0]).strip()
        key = create_fingerprint(raw)
        
        mode = "BOTH"
        if "(鬼)" in raw: mode = "CHALLENGE判定"
        elif "(激)" in raw: mode = "EXPERT判定"
        
        target = df_my[df_my['fp'] == key]
        status = "未プレイ"
        
        if not target.empty:
            row_data = target.iloc[0]
            if mode == "BOTH":
                e, c = str(row_data.get("EXPERT判定","")), str(row_data.get("CHALLENGE判定",""))
                if "未クリア" in e or "未クリア" in c: status = "未クリア"
                elif "クリア済み" in e and "クリア済み" in c: status = "クリア済み"
                elif "未クリア" in e: status = "未クリア"
            else:
                status = str(row_data.get(mode, ""))
        
        if "未クリア" in status: rev.append(raw)
        elif "クリア済み" not in status: unp.append(raw)
        
    if rev: pd.DataFrame(rev, columns=["曲名"]).to_csv(FILE_REVENGE, index=False)
    if unp: pd.DataFrame(unp, columns=["未プレイ曲名"]).to_csv(FILE_UNPLAYED, index=False)
    print("✅ 分析完了")

if __name__ == "__main__":
    update_wiki()
    update_official()
    analyze()
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

# GitHub Secrets
COOKIES_JSON = os.environ.get("DDR_COOKIES")

# ファイル設定
FILE_SCORE = "my_ddr_data.csv"
FILE_CALORIE = "my_calorie_data.csv"

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # ★追加：画面サイズをPCと同じにする（スマホ表示になるのを防ぐ）
    options.add_argument("--window-size=1920,1080") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def update_official():
    print("🚀 公式更新（単発テスト・診断モード）...")
    driver = get_driver()
    URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
    
    try:
        # 1. Cookieセット
        driver.get("https://p.eagate.573.jp/")
        if COOKIES_JSON:
            cookies = json.loads(COOKIES_JSON)
            for cookie in cookies:
                if "p.eagate.573.jp" in cookie.get("domain", ""):
                    cd = {
                        "name": cookie["name"], "value": cookie["value"],
                        "domain": cookie["domain"], "path": cookie["path"]
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

        # 2. スコアページへ
        print("🌍 ページ移動中...")
        driver.get(URL_SCORE)
        
        # 3. 待機と診断
        print("⏳ 読み込み待機中...")
        try:
            # class="data" があるか確認
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
            print("✅ データテーブル発見！成功です！")
        except:
            print("❌ タイムアウト：データが見つかりません。")
            print("-" * 30)
            print("【診断情報】")
            print(f"URL: {driver.current_url}")
            print(f"タイトル: {driver.title}")
            
            # ★画面に表示されている文字を読み取ってログに出す
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                # 最初の300文字だけ表示（「ログイン」や「ERROR」の文字を探すため）
                print(f"画面の文字(抜粋): {body_text[:300].replace(chr(10), ' ')}")
            except:
                print("画面の文字を読み取れませんでした")
            print("-" * 30)
            return

        # 4. データ取得（1ページ目のみ）
        score_data = []
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.find_all('tr', class_='data')
        
        print(f"📊 {len(rows)}行のデータを検出")
        
        for row in rows:
            title_div = row.find('div', class_='music_tit')
            name = title_div.text.strip() if title_div else row.find('a').text.strip()
            def check(did):
                td = row.find('td', id=did)
                if not td or not td.find('img'): return "未プレイ"
                return "未クリア(E)" if 'rank_s_e' in td.find('img').get('src', '') else "クリア済み"
            score_data.append([name, check('expert'), check('challenge')])
        
        # 保存
        if len(score_data) > 0:
            with open(FILE_SCORE, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"])
                writer.writerows(score_data)
            print(f"✅ 保存完了: {len(score_data)}曲")
        else:
            print("⚠️ データが0件です。")

    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    update_official()
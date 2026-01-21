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

# GitHub Secrets
COOKIES_JSON = os.environ.get("DDR_COOKIES")

# ファイル設定
FILE_SCORE = "my_ddr_data.csv"

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def update_official():
    print("🚀 公式データ更新（ドメイン制限解除版）")
    driver = get_driver()
    URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
    
    try:
        # 1. まずドメインにアクセス
        print("🌍 https://p.eagate.573.jp/ にアクセス中...")
        driver.get("https://p.eagate.573.jp/")
        
        # 2. Cookie登録
        if COOKIES_JSON:
            try:
                cookies = json.loads(COOKIES_JSON)
            except json.JSONDecodeError as e:
                print(f"❌ JSON形式エラー: {e}")
                return

            accepted_count = 0
            print(f"🍪 JSON内のCookie総数: {len(cookies)}個")

            for i, cookie in enumerate(cookies):
                domain = cookie.get("domain", "不明")
                name = cookie.get("name", "不明")
                
                # ログ出し（最初の5個だけ詳細表示）
                if i < 5:
                    print(f"   試行 {i+1}: Domain={domain}, Name={name}")

                # 必須項目
                cd = {
                    "name": cookie.get("name"),
                    "value": cookie.get("value"),
                    "path": cookie.get("path", "/"),
                    "domain": cookie.get("domain") # 一旦そのまま使う
                }
                
                # SameSite / Secure の調整
                if "sameSite" in cookie:
                    ss = cookie["sameSite"]
                    if ss in ["no_restriction", "None", "none"]: cd["sameSite"] = "None"
                    elif ss in ["lax", "Lax"]: cd["sameSite"] = "Lax"
                    elif ss in ["strict", "Strict"]: cd["sameSite"] = "Strict"
                if "secure" in cookie: cd["secure"] = cookie["secure"]

                # === 登録トライアル（どんなドメインでも挑む） ===
                try:
                    driver.add_cookie(cd)
                    accepted_count += 1
                except Exception as e1:
                    # 失敗したら「ドメイン指定なし」で再トライ
                    try:
                        if "domain" in cd: del cd["domain"]
                        driver.add_cookie(cd)
                        accepted_count += 1
                        # 成功したらログは出さない（うるさいので）
                    except Exception as e2:
                        pass # 無視して次へ

            print(f"✅ 登録成功したCookie: {accepted_count}個")
            
            if accepted_count == 0:
                print("💀 全てのCookieが拒否されました。正しいサイトでコピーしましたか？")
                return
        else:
            print("❌ エラー: Secretが空です")
            return

        # 3. スコアページへ移動
        print(f"🔄 スコアページへ移動: {URL_SCORE}")
        driver.get(URL_SCORE)
        
        # 4. 診断
        print("⏳ 読み込み待機中...")
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
            print("✅ データテーブル発見！成功！")
        except:
            print("❌ タイムアウト")
            print(f"   現在地: {driver.current_url}")
            print(f"   タイトル: {driver.title}")
            return

        # 5. データ取得
        score_data = []
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.find_all('tr', class_='data')
        
        print(f"📊 データ件数: {len(rows)}件")
        
        for row in rows:
            title_div = row.find('div', class_='music_tit')
            name = title_div.text.strip() if title_div else row.find('a').text.strip()
            def check(did):
                td = row.find('td', id=did)
                if not td or not td.find('img'): return "未プレイ"
                return "未クリア(E)" if 'rank_s_e' in td.find('img').get('src', '') else "クリア済み"
            score_data.append([name, check('expert'), check('challenge')])
        
        if len(score_data) > 0:
            with open(FILE_SCORE, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["曲名", "EXPERT判定", "CHALLENGE判定"])
                writer.writerows(score_data)
            print(f"✅ 保存完了: {len(score_data)}曲")
        else:
            print("⚠️ データなし")

    except Exception as e:
        print(f"❌ システムエラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    update_official()
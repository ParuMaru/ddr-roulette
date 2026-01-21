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
FILE_SCORE = "my_ddr_data.csv"

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    # 一般的なChromeに見せかける
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def update_official():
    print("🔎 ログイン診断を開始します...")
    driver = get_driver()
    
    # ターゲットURL（スコアページ）
    URL_SCORE = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
    
    try:
        # 1. まずサイトへ行く
        driver.get("https://p.eagate.573.jp/")

        # 2. Cookieの中身を点呼確認
        if not COOKIES_JSON:
            print("❌ エラー: Cookieが空っぽです！Secretsを確認してください。")
            return

        try:
            cookies = json.loads(COOKIES_JSON)
        except:
            print("❌ エラー: JSON形式が壊れています。")
            return

        print(f"📦 持っているCookie: {len(cookies)}個")
        
        # 重要な鍵があるかチェック
        has_key = False
        print("📋 Cookieリスト:")
        for c in cookies:
            name = c.get("name", "不明")
            print(f"   - {name}")
            if name == "M573SSID":
                has_key = True

        print("-" * 30)
        if has_key:
            print("✅ 本命の鍵 'M573SSID' を発見しました！")
        else:
            print("❌ エラー: 'M573SSID' がありません！")
            print("   -> コピーする時、リストの下の方まで選択されていなかった可能性があります。")
            print("   -> もう一度 EditThisCookie で確認してみてください。")
            return # 鍵がないならここで終了
        print("-" * 30)

        # 3. Cookieをブラウザにセット
        for cookie in cookies:
            cd = {
                "name": cookie.get("name"),
                "value": cookie.get("value"),
                "path": cookie.get("path", "/"),
                "domain": cookie.get("domain")
            }
            # セキュリティ属性の調整
            if "sameSite" in cookie:
                ss = cookie["sameSite"]
                if ss in ["no_restriction", "None", "none"]: cd["sameSite"] = "None"
                elif ss in ["lax", "Lax"]: cd["sameSite"] = "Lax"
                elif ss in ["strict", "Strict"]: cd["sameSite"] = "Strict"
            if "secure" in cookie: cd["secure"] = cookie["secure"]

            try:
                driver.add_cookie(cd)
            except:
                # 失敗しても気にせず次へ（ドメイン不一致など）
                try:
                    if "domain" in cd: del cd["domain"]
                    driver.add_cookie(cd)
                except:
                    pass

        # 4. ログイン確認（トップページで判定）
        print("🔄 トップページを更新して、ログイン状態を確認します...")
        driver.get("https://p.eagate.573.jp/game/ddr/ddrworld/top/index.html")
        time.sleep(3)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "ログアウト" in body_text:
            print("🎉 【成功】ログインできています！（'ログアウト'ボタンを確認）")
        elif "ログイン" in body_text:
            print("💀 【失敗】ログインできていません（'ログイン'ボタンが表示されています）")
            print("   -> Cookieは正しいですが、サーバー側で無効化された可能性があります。")
            return
        else:
            print("⚠️ 【不明】ログイン状態が判定できませんでした。とりあえず進みます。")

        # 5. スコアデータ取得へ
        print(f"🔄 スコアページへ移動: {URL_SCORE}")
        driver.get(URL_SCORE)
        
        print("⏳ データ読み込み中...")
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "data")))
            print("✅ データテーブル発見！取得を開始します。")
            
            # データ保存
            score_data = []
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all('tr', class_='data')
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

        except:
            print("❌ タイムアウト：やはりデータページに入れませんでした。")

    except Exception as e:
        print(f"❌ システムエラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    update_official()
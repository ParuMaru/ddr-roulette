import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    # 日本語環境を装う（重要）
    options.add_argument('--lang=ja-JP')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def update_official():
    print("🕵️ 最終診断：ブロックの原因を調査します...")
    driver = get_driver()
    
    try:
        # 1. まずKONAMIトップへ（Referer稼ぎ）
        driver.get("https://p.eagate.573.jp/")
        
        # 2. Cookieセット
        if not COOKIES_JSON:
            print("❌ Cookieが空です")
            return

        cookies = json.loads(COOKIES_JSON)
        # 鍵があるか再確認
        if any(c.get('name') == 'M573SSID' for c in cookies):
            print("✅ 鍵(M573SSID)は持っています！")
        else:
            print("❌ 鍵がありません（なぜ？さっきはあったのに...）")
            return

        # 全Cookie登録
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
                # ドメインなしで再トライ
                try:
                    if "domain" in cd: del cd["domain"]
                    driver.add_cookie(cd)
                except:
                    pass

        # 3. スコアページへ突撃
        target_url = "https://p.eagate.573.jp/game/ddr/ddrworld/playdata/music_data_single.html?offset=0&filter=2&filtertype=18&display=score"
        print(f"🔄 いざ、スコアページへ: {target_url}")
        driver.get(target_url)
        
        # 4. 【重要】画面の状態を文字で出力
        print("📸 現在表示されている画面の情報を取得中...")
        time.sleep(5) # 画面表示待ち
        
        page_title = driver.title
        current_url = driver.current_url
        
        print(f"🔗 URL: {current_url}")
        print(f"📄 タイトル: {page_title}")
        
        try:
            # 画面の本文を取得
            body_text = driver.find_element(By.TAG_NAME, "body").text
            # 改行を整理して表示
            clean_text = body_text.replace('\n', ' ')[:300]
            print("-" * 20)
            print("【画面の文字（抜粋）】")
            print(clean_text)
            print("-" * 20)
            
            # 判定ロジック
            if "Access Denied" in body_text or "Incapsula" in body_text:
                print("🚨 【結果】海外アクセス遮断（WAFブロック）されています。GitHubからは無理かもしれません。")
            elif "ログイン" in body_text and "ID" in body_text:
                print("💀 【結果】ログイン画面に戻されました。セッションが無効化されています。")
            elif "データ" in body_text or "楽曲" in body_text:
                print("🎉 【結果】おや？データが見えているかもしれません！")
            else:
                print("⚠️ 【結果】よく分からない画面です。上の文字を読んで判断してください。")
                
        except Exception as e:
            print(f"❌ 画面の文字すら読めませんでした: {e}")

    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    update_official()
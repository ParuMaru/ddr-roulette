import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPE_WIKI_SCRIPT = os.path.join(BASE_DIR, "scrapping_wiki_data.py")
SCRAPE_OFFICIAL_SCRIPT = os.path.join(BASE_DIR, "scrape_official_ddr.py")
ANALYZE_SCRIPT = os.path.join(BASE_DIR, "extract_lv18_separate.py")


def _run_script(script_path, label):
    if not os.path.exists(script_path):
        return f"{label}に失敗: スクリプトが見つかりません ({script_path})"

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        output = exc.stdout or exc.stderr or ""
        return f"{label}に失敗: {output.strip()}"
    except Exception as exc:
        return f"{label}に失敗: {exc}"

    if result.stdout:
        return f"{label}に成功\n{result.stdout.strip()}"
    return f"{label}に成功"


def update_wiki_data():
    return _run_script(SCRAPE_WIKI_SCRIPT, "Wiki更新")


def update_official_data():
    return _run_script(SCRAPE_OFFICIAL_SCRIPT, "公式データ更新")


def analyze_data():
    return _run_script(ANALYZE_SCRIPT, "分析")

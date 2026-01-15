import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# URL Configuration
TARGET_URL = "https://seller.kuajingmaihuo.com/settle/seller-login?redirectUrl=javascript%3A%2F%2Fagentseller.temu.com%0Aalert%28document.domain%29.com&region=1&source=https%3A%2F%2Fagentseller.temu.com%2Fmain%2Fauthentication%3FredirectUrl%3Djavascript%253A%252F%25252Fagentseller.temu.com%25250aalert%28document.domain%29.com"

def setup_stealth_driver():
    chrome_options = Options()
    
    # Enable Performance Logging to see network responses
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Standard Stealth Arguments
    chrome_options.add_argument("--headless=new")  # Use the modern headless engine
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def run_automation():
    driver = setup_stealth_driver()
    wait = WebDriverWait(driver, 20)

    try:
        print(f"Navigating to {TARGET_URL}...")
        driver.get(TARGET_URL)

        # 1. Login Logic
        print("Selecting country code...")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-testid="beast-core-select-htmlInput"]'))).click()
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(Keys.ARROW_DOWN, Keys.ENTER)
        
        print("Entering credentials...")
        wait.until(EC.presence_of_element_located((By.ID, "usernameId"))).send_keys("57059974")
        wait.until(EC.presence_of_element_located((By.ID, "passwordId"))).send_keys("Hamid2020@@")
        
        print("Clicking agreement and Login...")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="beast-core-checkbox-checkIcon"]'))).click()
        
        # Click the login button using the ID you provided
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-tracking-id="gnpTJKXw7QATc-Bx"]')))
        driver.execute_script("arguments[0].click();", login_btn)

        # 2. Wait and Intercept Response
        print("Watching for 'obtainCode' response...")
        
        code_extracted = False
        end_time = time.time() + 20  # Monitor for 20 seconds
        
        while time.time() < end_time and not code_extracted:
            logs = driver.get_log('performance')
            for entry in logs:
                message = json.loads(entry['message'])['message']
                
                if message['method'] == 'Network.responseReceived':
                    url = message['params']['response']['url']
                    
                    if 't/api/auth/obtainCode' in url:
                        request_id = message['params']['requestId']
                        try:
                            # Use Chrome DevTools Protocol to get the body content
                            response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            body_str = response['body']
                            data = json.loads(body_str)
                            
                            # --- EXTRACTION LOGIC ---
                            if data.get("success") and "result" in data:
                                auth_code = data["result"].get("code")
                                print("\n" + "="*30)
                                print(f"EXTRACTED CODE: {auth_code}")
                                print("="*30 + "\n")
                                code_extracted = True
                                break
                        except Exception:
                            continue
            time.sleep(1)

        if not code_extracted:
            print("Could not find the 'obtainCode' in network logs. Check for captchas.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    run_automation()

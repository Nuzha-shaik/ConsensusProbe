#!/usr/bin/env python3
"""End-to-end automated browser testing of ConsensusProbe using Selenium and Chrome."""
import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(ROOT, "results", "browser_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def create_sample_csv():
    csv_path = os.path.join(ROOT, "results", "test_retail_sample.csv")
    content = """item_id,product_name,category,price,stock_qty
101,Ultra Wireless Headphones,Electronics,99.99,50
102,Smart Fitness Watch,electronics,149.50,30
103,Ergonomic Office Chair,Furniture,,15
104,Organic Green Tea,Groceries,12.00,100
101,Ultra Wireless Headphones,Electronics,99.99,50
105,Mechanical Keyboard,ELECTRONICS,89.00,25
106,Stainless Steel Bottle,Home & Kitchen,24.99,80
107,Wireless Mouse,Electronics,,40
108,Ceramic Coffee Mug,Home & Kitchen,15.50,60
109,Protein Energy Bar,Groceries,2.99,200
"""
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[TEST] Created sample CSV: {csv_path}")
    return csv_path

def main():
    print("=" * 60)
    print("ConsensusProbe: Automated Browser & E2E Testing")
    print("=" * 60)

    # 1. Verify servers are reachable
    print("[1/6] Verifying local servers...")
    try:
        r_backend = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        assert r_backend.status_code == 200, f"Backend returned {r_backend.status_code}"
        print("  ✓ FastAPI backend responsive at http://127.0.0.1:8000")
    except Exception as e:
        print(f"  ✗ Backend check failed: {e}")
        return 1

    try:
        r_frontend = requests.get("http://127.0.0.1:5173/", timeout=5)
        assert r_frontend.status_code == 200, f"Frontend returned {r_frontend.status_code}"
        print("  ✓ Vite frontend responsive at http://127.0.0.1:5173")
    except Exception as e:
        print(f"  ✗ Frontend check failed: {e}")
        return 1

    # 2. Configure Selenium Chrome
    print("[2/6] Initializing Headless Chrome WebDriver...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # Step 1: Load Dashboard
        print("[3/6] Navigating to http://127.0.0.1:5173...")
        driver.get("http://127.0.0.1:5173")
        time.sleep(2)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "01_dashboard.png"))
        print("  ✓ Captured: 01_dashboard.png")

        # Step 2: Navigate to Upload
        print("[4/6] Navigating to Upload view & uploading dataset...")
        upload_tab_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Upload')]"))
        )
        upload_tab_btn.click()
        time.sleep(1)

        # Upload sample CSV
        sample_csv = create_sample_csv()
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(sample_csv)

        # Wait for profile to load (indicates successful upload)
        time.sleep(3)
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Dataset Profile')]")))
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "02_profile_loaded.png"))
        print("  ✓ Dataset successfully uploaded and profiled!")
        print("  ✓ Captured: 02_profile_loaded.png")

        # Step 3: Trigger ConsensusGate
        print("[5/6] Triggering ConsensusGate multi-plan cleaning...")
        clean_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Run ConsensusGate')]"))
        )
        clean_btn.click()
        time.sleep(3)

        # Wait for Workspace view to render
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'ConsensusGate Transformation Workspace')]")))
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "03_consensus_workspace.png"))
        print("  ✓ Captured: 03_consensus_workspace.png")

        # Step 4: Handle Clarification Question if present
        time.sleep(1)
        clarification_radios = driver.find_elements(By.CSS_SELECTOR, "input[name='clarification_opt']")
        if clarification_radios:
            print(f"  ✓ Disagreement detected! Clarification dialog has {len(clarification_radios)} options.")
            # Select option 0
            driver.execute_script("arguments[0].click();", clarification_radios[0])
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "04_clarification_selected.png"))
            print("  ✓ Captured: 04_clarification_selected.png")

            # Click Confirm & Apply Selected Strategy
            confirm_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Confirm & Apply')]"))
            )
            confirm_btn.click()
            time.sleep(3)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "05_clarification_applied.png"))
            print("  ✓ Clarification applied! Patches unified.")
            print("  ✓ Captured: 05_clarification_applied.png")

        # Step 5: Test Exports via API directly
        print("[6/6] Verifying Export outputs (CSV, XLSX, PDF)...")
        # Find dataset ID from page or database
        dataset_badge = driver.find_element(By.XPATH, "//*[contains(@class, 'truncate')]")
        filename = dataset_badge.text
        print(f"  Active dataset filename: {filename}")

        # Query backend for latest dataset ID
        # Upload endpoint already gave dataset ID, or we can fetch /profile endpoint or export
        # Let's inspect export links in DOM
        export_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/export/')]")
        for link in export_links:
            href = link.get_attribute("href")
            text = link.text.strip()
            res = requests.get(href)
            content_len = len(res.content)
            fmt = "PDF" if "pdf" in href else ("Excel" if "xlsx" in href else "CSV")
            assert res.status_code == 200, f"Export {fmt} failed with code {res.status_code}"
            assert content_len > 0, f"Export {fmt} returned empty body"
            out_file = os.path.join(SCREENSHOT_DIR, f"exported_output.{'pdf' if 'pdf' in href else ('xlsx' if 'xlsx' in href else 'csv')}")
            with open(out_file, "wb") as f:
                f.write(res.content)
            print(f"  ✓ Export {fmt} verified: {content_len} bytes written to {os.path.basename(out_file)}")

        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "06_final_verified.png"))
        print("  ✓ Captured: 06_final_verified.png")
        print("=" * 60)
        print("AUTOMATED BROWSER & E2E TESTING COMPLETED SUCCESSFULLY!")
        print(f"Screenshots and outputs saved to: {SCREENSHOT_DIR}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[ERROR] E2E Test encountered an exception: {e}")
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "error_state.png"))
        print(f"Saved error screenshot to: {os.path.join(SCREENSHOT_DIR, 'error_state.png')}")
        return 1
    finally:
        driver.quit()

if __name__ == "__main__":
    sys.exit(main())

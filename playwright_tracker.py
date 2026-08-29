import json
import os
import re
import time
from playwright.sync_api import sync_playwright

SHIPMENTS_FILE = "shipments.json"

def fetch_evergreen_eta(page, bkg_no):
    try:
        url = f"https://www.shipmentlink.com/servlet/TTrk_Tracking?bk_no={bkg_no}&type=BL"
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        text = page.content()
        # 尋找 ETA 日期特徵 (YYYY-MM-DD 或 MM/DD)
        dates = re.findall(r'202[4-7][-/.](?:0[1-9]|1[0-2])[-/.](?:0[1-9]|[12]\d|3[01])', text)
        if dates:
            d = re.split(r'[-/.]', dates[-1])
            return f"{int(d[1])}/{int(d[2])}"
    except Exception as e:
        print(f"[Evergreen] Error on {bkg_no}: {e}")
    return None

def fetch_yangming_eta(page, mbl):
    try:
        url = f"https://www.yangming.com/e-service/track_trace/track_trace_cargo_tracking.aspx?type=bl&num={mbl}"
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        text = page.content()
        dates = re.findall(r'202[4-7]/(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])', text)
        if dates:
            d = dates[-1].split('/')
            return f"{int(d[1])}/{int(d[2])}"
    except Exception as e:
        print(f"[Yang Ming] Error on {mbl}: {e}")
    return None

def fetch_wanhai_eta(page, mbl):
    try:
        url = f"https://www.wanhai.com/views/cargoTracking/cargoTracking.xhtml?blNo={mbl}"
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        text = page.content()
        dates = re.findall(r'202[4-7]/(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])', text)
        if dates:
            d = dates[-1].split('/')
            return f"{int(d[1])}/{int(d[2])}"
    except Exception as e:
        print(f"[Wan Hai] Error on {mbl}: {e}")
    return None

def main():
    if not os.path.exists(SHIPMENTS_FILE):
        print("shipments.json not found!")
        return

    with open(SHIPMENTS_FILE, "r", encoding="utf-8") as f:
        shipments = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        updated_count = 0
        for item in shipments:
            if item.get("isClosed", False):
                continue

            carrier = item.get("carrier")
            mbl = (item.get("mbl") or "").strip()

            new_eta = None
            if carrier == "Evergreen":
                new_eta = fetch_evergreen_eta(page, mbl)
            elif carrier == "Yang Ming":
                new_eta = fetch_yangming_eta(page, mbl)
            elif carrier == "Wan Hai":
                new_eta = fetch_wanhai_eta(page, mbl)

            if new_eta and new_eta != item.get("eta"):
                print(f"Updated {carrier} {mbl} ETA: {item.get('eta')} -> {new_eta}")
                item["eta"] = new_eta
                updated_count += 1
            
            time.sleep(2)

        browser.close()

    with open(SHIPMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(shipments, f, ensure_ascii=False, indent=2)

    print(f"Done! Successfully updated {updated_count} shipments.")

if __name__ == "__main__":
    main()

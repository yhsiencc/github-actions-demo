import json
import os
import requests


def get_anping_tide():
    print("=" * 40)
    print("正在抓取台南安平潮汐預報資料...")
    print("=" * 40)

    # 使用中央氣象署 F-A0021-001 (未來1個月潮汐預報) 的公開 JSON 或氣象資料
    # 這裡以簡易抓取氣象署開放 API / 網路潮汐資料為例：
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0021-001"

    # 免費公開的 CWA API Key (若無 Key 亦可模擬解析網頁)
    # 這裡範例示範直接取得安平站 (Anping) 數據結構
    params = {
        "Authorization": "CWA-87CD3C4D-64C0-410E-92CA-70F4A0EE7151",  # 氣象局預設測試金鑰/或公開接口
        "LocationName": "安平",
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("【成功取得台南安平潮汐資料】")

            # 解析並印出安平地點資訊
            location = data["records"]["location"][0]
            print(f"地點名稱: {location['locationName']}")

            # 取出最近一天的潮汐預報
            tide_forecasts = location["validTime"][0]
            print(f"預報日期: {tide_forecasts['startTime'][:10]}")

            # 將完整的安平潮汐資料寫入 JSON 檔案儲存
            file_name = "anping_tide.json"
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"已成功將潮汐資料寫入檔案: {file_name}")

        else:
            print(f"抓取失敗，HTTP 狀態碼: {response.status_code}")

    except Exception as e:
        print(f"發生錯誤: {e}")


if __name__ == "__main__":
    get_anping_tide()

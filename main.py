import json
import os
import requests


def generate_html(location_name, date_str, tide_events):
    """將抓到的潮汐資料格式化為漂亮的 HTML 網頁"""
    rows_html = ""
    for event in tide_events:
        tide_type = event.get("tide", "")
        time_str = event.get("time", "")
        height_str = event.get("height", "")

        # 標示乾潮與滿潮的顏色樣式
        badge_style = (
            "background-color: #2196F3; color: white;"
            if "滿" in tide_type
            else "background-color: #FF9800; color: white;"
        )

        rows_html += f"""
        <tr>
            <td style="padding: 12px;"><span style="padding: 4px 8px; border-radius: 4px; font-weight: bold; {badge_style}">{tide_type}</span></td>
            <td style="padding: 12px; font-size: 1.1em;">{time_str}</td>
            <td style="padding: 12px;">{height_str} cm</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{location_name} 潮汐預報</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f5f7fa; color: #333; margin: 0; padding: 20px; }}
        .card {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 24px; }}
        h1 {{ color: #1e3a8a; margin-top: 0; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; }}
        .meta {{ color: #6b7280; font-size: 0.9em; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th {{ background-color: #f3f4f6; padding: 12px; color: #4b5563; }}
        tr:nth-child(even) {{ background-color: #f9fafb; }}
        tr {{ border-bottom: 1px solid #e5e7eb; }}
        .footer {{ margin-top: 20px; text-align: center; font-size: 0.8em; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🌊 {location_name} 潮汐預報</h1>
        <div class="meta">預報日期：<strong>{date_str}</strong></div>
        <table>
            <thead>
                <tr>
                    <th>狀態</th>
                    <th>時間</th>
                    <th>潮高</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        <div class="footer">資料來源：中央氣象署開放資料平台 | 自動更新於 GitHub Actions</div>
    </div>
</body>
</html>
"""
    with open("anping_tide.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("成功產生安平潮汐 HTML 網頁：anping_tide.html")


def get_anping_tide():
    # 優先嘗試從 GitHub Secrets 讀取 API Key，若無則讀取環境變數
    api_key = os.environ.get("CWA_API_KEY", "").strip()

    if not api_key:
        print("錯誤：找不到 CWA_API_KEY，請確認環境變數已正確設定！")
        return

    print("=" * 40)
    print("正在透過中央氣象署 API 抓取台南安平潮汐預報...")
    print("=" * 40)

    # 中央氣象署未來 1 個月潮汐預報 API (F-A0021-001)
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0021-001"
    params = {
        "Authorization": api_key,
        "LocationName": "安平",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            location = data["records"]["location"][0]
            location_name = location["locationName"]

            # 抓取最近一天的潮汐數據
            valid_time = location["validTime"][0]
            date_str = valid_time["startTime"][:10]

            # 提取當天潮汐事件（滿潮/乾潮）
            tide_events = []
            if "tideTime" in valid_time:
                for t in valid_time["tideTime"]:
                    tide_events.append(
                        {
                            "tide": t.get("tide", ""),
                            "time": t.get("time", "")[-8:-3],  # 取 HH:MM
                            "height": t.get("height", ""),
                        }
                    )

            # 產生 HTML 網頁檔
            generate_html(location_name, date_str, tide_events)

        else:
            print(f"抓取失敗，HTTP 狀態碼: {response.status_code}")

    except Exception as e:
        print(f"發生錯誤: {e}")


if __name__ == "__main__":
    get_anping_tide()

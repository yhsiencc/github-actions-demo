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
                    <th>潮高 (TWVD)</th>
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


def find_key_recursive(data, target_key):
    """遞迴搜尋 JSON 結構中指定的 Key"""
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() == target_key.lower():
                return v
            res = find_key_recursive(v, target_key)
            if res is not None:
                return res
    elif isinstance(data, list):
        for item in data:
            res = find_key_recursive(item, target_key)
            if res is not None:
                return res
    return None


def get_anping_tide():
    api_key = os.environ.get("CWA_API_KEY", "").strip()

    if not api_key:
        print("錯誤：找不到 CWA_API_KEY，請確認環境變數已正確設定！")
        return

    print("=" * 40)
    print("正在透過中央氣象署 API 抓取台南安平潮汐預報...")
    print("=" * 40)

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0021-001"
    params = {"Authorization": api_key, "LocationName": "安平"}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # 全局遞迴搜尋 Location / TideForecasts 陣列
            locations = (
                find_key_recursive(data, "Location")
                or find_key_recursive(data, "TideForecasts")
                or []
            )

            if not locations or not isinstance(locations, list):
                print("錯誤：無法尋獲 Location 節點列表。")
                return

            target_loc = locations[0]
            location_name = "台南安平"

            # 全局尋找預報日期的陣列 (Daily / validTime / LocationPeriods)
            daily_data = (
                find_key_recursive(target_loc, "Daily")
                or find_key_recursive(target_loc, "validTime")
                or find_key_recursive(target_loc, "LocationPeriods")
            )

            if isinstance(daily_data, dict):
                daily_data = [daily_data]

            if not daily_data or not isinstance(daily_data, list):
                print("錯誤：找不到每日預報列表，請檢查 API 回傳結構。")
                return

            today_item = daily_data[0]
            date_str = (
                today_item.get("Date")
                or today_item.get("startTime", "")[:10]
                or "今日預報"
            )

            # 全局尋找乾滿潮點陣列 (TimePeriods / tideTime)
            time_periods = (
                find_key_recursive(today_item, "TimePeriods")
                or find_key_recursive(today_item, "tideTime")
                or []
            )

            if not time_periods or not isinstance(time_periods, list):
                # 嘗試直接從 today_item 抓取所有包含 Tide 的 dict
                time_periods = [
                    v
                    for v in today_item.values()
                    if isinstance(v, list) and len(v) > 0
                ]
                if time_periods:
                    time_periods = time_periods[0]

            tide_events = []
            for tp in time_periods:
                if not isinstance(tp, dict):
                    continue

                tide_type = (
                    tp.get("Tide")
                    or tp.get("tide")
                    or tp.get("TideStatus")
                    or "潮汐"
                )
                raw_time = (
                    tp.get("DateTime")
                    or tp.get("time")
                    or tp.get("TideTime")
                    or "--:--"
                )
                time_display = (
                    raw_time[-8:-3] if len(raw_time) >= 8 else raw_time
                )

                # 尋找潮高
                height = "--"
                height_data = find_key_recursive(tp, "AboveTWVD")
                if height_data is not None:
                    height = height_data
                elif "height" in tp:
                    height = tp["height"]

                tide_events.append(
                    {
                        "tide": tide_type,
                        "time": time_display,
                        "height": height,
                    }
                )

            generate_html(location_name, date_str, tide_events)

        else:
            print(f"抓取失敗，HTTP 狀態碼: {response.status_code}")

    except Exception as e:
        print(f"發生錯誤: {e}")


if __name__ == "__main__":
    get_anping_tide()

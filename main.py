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


def get_anping_tide():
    api_key = os.environ.get("CWA_API_KEY", "").strip()

    if not api_key:
        print("錯誤：找不到 CWA_API_KEY，請確認環境變數已正確設定！")
        return

    print("=" * 40)
    print("正在透過中央氣象署 API 抓取台南安平潮汐預報...")
    print("=" * 40)

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0021-001"
    # Swagger 規範：LocationName 帶入 LocationName 參數，格式建議為 LocationName=安平
    params = {
        "Authorization": api_key,
        "LocationName": "安平",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", {})

            # 依據 Swagger Schema：records 下方包含 Location 陣列或 TideForecasts 結構
            locations = (
                records.get("Location", [])
                or records.get("location", [])
                or records.get("TideForecasts", [])
            )

            # 若特定過濾無資料，拉取全部進行比對
            if not locations:
                res_all = requests.get(
                    url, params={"Authorization": api_key}, timeout=10
                )
                records_all = res_all.json().get("records", {})
                locations = (
                    records_all.get("Location", [])
                    or records_all.get("location", [])
                    or records_all.get("TideForecasts", [])
                )

            target_loc = None
            for loc in locations:
                loc_name = str(
                    loc.get("LocationName") or loc.get("locationName") or ""
                )
                if "安平" in loc_name:
                    target_loc = loc
                    break

            if not target_loc and locations:
                target_loc = locations[0]

            if not target_loc:
                print("錯誤：無法找到潮汐測站資料")
                return

            location_name = target_loc.get(
                "LocationName"
            ) or target_loc.get("locationName", "台南安平")

            # 解析 Daily 潮汐預報
            daily_periods = []
            if "LocationPeriods" in target_loc:
                daily_periods = target_loc["LocationPeriods"].get("Daily", [])
            elif "validTime" in target_loc:
                daily_periods = target_loc.get("validTime", [])

            if not daily_periods:
                print("錯誤：未找到潮汐預報每日數據 (Daily/validTime)")
                return

            today_data = daily_periods[0]
            date_str = str(
                today_data.get("Date")
                or today_data.get("startTime", "")[:10]
            )

            # 解析 TimePeriods (乾潮/滿潮時間點與潮高)
            time_periods = (
                today_data.get("TimePeriods", [])
                or today_data.get("tideTime", [])
            )

            tide_events = []
            for tp in time_periods:
                tide_type = tp.get("Tide") or tp.get("tide") or "潮汐"
                raw_time = tp.get("DateTime") or tp.get("time") or "--:--"
                time_display = (
                    raw_time[-8:-3] if len(raw_time) >= 8 else raw_time
                )

                # 解析 TideHeights 下的 AboveTWVD (臺灣高程基準) 潮高
                height = "--"
                tide_heights = tp.get("TideHeights") or {}
                if isinstance(tide_heights, dict):
                    height = tide_heights.get("AboveTWVD") or tide_heights.get(
                        "AboveTWVD_cm", "--"
                    )
                elif "height" in tp:
                    height = tp.get("height")

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

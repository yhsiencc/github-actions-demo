import os
import json
import requests
from datetime import datetime

API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0021-001"
LOCATION_NAME = "安平"


def find_key_recursive(obj, target_key):
    """
    遞迴搜尋所有符合 target_key 的節點
    """
    results = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() == target_key.lower():
                results.append(v)

            results.extend(find_key_recursive(v, target_key))

    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_key_recursive(item, target_key))

    return results


def find_location(data, location_name):
    """
    遞迴尋找 LocationName=安平 的節點
    """

    def walk(obj):
        if isinstance(obj, dict):
            if str(obj.get("LocationName", "")).strip() == location_name:
                return obj

            for v in obj.values():
                result = walk(v)
                if result:
                    return result

        elif isinstance(obj, list):
            for item in obj:
                result = walk(item)
                if result:
                    return result

        return None

    return walk(data)


def extract_tide_data(location_obj):
    """
    強健解析：
    自動尋找 Daily → TimePeriods
    """

    results = []

    daily_nodes = find_key_recursive(location_obj, "Daily")

    for daily in daily_nodes:

        if isinstance(daily, list):
            daily_list = daily
        else:
            daily_list = [daily]

        for day in daily_list:

            date_value = (
                day.get("Date")
                or day.get("DataTime")
                or day.get("ForecastDate")
                or ""
            )

            time_periods = (
                day.get("TimePeriods")
                or day.get("TimePeriod")
                or []
            )

            if not isinstance(time_periods, list):
                continue

            day_data = {
                "date": date_value,
                "events": []
            }

            for tp in time_periods:

                tide_type = (
                    tp.get("Tide")
                    or tp.get("TideType")
                    or tp.get("Type")
                    or ""
                )

                tide_time = (
                    tp.get("DateTime")
                    or tp.get("Time")
                    or tp.get("DataTime")
                    or ""
                )

                tide_height = (
                    tp.get("AboveTWVD")
                    or tp.get("TideHeight")
                    or tp.get("Height")
                    or ""
                )

                if isinstance(tide_height, dict):
                    tide_height = (
                        tide_height.get("Value")
                        or tide_height.get("value")
                        or ""
                    )

                day_data["events"].append({
                    "type": tide_type,
                    "time": tide_time,
                    "height": tide_height
                })

            if day_data["events"]:
                results.append(day_data)

    return results


def build_html(tide_data):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cards_html = ""

    for day in tide_data:

        event_html = ""

        for event in day["events"]:

            tide_type = str(event["type"])

            if "滿" in tide_type:
                badge_class = "high"
            elif "乾" in tide_type:
                badge_class = "low"
            else:
                badge_class = "normal"

            event_html += f"""
            <div class="event">
                <span class="badge {badge_class}">
                    {tide_type}
                </span>

                <div class="info">
                    <div><strong>時間：</strong>{event['time']}</div>
                    <div><strong>潮高：</strong>{event['height']} cm</div>
                </div>
            </div>
            """

        cards_html += f"""
        <div class="card">
            <h2>{day['date']}</h2>
            {event_html}
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>台南安平潮汐預報</title>

<style>
body {{
    font-family: Arial, Helvetica, sans-serif;
    background:#f5f7fb;
    margin:0;
    padding:20px;
}}

.container {{
    max-width:1200px;
    margin:auto;
}}

h1 {{
    text-align:center;
}}

.updated {{
    text-align:center;
    color:#666;
    margin-bottom:20px;
}}

.grid {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
    gap:20px;
}}

.card {{
    background:white;
    border-radius:16px;
    padding:20px;
    box-shadow:0 4px 10px rgba(0,0,0,.08);
}}

.event {{
    display:flex;
    gap:12px;
    margin-bottom:12px;
    padding:10px;
    border:1px solid #eee;
    border-radius:10px;
}}

.badge {{
    color:white;
    padding:6px 12px;
    border-radius:20px;
    height:fit-content;
    font-weight:bold;
}}

.high {{
    background:#2563eb;
}}

.low {{
    background:#ea580c;
}}

.normal {{
    background:#6b7280;
}}

.info {{
    flex:1;
}}
</style>

</head>

<body>

<div class="container">

<h1>台南安平潮汐預報</h1>

<div class="updated">
更新時間：{update_time}
</div>

<div class="grid">
{cards_html}
</div>

</div>

</body>
</html>
"""


def main():

    api_key = os.getenv("CWA_API_KEY")

    if not api_key:
        raise RuntimeError("CWA_API_KEY not found")

    params = {
        "Authorization": api_key,
        "format": "JSON",
        "LocationName": LOCATION_NAME
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    location = find_location(data, LOCATION_NAME)

    if not location:
        raise RuntimeError("找不到安平資料")

    tide_data = extract_tide_data(location)

    if not tide_data:
        raise RuntimeError("找不到潮汐資料")

    html = build_html(tide_data)

    with open(
        "anping_tide.html",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(html)

    print("Generated anping_tide.html")


if __name__ == "__main__":
    main()

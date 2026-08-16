import re
import requests


def get_anping_tide():
    print("=" * 40)
    print("正在抓取台南安平潮汐預報資料...")
    print("=" * 40)

    # 氣象署公開潮汐預報網頁（台南安平）
    url = "https://www.cwa.gov.tw/V8/C/M/tide.html"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("【成功連線至中央氣象署潮汐頁面】")
            print("狀態碼: 200 OK")
            print("安平潮汐網頁資料已成功載入！")
            
            # 將網頁原始碼儲存
            with open("anping_tide.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("已將網頁備份至 anping_tide.html")
        else:
            print(f"抓取失敗，HTTP 狀態碼: {response.status_code}")

    except Exception as e:
        print(f"發生錯誤: {e}")


if __name__ == "__main__":
    get_anping_tide()

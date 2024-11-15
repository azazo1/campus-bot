import requests
import json
from config import API_URL, HEADERS

def fetch_all_data(shop_id):
    """
    获取指定 shop_id 下的洗衣机数据，并合并到一个列表中。
    """
    all_items = []
    page = 1
    while True:
        # 根据接口要求构建请求的 body
        body = {
            "positionId": shop_id,  # 设置为当前选择的 positionId
            "categoryCode": "00",   # 洗衣机类别
            "page": page,           # 当前页数
            "pageSize": 10          # 每页数据量
        }
        
        response = requests.post(API_URL, headers=HEADERS, json=body)

        # print(f"状态码：{response.status_code}")
        # print(f"响应内容：{response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data["code"] == 0:
                items = data["data"]["items"]
                all_items.extend(items)
                
                # 判断是否为最后一页
                if len(items) < data["data"]["pageSize"]:  
                    break
                page += 1
            else:
                print(f"API 返回错误：{data['message']}")
                break
        else:
            print(f"请求失败，状态码：{response.status_code}")
            break
    
    return all_items

def save_to_file(data, filename="laundry_data.json"):
    """
    将抓取的数据保存到 JSON 文件。
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# from src.laundry.utils import fetch_all_data, save_to_file

# def laundry_data(shop_id):
#     """
#     获取洗衣机状态数据，并保存到 JSON 文件
#     """
#     print("开始抓取洗衣机状态数据...")
#     try:
#         all_data = fetch_all_data(shop_id=shop_id)
#         print(f"成功抓取到 {len(all_data)} 条数据")
#         save_to_file(all_data, "laundry_data.json")
#     except Exception as e:
#         print(f"运行洗衣机爬虫时发生错误：{e}")

# if __name__ == "__main__":
#     shop_id = "27316"  # 传入你要获取数据的具体 shop_id
#     laundry_data(shop_id)

# 不知道为什么，他找不到这个src module
#     from src.laundry.utils import fetch_all_data, save_to_file
#     ModuleNotFoundError: No module named 'src'
# 这个test文件就先放弃他原有的作用吧，生气、
# 到src/laundry/laundry_data.py去看

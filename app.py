import toml
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 面包屑字典, 请在每添加一个新页面时更新此字典
PAGE_TITLES = {
    "/": "首页",
    "/admin/file": "文件管理",
    "/admin/plugins": "插件配置",
    "/admin/reminders": "课前提醒",
}

CONFIG_FILE = 'plugin_config.toml'

# todo 不能这样加载配置文件.
# 加载配置文件
def load_config():
    with open(CONFIG_FILE, "r") as f:
        return toml.load(f)

# 保存配置文件
def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        toml.dump(data, f)

@app.route('/api/get_param', methods=['GET'])
def get_param():
    config = load_config()
    value = config['calendar_notice']['notice_before_class_start']
    return jsonify({"value": value})

@app.route('/api/set_param', methods=['POST'])
def set_param():
    data = request.json
    new_value = data.get("value", 600)  # 默认值 600
    config = load_config()
    config['calendar_notice']['notice_before_class_start'] = int(new_value)
    save_config(config)
    return jsonify({"status": "success", "new_value": new_value})

@app.context_processor
def inject_breadcrumbs() -> dict:
    """
    注入面包屑导航到模板上下文

    :return: 返回面包屑变量到模板
    """
    # 获取当前路径并解析
    path = request.path.strip("/")  # 去掉首尾的 "/"
    breadcrumbs = []
    current_path = ""
    for segment in path.split("/"):  # 遍历路径片段
        current_path += f"/{segment}"
        breadcrumbs.append({
            "name": PAGE_TITLES.get(current_path, segment),
            "url": current_path if current_path != request.path else None,  # 最后一级不需要链接
        })
    return {"breadcrumbs": breadcrumbs}


# Root Index
@app.route('/')
def index():  # put application's code here
    return render_template("index.html")

# 管理员页面
@app.route('/admin')
def admin():
    return render_template("admin.html")

# 文件管理
@app.route('/admin/file')
def file():
    return render_template("file.html")

# 课表提醒
@app.route('/admin/class_reminder')
def class_reminder():
    return render_template("class_reminder.html")


if __name__ == '__main__':
    app.run(debug=True)

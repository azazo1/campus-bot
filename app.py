from flask import Flask, render_template, request

app = Flask(__name__)

PAGE_TITLES = {
    "/": "首页",
    "/admin/file": "文件管理",
    "/admin/plugins": "插件配置",
    "/admin/reminders": "课前提醒",
}

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

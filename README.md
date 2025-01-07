# 华师大校园小插件

<div align="center">
  <h1><a href="https://github.com/azazo1/ecnu-campus-plugins"><img alt="ECNU Campus Plugins" src="assets/icon.png" width=132/></a></h1>

华师大校园小插件旨在利用校园内已提供的服务为学生提供一个更自动化, 人性化的便利服务.
</div>

## 功能简介

本项目实现了以下功能:

- [x] 课前邮件提醒
- [x] 课后研修间与图书馆的全自动预约
- [x] 宿舍电费自动查询及充值提醒

## 部署方法

### 环境准备

进入项目目录, 运行:

```shell
pip install -r requirements.txt
```

### 邮箱

项目有 SMTP 邮件提醒功能, 如需使用此功能, 在项目运行时进入 `email_notifier` 插件的配置界面即可填写
SMTP 相关信息.

![email_notifier 插件配置界面](assets/readme/email_config.png)

[SMTP 授权码获取方式(QQ邮箱)](https://service.mail.qq.com/detail/128/53)

### WebDriver(Edge)

项目使用 Edge WebDriver 来进行 ECNU 的登录操作, 需要正确配置 Webdriver 才能正常使用项目大部分功能.

进入 [Edge 版本](edge://version) 查看版本号(在 Edge 的地址栏输入 `edge://version` 亦可),
并从此链接中下载对应版本的 [WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/).

下载完成后解压, 将 msedgedriver.exe 放置在 Python 的安装目录中.

```text
Python/
|-- Scripts/
|-- Lib/
|-- mseedgedriver.exe # 在此处放置
|-- python.exe
|-- ...
```

- 若使用的不是最新版本,
  请拉至最底下进入 [Go to full directory](https://msedgewebdriverstorage.z22.web.core.windows.net/?form=MA13LH),
  找到对应的版本号并下载
- 可以在终端使用 `where python` 查看 Python 的安装目录.
- 可以通过`Win + I`打开系统 -> 系统信息, 若 _设备规格_ 中显示基于 x64 的处理器, 请下载 win64 版本,
  若显示基于 ARM 的处理器, 请下载 arm64 版本.

### 自动登录 ECNU 统一身份认证

项目登录 ECNU 统一身份认证默认不会全自动登录, 每次登录都需要使用者需要手动登录.

但如果在项目根目录下创建文件 `login_info.toml`,
并填写以下内容(替换尖括号及其中内容), 便可以启动自动登录功能, ECNU 登录不需要手动操作.

```toml
stu_number = "<您的学号>"
password = "<公共数据库密码>"
```

### 电费查询插件

电费查询插件的正常使用需要服务器的参与,
参阅仓库 [ecnu-query-electric-bill](https://github.com/azazo1/ecnu-query-electric-bill) 获得帮助.

## 联系我们

- 若您在使用过程中遇到相关的问题, 您可以向仓库提交 Issues
- 若您对部分代码有相关的兴趣, 欢迎向我们提交 Pull Request.

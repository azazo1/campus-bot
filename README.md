# 华师大校园小插件

华师大校园小插件旨在利用校园内已提供的服务为学生提供一个更自动化, 人性化的便利服务.

## 部署方法

在项目根目录创建文件 `configuration.toml` 配置文件.

```text
ecnu-campus-plugin/
|-- configuration.toml # 在此处创建
|-- src/
    |-- config
    |--  ....
```

### 邮箱配置

在 `configuration.toml` 内添加如下配置.

```toml
[smtp]
host = "<host_smtp_server>" # e.g. smtp.qq.com
user = "<sender_email>" # SMTP 协议邮箱, 用于发送邮箱消息.
pass = "<token>" # SMTP 协议的邮箱授权码.
to = "<receiver_email>" # 提醒接收邮箱.
```

### WebDriver 配置

请为 python 配置 Edge 的 webdriver,
见 [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/?form=MA13LH).

### 微信配置

脚本测试微信版本为: 3.9.10.27, 语言和系统语言中文.

脚本对微信的控制需要和 Windows 任务栏交互, 请确保 Windows 任务栏存在, 可按照喜好允许任务栏自动缩回.

### 环境准备

进入项目目录, 运行:

```shell
pip install -r requirements.txt
```

### 编译 C++ 代码

使用 python 运行 [copyfile_setup.py](src/cpp/copyfile_build/copyfile_setup.py), 来编译 C++ 代码,
不编译则无法使用脚本向微信发送文件功能.

[//]: # (todo 更加细节的文档, 比如 SMTP 具体配置操作, webdriver 喂奶配置教程)
[//]: # (todo 添加编写自己的 plugins 的教程.)
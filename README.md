# 华师大校园小插件

![](https://img.shields.io/github/languages/top/azazo1/ecnu-campus-plugins "语言")
[![](https://img.shields.io/github/actions/workflow/status/azazo1/ecnu-campus-plugins/golangci-lint.yml?branch=master)](https://github.com/azazo1/ecnu-campus-plugins/actions/workflows/python-cli.yml "代码分析")
[![](https://img.shields.io/github/contributors/azazo1/ecnu-campus-plugins)](https://github.com/azazo1/ecnu-campus-plugins/graphs/contributors "贡献者")
[![](https://img.shields.io/github/license/azazo1/ecnu-campus-plugins)](https://github.com/azazo1/ecnu-campus-plugins/blob/master/LICENSE "许可协议")

[//]: # (todo 将仓库状态变为 Public, 添加./github/workflows/python-cli.yml)


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



### LateX 环境准备

安装 LateX 环境, 用于生成课程表图片. 详情见: [LateX 安装](https://www.latex-project.org/get/).

[//]: # (todo 更加细节的文档, 比如 SMTP 具体配置操作, webdriver 喂奶配置教程)
[//]: # (todo 添加编写自己的 plugins 的教程.)

# Wiki 文档

本 Wiki 介绍了 ecnu-campus-plugins 的部分运行原理, 供您参考如何编写一个关于 ECNU 的插件.

[![Wiki](https://img.shields.io/badge/Go_to-Wiki-blue?style=for-the-badge)](https://github.com/azazo1/ecnu-campus-plugins/wiki)

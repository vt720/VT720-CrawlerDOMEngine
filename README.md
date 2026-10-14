# VT720-CrawlerDOMEngine

> 基于 DOM 解析、深度爬取与 JavaScript 深挖的 **子域名收集引擎**，使用 Python 编写。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 简介

`VT720-CrawlerDOMEngine`（简称 **CDOM**）是一款面向**信息收集与资产测绘**场景的子域名发现工具。

它通过 DOM 解析、多层级深度爬取、并发探活以及 JavaScript 文件静态分析，尽可能全面地提取目标主域名下的子域名资产。

> ⚠️ **使用声明：** 本项目仅供**授权范围内的安全测试、学习与研究**使用。请遵守 [DISCLAIMER.md](DISCLAIMER.md)。

---

## ✨ 核心特性

- 🔍 **DOM 解析提取**：基于页面结构提取链接与资源引用。
- 🕸️ **多层级深度爬取**：支持自定义爬取深度，逐层挖掘同域链接。
- 🚀 **并发探活**：通过多线程并发请求，快速筛选存活目标。
- 🧠 **JavaScript 深挖**：自动获取同域外部 JS 文件，并通过正则表达式匹配潜在子域名。
- 🛑 **爬取规模限制**：内置最大页面数上限，降低对目标服务器造成过大压力的风险。
- 📦 **JSON 输出**：支持结构化输出，便于后续处理与集成。

---

## 📦 环境要求

- Python 3.8+
- 第三方依赖见 [`requirements.txt`](requirements.txt)。

---

## 🔧 安装

### 1. 克隆仓库

```bash
git clone https://github.com/vt720/VT720-CrawlerDOMEngine.git
cd VT720-CrawlerDOMEngine
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

---

## 🚀 使用方法

### 基本语法

```bash
python CDOM.py -d <domain> [options]
```

---

## ⚙️ 参数说明

| 参数 | 简写 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `--domain` | `-d` | `str` | 必填 | 待挖掘的主域名，不带协议头，例如 `example.com` |
| `--depth` | `-depth` | `int` | `2` | 爬取深度。深度为 `1` 时，仅爬取主页提取到的链接；深度为 `2` 时，会继续爬取同域链接 |
| `--max-pages` | — | `int` | `30` | 最大爬取页面数量。达到上限后停止继续爬取，以限制请求规模 |
| `--deep-js` | — | `flag` | 关闭 | 开启后，遇到同域外部 `.js` 文件时，会主动获取文件并通过正则表达式挖掘子域名 |
| `--concurrency` | `-c` | `int` | `20` | 探活阶段的最大并发工作线程数 |
| `--timeout` | — | `float` | `3.0` | 单次探活请求的超时时间，单位为秒 |
| `--output` | `-o` | `str` | — | 输出文件名，使用 JSON 格式 |

---

## 💻 使用示例

### 1. 基础用法

爬取 `example.com`，使用默认爬取深度 `2`：

```bash
python CDOM.py -d example.com
```

### 2. 深度爬取 + 开启 JS 深挖 + 保存结果

```bash
python CDOM.py -d example.com -depth 3 --deep-js -o result.json
```

### 3. 高并发 + 较短超时时间

```bash
python CDOM.py -d example.com -c 50 --timeout 2.0 -o fast.json
```

### 4. 限制爬取页面数量

将最大爬取页面数设置为 `100`：

```bash
python CDOM.py -d example.com --max-pages 100 -o result.json
```

> 请仅对拥有明确授权的目标执行扫描，并根据目标环境合理设置并发数、超时时间和页面数量上限。

---

## 📤 输出格式

结果以 JSON 格式输出。默认打印到终端，也可以通过 `-o` 参数保存到文件。

示例：

```json
{
  "domain": "example.com",
  "subdomains": [
    "api.example.com",
    "cdn.example.com",
    "mail.example.com"
  ]
}
```

具体字段及输出内容以程序实际运行结果为准。

---

## 🔬 工作原理

```text
[主域名]
   |
   v
[DOM 解析] ── 提取页面中的链接与资源引用
   |
   v
[深度爬取] ── 按 depth 逐层访问同域链接
   |
   v
[JS 深挖] ── 启用 --deep-js 时，获取同域 JS 文件并进行正则匹配
   |
   v
[并发探活] ── 使用多线程验证子域名的存活情况
   |
   v
[JSON 输出]
```

---

## 🗂️ 目录结构

```text
VT720-CrawlerDOMEngine/
├── CDOM.py              # 主程序入口
├── requirements.txt     # 依赖列表
├── README.md            # 项目说明
├── CHANGELOG.md         # 更新日志
├── DISCLAIMER.md        # 免责声明
├── LICENSE              # MIT 开源协议
└── .gitignore
```

---

## 🛡️ 免责声明

本项目仅供学习、研究及授权范围内的安全测试使用。使用者应自行确保相关行为符合当地法律法规及目标网站的服务条款。因使用本项目产生的一切后果由使用者自行承担。

详细内容请参阅 [DISCLAIMER.md](DISCLAIMER.md)。

---

## 📄 License

本项目基于 **MIT License** 开源，具体条款请参阅 [LICENSE](LICENSE)。

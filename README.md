# 🕷️ PDF Downloader - 智能PDF爬蟲系統

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://github.com/amoshung/pdf-downloader)

> **一個基於 Playwright 的智能 PDF 爬蟲系統，專為法律法規文檔下載而設計，具備智能過濾、PDF合併、動態配置等強大功能。**

## 🎯 專案概述

**PDF Downloader** 是一個專為法律法規文檔下載而設計的智能PDF爬蟲系統。系統採用現代Python技術棧，結合Playwright瀏覽器自動化技術，能夠智能識別網頁中的PDF連結，支援多種過濾策略，並提供PDF合併功能，為法律從業者、研究人員和學生提供高效的文檔獲取工具。

### 🌟 核心特色

- 🕷️ **智能爬取**: 使用 Playwright 自動化瀏覽器，支援 JavaScript 渲染
- 📄 **智能識別**: 多種方式識別頁面中的 PDF 連結和文字
- 🔍 **靈活過濾**: 支援圖表開頭檔名過濾、自訂關鍵字過濾，或全部下載
- 📄 **PDF合併**: 下載完成後可選擇將所有PDF合併為單一檔案
- 🚀 **並發下載**: 支援多線程並發下載，提升效率
- 📁 **智能管理**: 自動建立目錄結構，避免重複下載
- 🔄 **重試機制**: 內建重試邏輯，提高下載成功率
- 📊 **詳細報告**: 生成完整的執行報告和下載統計
- ⚙️ **動態配置**: 支援運行時配置調整和熱重載

## 🏗️ 系統架構與設計理念

### 架構哲學

本系統採用**模組化設計**和**關注點分離**的原則，將複雜的PDF爬取任務分解為多個獨立且協作的組件。這種設計不僅提高了代碼的可維護性，也為未來的功能擴展奠定了堅實的基礎。

### 核心架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py (主程式入口)                      │
│              ┌─────────────────────────────────┐            │
│              │        用戶界面層                │            │
│              │    (選單系統 + 參數處理)         │            │
└──────────────┼─────────────────────────────────┼────────────┘
               │                                 │
┌──────────────▼─────────────────────────────────▼────────────┐
│                    PDFCrawler (核心控制器)                   │
│              ┌─────────────────────────────────┐            │
│              │        爬蟲邏輯協調             │            │
│              │    (流程控制 + 狀態管理)        │            │
└──────────────┼─────────────────────────────────┼────────────┘
               │                                 │
    ┌──────────▼──────────┐    ┌─────────────────▼──────────┐
    │   PlaywrightBrowser │    │      PDFMerger            │
    │   (瀏覽器管理)       │    │     (PDF合併處理)          │
    └─────────────────────┘    └────────────────────────────┘
               │                                 │
    ┌──────────▼──────────┐    ┌─────────────────▼──────────┐
    │    URLHandler       │    │     FileManager            │
    │    (URL處理)        │    │     (檔案管理)             │
    └─────────────────────┘    └────────────────────────────┘
```

### 設計模式應用

#### 1. **Command Pattern (命令模式)**
- 將每個爬取操作封裝為命令對象
- 支援操作的撤銷和重做
- 便於添加新的爬取策略

#### 2. **Factory Pattern (工廠模式)**
- 根據檔案類型創建適當的處理器
- 統一的檔案操作介面
- 易於擴展新的檔案類型支援

#### 3. **Strategy Pattern (策略模式)**
- 支援多種PDF過濾策略
- 可配置的下載策略
- 靈活的配置管理策略

### 技術架構特點

#### **模組化設計**
- **高內聚，低耦合**: 每個模組都有明確的職責邊界
- **依賴注入**: 通過配置系統實現組件間的鬆散耦合
- **插件式架構**: 支援新功能的無縫集成

#### **並發處理策略**
- **ThreadPoolExecutor**: 智能線程池管理
- **資源隔離**: 單個下載失敗不影響其他任務
- **記憶體優化**: 流式下載，及時釋放資源

#### **錯誤處理架構**
- **分層異常處理**: 網路、解析、檔案、業務異常分別處理
- **智能重試機制**: 指數退避策略，避免無效請求
- **詳細日誌記錄**: 完整的操作追蹤和錯誤診斷

## 🚀 功能詳解

### 1. 智能PDF識別與過濾

#### **多維度識別策略**
```python
# 支援多種PDF識別方式
- 直接PDF連結檢測
- 文字內容PDF關鍵字搜尋
- 模擬點擊PDF連結
- 圖表開頭檔名智能過濾
```

#### **靈活過濾選項**
- **選項1**: 只抓取圖、表開頭的檔名
  - 自動過濾以「圖」、「表」、「figure」、「table」開頭的文件
  - 適用於需要提取圖表資料的場景

- **選項2**: 自訂關鍵字過濾
  - 輸入自訂關鍵字，用逗號分隔
  - 例如：`圖表,附表,附件,附錄`
  - 程式會檢查文件名和連結文字是否包含關鍵字

- **選項3**: 全部下載
  - 下載頁面中發現的所有PDF文件
  - 適用於需要完整資料的場景

### 2. PDF合併與檔案管理

#### **智能合併功能**
- **多文件合併**: 支援批量處理和路徑處理
- **文件驗證**: 自動檢查PDF文件有效性
- **進度顯示**: 詳細的處理狀態和結果報告
- **原始檔案管理**: 可選擇合併後刪除原始檔案，節省空間

#### **檔案管理系統**
- **智能路徑處理**: 跨平台相容，支援絕對路徑和相對路徑
- **文件去重**: 自動重複檢測，避免重複下載
- **備份管理**: 配置自動備份，確保系統穩定性
- **日誌記錄**: 完整的操作記錄和錯誤追蹤

### 3. 動態配置管理

#### **配置系統特點**
- **User-Agent隨機化**: 多瀏覽器版本支援，降低被檢測風險
- **智能Headers**: 網站特定配置，提高爬取成功率
- **配置模板**: minimal、aggressive、stealth三種預設配置
- **熱重載**: 運行時配置更新，無需重啟程式

#### **配置優先級**
```
用戶輸入 > 命令行參數 > 配置文件 > 預設值
```

## 📋 系統需求

- **Python**: 3.8 或更高版本
- **作業系統**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **記憶體**: 建議 4GB 以上
- **網路**: 穩定的網際網路連線
- **瀏覽器**: 系統預設瀏覽器（Chrome、Firefox、Safari、Edge）

## 🛠️ 安裝指南

### 方法一：從源碼安裝（推薦）

#### 1. 克隆專案
```bash
git clone https://github.com/amoshung/pdf-downloader.git
cd pdf-downloader
```

#### 2. 建立虛擬環境
```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

#### 3. 啟動虛擬環境
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
.\venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

#### 4. 安裝依賴套件
```bash
pip install -r requirements.txt
```

#### 5. 安裝 Playwright 瀏覽器
```bash
playwright install
```

### 方法二：使用 pip 安裝

```bash
pip install pdf-downloader
```

### 方法三：Docker 安裝

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

COPY . .
CMD ["python", "main.py"]
```

## 🎮 使用方法

### 快速開始

#### 1. 啟動程式
```bash
python main.py
```

#### 2. 選擇功能
程式會顯示主選單：
```
🎯 請選擇要執行的功能
=====================================
1. 🌐 抓取網頁PDF
2. 📄 指定資料夾PDF合成單一檔案
3. ⚙️  動態配置管理
4. ❌ 退出程式

請選擇功能 (1/2/3/4): 
```

#### 3. 抓取PDF檔案
選擇選項1後，按照提示輸入參數：

```
🌐 請輸入要下載PDF的網址: https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0030018
📁 請輸入下載資料夾名稱: 法規資料
🔍 檔案過濾選項：1. 只抓圖表開頭 2. 自訂關鍵字 3. 全部下載
請選擇過濾方式 (1/2/3, 預設: 3): 1
📄 下載完成後是否要合併所有PDF為一個檔案? (y/n, 預設: n): y
```

### 進階用法

#### 命令行參數
```bash
# 基本用法
python main.py

# 指定配置檔案
python main.py --config custom_config.json

# 啟用詳細日誌
python main.py --verbose

# 指定下載目錄
python main.py --output ./my_downloads
```

#### 配置檔案範例
```json
{
  "download": {
    "max_workers": 8,
    "timeout": 30,
    "chunk_size": 8192,
    "retry_times": 3
  },
  "output": {
    "base_dir": "./downloads",
    "create_subfolder": false,
    "overwrite_existing": false
  },
  "browser": {
    "headless": true,
    "slow_mo": 100
  },
  "filter": {
    "chart_prefix": true,
    "custom_keywords": ["圖表", "附表", "附件"]
  }
}
```

## 📊 使用範例

### 範例1：下載法規圖表

```bash
# 啟動程式
python main.py

# 選擇選項1：抓取網頁PDF檔案
# 輸入網址：https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0030018
# 輸入資料夾：法規圖表
# 選擇過濾：1 (只抓圖表開頭)
# 選擇合併：y (合併PDF)

# 執行結果
🚀 開始下載...
============================================================
📊 下載完成！
✅ 成功下載: 3 個PDF文件
🔗 找到連結: 15 個
🔍 過濾後連結: 3 個
📁 下載位置: downloads/法規圖表

📄 開始PDF合併...
✅ PDF合併成功！
📄 合併後文件: downloads/法規圖表/法規圖表.pdf
📊 總頁數: 45
🔗 合併文件數: 3
💾 文件大小: 2.34 MB
```

### 範例2：批量PDF合併

```bash
# 選擇選項2：合併PDF檔案
# 選擇資料夾：downloads/法規資料
# 選擇刪除原始檔案：y

# 執行結果
📄 開始PDF合併...
✅ PDF合併成功！
📄 合併後文件: downloads/法規資料/法規資料.pdf
📊 總頁數: 156
🔗 合併文件數: 8
💾 文件大小: 8.76 MB
🗑️ 已刪除原始檔案: 8 個
```

## 🧪 測試與驗證

### 運行測試套件

```bash
# 安裝測試依賴
pip install pytest pytest-cov

# 運行所有測試
python -m pytest tests/ -v

# 運行特定測試
python -m pytest tests/test_pdf_crawler.py -v

# 生成測試覆蓋率報告
python -m pytest tests/ --cov=src --cov-report=html
```

### 端到端測試

```bash
# 運行端到端測試
python test_end_to_end.py

# 運行新功能測試
python test_new_features.py
```

### 測試結果
- **單元測試**: 85個測試 ✅
- **整合測試**: 完整覆蓋 ✅
- **端到端測試**: 6/6測試通過 ✅
- **測試通過率**: 100% ✅

## 📁 專案結構

```
pdf-downloader/
├── 📁 src/                    # 核心模組
│   ├── 📄 __init__.py
│   ├── 📄 file_manager.py     # 檔案管理
│   ├── 📄 url_handler.py      # URL處理
│   ├── 📄 playwright_browser.py  # 瀏覽器管理
│   ├── 📄 pdf_crawler.py      # 主控制器
│   ├── 📄 pdf_merger.py       # PDF合併
│   └── 📄 dynamic_config.py   # 動態配置
├── 📁 tests/                  # 測試套件
├── 📁 memory-bank/            # 專案知識庫
│   ├── 📄 projectbrief.md     # 專案概述
│   ├── 📄 productContext.md   # 產品上下文
│   ├── 📄 systemPatterns.md   # 系統架構
│   ├── 📄 techContext.md      # 技術上下文
│   ├── 📄 activeContext.md    # 當前狀態
│   └── 📄 progress.md         # 進度追蹤
├── 📁 downloads/              # 下載檔案目錄
├── 📁 config_backups/         # 配置備份目錄
├── 📁 test_downloads/         # 測試下載目錄
├── 📁 test_merge/             # 測試合併目錄
├── 📁 venv/                   # 虛擬環境
├── 📄 main.py                 # 主程式入口
├── 📄 requirements.txt        # 依賴套件
├── 📄 config.json            # 配置檔案
├── 📄 README.md              # 專案說明
└── 📄 .gitignore             # Git忽略檔案
```

## 🔧 配置說明

### 主要配置參數

| 參數 | 說明 | 預設值 | 建議值 |
|------|------|--------|--------|
| `max_workers` | 最大並發下載數量 | 8 | 4-16 |
| `timeout` | 下載超時時間(秒) | 30 | 30-60 |
| `chunk_size` | 下載塊大小(bytes) | 8192 | 4096-16384 |
| `retry_times` | 重試次數 | 3 | 3-5 |
| `headless` | 無頭瀏覽器模式 | true | true |
| `slow_mo` | 瀏覽器操作延遲(ms) | 100 | 50-200 |

### 環境變數

```bash
# 設定代理伺服器
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# 設定下載目錄
export PDF_DOWNLOADER_DOWNLOAD_DIR=/path/to/downloads

# 設定日誌等級
export PDF_DOWNLOADER_LOG_LEVEL=INFO
```

## 🚨 故障排除

### 常見問題

#### 1. Playwright 瀏覽器安裝失敗
```bash
# 解決方案：手動安裝瀏覽器
playwright install --force
```

#### 2. 下載速度慢
```bash
# 調整並發數量
# 在 config.json 中設定 max_workers: 16
```

#### 3. 記憶體使用過高
```bash
# 減少並發數量
# 設定 max_workers: 4
```

#### 4. PDF合併失敗
```bash
# 檢查檔案是否為有效PDF
# 確認檔案權限
# 檢查磁碟空間
```

### 日誌分析

```bash
# 查看詳細日誌
python main.py --verbose

# 查看日誌檔案
tail -f crawler.log
```

## 🤝 貢獻指南

### 開發環境設置

```bash
# 1. Fork 專案
# 2. 克隆你的 Fork
git clone https://github.com/yourusername/pdf-downloader.git

# 3. 建立功能分支
git checkout -b feature/amazing-feature

# 4. 提交變更
git commit -m 'Add amazing feature'

# 5. 推送到分支
git push origin feature/amazing-feature

# 6. 建立 Pull Request
```

### 代碼規範

- 遵循 PEP 8 代碼風格
- 使用類型提示 (Type Hints)
- 撰寫完整的文檔字串
- 確保測試覆蓋率 > 90%

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [Playwright](https://playwright.dev/) - 現代瀏覽器自動化框架
- [PyPDF2](https://pypdf2.readthedocs.io/) - PDF處理庫
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML解析庫
- [tqdm](https://tqdm.github.io/) - 進度條顯示

## 📞 聯絡資訊

- **專案維護者**: [amoshung](https://github.com/amoshung)
- **專案網址**: https://github.com/amoshung/pdf-downloader
- **問題回報**: https://github.com/amoshung/pdf-downloader/issues
- **功能建議**: https://github.com/amoshung/pdf-downloader/discussions

---

<div align="center">

**⭐ 如果這個專案對你有幫助，請給我們一個星標！⭐**

[![GitHub stars](https://img.shields.io/github/stars/amoshung/pdf-downloader?style=social)](https://github.com/amoshung/pdf-downloader)
[![GitHub forks](https://img.shields.io/github/forks/amoshung/pdf-downloader?style=social)](https://github.com/amoshung/pdf-downloader)
[![GitHub issues](https://img.shields.io/github/issues/amoshung/pdf-downloader)](https://github.com/amoshung/pdf-downloader/issues)

</div>
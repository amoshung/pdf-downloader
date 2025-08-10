# 技術背景 - PDF爬蟲程式

## 技術棧選擇

### 核心語言
- **Python 3.8+**: 成熟的生態系統，豐富的網路和檔案處理庫

### 主要依賴庫

#### 網路請求 (必需)
```
requests>=2.31.0
```
- **選擇理由**: 最受歡迎的HTTP庫，API簡潔，功能完整
- **替代方案**: urllib (標準庫，但API較複雜)
- **優勢**: 自動處理cookies、重定向、連接池

#### 網頁自動化 (必需)
```
playwright>=1.40.0
```
- **Playwright**: 現代化的瀏覽器自動化工具
- **選擇理由**: 內建瀏覽器引擎，支援JavaScript渲染，可以模擬點擊和文字搜尋
- **優勢**: 不需要安裝完整瀏覽器，效能優於Selenium

#### HTML解析 (輔助)
```
beautifulsoup4>=4.12.0
lxml>=4.9.0
```
- **BeautifulSoup4**: 易用的HTML/XML解析器
- **lxml**: 高效能的XML解析器，作為BeautifulSoup的後端
- **選擇理由**: 配合Playwright使用，提供額外的解析能力

#### 進度顯示 (可選)
```
tqdm>=4.66.0
```
- **選擇理由**: 輕量級進度條庫，支援多線程
- **可選性**: 不影響核心功能，僅提升用戶體驗

#### 重試機制 (可選)
```
tenacity>=8.2.0
```
- **選擇理由**: 強大的重試裝飾器，支援多種重試策略
- **替代方案**: 自實現重試邏輯

### Python標準庫使用

#### 核心模組
```python
import os                    # 檔案系統操作
import pathlib              # 現代路徑處理
import urllib.parse         # URL解析和處理
import concurrent.futures   # 並發處理
import logging              # 日誌記錄
import time                 # 時間處理
import re                   # 正規表達式
import json                 # 配置檔案處理
```

#### 網路相關
```python
import socket               # 網路底層操作
import ssl                  # SSL/TLS支援
from urllib.parse import urljoin, urlparse
```

## 環境需求

### 系統需求
- **作業系統**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python版本**: 3.8 - 3.12
- **記憶體**: 最少512MB，建議1GB+
- **磁碟空間**: 依下載檔案大小而定，建議預留2GB+

### 網路需求
- **連線**: 穩定的網際網路連接
- **頻寬**: 建議10Mbps+以發揮並發下載優勢
- **防火牆**: 允許HTTP/HTTPS出站連接

## 開發環境設置

### 虛擬環境建立
```bash
# 建立虛擬環境
python -m venv lawpdffetcher_env

# 啟動虛擬環境 (Windows)
lawpdffetcher_env\Scripts\activate

# 啟動虛擬環境 (Linux/Mac)
source lawpdffetcher_env/bin/activate
```

### 依賴安裝
```bash
# 基礎安裝
pip install playwright requests beautifulsoup4 lxml tqdm

# 安裝Playwright瀏覽器引擎
playwright install chromium

# 或使用requirements.txt
pip install -r requirements.txt
```

### Proxy設置 (如需要)
```bash
# 使用proxy安裝
pip install playwright requests beautifulsoup4 lxml tqdm --proxy http://203968:890230@172.20.199.215:3128 --trusted-host pypi.org --trusted-host files.pythonhosted.org

# 安裝Playwright瀏覽器引擎 (可能需要proxy)
playwright install chromium
```

## 配置管理

### 配置檔案結構
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
        "create_subfolder": true,
        "overwrite_existing": false
    },
    "network": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    }
}
```

## 效能調優參數

### 並發設置
```python
# CPU密集型任務
max_workers = min(32, (os.cpu_count() or 1) + 4)

# I/O密集型任務 (網路下載)
max_workers = min(50, (os.cpu_count() or 1) * 5)
```

### 記憶體管理
```python
# 檔案下載塊大小
CHUNK_SIZE = 8192  # 8KB per chunk

# 連接池大小
POOL_CONNECTIONS = 10
POOL_MAXSIZE = 20
```

### 網路優化
```python
# 請求超時設置
CONNECT_TIMEOUT = 10  # 連接超時
READ_TIMEOUT = 30     # 讀取超時

# User-Agent設置 (避免被當作機器人)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

## 安全考量

### 檔案安全
- 檔案名稱清理，移除特殊字符
- 路徑遍歷攻擊防護
- 檔案大小限制檢查

### 網路安全
- SSL證書驗證
- 惡意URL過濾
- 請求頻率限制

### 隱私保護
- 不記錄敏感URL資訊
- 支援代理伺服器
- 可配置User-Agent

## 部署建議

### 開發環境
```bash
# 開發模式運行
python main.py --debug --verbose
```

### 生產環境
```bash
# 生產模式運行
python main.py --config config.json --log-file crawler.log
```

### Docker化 (可選)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 相容性說明

### Python版本相容性
- **3.8**: 最低支援版本
- **3.9-3.11**: 完全測試支援
- **3.12**: 基本支援 (需測試)

### 作業系統相容性
- **Windows**: 完全支援，包括路徑處理
- **Linux**: 完全支援
- **macOS**: 完全支援

### 依賴庫版本鎖定
```
playwright>=1.40.0,<2.0.0
requests>=2.31.0,<3.0.0
beautifulsoup4>=4.12.0,<5.0.0
lxml>=4.9.0,<5.0.0
tqdm>=4.66.0,<5.0.0
```

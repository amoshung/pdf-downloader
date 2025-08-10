# 系統架構 - PDF爬蟲程式

## 架構概覽
採用模組化設計，將功能分離為獨立的組件，確保代碼可維護性和擴展性。

```
┌─────────────────────────────────────────┐
│                main.py                  │
│            (主程式入口)                   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│            PDFCrawler                   │
│         (核心爬蟲控制器)                   │
└─┬─────────────────────────────────────┬─┘
  │                                     │
┌─▼──────────────┐            ┌────────▼──┐
│  URLHandler    │            │FileManager│
│   (URL處理)     │            │ (檔案管理) │
└────────────────┘            └───────────┘
```

## 核心組件設計

### 1. PDFCrawler (主控制器)
**職責**: 統籌整個爬取流程
```python
class PDFCrawler:
    - fetch_webpage()      # 使用Playwright獲取網頁內容
    - find_pdf_links()     # 搜尋頁面中的PDF連結
    - simulate_clicks()    # 模擬點擊PDF連結
    - download_pdfs()      # 批量下載PDF
    - generate_report()    # 生成結果報告
```

**設計模式**: Command Pattern
- 將每個操作封裝為命令對象
- 支援操作的撤銷和重做
- 便於添加新的爬取策略

### 2. URLHandler (URL處理器)
**職責**: 處理所有URL相關操作
```python
class URLHandler:
    - normalize_url()      # URL標準化
    - resolve_relative()   # 相對路徑解析
    - validate_pdf_url()   # PDF URL驗證
    - extract_filename()   # 檔案名提取
    - find_pdf_text()      # 搜尋頁面中的PDF文字
```

**設計模式**: Utility Pattern
- 提供靜態方法集合
- 無狀態設計，線程安全
- 可重用的URL處理邏輯

### 3. FileManager (檔案管理器)
**職責**: 管理檔案系統操作
```python
class FileManager:
    - create_download_dir()  # 建立下載目錄
    - check_file_exists()    # 檢查檔案存在
    - save_file()           # 保存檔案
    - generate_unique_name() # 生成唯一檔名
```

**設計模式**: Factory Pattern
- 根據檔案類型創建適當的處理器
- 統一的檔案操作介面
- 易於擴展新的檔案類型支援

## 資料流設計

### 主要資料流
```
URL輸入 → Playwright網頁載入 → JavaScript渲染 → PDF文字搜尋 → 連結提取 → 模擬點擊 → 並發下載 → 結果報告
```

### 資料結構
```python
# PDF連結資訊
PDFLink = {
    'url': str,           # PDF的完整URL
    'filename': str,      # 建議的檔案名
    'size': int,          # 檔案大小(bytes)
    'valid': bool         # 連結有效性
}

# 下載結果
DownloadResult = {
    'success': bool,      # 下載成功與否
    'filepath': str,      # 本地檔案路徑
    'error_msg': str,     # 錯誤訊息
    'download_time': float # 下載耗時
}
```

## 並發處理策略

### ThreadPoolExecutor 配置
- **最大線程數**: min(32, (os.cpu_count() or 1) + 4)
- **任務佇列**: 使用Future對象管理異步任務
- **錯誤隔離**: 單個下載失敗不影響其他任務

### 資源管理
```python
# 連接池配置
session = requests.Session()
session.mount('http://', HTTPAdapter(pool_connections=10, pool_maxsize=20))
session.mount('https://', HTTPAdapter(pool_connections=10, pool_maxsize=20))
```

## 錯誤處理架構

### 異常層次
1. **網路異常**: ConnectionError, Timeout, HTTPError
2. **解析異常**: HTMLParseError, URLParseError
3. **檔案異常**: FileNotFoundError, PermissionError
4. **業務異常**: InvalidPDFError, DuplicateFileError

### 重試機制
```python
@retry(stop=stop_after_attempt(3), 
       wait=wait_exponential(multiplier=1, min=4, max=10))
def download_with_retry(url, filepath):
    # 下載邏輯
```

## 擴展點設計

### 1. 解析器擴展
- 支援不同網站的特殊解析邏輯
- 插件式架構，動態載入解析器
- Playwright頁面互動策略擴展

### 2. 下載器擴展
- 支援不同的下載協議
- 可配置的下載策略

### 3. 儲存擴展
- 支援雲端儲存
- 資料庫記錄管理

## 效能考量

### 記憶體優化
- 流式下載大檔案
- 及時釋放已處理的資源
- 限制並發數量避免記憶體溢出

### 網路優化
- Keep-Alive連接重用
- 壓縮傳輸支援
- 智能重試避免無效請求

### 磁碟I/O優化
- 批量寫入減少磁碟操作
- 預分配檔案空間
- 異步I/O處理

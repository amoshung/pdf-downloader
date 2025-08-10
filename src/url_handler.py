"""
URL處理模組
負責URL的標準化、驗證和處理
"""

import re
import logging
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urljoin, urlunparse, quote, unquote, parse_qsl
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class URLHandler:
    """URL處理工具類別"""
    
    @staticmethod
    def normalize_url(url: str, base_url: str = None) -> str:
        """
        標準化URL
        
        Args:
            url: 原始URL
            base_url: 基礎URL，用於解析相對路徑
            
        Returns:
            str: 標準化的URL
        """
        try:
            if not url:
                return ""
                
            # 移除前後空白
            url = url.strip()
            
            # 如果是相對路徑且有基礎URL
            if base_url and not URLHandler._is_absolute_url(url):
                url = urljoin(base_url, url)
                
            # 解析URL
            parsed = urlparse(url)
            
            # 確保有scheme
            if not parsed.scheme:
                # 如果沒有netloc但有路徑，說明是example.com這種格式
                if not parsed.netloc and parsed.path and '.' in parsed.path:
                    # 將第一個路徑段作為netloc
                    path_parts = parsed.path.split('/', 1)
                    if len(path_parts) > 1:
                        parsed = parsed._replace(
                            scheme='http',
                            netloc=path_parts[0],
                            path='/' + path_parts[1] if path_parts[1] else '/'
                        )
                    else:
                        parsed = parsed._replace(scheme='http', netloc=path_parts[0], path='/')
                else:
                    parsed = parsed._replace(scheme='http')
                
            # 標準化路徑
            path = parsed.path
            if not path:
                path = '/'
            elif not path.startswith('/'):
                path = '/' + path
                
            # 移除路徑中的雙斜線
            path = re.sub(r'/+', '/', path)
            
            # 重新組合URL
            normalized = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            logger.debug(f"URL標準化: {url} -> {normalized}")
            return normalized
            
        except Exception as e:
            logger.error(f"URL標準化失敗: {url}, 錯誤: {e}")
            return url
            
    @staticmethod
    def _is_absolute_url(url: str) -> bool:
        """檢查是否為絕對URL"""
        return bool(urlparse(url).scheme)
        
    @staticmethod
    def validate_pdf_url(url: str) -> bool:
        """
        驗證PDF URL的有效性
        
        Args:
            url: 要驗證的URL
            
        Returns:
            bool: URL是否有效
        """
        try:
            if not url:
                return False
                
            # 檢查URL格式
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # 只允許 HTTP 和 HTTPS 協議
            if parsed.scheme not in ['http', 'https']:
                return False
                
            # 檢查是否為PDF檔案
            if not URLHandler._is_pdf_url(url):
                return False
                
            # 檢查URL長度
            if len(url) > 2048:
                logger.warning(f"URL過長: {url}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"URL驗證失敗: {url}, 錯誤: {e}")
            return False
            
    @staticmethod
    def _is_pdf_url(url: str) -> bool:
        """檢查URL是否指向PDF檔案"""
        url_lower = url.lower()
        
        # 檢查檔案擴展名 (支援查詢參數和片段)
        if '.pdf' in url_lower:
            # 檢查路徑中的.pdf
            parsed = urlparse(url)
            path_lower = parsed.path.lower()
            if path_lower.endswith('.pdf'):
                return True
                
        # 檢查查詢參數中的檔案類型
        if 'pdf' in url_lower and any(param in url_lower for param in ['type=pdf', 'format=pdf', 'file=pdf']):
            return True
            
        # 檢查路徑中的PDF關鍵字
        if '/pdf/' in url_lower or '/document/' in url_lower:
            return True
            
        return False
        
    @staticmethod
    def extract_filename_from_url(url: str, fallback_text: str = "") -> str:
        """
        從URL中提取檔案名
        
        Args:
            url: PDF的URL
            fallback_text: 備用的檔案名文字
            
        Returns:
            str: 建議的檔案名
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # 從路徑中提取檔案名
            if path:
                filename = path.split('/')[-1]
                if filename and '.' in filename:
                    # 移除URL編碼
                    filename = unquote(filename)
                    # 清理檔案名
                    filename = URLHandler._clean_filename(filename)
                    if filename:
                        return filename
                        
            # 從查詢參數中提取
            if parsed.query:
                query_params = dict(parse_qsl(parsed.query))
                for key in ['file', 'filename', 'name']:
                    if key in query_params:
                        filename = query_params[key]
                        if filename and '.' in filename:
                            filename = unquote(filename)
                            filename = URLHandler._clean_filename(filename)
                            if filename:
                                return filename
                                
            # 使用備用文字
            if fallback_text:
                filename = URLHandler._clean_filename(fallback_text)
                if filename:
                    # 避免重複的.pdf擴展名
                    if not filename.lower().endswith('.pdf'):
                        return f"{filename}.pdf"
                    return filename
                    
            # 最後的備選方案
            return f"document_{int(time.time())}.pdf"
            
        except Exception as e:
            logger.error(f"提取檔案名失敗: {url}, 錯誤: {e}")
            return f"document_{int(time.time())}.pdf"
            
    @staticmethod
    def _clean_filename(filename: str) -> str:
        """
        清理檔案名，移除非法字符
        
        Args:
            filename: 原始檔案名
            
        Returns:
            str: 清理後的檔案名
        """
        if not filename:
            return ""
            
        # 移除或替換非法字符
        # Windows: < > : " | ? * \
        # Unix: /
        illegal_chars = r'[<>:"|?*\\/]'
        cleaned = re.sub(illegal_chars, '_', filename)
        
        # 移除多餘的空白和底線
        cleaned = re.sub(r'[\s_]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        
        # 處理連續的點號 (如 file..pdf -> file.pdf)
        cleaned = re.sub(r'\.+', '.', cleaned)
        
        # 限制長度
        if len(cleaned) > 200:
            cleaned = cleaned[:200]
            
        return cleaned
        
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def check_url_accessible(url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        檢查URL是否可訪問
        
        Args:
            url: 要檢查的URL
            timeout: 超時時間(秒)
            
        Returns:
            Dict: 包含檢查結果的字典
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            result = {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': response.headers.get('content-length'),
                'is_pdf': 'pdf' in response.headers.get('content-type', '').lower(),
                'final_url': response.url
            }
            
            logger.debug(f"URL檢查結果: {url} -> {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"URL檢查失敗: {url}, 錯誤: {e}")
            return {
                'accessible': False,
                'error': str(e),
                'status_code': None,
                'content_type': '',
                'content_length': None,
                'is_pdf': False,
                'final_url': url
            }
            
    @staticmethod
    def find_pdf_text_in_html(html_content: str) -> List[Dict[str, Any]]:
        """
        在HTML內容中搜尋PDF相關文字
        
        Args:
            html_content: HTML內容
            
        Returns:
            List[Dict]: 找到的PDF文字列表
        """
        pdf_texts = []
        
        try:
            # 搜尋包含"PDF"的連結文字
            pdf_link_pattern = r'<a[^>]*>([^<]*PDF[^<]*)</a>'
            pdf_links = re.findall(pdf_link_pattern, html_content, re.IGNORECASE)
            
            for text in pdf_links:
                pdf_texts.append({
                    'text': text.strip(),
                    'type': 'link_text',
                    'pattern': 'pdf_link'
                })
                
            # 搜尋包含"PDF"的按鈕文字
            pdf_button_pattern = r'<button[^>]*>([^<]*PDF[^<]*)</button>'
            pdf_buttons = re.findall(pdf_button_pattern, html_content, re.IGNORECASE)
            
            for text in pdf_buttons:
                pdf_texts.append({
                    'text': text.strip(),
                    'type': 'button_text',
                    'pattern': 'pdf_button'
                })
                
            # 搜尋包含"PDF"的其他元素文字
            pdf_element_pattern = r'<[^>]*>([^<]*PDF[^<]*)</[^>]*>'
            pdf_elements = re.findall(pdf_element_pattern, html_content, re.IGNORECASE)
            
            for text in pdf_elements:
                if text.strip() and 'PDF' in text.upper():
                    pdf_texts.append({
                        'text': text.strip(),
                        'type': 'element_text',
                        'pattern': 'pdf_element'
                    })
                    
            # 移除重複
            unique_texts = []
            seen_texts = set()
            for item in pdf_texts:
                if item['text'] not in seen_texts:
                    unique_texts.append(item)
                    seen_texts.add(item['text'])
                    
            logger.debug(f"在HTML中找到 {len(unique_texts)} 個PDF相關文字")
            return unique_texts
            
        except Exception as e:
            logger.error(f"搜尋PDF文字失敗: {e}")
            return []
            
    @staticmethod
    def build_search_urls(base_url: str, search_terms: List[str]) -> List[str]:
        """
        根據搜尋詞建立搜尋URL列表
        
        Args:
            base_url: 基礎URL
            search_terms: 搜尋詞列表
            
        Returns:
            List[str]: 搜尋URL列表
        """
        search_urls = []
        
        try:
            for term in search_terms:
                # 編碼搜尋詞
                encoded_term = quote(term)
                
                # 建立搜尋URL (根據常見的搜尋參數)
                search_params = [
                    f'q={encoded_term}',
                    f'search={encoded_term}',
                    f'keyword={encoded_term}',
                    f'query={encoded_term}'
                ]
                
                for param in search_params:
                    search_url = f"{base_url}?{param}"
                    search_urls.append(search_url)
                    
            logger.debug(f"建立 {len(search_urls)} 個搜尋URL")
            return search_urls
            
        except Exception as e:
            logger.error(f"建立搜尋URL失敗: {e}")
            return []

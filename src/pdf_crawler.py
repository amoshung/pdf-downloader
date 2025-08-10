"""
PDF爬蟲主控制器
整合所有組件，提供完整的PDF爬取和下載功能
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright_browser import PlaywrightBrowser
from url_handler import URLHandler
from file_manager import FileManager

logger = logging.getLogger(__name__)


class PDFCrawler:
    """PDF爬蟲主控制器"""
    
    def __init__(self, config: Dict[str, Any] = None, base_dir: str = None, max_concurrent_downloads: int = None, download_timeout: int = None):
        """
        初始化PDF爬蟲
        
        Args:
            config: 配置字典
            base_dir: 下載目錄基礎路徑 (向後相容)
            max_concurrent_downloads: 最大並發下載數量 (向後相容)
            download_timeout: 下載超時時間 (向後相容)
        """
        self.config = config or self._get_default_config()
        
        # 向後相容性處理
        if base_dir:
            self.config['output']['base_dir'] = base_dir
        if max_concurrent_downloads:
            self.config['download']['max_workers'] = max_concurrent_downloads
        if download_timeout:
            self.config['download']['timeout'] = download_timeout
            
        self.browser: Optional[PlaywrightBrowser] = None
        self.file_manager = FileManager(
            base_dir=self.config.get('output', {}).get('base_dir', './downloads'),
            create_subfolder=self.config.get('output', {}).get('create_subfolder', False),
            verify_ssl=self.config.get('network', {}).get('verify_ssl', False)
        )
        self.url_handler = URLHandler()
        
        # 設置日誌
        self._setup_logging()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            'download': {
                'max_workers': 8,
                'timeout': 30,
                'chunk_size': 8192,
                'retry_times': 3
            },
            'output': {
                'base_dir': './downloads',
                'create_subfolder': False,
                'overwrite_existing': False
            },
            'network': {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
            },
            'browser': {
                'headless': True,
                'slow_mo': 100
            }
        }
        
    def _setup_logging(self):
        """設置日誌配置"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    async def crawl_website(self, url: str, filter_option: str = "3", 
                           custom_keywords: List[str] = None) -> Dict[str, Any]:
        """
        爬取指定網站的PDF檔案
        
        Args:
            url: 目標網站URL
            filter_option: 過濾選項 ("1": 圖表開頭, "2": 自訂關鍵字, "3": 全部)
            custom_keywords: 自訂關鍵字列表
            
        Returns:
            Dict: 爬取結果
        """
        start_time = time.time()
        result = {
            'success': False,
            'url': url,
            'pdf_links_found': 0,
            'pdf_links_filtered': 0,
            'pdf_downloaded': 0,
            'filter_option': filter_option,
            'custom_keywords': custom_keywords,
            'errors': [],
            'downloads': [],
            'execution_time': 0
        }
        
        try:
            logger.info(f"開始爬取網站: {url}")
            logger.info(f"過濾選項: {filter_option}")
            if custom_keywords:
                logger.info(f"自訂關鍵字: {', '.join(custom_keywords)}")
            
            # 設置下載目錄
            self.file_manager.set_download_dir(url)
            
            # 啟動瀏覽器
            async with PlaywrightBrowser(
                headless=self.config.get('browser', {}).get('headless', True),
                slow_mo=self.config.get('browser', {}).get('slow_mo', 100),
                user_agent=self.config.get('network', {}).get('user_agent'),
                headers=self.config.get('network', {}).get('headers', {})
            ) as browser:
                self.browser = browser
                
                # 導航到目標頁面
                if not await browser.navigate_to(url):
                    raise RuntimeError(f"無法導航到頁面: {url}")
                
                # 等待頁面載入
                await browser.wait_for_page_load()
                
                # 額外等待時間，確保頁面完全加載
                import asyncio
                await asyncio.sleep(3)
                logger.info("額外等待3秒，確保頁面完全加載")
                
                # 搜尋PDF連結 - 使用與test_pdf_download.py相同的邏輯
                pdf_links = await browser.find_pdf_links()
                
                # 如果沒有找到PDF連結，嘗試使用更直接的方法
                if not pdf_links:
                    logger.info("使用直接方法搜尋PDF連結...")
                    pdf_links = await self._find_pdf_links_directly(browser)
                
                result['pdf_links_found'] = len(pdf_links)
                logger.info(f"找到 {len(pdf_links)} 個PDF連結")
                
                if not pdf_links:
                    result['success'] = True
                    result['execution_time'] = time.time() - start_time
                    return result
                
                # 應用過濾
                filtered_links = self._filter_pdf_links(pdf_links, filter_option, custom_keywords)
                result['pdf_links_filtered'] = len(filtered_links)
                
                if not filtered_links:
                    logger.info("過濾後沒有符合條件的PDF連結")
                    result['success'] = True
                    result['execution_time'] = time.time() - start_time
                    return result
                
                # 下載PDF檔案
                download_results = await self._download_pdfs(filtered_links, filter_option, custom_keywords)
                result['downloads'] = download_results
                result['pdf_downloaded'] = len([r for r in download_results if r['success']])
                
                result['success'] = True
                logger.info(f"成功下載 {result['pdf_downloaded']} 個PDF檔案")
                
        except Exception as e:
            error_msg = f"爬取過程中發生錯誤: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            
        finally:
            result['execution_time'] = time.time() - start_time
            if self.browser:
                await self.browser.close()
                
        return result
        
    async def _find_pdf_links_directly(self, browser) -> List[Dict[str, Any]]:
        """
        使用直接方法搜尋PDF連結，作為備用方案
        
        Args:
            browser: PlaywrightBrowser實例
            
        Returns:
            List: PDF連結列表
        """
        try:
            logger.info("使用直接方法搜尋PDF連結...")
            
            # 直接搜尋所有包含.pdf的連結
            pdf_links = []
            page = browser.page
            
            # 方法1: 搜尋href包含.pdf的連結
            pdf_ext_links = await page.query_selector_all('a[href*=".pdf"]')
            logger.info(f"找到 {len(pdf_ext_links)} 個.pdf連結")
            
            for link in pdf_ext_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href:
                        # 構建完整URL
                        from urllib.parse import urljoin
                        full_url = urljoin(page.url, href)
                        
                        # 提取檔名
                        filename = browser._extract_filename_from_url(full_url, text)
                        
                        pdf_links.append({
                            'url': full_url,
                            'text': text.strip() if text else '',
                            'filename': filename,
                            'type': 'direct_extension_match'
                        })
                        
                except Exception as e:
                    logger.warning(f"處理直接PDF連結時發生錯誤: {e}")
                    continue
            
            # 方法2: 搜尋包含"PDF"文字的連結
            pdf_text_links = await page.query_selector_all('a:has-text("PDF")')
            logger.info(f"找到 {len(pdf_text_links)} 個包含PDF文字的連結")
            
            for link in pdf_text_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href:
                        from urllib.parse import urljoin
                        full_url = urljoin(page.url, href)
                        filename = browser._extract_filename_from_url(full_url, text)
                        
                        # 檢查是否已經存在
                        if not any(pl['url'] == full_url for pl in pdf_links):
                            pdf_links.append({
                                'url': full_url,
                                'text': text.strip() if text else '',
                                'filename': filename,
                                'type': 'direct_text_match'
                            })
                        
                except Exception as e:
                    logger.warning(f"處理直接PDF文字連結時發生錯誤: {e}")
                    continue
            
            logger.info(f"直接方法找到 {len(pdf_links)} 個PDF連結")
            return pdf_links
            
        except Exception as e:
            logger.error(f"直接搜尋PDF連結時發生錯誤: {e}")
            return []
        
    def _filter_pdf_links(self, pdf_links: List[Dict[str, Any]], 
                          filter_option: str = "3", 
                          custom_keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        根據過濾選項過濾PDF連結
        
        Args:
            pdf_links: PDF連結列表
            filter_option: 過濾選項 ("1": 圖表開頭, "2": 自訂關鍵字, "3": 全部)
            custom_keywords: 自訂關鍵字列表
            
        Returns:
            List: 過濾後的PDF連結列表
        """
        if filter_option == "3":  # 全部下載
            return pdf_links
        
        filtered_links = []
        
        for link_info in pdf_links:
            filename = link_info.get('filename', '').lower()
            text = link_info.get('text', '').lower()
            
            # 檢查文件名和連結文字
            include_file = False
            
            if filter_option == "1":  # 只抓圖表開頭
                # 檢查文件名是否以圖、表、figure、table開頭
                if (filename.startswith(('圖', '表', 'figure', 'table')) or 
                    text.startswith(('圖', '表', 'figure', 'table'))):
                    include_file = True
                    
            elif filter_option == "2" and custom_keywords:  # 自訂關鍵字
                # 檢查文件名或連結文字是否包含關鍵字
                for keyword in custom_keywords:
                    if (keyword.lower() in filename or 
                        keyword.lower() in text):
                        include_file = True
                        break
            
            if include_file:
                filtered_links.append(link_info)
                logger.debug(f"包含文件: {filename} (符合過濾條件)")
            else:
                logger.debug(f"過濾文件: {filename} (不符合過濾條件)")
        
        logger.info(f"過濾完成: 原始 {len(pdf_links)} 個連結，過濾後 {len(filtered_links)} 個連結")
        return filtered_links

    async def _download_pdfs(self, pdf_links: List[Dict[str, Any]], 
                            filter_option: str = "3", 
                            custom_keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        下載PDF檔案列表
        
        Args:
            pdf_links: PDF連結列表
            filter_option: 過濾選項 ("1": 圖表開頭, "2": 自訂關鍵字, "3": 全部)
            custom_keywords: 自訂關鍵字列表
            
        Returns:
            List: 下載結果列表
        """
        download_results = []
        
        # 準備下載任務
        download_tasks = []
        for link_info in pdf_links:
            # 為所有找到的PDF連結添加valid標記
            if 'valid' not in link_info:
                link_info['valid'] = True
                
            if not link_info.get('valid', False):
                continue
                
            url = link_info['url']
            filename = link_info.get('filename', '')
            
            if not filename:
                filename = self.url_handler.extract_filename_from_url(url)
                
            # 檢查檔案是否已存在
            overwrite_existing = self.config.get('output', {}).get('overwrite_existing', False)
            if not overwrite_existing:
                if self.file_manager.check_file_exists(filename):
                    logger.info(f"檔案已存在，跳過: {filename}")
                    download_results.append({
                        'success': True,
                        'url': url,
                        'filename': filename,
                        'status': 'already_exists',
                        'message': '檔案已存在'
                    })
                    continue
                    
            download_tasks.append({
                'url': url,
                'filename': filename,
                'link_info': link_info
            })
            
        if not download_tasks:
            return download_results
            
        # 並發下載
        max_workers = self.config.get('download', {}).get('max_workers', 4)
        logger.info(f"開始並發下載，最大並發數: {max_workers}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交下載任務
            future_to_task = {
                executor.submit(self._download_single_pdf, task): task
                for task in download_tasks
            }
            
            # 處理完成的下載任務
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    download_results.append(result)
                except Exception as e:
                    error_result = {
                        'success': False,
                        'url': task['url'],
                        'filename': task['filename'],
                        'error_msg': str(e),
                        'status': 'failed'
                    }
                    download_results.append(error_result)
                    logger.error(f"下載失敗: {task['url']}, 錯誤: {e}")
                    
        return download_results
        
    def _download_single_pdf(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        下載單個PDF檔案
        
        Args:
            task: 下載任務
            
        Returns:
            Dict: 下載結果
        """
        url = task['url']
        filename = task['filename']
        
        try:
            logger.info(f"開始下載: {filename}")
            
            # 使用FileManager下載
            result = self.file_manager.download_file(
                url=url,
                filename=filename,
                chunk_size=self.config['download']['chunk_size']
            )
            
            if result['success']:
                logger.info(f"下載成功: {filename}")
                return {
                    'success': True,
                    'url': url,
                    'filename': filename,
                    'filepath': str(result['filepath']),
                    'size': result.get('size', 0),
                    'download_time': result.get('download_time', 0),
                    'status': 'completed'
                }
            else:
                logger.error(f"下載失敗: {filename}, 錯誤: {result.get('error', '未知錯誤')}")
                return {
                    'success': False,
                    'url': url,
                    'filename': filename,
                    'error_msg': result.get('error', '未知錯誤'),
                    'status': 'failed'
                }
                
        except Exception as e:
            logger.error(f"下載過程中發生異常: {filename}, 錯誤: {e}")
            return {
                'success': False,
                'url': url,
                'filename': filename,
                'error_msg': str(e),
                'status': 'failed'
            }
            
    def generate_report(self, result: Dict[str, Any]) -> str:
        """
        生成爬取結果報告
        
        Args:
            result: 爬取結果
            
        Returns:
            str: 報告內容
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("PDF爬蟲執行報告")
        report_lines.append("=" * 60)
        report_lines.append(f"目標網站: {result['url']}")
        report_lines.append(f"執行時間: {result['execution_time']:.2f} 秒")
        report_lines.append(f"執行狀態: {'成功' if result['success'] else '失敗'}")
        report_lines.append(f"發現PDF連結: {result['pdf_links_found']} 個")
        report_lines.append(f"成功下載: {result['pdf_downloaded']} 個")
        report_lines.append("")
        
        if result['downloads']:
            report_lines.append("下載詳情:")
            report_lines.append("-" * 40)
            for download in result['downloads']:
                status_icon = "[成功]" if download['success'] else "[失敗]"
                report_lines.append(f"{status_icon} {download['filename']}")
                if download['success']:
                    report_lines.append(f"    檔案路徑: {download.get('filepath', 'N/A')}")
                    report_lines.append(f"    檔案大小: {download.get('size', 0)} bytes")
                    report_lines.append(f"    下載時間: {download.get('download_time', 0):.2f} 秒")
                else:
                    report_lines.append(f"    錯誤訊息: {download.get('error_msg', 'N/A')}")
                report_lines.append("")
                
        if result['errors']:
            report_lines.append("錯誤詳情:")
            report_lines.append("-" * 40)
            for error in result['errors']:
                report_lines.append(f"[錯誤] {error}")
                
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
        
    def save_report(self, result: Dict[str, Any], output_path: str = None) -> str:
        """
        保存爬取結果報告
        
        Args:
            result: 爬取結果
            output_path: 輸出路徑
            
        Returns:
            str: 保存的檔案路徑
        """
        if not output_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"crawl_report_{timestamp}.txt"
            
        report_content = self.generate_report(result)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"報告已保存到: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"保存報告失敗: {e}")
            raise
            
    def _validate_url(self, url: str) -> bool:
        """
        驗證URL的有效性
        
        Args:
            url: 要驗證的URL
            
        Returns:
            bool: URL是否有效
        """
        try:
            if not url:
                return False
                
            # 檢查URL格式
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # 只允許 HTTP 和 HTTPS 協議
            if parsed.scheme not in ['http', 'https']:
                return False
                
            # 檢查URL長度
            if len(url) > 2048:
                return False
                
            return True
            
        except Exception:
            return False
        
    def _filter_valid_urls(self, urls: List[str]) -> List[str]:
        """
        過濾有效的URL列表
        
        Args:
            urls: 原始URL列表
            
        Returns:
            List[str]: 有效的URL列表
        """
        return [url for url in urls if self._validate_url(url)]

"""
Playwright瀏覽器管理模組
負責瀏覽器的啟動、頁面載入和基本操作
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from urllib.parse import urlparse, urljoin
import time

logger = logging.getLogger(__name__)


class PlaywrightBrowser:
    """Playwright瀏覽器管理類別"""
    
    def __init__(self, headless: bool = True, slow_mo: int = 100, user_agent: str = None, headers: Dict[str, str] = None):
        """
        初始化瀏覽器管理器
        
        Args:
            headless: 是否使用無頭模式
            slow_mo: 操作間隔時間(毫秒)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.user_agent = user_agent
        self.headers = headers or {}
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()
        
    async def start(self):
        """啟動瀏覽器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 啟動Chromium瀏覽器
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            
            # 建立瀏覽器上下文
            # 使用動態配置的 User-Agent
            user_agent = getattr(self, 'user_agent', None)
            if not user_agent:
                # 預設 User-Agent
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            self.context = await self.browser.new_context(
                user_agent=user_agent
            )
            
            # 建立新頁面
            self.page = await self.context.new_page()
            
            # 設置頁面超時
            self.page.set_default_timeout(30000)  # 30秒
            
            logger.info("Playwright瀏覽器啟動成功")
            
        except Exception as e:
            logger.error(f"啟動瀏覽器失敗: {e}")
            raise
            
    async def close(self):
        """關閉瀏覽器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("瀏覽器已關閉")
        except Exception as e:
            logger.error(f"關閉瀏覽器時發生錯誤: {e}")
            
    async def navigate_to(self, url: str) -> bool:
        """
        導航到指定URL
        
        Args:
            url: 目標URL
            
        Returns:
            bool: 導航是否成功
        """
        try:
            if not self.page:
                raise RuntimeError("瀏覽器頁面未初始化")
                
            logger.info(f"正在導航到: {url}")
            response = await self.page.goto(url, wait_until="networkidle")
            
            if response and response.ok:
                logger.info(f"成功載入頁面: {url}")
                return True
            else:
                logger.warning(f"頁面載入可能不完整: {url}")
                return False
                
        except Exception as e:
            logger.error(f"導航到 {url} 失敗: {e}")
            return False
            
    async def find_pdf_links(self) -> List[Dict[str, Any]]:
        """
        在頁面中搜尋PDF連結
        
        Returns:
            List[Dict]: PDF連結列表，每個包含url、text、filename等資訊
        """
        if not self.page:
            raise RuntimeError("瀏覽器頁面未初始化")
            
        pdf_links = []
        
        try:
            # 方法1: 搜尋包含"PDF"文字的連結
            pdf_text_links = await self.page.query_selector_all('a:has-text("PDF")')
            
            for link in pdf_text_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href:
                        full_url = urljoin(self.page.url, href)
                        filename = self._extract_filename_from_url(full_url, text)
                        
                        pdf_links.append({
                            'url': full_url,
                            'text': text.strip() if text else '',
                            'filename': filename,
                            'type': 'text_match'
                        })
                        
                except Exception as e:
                    logger.warning(f"處理PDF連結時發生錯誤: {e}")
                    continue
                    
            # 方法2: 搜尋href包含.pdf的連結
            pdf_ext_links = await self.page.query_selector_all('a[href*=".pdf"]')
            
            for link in pdf_ext_links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href:
                        full_url = urljoin(self.page.url, href)
                        filename = self._extract_filename_from_url(full_url, text)
                        
                        # 檢查是否已經存在
                        if not any(pl['url'] == full_url for pl in pdf_links):
                            pdf_links.append({
                                'url': full_url,
                                'text': text.strip() if text else '',
                                'filename': filename,
                                'type': 'extension_match'
                            })
                            
                except Exception as e:
                    logger.warning(f"處理PDF擴展名連結時發生錯誤: {e}")
                    continue
                    
            # 方法3: 搜尋包含"PDF"文字的按鈕或其他元素
            pdf_elements = await self.page.query_selector_all('*:has-text("PDF")')
            
            for element in pdf_elements:
                try:
                    # 檢查元素是否可點擊
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    
                    if tag_name in ['button', 'div', 'span']:
                        # 嘗試找到父級或相關的連結
                        parent_link = await element.query_selector('a')
                        if parent_link:
                            href = await parent_link.get_attribute('href')
                            if href:
                                full_url = urljoin(self.page.url, href)
                                text = await element.text_content()
                                filename = self._extract_filename_from_url(full_url, text)
                                
                                if not any(pl['url'] == full_url for pl in pdf_links):
                                    pdf_links.append({
                                        'url': full_url,
                                        'text': text.strip() if text else '',
                                        'filename': filename,
                                        'type': 'element_match'
                                    })
                                    
                except Exception as e:
                    logger.warning(f"處理PDF元素時發生錯誤: {e}")
                    continue
                    
            logger.info(f"找到 {len(pdf_links)} 個PDF連結")
            return pdf_links
            
        except Exception as e:
            logger.error(f"搜尋PDF連結時發生錯誤: {e}")
            return []
            
    async def click_pdf_link(self, link_info: Dict[str, Any]) -> bool:
        """
        點擊PDF連結
        
        Args:
            link_info: 連結資訊字典
            
        Returns:
            bool: 點擊是否成功
        """
        if not self.page:
            raise RuntimeError("瀏覽器頁面未初始化")
            
        try:
            # 找到對應的連結元素
            selector = f'a[href*="{link_info["url"].split("/")[-1]}"]'
            link_element = await self.page.query_selector(selector)
            
            if link_element:
                await link_element.click()
                logger.info(f"成功點擊PDF連結: {link_info['filename']}")
                return True
            else:
                logger.warning(f"找不到可點擊的PDF連結元素: {link_info['filename']}")
                return False
                
        except Exception as e:
            logger.error(f"點擊PDF連結失敗: {e}")
            return False
            
    def _extract_filename_from_url(self, url: str, text: str = "") -> str:
        """
        從URL和文字中提取檔案名
        
        Args:
            url: PDF的URL
            text: 連結文字
            
        Returns:
            str: 建議的檔案名
        """
        try:
            # 從URL路徑中提取檔案名
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # 如果路徑以.pdf結尾，提取檔案名
            if path.lower().endswith('.pdf'):
                filename = path.split('/')[-1]
                # 移除URL編碼
                import urllib.parse
                filename = urllib.parse.unquote(filename)
                return filename
                
            # 如果沒有.pdf擴展名，從文字中提取
            if text:
                # 清理文字，移除特殊字符
                import re
                clean_text = re.sub(r'[<>:"/\\|?*]', '_', text.strip())
                clean_text = re.sub(r'\s+', '_', clean_text)
                return f"{clean_text}.pdf"
                
            # 最後的備選方案
            return f"document_{int(time.time())}.pdf"
            
        except Exception as e:
            logger.warning(f"提取檔案名時發生錯誤: {e}")
            return f"document_{int(time.time())}.pdf"
            
    async def wait_for_page_load(self, timeout: int = 30000):
        """
        等待頁面載入完成
        
        Args:
            timeout: 超時時間(毫秒)
        """
        if not self.page:
            return
            
        try:
            # 首先等待DOM載入完成
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout)
            logger.info("DOM載入完成")
            
            # 然後等待網絡靜止，但使用更寬鬆的超時
            try:
                await self.page.wait_for_load_state('networkidle', timeout=15000)
                logger.info("網絡靜止，頁面完全載入")
            except Exception as e:
                logger.warning(f"等待網絡靜止超時，繼續執行: {e}")
                
            # 額外等待2秒，確保JavaScript執行完成
            await asyncio.sleep(2)
            logger.info("額外等待完成")
            
        except Exception as e:
            logger.warning(f"等待頁面載入超時: {e}")
            
    async def get_page_content(self) -> str:
        """
        獲取頁面HTML內容
        
        Returns:
            str: 頁面HTML內容
        """
        if not self.page:
            raise RuntimeError("瀏覽器頁面未初始化")
            
        try:
            content = await self.page.content()
            return content
        except Exception as e:
            logger.error(f"獲取頁面內容失敗: {e}")
            return ""
            
    async def take_screenshot(self, path: str = None) -> str:
        """
        截取頁面截圖
        
        Args:
            path: 截圖保存路徑
            
        Returns:
            str: 截圖檔案路徑
        """
        if not self.page:
            raise RuntimeError("瀏覽器頁面未初始化")
            
        try:
            if not path:
                path = f"screenshot_{int(time.time())}.png"
                
            await self.page.screenshot(path=path)
            logger.info(f"截圖已保存: {path}")
            return path
            
        except Exception as e:
            logger.error(f"截圖失敗: {e}")
            return ""

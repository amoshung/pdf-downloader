"""
檔案管理模組
負責檔案系統操作、下載管理和檔案處理
"""

import os
import shutil
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class FileManager:
    """檔案管理類別"""
    
    def __init__(self, base_dir: str = "./downloads", create_subfolder: bool = False, verify_ssl: bool = False):
        """
        初始化檔案管理器
        
        Args:
            base_dir: 下載目錄基礎路徑
            create_subfolder: 是否為每個網站建立子目錄
            verify_ssl: 是否驗證SSL證書
        """
        self.base_dir = Path(base_dir)
        self.create_subfolder = create_subfolder
        self.verify_ssl = verify_ssl
        self.download_dir = self.base_dir
        self.session = requests.Session()
        
        # 設置請求頭
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 建立下載目錄
        self._ensure_download_dir()
        
    def _ensure_download_dir(self):
        """確保下載目錄存在"""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"下載目錄已建立: {self.base_dir}")
        except Exception as e:
            logger.error(f"建立下載目錄失敗: {e}")
            raise
            
    def set_download_dir(self, url: str = None):
        """
        設置下載目錄
        
        Args:
            url: 網站URL，用於建立子目錄
        """
        if not self.create_subfolder or not url:
            self.download_dir = self.base_dir
            return
            
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # 清理域名，移除特殊字符
            import re
            clean_domain = re.sub(r'[<>:"|?*\\/]', '_', domain)
            clean_domain = re.sub(r'[^\w\-_.]', '_', clean_domain)
            
            # 建立子目錄
            sub_dir = self.base_dir / clean_domain
            sub_dir.mkdir(parents=True, exist_ok=True)
            self.download_dir = sub_dir
            
            logger.info(f"設置下載目錄: {self.download_dir}")
            
        except Exception as e:
            logger.warning(f"設置子目錄失敗，使用基礎目錄: {e}")
            self.download_dir = self.base_dir
            
    def _clean_filename(self, filename: str) -> str:
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
        import re
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
        
    def get_unique_filename(self, filename: str) -> str:
        """
        生成唯一的檔案名
        
        Args:
            filename: 原始檔案名
            
        Returns:
            str: 唯一的檔案名
        """
        try:
            file_path = self.download_dir / filename
            
            if not file_path.exists():
                return filename
                
            # 檔案已存在，添加數字後綴
            name, ext = os.path.splitext(filename)
            counter = 1
            
            while True:
                new_filename = f"{name}_{counter}{ext}"
                new_path = self.download_dir / new_filename
                
                if not new_path.exists():
                    return new_filename
                    
                counter += 1
                
        except Exception as e:
            logger.error(f"生成唯一檔案名失敗: {e}")
            return f"file_{int(time.time())}.pdf"
            
    def check_file_exists(self, filename: str) -> bool:
        """
        檢查檔案是否已存在
        
        Args:
            filename: 檔案名
            
        Returns:
            bool: 檔案是否存在
        """
        try:
            file_path = self.download_dir / filename
            return file_path.exists()
        except Exception as e:
            logger.error(f"檢查檔案存在性失敗: {e}")
            return False
            
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        獲取檔案資訊
        
        Args:
            filepath: 檔案路徑
            
        Returns:
            Dict: 檔案資訊字典
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return {}
                
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'path': str(file_path.absolute()),
                'exists': True
            }
            
        except Exception as e:
            logger.error(f"獲取檔案資訊失敗: {e}")
            return {}
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def download_file(self, url: str, filename: str, chunk_size: int = 8192) -> Dict[str, Any]:
        """
        下載單個檔案
        
        Args:
            url: 檔案URL
            filename: 本地檔案名
            chunk_size: 下載塊大小
            
        Returns:
            Dict: 下載結果
        """
        start_time = time.time()
        file_path = self.download_dir / filename
        
        try:
            # 檢查檔案是否已存在
            if file_path.exists():
                logger.info(f"檔案已存在，跳過下載: {filename}")
                return {
                    'success': True,
                    'filepath': str(file_path),
                    'size': file_path.stat().st_size,
                    'download_time': 0,
                    'message': '檔案已存在'
                }
                
            # 開始下載
            logger.info(f"開始下載: {url} -> {filename}")
            
            response = self.session.get(url, stream=True, timeout=30, verify=self.verify_ssl)
            response.raise_for_status()
            
            # 獲取檔案大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 使用tqdm顯示進度
            with open(file_path, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=filename,
                    leave=False
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
                            
            download_time = time.time() - start_time
            file_size = file_path.stat().st_size
            
            logger.info(f"下載完成: {filename} ({file_size} bytes, {download_time:.2f}s)")
            
            return {
                'success': True,
                'filepath': str(file_path),
                'size': file_size,
                'download_time': download_time,
                'message': '下載成功'
            }
            
        except Exception as e:
            logger.error(f"下載失敗: {url} -> {filename}, 錯誤: {e}")
            
            # 清理失敗的檔案
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
                    
            return {
                'success': False,
                'filepath': str(file_path),
                'size': 0,
                'download_time': time.time() - start_time,
                'error': str(e),
                'message': f'下載失敗: {e}'
            }
            
    def download_files_batch(self, file_list: List[Dict[str, Any]], max_workers: int = 4) -> List[Dict[str, Any]]:
        """
        批量下載檔案
        
        Args:
            file_list: 檔案列表，每個包含url和filename
            max_workers: 最大並發數
            
        Returns:
            List[Dict]: 下載結果列表
        """
        results = []
        
        try:
            logger.info(f"開始批量下載 {len(file_list)} 個檔案，並發數: {max_workers}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交下載任務
                future_to_file = {
                    executor.submit(self.download_file, item['url'], item['filename']): item
                    for item in file_list
                }
                
                # 處理完成的任務
                for future in as_completed(future_to_file):
                    file_info = future_to_file[future]
                    try:
                        result = future.result()
                        result['original_info'] = file_info
                        results.append(result)
                    except Exception as e:
                        logger.error(f"下載任務執行失敗: {file_info}, 錯誤: {e}")
                        results.append({
                            'success': False,
                            'filepath': '',
                            'size': 0,
                            'download_time': 0,
                            'error': str(e),
                            'message': f'任務執行失敗: {e}',
                            'original_info': file_info
                        })
                        
            # 統計結果
            success_count = sum(1 for r in results if r['success'])
            total_size = sum(r['size'] for r in results if r['success'])
            total_time = sum(r['download_time'] for r in results if r['success'])
            
            logger.info(f"批量下載完成: 成功 {success_count}/{len(file_list)}, "
                       f"總大小: {total_size} bytes, 總時間: {total_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"批量下載失敗: {e}")
            return []
            
    def calculate_file_hash(self, filepath: str, algorithm: str = 'md5') -> str:
        """
        計算檔案雜湊值
        
        Args:
            filepath: 檔案路徑
            algorithm: 雜湊算法 (md5, sha1, sha256)
            
        Returns:
            str: 雜湊值
        """
        try:
            hash_func = getattr(hashlib, algorithm.lower())
            hash_obj = hash_func()
            
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
                    
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"計算檔案雜湊值失敗: {filepath}, 錯誤: {e}")
            return ""
            
    def find_duplicate_files(self, directory: str = None) -> List[List[str]]:
        """
        尋找重複檔案
        
        Args:
            directory: 要檢查的目錄，預設為下載目錄
            
        Returns:
            List[List[str]]: 重複檔案組列表
        """
        if directory is None:
            directory = self.download_dir
            
        try:
            file_hashes = {}
            duplicate_groups = []
            
            # 遍歷目錄中的所有檔案
            for file_path in Path(directory).rglob('*'):
                if file_path.is_file():
                    file_hash = self.calculate_file_hash(str(file_path))
                    if file_hash:
                        if file_hash in file_hashes:
                            file_hashes[file_hash].append(str(file_path))
                        else:
                            file_hashes[file_hash] = [str(file_path)]
                            
            # 找出重複的檔案
            for file_hash, file_list in file_hashes.items():
                if len(file_list) > 1:
                    duplicate_groups.append(file_list)
                    
            logger.info(f"找到 {len(duplicate_groups)} 組重複檔案")
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"尋找重複檔案失敗: {e}")
            return []
            
    def cleanup_downloads(self, max_age_days: int = 30, min_size_mb: float = 0.1):
        """
        清理下載目錄
        
        Args:
            max_age_days: 最大保留天數
            min_size_mb: 最小檔案大小(MB)，小於此大小的檔案會被刪除
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            min_size_bytes = min_size_mb * 1024 * 1024
            
            deleted_count = 0
            deleted_size = 0
            
            for file_path in self.download_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        file_age = current_time - stat.st_mtime
                        file_size = stat.st_size
                        
                        # 檢查是否需要刪除
                        should_delete = False
                        
                        if file_age > max_age_seconds:
                            should_delete = True
                            reason = f"超過 {max_age_days} 天"
                        elif file_size < min_size_bytes:
                            should_delete = True
                            reason = f"小於 {min_size_mb}MB"
                            
                        if should_delete:
                            file_path.unlink()
                            deleted_count += 1
                            deleted_size += file_size
                            logger.debug(f"刪除檔案: {file_path.name} ({reason})")
                            
                    except Exception as e:
                        logger.warning(f"刪除檔案失敗: {file_path}, 錯誤: {e}")
                        
            logger.info(f"清理完成: 刪除 {deleted_count} 個檔案，"
                       f"釋放空間 {deleted_size / (1024*1024):.2f}MB")
                       
        except Exception as e:
            logger.error(f"清理下載目錄失敗: {e}")
            
    def get_download_stats(self) -> Dict[str, Any]:
        """
        獲取下載統計資訊
        
        Returns:
            Dict: 統計資訊字典
        """
        try:
            total_files = 0
            total_size = 0
            file_types = {}
            
            for file_path in self.download_dir.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
                    
                    # 統計檔案類型
                    ext = file_path.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'file_types': file_types,
                'download_dir': str(self.download_dir)
            }
            
        except Exception as e:
            logger.error(f"獲取下載統計失敗: {e}")
            return {}
            
    def create_backup(self, backup_dir: str = None) -> str:
        """
        建立下載目錄備份
        
        Args:
            backup_dir: 備份目錄路徑
            
        Returns:
            str: 備份檔案路徑
        """
        try:
            if backup_dir is None:
                backup_dir = f"backup_{int(time.time())}"
                
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 複製下載目錄
            shutil.copytree(self.download_dir, backup_path / self.download_dir.name, dirs_exist_ok=True)
            
            logger.info(f"備份完成: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"建立備份失敗: {e}")
            return ""

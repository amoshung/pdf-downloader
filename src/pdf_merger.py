"""
PDF合併模組
負責將多個PDF文件合併為一個文件
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


class PDFMerger:
    """PDF合併器"""
    
    def __init__(self, output_dir: str = "./downloads"):
        """
        初始化PDF合併器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def merge_pdfs(self, pdf_files: List[str], output_filename: str = None, delete_originals: bool = True) -> Dict[str, Any]:
        """
        合併多個PDF文件
        
        Args:
            pdf_files: PDF文件路徑列表
            output_filename: 輸出文件名（不含副檔名）
            delete_originals: 合併成功後是否刪除原始檔案
            
        Returns:
            Dict: 合併結果
        """
        if not pdf_files:
            return {
                'success': False,
                'error': '沒有PDF文件可以合併',
                'output_file': None
            }
        
        # 過濾有效的PDF文件
        valid_pdfs = []
        for pdf_file in pdf_files:
            pdf_path = Path(pdf_file)
            if pdf_path.exists() and pdf_path.suffix.lower() == '.pdf':
                valid_pdfs.append(pdf_file)
            else:
                logger.warning(f"跳過無效的PDF文件: {pdf_file}")
        
        if not valid_pdfs:
            return {
                'success': False,
                'error': '沒有找到有效的PDF文件',
                'output_file': None
            }
        
        # 設置輸出文件名
        if not output_filename:
            output_filename = "merged_pdfs"
        
        output_path = self.output_dir / f"{output_filename}.pdf"
        
        try:
            # 創建PDF寫入器
            pdf_writer = PdfWriter()
            total_pages = 0
            
            logger.info(f"開始合併 {len(valid_pdfs)} 個PDF文件...")
            
            # 逐個讀取並合併PDF
            for i, pdf_file in enumerate(valid_pdfs, 1):
                try:
                    logger.info(f"處理第 {i}/{len(valid_pdfs)} 個文件: {os.path.basename(pdf_file)}")
                    
                    with open(pdf_file, 'rb') as file:
                        pdf_reader = PdfReader(file)
                        
                        # 檢查PDF是否加密
                        if pdf_reader.is_encrypted:
                            logger.warning(f"PDF文件已加密，跳過: {pdf_file}")
                            continue
                        
                        # 添加所有頁面
                        for page_num in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_num]
                            pdf_writer.add_page(page)
                            total_pages += 1
                            
                except Exception as e:
                    logger.error(f"處理PDF文件時發生錯誤 {pdf_file}: {e}")
                    continue
            
            if total_pages == 0:
                return {
                    'success': False,
                    'error': '沒有成功讀取任何PDF頁面',
                    'output_file': None
                }
            
            # 寫入合併後的PDF
            logger.info(f"寫入合併後的PDF文件: {output_path}")
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            logger.info(f"PDF合併完成！總頁數: {total_pages}, 輸出文件: {output_path}")
            
            # 合併成功後，根據設定刪除原始檔案
            deleted_files = []
            if delete_originals:
                logger.info("開始刪除原始PDF檔案...")
                for pdf_file in valid_pdfs:
                    try:
                        pdf_path = Path(pdf_file)
                        if pdf_path.exists():
                            pdf_path.unlink()
                            deleted_files.append(pdf_file)
                            logger.info(f"已刪除原始檔案: {pdf_file}")
                    except Exception as e:
                        logger.warning(f"刪除原始檔案失敗 {pdf_file}: {e}")
                
                logger.info(f"成功刪除 {len(deleted_files)} 個原始PDF檔案")
            
            return {
                'success': True,
                'output_file': str(output_path),
                'total_pages': total_pages,
                'files_merged': len(valid_pdfs),
                'output_size_mb': output_path.stat().st_size / (1024 * 1024),
                'deleted_originals': delete_originals,
                'deleted_files': deleted_files
            }
            
        except Exception as e:
            error_msg = f"PDF合併過程中發生錯誤: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'output_file': None
            }
    
    def merge_pdfs_in_directory(self, directory: str, output_filename: str = None, 
                               file_filter: str = "3", custom_keywords: List[str] = None,
                               delete_originals: bool = True) -> Dict[str, Any]:
        """
        合併目錄中的所有PDF文件
        
        Args:
            directory: 目錄路徑
            output_filename: 輸出文件名（不含副檔名）
            file_filter: 文件過濾選項 ("1": 圖表開頭, "2": 自訂關鍵字, "3": 全部)
            custom_keywords: 自訂關鍵字列表
            delete_originals: 合併成功後是否刪除原始檔案
            
        Returns:
            Dict: 合併結果
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return {
                'success': False,
                'error': f'目錄不存在: {directory}',
                'output_file': None
            }
        
        # 收集PDF文件
        pdf_files = []
        for file_path in dir_path.rglob("*.pdf"):
            if file_path.is_file():
                filename = file_path.name.lower()
                
                # 根據過濾選項決定是否包含該文件
                include_file = True
                
                if file_filter == "1":  # 只抓圖表開頭
                    include_file = filename.startswith(('圖', '表', 'figure', 'table'))
                elif file_filter == "2" and custom_keywords:  # 自訂關鍵字
                    include_file = any(keyword.lower() in filename for keyword in custom_keywords)
                
                if include_file:
                    pdf_files.append(str(file_path))
        
        if not pdf_files:
            return {
                'success': False,
                'error': f'在目錄 {directory} 中沒有找到符合條件的PDF文件',
                'output_file': None
            }
        
        # 按文件名排序
        pdf_files.sort()
        
        logger.info(f"找到 {len(pdf_files)} 個符合條件的PDF文件")
        for pdf_file in pdf_files:
            logger.info(f"  - {os.path.basename(pdf_file)}")
        
        # 執行合併
        return self.merge_pdfs(pdf_files, output_filename, delete_originals)
    
    def get_merge_info(self, pdf_files: List[str]) -> Dict[str, Any]:
        """
        獲取PDF合併信息
        
        Args:
            pdf_files: PDF文件路徑列表
            
        Returns:
            Dict: 合併信息
        """
        total_size = 0
        total_pages = 0
        valid_files = 0
        
        for pdf_file in pdf_files:
            pdf_path = Path(pdf_file)
            if pdf_path.exists() and pdf_path.suffix.lower() == '.pdf':
                try:
                    with open(pdf_file, 'rb') as file:
                        pdf_reader = PdfReader(file)
                        if not pdf_reader.is_encrypted:
                            total_pages += len(pdf_reader.pages)
                            total_size += pdf_path.stat().st_size
                            valid_files += 1
                except Exception as e:
                    logger.warning(f"無法讀取PDF文件 {pdf_file}: {e}")
        
        return {
            'total_files': len(pdf_files),
            'valid_files': valid_files,
            'total_pages': total_pages,
            'total_size_mb': total_size / (1024 * 1024),
            'estimated_output_size_mb': total_size / (1024 * 1024) * 0.95  # 預估輸出大小
        }

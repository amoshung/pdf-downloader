#!/usr/bin/env python3
"""
法規PDF下載器 - 互動版本
自動下載法規網站上的所有PDF文件，或合併指定資料夾的PDF文件
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# 導入動態配置生成器
try:
    from src.dynamic_config import DynamicConfigGenerator, create_dynamic_config, hot_reload_config
    DYNAMIC_CONFIG_AVAILABLE = True
except ImportError:
    DYNAMIC_CONFIG_AVAILABLE = False
    print("⚠️  動態配置功能不可用，將使用靜態配置")

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_crawler import PDFCrawler
from file_manager import FileManager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crawler.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def print_banner():
    """顯示系統功能介紹"""
    print("=" * 60)
    print("🔍 法規PDF下載器 - 智能爬蟲系統")
    print("=" * 60)
    print()
    print("📋 系統功能：")
    print("   • 自動掃描法規網站，尋找所有PDF文件")
    print("   • 智能下載並組織文件到指定資料夾")
    print("   • 支援多線程下載，提高效率")
    print("   • 自動處理文件名和路徑")
    print("   • 詳細的日誌記錄和進度顯示")
    print("   • PDF文件合併功能")
    print()
    print("🎯 適用網站：")
    print("   • 全國法規資料庫 (law.moj.gov.tw)")
    print("   • 其他包含PDF連結的政府網站")
    print()
    print("💡 使用提示：")
    print("   • 建議使用完整的網址")
    print("   • 資料夾名稱建議使用英文或數字")
    print("   • 下載過程可能需要幾分鐘，請耐心等待")
    print()

def print_main_menu():
    """顯示主選單"""
    print("=" * 60)
    print("🎯 請選擇要執行的功能")
    print("=" * 60)
    print()
    print("1. 🌐 抓取網頁PDF")
    print("2. 📄 指定資料夾PDF合成單一檔案")
    if DYNAMIC_CONFIG_AVAILABLE:
        print("3. ⚙️  動態配置管理")
        print("4. ❌ 退出程式")
    else:
        print("3. ❌ 退出程式")
    print()

def get_main_choice():
    """獲取主選單選擇"""
    while True:
        if DYNAMIC_CONFIG_AVAILABLE:
            choice = input("請選擇功能 (1/2/3/4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            else:
                print("❌ 請輸入有效的選項 (1/2/3/4)")
        else:
            choice = input("請選擇功能 (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                return choice
            else:
                print("❌ 請輸入有效的選項 (1/2/3)")

def get_folder_path():
    """獲取資料夾路徑（絕對路徑或相對路徑）"""
    print("📁 請指定PDF資料夾路徑：")
    print("💡 提示：")
    print("   • 絕對路徑：例如 C:\\Users\\username\\Documents\\PDFs")
    print("   • 相對路徑：例如 downloads\\my_pdfs")
    print("   • 相對路徑會自動在專案根目錄的 downloads 資料夾下尋找")
    print()
    
    while True:
        folder_path = input("請輸入資料夾路徑: ").strip()
        if not folder_path:
            print("❌ 路徑不能為空")
            continue
            
        # 檢查是否為絕對路徑
        if os.path.isabs(folder_path):
            if os.path.exists(folder_path):
                return folder_path
            else:
                print(f"❌ 絕對路徑不存在: {folder_path}")
                continue
        else:
            # 相對路徑，在專案根目錄的 downloads 資料夾下尋找
            project_root = Path(__file__).parent
            full_path = project_root / "downloads" / folder_path
            
            if full_path.exists():
                return str(full_path)
            else:
                print(f"❌ 相對路徑不存在: {full_path}")
                print("💡 請確認路徑是否正確，或使用絕對路徑")
                continue

def manage_dynamic_config():
    """動態配置管理功能"""
    if not DYNAMIC_CONFIG_AVAILABLE:
        print("❌ 動態配置功能不可用")
        return
    
    print("=" * 60)
    print("⚙️  動態配置管理")
    print("=" * 60)
    print()
    print("1. 🔄 熱重載配置")
    print("2. 🎯 為特定網站生成配置")
    print("3. 📋 查看配置信息")
    print("4. 🎨 應用配置模板")
    print("5. ↩️  返回主選單")
    print()
    
    while True:
        choice = input("請選擇配置管理選項 (1-5): ").strip()
        
        if choice == "1":
            # 熱重載配置
            print("\n🔄 熱重載配置...")
            target_url = input("請輸入目標網站URL (可選): ").strip() or None
            try:
                new_config = hot_reload_config(target_url)
                print("✅ 配置熱重載成功！")
                print(f"📅 生成時間: {new_config.get('_dynamic_config', {}).get('generated_at', 'N/A')}")
                if target_url:
                    print(f"🌐 目標網站: {target_url}")
            except Exception as e:
                print(f"❌ 配置熱重載失敗: {e}")
        
        elif choice == "2":
            # 為特定網站生成配置
            print("\n🎯 為特定網站生成配置...")
            target_url = input("請輸入目標網站URL: ").strip()
            if not target_url:
                print("❌ URL不能為空")
                continue
            
            language = input("請選擇語言 (zh-TW/zh-CN/en-US/ja-JP, 預設: zh-TW): ").strip() or "zh-TW"
            browser_type = input("請選擇瀏覽器類型 (chrome/firefox/safari/edge, 預設: chrome): ").strip() or "chrome"
            
            try:
                config = create_dynamic_config(target_url, language, browser_type, save=True)
                print("✅ 配置生成成功！")
                print(f"🌐 目標網站: {target_url}")
                print(f"🌍 語言: {language}")
                print(f"🌐 瀏覽器: {browser_type}")
                print(f"📄 User-Agent: {config['network']['user_agent'][:50]}...")
            except Exception as e:
                print(f"❌ 配置生成失敗: {e}")
        
        elif choice == "3":
            # 查看配置信息
            print("\n📋 配置信息...")
            try:
                generator = DynamicConfigGenerator()
                info = generator.get_config_info()
                print(f"📁 配置文件路徑: {info['config_path']}")
                print(f"📊 配置文件大小: {info['config_size']} bytes")
                print(f"📦 備份文件數量: {info['backup_count']}")
                print(f"🕒 最後修改時間: {info['last_modified']}")
                print(f"📋 配置部分: {', '.join(info['sections'])}")
                
                if info['dynamic_config']:
                    print(f"🔄 動態配置信息:")
                    for key, value in info['dynamic_config'].items():
                        print(f"   • {key}: {value}")
            except Exception as e:
                print(f"❌ 獲取配置信息失敗: {e}")
        
        elif choice == "4":
            # 應用配置模板
            print("\n🎨 應用配置模板...")
            print("可用的模板:")
            print("1. minimal - 最小配置 (4個並發，30秒超時)")
            print("2. aggressive - 激進配置 (16個並發，60秒超時)")
            print("3. stealth - 隱身配置 (2個並發，45秒超時，慢速模式)")
            print()
            
            template_choice = input("請選擇模板 (1/2/3): ").strip()
            template_map = {'1': 'minimal', '2': 'aggressive', '3': 'stealth'}
            
            if template_choice in template_map:
                template_name = template_map[template_choice]
                try:
                    generator = DynamicConfigGenerator()
                    if generator.apply_config_template(template_name):
                        print(f"✅ 模板 '{template_name}' 應用成功！")
                    else:
                        print(f"❌ 模板 '{template_name}' 應用失敗")
                except Exception as e:
                    print(f"❌ 應用模板失敗: {e}")
            else:
                print("❌ 無效的模板選擇")
        
        elif choice == "5":
            print("↩️  返回主選單")
            break
        
        else:
            print("❌ 請輸入有效的選項 (1-5)")
        
        print("\n" + "=" * 40)
        input("按 Enter 繼續...")
        print("=" * 60)
        print("⚙️  動態配置管理")
        print("=" * 60)
        print()
        print("1. 🔄 熱重載配置")
        print("2. 🎯 為特定網站生成配置")
        print("3. 📋 查看配置信息")
        print("4. 🎨 應用配置模板")
        print("5. ↩️  返回主選單")
        print()


def merge_pdfs_from_folder():
    """從指定資料夾合併PDF文件"""
    print("=" * 60)
    print("📄 PDF文件合併功能")
    print("=" * 60)
    print()
    
    # 獲取資料夾路徑
    folder_path = get_folder_path()
    print(f"✅ 已選擇資料夾: {folder_path}")
    
    # 檢查資料夾中是否有PDF文件
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    if not pdf_files:
        print("❌ 指定資料夾中沒有找到PDF文件")
        return
    
    print(f"📊 找到 {len(pdf_files)} 個PDF文件")
    
    # 顯示PDF文件列表
    print("\n📋 PDF文件列表：")
    for i, pdf_file in enumerate(pdf_files, 1):
        file_size = pdf_file.stat().st_size / (1024 * 1024)  # MB
        print(f"   {i}. {pdf_file.name} ({file_size:.2f} MB)")
    
    print()
    
    # 獲取輸出文件名
    output_name = input("請輸入合併後的PDF文件名 (不含副檔名): ").strip()
    if not output_name:
        output_name = "merged_pdfs"
    
    # 確認合併
    print(f"\n📄 將合併 {len(pdf_files)} 個PDF文件為: {output_name}.pdf")
    confirm = input("確認開始合併? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 合併已取消")
        return
    
    # 詢問是否刪除原始檔案
    delete_originals = input("合併成功後是否要刪除原始PDF檔案? (y/n, 預設: y): ").strip().lower()
    delete_originals = delete_originals != 'n'  # 預設為是
    
    if delete_originals:
        print("⚠️  注意：合併成功後將刪除原始PDF檔案！")
        final_confirm = input("確認刪除原始檔案? (y/n): ").strip().lower()
        if final_confirm != 'y':
            delete_originals = False
            print("📁 原始檔案將被保留")
        else:
            print("🗑️  原始檔案將在合併成功後被刪除")
    else:
        print("📁 原始檔案將被保留")
    
    print("\n🚀 開始PDF合併...")
    print("=" * 60)
    
    try:
        # 導入PDF合併模組
        from src.pdf_merger import PDFMerger
        
        # 創建PDF合併器
        merger = PDFMerger(folder_path)
        
        # 執行合併
        merge_result = merger.merge_pdfs_in_directory(
            directory=folder_path,
            output_filename=output_name,
            file_filter="3",  # 全部合併
            custom_keywords=[],
            delete_originals=delete_originals
        )
        
        if merge_result['success']:
            print("✅ PDF合併成功！")
            print(f"📄 合併後文件: {merge_result['output_file']}")
            print(f"📊 總頁數: {merge_result['total_pages']}")
            print(f"🔗 合併文件數: {merge_result['files_merged']}")
            print(f"💾 文件大小: {merge_result['output_size_mb']:.2f} MB")
            
            # 顯示刪除原始檔案的結果
            if merge_result.get('deleted_originals', False):
                deleted_count = len(merge_result.get('deleted_files', []))
                print(f"🗑️ 已刪除原始檔案: {deleted_count} 個")
                if deleted_count > 0:
                    print("📝 刪除的原始檔案:")
                    for deleted_file in merge_result['deleted_files']:
                        print(f"   • {os.path.basename(deleted_file)}")
            else:
                print("📁 原始檔案已保留")
        else:
            print("❌ PDF合併失敗")
            print(f"錯誤信息: {merge_result['error']}")
            
    except ImportError:
        print("❌ 無法導入PDF合併模組，請確保已安裝PyPDF2")
        print("💡 請運行: pip install PyPDF2")
    except Exception as e:
        print(f"❌ PDF合併過程中發生錯誤: {e}")
        logger.error(f"PDF合併錯誤: {e}")

def get_user_input():
    """獲取用戶輸入"""
    print("=" * 60)
    print("📝 請輸入下載參數")
    print("=" * 60)
    print()
    
    # 獲取網址
    while True:
        url = input("🌐 請輸入要下載PDF的網址: ").strip()
        if url:
            if url.startswith(('http://', 'https://')):
                break
            else:
                print("❌ 請輸入完整的網址，包含 http:// 或 https://")
        else:
            print("❌ 網址不能為空")
    
    print()
    
    # 獲取資料夾名稱
    while True:
        folder_name = input("📁 請輸入下載資料夾名稱 (預設: auto_generated): ").strip()
        if not folder_name:
            folder_name = "auto_generated"
            print(f"✅ 使用預設資料夾名稱: {folder_name}")
            break
        elif folder_name.replace('_', '').replace('-', '').isalnum():
            break
        else:
            print("❌ 資料夾名稱只能包含字母、數字、底線(_)和連字號(-)")
    
    print()
    
    # 獲取檔案過濾選項
    print("🔍 檔案過濾選項：")
    print("   1. 只抓取圖、表開頭的檔名")
    print("   2. 自訂關鍵字過濾")
    print("   3. 全部下載")
    
    while True:
        filter_option = input("請選擇過濾方式 (1/2/3, 預設: 3): ").strip()
        if not filter_option:
            filter_option = "3"
            print("✅ 使用預設選項: 全部下載")
            break
        elif filter_option in ['1', '2', '3']:
            break
        else:
            print("❌ 請輸入有效的選項 (1/2/3)")
    
    # 如果選擇自訂關鍵字，獲取關鍵字
    custom_keywords = []
    if filter_option == "2":
        print()
        print("📝 自訂關鍵字設定：")
        print("💡 提示：可以輸入多個關鍵字，用逗號分隔")
        print("   例如：圖表,附表,附件,附錄")
        while True:
            keywords_input = input("請輸入關鍵字 (用逗號分隔): ").strip()
            if keywords_input:
                custom_keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
                if custom_keywords:
                    print(f"✅ 已設定關鍵字: {', '.join(custom_keywords)}")
                    break
                else:
                    print("❌ 關鍵字不能為空，請重新輸入")
            else:
                print("❌ 關鍵字不能為空，請重新輸入")
    
    print()
    
    # 獲取PDF合併選項
    print("📄 PDF合併選項：")
    merge_pdfs = input("下載完成後是否要合併所有PDF為一個檔案? (y/n, 預設: n): ").strip().lower()
    merge_pdfs = merge_pdfs == 'y'
    
    print()
    
    # 獲取其他選項
    print("⚙️ 下載選項：")
    verbose = input("是否顯示詳細日誌? (y/n, 預設: y): ").strip().lower()
    verbose = verbose != 'n'
    
    headless = input("是否使用無頭瀏覽器? (y/n, 預設: n): ").strip().lower()
    headless = headless == 'y'
    
    max_workers = input("同時下載數量 (1-10, 預設: 5): ").strip()
    try:
        max_workers = int(max_workers) if max_workers else 5
        max_workers = max(1, min(10, max_workers))
    except ValueError:
        max_workers = 5
    
    print()
    
    return {
        'url': url,
        'folder_name': folder_name,
        'filter_option': filter_option,
        'custom_keywords': custom_keywords,
        'merge_pdfs': merge_pdfs,
        'verbose': verbose,
        'headless': headless,
        'max_workers': max_workers
    }

def load_config() -> Dict[str, Any]:
    """載入配置文件"""
    config_path = Path('config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"載入配置文件失敗: {e}")
    
    # 預設配置
    return {
        "output": {
            "base_dir": "downloads"
        },
        "download": {
            "max_workers": 5,
            "chunk_size": 1024 * 1024,  # 1MB
            "timeout": 30,
            "retry_count": 3
        },
        "browser": {
            "headless": False,
            "slow_mo": 1000,
            "timeout": 30000
        }
    }

def merge_config_with_args(config: Dict[str, Any], user_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    將用戶輸入合併到配置中
    
    Args:
        config: 原始配置
        user_input: 用戶輸入參數
        
    Returns:
        Dict: 合併後的配置
    """
    # 深層複製配置
    merged_config = json.loads(json.dumps(config))
    
    # 設置預設值
    if 'output' not in merged_config:
        merged_config['output'] = {}
    if 'download' not in merged_config:
        merged_config['download'] = {}
    if 'browser' not in merged_config:
        merged_config['browser'] = {}
        
    # 合併用戶輸入
    merged_config['output']['base_dir'] = f"downloads/{user_input['folder_name']}"
    merged_config['output']['create_subfolder'] = False  # 避免自動創建網站域名子目錄
    merged_config['download']['max_workers'] = user_input['max_workers']
    merged_config['browser']['headless'] = user_input['headless']
    
    return merged_config

async def main():
    """主函數"""
    try:
        # 顯示主選單
        print_main_menu()
        
        # 獲取主選擇
        main_choice = get_main_choice()
        
        if main_choice == "1":
            # 顯示系統介紹
            print_banner()
            
            # 獲取用戶輸入
            user_input = get_user_input()
            
            # 確認下載參數
            print("=" * 60)
            print("📋 下載參數確認")
            print("=" * 60)
            print(f"🌐 目標網址: {user_input['url']}")
            print(f"📁 下載資料夾: {user_input['folder_name']}")
            print(f"🔍 檔案過濾: {'是' if user_input['filter_option'] != '3' else '否'}")
            if user_input['filter_option'] == "1":
                print("   • 過濾方式: 只抓取圖、表開頭的檔名")
            elif user_input['filter_option'] == "2":
                print(f"   • 過濾方式: 自訂關鍵字 ({', '.join(user_input['custom_keywords'])})")
            else:
                print("   • 過濾方式: 全部下載")
            print(f"📄 PDF合併: {'是' if user_input['merge_pdfs'] else '否'}")
            print(f"📊 同時下載數: {user_input['max_workers']}")
            print(f"🔍 詳細日誌: {'是' if user_input['verbose'] else '否'}")
            print(f"🌐 無頭瀏覽器: {'是' if user_input['headless'] else '否'}")
            print()
            
            confirm = input("確認開始下載? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ 下載已取消")
                return
            
            print()
            print("🚀 開始下載...")
            print("=" * 60)
            
            # 載入配置
            config = load_config()
            
            # 合併用戶輸入
            config = merge_config_with_args(config, user_input)
            
            # 設置日誌級別
            if user_input['verbose']:
                logging.getLogger().setLevel(logging.DEBUG)
            
            # 創建PDF爬蟲實例
            crawler = PDFCrawler(config)
            
            # 開始爬取和下載
            result = await crawler.crawl_website(
                user_input['url'], 
                user_input['filter_option'], 
                user_input['custom_keywords']
            )
            
            # 顯示結果
            print()
            print("=" * 60)
            print("📊 下載完成！")
            print("=" * 60)
            print(f"✅ 成功下載: {result.get('pdf_downloaded', 0)} 個PDF文件")
            print(f"🔗 找到連結: {result.get('pdf_links_found', 0)} 個")
            print(f"🔍 過濾後連結: {result.get('pdf_links_filtered', 0)} 個")
            print(f"📁 下載位置: {config['output']['base_dir']}")
            print(f"⏱️ 總耗時: {result.get('execution_time', 0):.2f} 秒")
            
            if result.get('errors'):
                print(f"⚠️ 錯誤數量: {len(result['errors'])}")
                for error in result['errors'][:5]:  # 只顯示前5個錯誤
                    print(f"   • {error}")
            
            # 如果用戶選擇合併PDF，執行合併
            if user_input['merge_pdfs'] and result.get('pdf_downloaded', 0) > 0:
                print()
                print("=" * 60)
                print("📄 開始PDF合併...")
                print("=" * 60)
                
                try:
                    # 導入PDF合併模組
                    from src.pdf_merger import PDFMerger
                    
                    # 創建PDF合併器
                    merger = PDFMerger(config['output']['base_dir'])
                    
                    # 執行合併
                    merge_result = merger.merge_pdfs_in_directory(
                        directory=config['output']['base_dir'],
                        output_filename=user_input['folder_name'],
                        file_filter=user_input['filter_option'],
                        custom_keywords=user_input['custom_keywords']
                    )
                    
                    if merge_result['success']:
                        print("✅ PDF合併成功！")
                        print(f"📄 合併後文件: {merge_result['output_file']}")
                        print(f"📊 總頁數: {merge_result['total_pages']}")
                        print(f"🔗 合併文件數: {merge_result['files_merged']}")
                        print(f"💾 文件大小: {merge_result['output_size_mb']:.2f} MB")
                        
                        # 顯示刪除原始檔案的結果
                        if merge_result.get('deleted_originals', False):
                            deleted_count = len(merge_result.get('deleted_files', []))
                            print(f"🗑️ 已刪除原始檔案: {deleted_count} 個")
                            if deleted_count > 0:
                                print("📝 刪除的原始檔案:")
                                for deleted_file in merge_result['deleted_files']:
                                    print(f"   • {os.path.basename(deleted_file)}")
                        else:
                            print("📁 原始檔案已保留")
                    else:
                        print("❌ PDF合併失敗")
                        print(f"錯誤信息: {merge_result['error']}")
                        
                except ImportError:
                    print("❌ 無法導入PDF合併模組，請確保已安裝PyPDF2")
                    print("💡 請運行: pip install PyPDF2")
                except Exception as e:
                    print(f"❌ PDF合併過程中發生錯誤: {e}")
            
            print()
            print("🎉 任務完成！請檢查下載資料夾。")
        
        elif main_choice == "2":
            # 執行PDF合併功能
            merge_pdfs_from_folder()
        
        elif main_choice == "3":
            if DYNAMIC_CONFIG_AVAILABLE:
                # 執行動態配置管理功能
                manage_dynamic_config()
            else:
                print("❌ 退出程式")
                return
        
        elif main_choice == "4":
            if DYNAMIC_CONFIG_AVAILABLE:
                print("❌ 退出程式")
                return
            else:
                print("❌ 無效選項")
        
    except KeyboardInterrupt:
        print("\n❌ 用戶中斷下載")
    except Exception as e:
        logger.error(f"下載過程中發生錯誤: {e}")
        print(f"❌ 下載失敗: {e}")
        print("💡 請檢查網址是否正確，或查看日誌文件獲取詳細信息")

if __name__ == "__main__":
    # 檢查是否在虛擬環境中
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  警告：建議在虛擬環境中運行此腳本")
        print("💡 請先啟動虛擬環境：")
        print("   Windows: .\\venv\\Scripts\\Activate.ps1")
        print("   Linux/Mac: source venv/bin/activate")
        print()
    
    # 運行主程序
    asyncio.run(main())

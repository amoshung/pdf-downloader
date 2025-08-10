"""
動態配置生成器
提供動態 User-Agent 生成、智能 Headers 生成和配置熱更新功能
"""

import random
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DynamicConfigGenerator:
    """動態配置生成器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config_backup_dir = Path("config_backups")
        self.config_backup_dir.mkdir(exist_ok=True)
        
        # User-Agent 模板庫
        self.user_agent_templates = {
            'chrome': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36'
            ],
            'firefox': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{version}) Gecko/20100101 Firefox/{version}',
                'Mozilla/5.0 (X11; Linux x86_64; rv:{version}) Gecko/20100101 Firefox/{version}'
            ],
            'safari': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'
            ],
            'edge': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36 Edg/{version}.0.0.0'
            ]
        }
        
        # 瀏覽器版本範圍
        self.browser_versions = {
            'chrome': range(100, 121),  # Chrome 100-120
            'firefox': range(100, 121),  # Firefox 100-120
            'safari': range(15, 18),     # Safari 15-17
            'edge': range(100, 121)      # Edge 100-120
        }
        
        # 語言和地區設定
        self.language_settings = {
            'zh-TW': {
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            },
            'zh-CN': {
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            },
            'en-US': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            },
            'ja-JP': {
                'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            }
        }
        
        # 網站特定的配置模板
        self.site_specific_configs = {
            'law.moj.gov.tw': {
                'user_agent_preference': 'chrome',
                'language': 'zh-TW',
                'custom_headers': {
                    'Referer': 'https://law.moj.gov.tw/',
                    'Cache-Control': 'no-cache'
                }
            },
            'www.cec.gov.tw': {
                'user_agent_preference': 'chrome',
                'language': 'zh-TW',
                'custom_headers': {
                    'Referer': 'https://www.cec.gov.tw/',
                    'Cache-Control': 'no-cache'
                }
            }
        }
    
    def generate_random_user_agent(self, browser_type: str = None) -> str:
        """
        生成隨機 User-Agent
        
        Args:
            browser_type: 瀏覽器類型 (chrome, firefox, safari, edge)
            
        Returns:
            str: 隨機生成的 User-Agent
        """
        if browser_type is None:
            browser_type = random.choice(list(self.user_agent_templates.keys()))
        
        if browser_type not in self.user_agent_templates:
            browser_type = 'chrome'
        
        template = random.choice(self.user_agent_templates[browser_type])
        version = random.choice(list(self.browser_versions[browser_type]))
        
        return template.format(version=version)
    
    def generate_smart_headers(self, target_url: str = None, language: str = None) -> Dict[str, str]:
        """
        生成智能 HTTP Headers
        
        Args:
            target_url: 目標網站URL
            language: 語言偏好
            
        Returns:
            Dict[str, str]: 生成的 Headers
        """
        # 檢測目標網站
        site_config = None
        if target_url:
            for domain, config in self.site_specific_configs.items():
                if domain in target_url:
                    site_config = config
                    break
        
        # 選擇語言
        if language is None:
            if site_config and 'language' in site_config:
                language = site_config['language']
            else:
                language = 'zh-TW'  # 預設繁體中文
        
        # 基礎 Headers
        headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        # 添加語言相關 Headers
        if language in self.language_settings:
            headers.update(self.language_settings[language])
        
        # 添加網站特定 Headers
        if site_config and 'custom_headers' in site_config:
            headers.update(site_config['custom_headers'])
        
        # 隨機化一些 Headers
        headers['User-Agent'] = self.generate_random_user_agent(
            site_config.get('user_agent_preference') if site_config else None
        )
        
        return headers
    
    def generate_dynamic_config(self, target_url: str = None, 
                               language: str = None,
                               browser_type: str = None) -> Dict[str, Any]:
        """
        生成完整的動態配置
        
        Args:
            target_url: 目標網站URL
            language: 語言偏好
            browser_type: 瀏覽器類型偏好
            
        Returns:
            Dict[str, Any]: 完整的動態配置
        """
        # 讀取基礎配置
        base_config = self.load_config()
        
        # 生成動態部分
        dynamic_network = {
            'user_agent': self.generate_random_user_agent(browser_type),
            'verify_ssl': base_config.get('network', {}).get('verify_ssl', False),
            'headers': self.generate_smart_headers(target_url, language)
        }
        
        # 更新配置
        if 'network' not in base_config:
            base_config['network'] = {}
        
        base_config['network'].update(dynamic_network)
        
        # 添加動態配置元數據
        base_config['_dynamic_config'] = {
            'generated_at': datetime.now().isoformat(),
            'target_url': target_url,
            'language': language,
            'browser_type': browser_type,
            'version': '1.0.0'
        }
        
        return base_config
    
    def load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any], backup: bool = True) -> bool:
        """
        保存配置文件
        
        Args:
            config: 要保存的配置
            backup: 是否創建備份
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 創建備份
            if backup and self.config_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.config_backup_dir / f"config_backup_{timestamp}.json"
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_config, f, indent=2, ensure_ascii=False)
                logger.info(f"配置備份已創建: {backup_path}")
            
            # 保存新配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失敗: {e}")
            return False
    
    def update_config_section(self, section: str, updates: Dict[str, Any], 
                            backup: bool = True) -> bool:
        """
        更新配置文件的特定部分
        
        Args:
            section: 要更新的配置部分
            updates: 更新的內容
            backup: 是否創建備份
            
        Returns:
            bool: 更新是否成功
        """
        try:
            config = self.load_config()
            
            if section not in config:
                config[section] = {}
            
            config[section].update(updates)
            
            return self.save_config(config, backup)
            
        except Exception as e:
            logger.error(f"更新配置部分失敗: {e}")
            return False
    
    def hot_reload_config(self, target_url: str = None) -> Dict[str, Any]:
        """
        熱重載配置（運行時動態更新）
        
        Args:
            target_url: 目標網站URL
            
        Returns:
            Dict[str, Any]: 新的配置
        """
        logger.info("開始熱重載配置...")
        
        # 生成新的動態配置
        new_config = self.generate_dynamic_config(target_url)
        
        # 保存配置
        if self.save_config(new_config, backup=True):
            logger.info("配置熱重載成功")
        else:
            logger.warning("配置熱重載失敗，使用內存配置")
        
        return new_config
    
    def get_config_template(self, template_name: str) -> Dict[str, Any]:
        """
        獲取預定義的配置模板
        
        Args:
            template_name: 模板名稱
            
        Returns:
            Dict[str, Any]: 配置模板
        """
        templates = {
            'minimal': {
                'download': {'max_workers': 4, 'timeout': 30},
                'output': {'base_dir': './downloads', 'create_subfolder': False},
                'network': {'verify_ssl': False},
                'browser': {'headless': True}
            },
            'aggressive': {
                'download': {'max_workers': 16, 'timeout': 60},
                'output': {'base_dir': './downloads', 'create_subfolder': False},
                'network': {'verify_ssl': False},
                'browser': {'headless': True, 'slow_mo': 0}
            },
            'stealth': {
                'download': {'max_workers': 2, 'timeout': 45},
                'output': {'base_dir': './downloads', 'create_subfolder': False},
                'network': {'verify_ssl': True},
                'browser': {'headless': False, 'slow_mo': 2000}
            }
        }
        
        return templates.get(template_name, templates['minimal'])
    
    def apply_config_template(self, template_name: str, backup: bool = True) -> bool:
        """
        應用配置模板
        
        Args:
            template_name: 模板名稱
            backup: 是否創建備份
            
        Returns:
            bool: 應用是否成功
        """
        try:
            template = self.get_config_template(template_name)
            current_config = self.load_config()
            
            # 合併模板和當前配置
            for section, settings in template.items():
                if section not in current_config:
                    current_config[section] = {}
                current_config[section].update(settings)
            
            return self.save_config(current_config, backup)
            
        except Exception as e:
            logger.error(f"應用配置模板失敗: {e}")
            return False
    
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
                'verify_ssl': False
            },
            'browser': {
                'headless': True,
                'slow_mo': 1000
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
    
    def get_config_info(self) -> Dict[str, Any]:
        """獲取配置信息"""
        config = self.load_config()
        
        info = {
            'config_path': str(self.config_path),
            'config_size': self.config_path.stat().st_size if self.config_path.exists() else 0,
            'backup_count': len(list(self.config_backup_dir.glob('config_backup_*.json'))),
            'last_modified': datetime.fromtimestamp(
                self.config_path.stat().st_mtime
            ).isoformat() if self.config_path.exists() else None,
            'sections': list(config.keys()),
            'dynamic_config': config.get('_dynamic_config', {})
        }
        
        return info


# 便捷函數
def create_dynamic_config(target_url: str = None, 
                         language: str = None,
                         browser_type: str = None,
                         save: bool = True) -> Dict[str, Any]:
    """
    創建動態配置的便捷函數
    
    Args:
        target_url: 目標網站URL
        language: 語言偏好
        browser_type: 瀏覽器類型
        save: 是否保存到文件
        
    Returns:
        Dict[str, Any]: 生成的配置
    """
    generator = DynamicConfigGenerator()
    config = generator.generate_dynamic_config(target_url, language, browser_type)
    
    if save:
        generator.save_config(config)
    
    return config


def hot_reload_config(target_url: str = None) -> Dict[str, Any]:
    """
    熱重載配置的便捷函數
    
    Args:
        target_url: 目標網站URL
        
    Returns:
        Dict[str, Any]: 新的配置
    """
    generator = DynamicConfigGenerator()
    return generator.hot_reload_config(target_url)


if __name__ == "__main__":
    # 測試代碼
    logging.basicConfig(level=logging.INFO)
    
    generator = DynamicConfigGenerator()
    
    # 測試動態配置生成
    print("=== 測試動態配置生成 ===")
    config = generator.generate_dynamic_config(
        target_url="https://law.moj.gov.tw/",
        language="zh-TW",
        browser_type="chrome"
    )
    
    print(f"生成的 User-Agent: {config['network']['user_agent']}")
    print(f"生成的 Headers: {json.dumps(config['network']['headers'], indent=2, ensure_ascii=False)}")
    
    # 測試配置模板
    print("\n=== 測試配置模板 ===")
    templates = ['minimal', 'aggressive', 'stealth']
    for template in templates:
        print(f"\n{template} 模板:")
        template_config = generator.get_config_template(template)
        print(json.dumps(template_config, indent=2, ensure_ascii=False))
    
    # 測試配置信息
    print("\n=== 配置信息 ===")
    info = generator.get_config_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))

# src/plugins/help/styles.py
from typing import Dict, Optional
import pillowmd
from pathlib import Path
import yaml
from .config import HelpConfig, CONFIG_FILE_PATH


def load_config() -> HelpConfig:
    """加载配置文件"""
    print(f"尝试加载配置文件: {CONFIG_FILE_PATH}")
    print(f"配置文件是否存在: {CONFIG_FILE_PATH.exists()}")
    
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            print(f"加载的配置数据: {config_data}")
            result = HelpConfig(**(config_data or {}))
            print(f"解析后的配置: default_style={result.default_style}, enable_custom_style_loading={result.enable_custom_style_loading}")
            return result
        except Exception as e:
            print(f"警告：无法加载配置文件 {CONFIG_FILE_PATH}: {e}")
    
    # 返回默认配置
    print("使用默认配置")
    return HelpConfig()


def load_custom_styles(config: HelpConfig) -> Dict[str, object]:
    """根据配置加载自定义样式"""
    print(f"加载样式，配置: default_style={config.default_style}")
    
    styles = {
        "style1": pillowmd.SampleStyles.STYLE1,
        "style2": pillowmd.SampleStyles.STYLE2,
        "style3": pillowmd.SampleStyles.STYLE3,
        "style4": pillowmd.SampleStyles.STYLE4,
        "style5": pillowmd.SampleStyles.STYLE5,
        "unicorn_sugar": pillowmd.SampleStyles.STYLE1,  # 独角兽Sugar风格，可爱系
        "unicorn_gif": pillowmd.SampleStyles.STYLE2,     # 独角兽Suagar-GIF风格，GIF示例
        "function_bg": pillowmd.SampleStyles.STYLE3,     # 函数绘制背景示例
        "simple_beige": pillowmd.SampleStyles.STYLE4,    # 朴素米黄风格
        "retro": pillowmd.SampleStyles.STYLE5,           # 最朴素的复古风格
        "default": pillowmd.MdStyle()                    # 默认样式
    }
    
    print(f"可用样式: {list(styles.keys())}")
    
    # 如果启用自定义样式加载且有配置的自定义样式
    if config.enable_custom_style_loading and config.custom_styles:
        for style_config in config.custom_styles:
            try:
                # 尝试加载自定义样式
                style_path = Path(style_config.path).resolve()
                if style_path.exists():
                    custom_style = pillowmd.LoadMarkdownStyles(style_path)
                    styles[style_config.name] = custom_style
                else:
                    print(f"警告：样式路径不存在 '{style_path}'")
            except Exception as e:
                # 如果加载失败，记录错误但不中断程序
                print(f"警告：无法加载样式 '{style_config.name}' 从路径 '{style_config.path}': {e}")
    
    return styles


def get_default_style(config: HelpConfig) -> str:
    """获取默认样式名称"""
    print(f"获取默认样式名称: {config.default_style}")
    return config.default_style
# src/plugins/help/config.py
from pathlib import Path

from pydantic import BaseModel


class StyleConfig(BaseModel):
    """样式配置"""

    name: str
    path: str


class HelpConfig(BaseModel):
    """帮助插件配置"""

    default_style: str = "default"
    custom_styles: list[StyleConfig] = []
    enable_custom_style_loading: bool = True
    ignored_plugins: list[str] = []  # 添加忽略插件列表


# 默认配置实例
DEFAULT_CONFIG = HelpConfig()

# 配置文件路径
CONFIG_FILE_PATH = Path(__file__).parent / "config.yaml"

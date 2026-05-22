#!/usr/bin/env python3
"""
一键切换 ZerolanLiveRobot 的 LLM 配置。

用法：
    python switch_llm.py xiaomi        切换到小米 MiMo
    python switch_llm.py kimi          切换到 Kimi 标准版
    python switch_llm.py kimi-coding   切换到 Kimi Coding
    python switch_llm.py deepseek      切换到 DeepSeek
    python switch_llm.py doubao        切换到豆包
    python switch_llm.py glm           切换到智谱 GLM
    python switch_llm.py --show        显示当前配置

配置项说明：
    - api_key      : API 密钥（从 secrets.yaml 读取，不入代码）
    - model_id     : 模型标识
    - predict_url  : 预测接口地址
    - stream_predict_url : 流式预测接口地址
    - openai_format : 是否使用 OpenAI 兼容格式

注意：
    - 切换前会自动备份当前配置到 ./resources/config.yaml.bak.<时间戳>
    - 切换后需要重启 ZerolanLiveRobot 才能生效
    - API Key 存放在 ./resources/secrets.yaml（已被 git 忽略）
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "resources" / "config.yaml"
SECRETS_PATH = Path(__file__).parent / "resources" / "secrets.yaml"

# ============================================================
# 预设配置：只放公开信息，api_key 从 secrets.yaml 读取
# ============================================================
PRESETS = {
    "xiaomi": {
        "api_key": "",
        "model_id": "mimo-v2.5",
        "predict_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "stream_predict_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "openai_format": True,
    },
    "xiaomi-pro": {
        "api_key": "",
        "model_id": "mimo-v2.5-pro",
        "predict_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "stream_predict_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "openai_format": True,
    },
    "kimi": {
        "api_key": "",
        "model_id": "moonshot-v1-8k",
        "predict_url": "https://api.moonshot.cn/v1",
        "stream_predict_url": "https://api.moonshot.cn/v1",
        "openai_format": True,
    },
    "kimi-coding": {
        "api_key": "",
        "model_id": "kimi-for-coding",
        "predict_url": "https://api.kimi.com/coding/v1",
        "stream_predict_url": "https://api.kimi.com/coding/v1",
        "openai_format": True,
    },
    "deepseek": {
        "api_key": "",
        "model_id": "deepseek-chat",
        "predict_url": "https://api.deepseek.com/v1",
        "stream_predict_url": "https://api.deepseek.com/v1",
        "openai_format": True,
    },
    "doubao": {
        "api_key": "",
        "model_id": "doubao-seed-1-6-flash-250715",
        "predict_url": "https://ark.cn-beijing.volces.com/api/v3",
        "stream_predict_url": "https://ark.cn-beijing.volces.com/api/v3",
        "openai_format": True,
    },
    "glm": {
        "api_key": "",
        "model_id": "glm-4.6v-flash",
        "predict_url": "https://open.bigmodel.cn/api/paas/v4",
        "stream_predict_url": "https://open.bigmodel.cn/api/paas/v4",
        "openai_format": True,
    },
}

# ANSI 颜色
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_ok(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")


def print_warn(msg: str):
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def print_err(msg: str):
    print(f"{RED}[ERR]{RESET} {msg}")


def print_info(msg: str):
    print(f"{CYAN}[INFO]{RESET} {msg}")


def load_secrets() -> dict:
    """从 secrets.yaml 读取 API Key，覆盖 PRESETS"""
    if not SECRETS_PATH.exists():
        return {}
    try:
        with open(SECRETS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def merge_secrets():
    """用 secrets.yaml 中的 api_key 覆盖 PRESETS"""
    secrets = load_secrets()
    for provider, cfg in secrets.items():
        if provider in PRESETS and isinstance(cfg, dict):
            key = cfg.get("api_key", "")
            if key:
                PRESETS[provider]["api_key"] = key


def backup_config():
    """备份当前配置文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = CONFIG_PATH.with_suffix(f".yaml.bak.{timestamp}")
    shutil.copy2(CONFIG_PATH, backup_path)
    print_info(f"已备份配置到: {backup_path}")
    return backup_path


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def show_current(cfg: dict):
    llm = cfg.get("pipeline", {}).get("llm", {})
    print_info("当前 LLM 配置:")
    print(f"  model_id : {llm.get('model_id', 'N/A')}")
    print(f"  predict_url : {llm.get('predict_url', 'N/A')}")
    print(f"  openai_format : {llm.get('openai_format', 'N/A')}")
    key = llm.get("api_key", "")
    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "(empty)"
    print(f"  api_key : {masked}")


def switch(provider: str):
    provider = provider.lower()
    if provider not in PRESETS:
        print_err(f"不支持的提供商: {provider}")
        print_info(f"可用选项: {', '.join(PRESETS.keys())}")
        sys.exit(1)

    if not CONFIG_PATH.exists():
        print_err(f"配置文件不存在: {CONFIG_PATH}")
        print_warn("请先运行 `python main.py` 生成默认配置")
        sys.exit(1)

    # 先加载 secrets，覆盖 PRESETS 中的 api_key
    merge_secrets()

    preset = PRESETS[provider]
    cfg = load_config()

    show_current(cfg)
    print()

    # 检查 api_key 是否为空
    if not preset["api_key"]:
        print_warn(f"[{provider}] 的 api_key 为空！")
        print_info(f"请填写 {SECRETS_PATH} 中对应提供商的 api_key")

    backup_config()

    llm = cfg.setdefault("pipeline", {}).setdefault("llm", {})
    llm["api_key"] = preset["api_key"]
    llm["model_id"] = preset["model_id"]
    llm["predict_url"] = preset["predict_url"]
    llm["stream_predict_url"] = preset["stream_predict_url"]
    llm["openai_format"] = preset["openai_format"]

    save_config(cfg)

    print_ok(f"已切换至 [{provider}]")
    print_info("新配置:")
    print(f"  model_id : {preset['model_id']}")
    print(f"  predict_url : {preset['predict_url']}")
    print()
    print_warn("请重启 ZerolanLiveRobot 使配置生效！")
    print_info("启动命令: .\\start_all.ps1")


def main():
    parser = argparse.ArgumentParser(
        description="一键切换 ZerolanLiveRobot 的 LLM 配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "示例:",
            "  python switch_llm.py xiaomi",
            "  python switch_llm.py kimi-coding",
            "  python switch_llm.py deepseek",
            "  python switch_llm.py glm",
            "  python switch_llm.py --show",
        ])
    )
    parser.add_argument(
        "provider",
        nargs="?",
        help="目标 LLM 提供商 (xiaomi/xiaomi-pro/kimi/kimi-coding/deepseek/doubao/glm)"
    )
    parser.add_argument(
        "--show", "-s",
        action="store_true",
        help="仅显示当前配置，不做切换"
    )

    args = parser.parse_args()

    if args.show:
        cfg = load_config()
        show_current(cfg)
        return

    if not args.provider:
        parser.print_help()
        sys.exit(1)

    switch(args.provider)


if __name__ == "__main__":
    main()

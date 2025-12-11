import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# 初期設定（config.json が存在しない場合に使われる）
DEFAULT_CONFIG = {
    "mode": "個人",            # 「個人」 or 「全体」
    "listener_only": False,    # 聞くだけモード
}

def load_config():
    """設定ファイルを読み込む（なければ作成してデフォルトを返す）"""
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # ファイル破損時も初期化
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config: dict):
    """設定を保存する"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

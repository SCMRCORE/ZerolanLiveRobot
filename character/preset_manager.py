import os
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

from character.config import CharacterPreset, CharacterConfig


class CharacterPresetManager:
    _instance: Optional['CharacterPresetManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, characters_dir: str = "resources/characters"):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._characters_dir = characters_dir
        self._presets: dict[str, CharacterPreset] = {}
        self._initialized = True
    
    def get_preset_path(self, preset_name: str) -> Path:
        return Path(self._characters_dir) / f"{preset_name}.yaml"
    
    def list_presets(self) -> list[str]:
        characters_path = Path(self._characters_dir)
        if not characters_path.exists():
            logger.warning(f"Characters directory not found: {characters_path}")
            return []
        
        presets = []
        for file in characters_path.glob("*.yaml"):
            presets.append(file.stem)
        return presets
    
    def load_preset(self, preset_name: str) -> Optional[CharacterPreset]:
        if preset_name in self._presets:
            return self._presets[preset_name]
        
        preset_path = self.get_preset_path(preset_name)
        if not preset_path.exists():
            logger.error(f"Preset file not found: {preset_path}")
            return None
        
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            preset = CharacterPreset(**data)
            self._presets[preset_name] = preset
            logger.info(f"Loaded character preset: {preset_name}")
            return preset
        except Exception as e:
            logger.error(f"Failed to load preset {preset_name}: {e}")
            return None
    
    def apply_preset(self, preset_name: str, base_config: Optional[CharacterConfig] = None) -> CharacterConfig:
        preset = self.load_preset(preset_name)
        if preset is None:
            logger.warning(f"Using default character config due to preset load failure")
            return base_config or CharacterConfig()
        
        config = CharacterConfig(
            bot_name=preset.bot_name,
            live2d=preset.live2d,
            chat=preset.chat,
            speech=preset.speech
        )
        
        if base_config:
            if base_config.bot_name != "<YOUR_BOT_NAME>":
                config.bot_name = base_config.bot_name
        
        logger.info(f"Applied character preset: {preset_name} -> {config.bot_name}")
        return config


_preset_manager: Optional[CharacterPresetManager] = None


def get_preset_manager(characters_dir: str = "resources/characters") -> CharacterPresetManager:
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = CharacterPresetManager(characters_dir)
    return _preset_manager

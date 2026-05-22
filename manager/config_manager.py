import os
from pathlib import Path

import yaml
from loguru import logger
from typeguard import typechecked

from common.generator.config_gen import ConfigFileGenerator
from config import ZerolanLiveRobotConfig
from character.preset_manager import get_preset_manager

# Should not import these global value!
_project_dir: Path | None = None
_config: ZerolanLiveRobotConfig | None = None


@typechecked
def generate_config_file(config_path: Path):
    res_dir = config_path.parent
    if not os.path.exists(res_dir):
        res_dir.mkdir()
    gen = ConfigFileGenerator()
    config = gen.generate_yaml(ZerolanLiveRobotConfig())
    with open(config_path, mode="w+", encoding="utf-8") as f:
        f.write(config)
    logger.warning(
        "`resources/config.yaml` was not found. I have generated the file for you! \n"
        "Please edit the config file and re-run the program.")
    exit()


@typechecked
def _check_license(path: Path) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        if "Copyright (c) 2024 AkagawaTsurunaki" in f.read():
            logger.info("☺️ License validation passed! Thanks for your support!")
            return True
        else:
            logger.error("😭 License validation failed! You may be a victim of pirated software.")
            return False


@typechecked
def _find_license_recursively(path: Path, depth=0, max_depth=5) -> Path:
    if depth > max_depth:
        raise RecursionError("Could not find valid LICENSE file within max depth.")
    # Only search current directory, not deep subdirectories like node_modules
    for file in path.glob("LICENSE"):
        logger.info(f"Found candidate path: {file}")
        if _check_license(file):
            return Path(file)
    depth += 1
    return _find_license_recursively(path.parent, depth)


@typechecked
def get_project_dir() -> Path:
    global _project_dir
    if _project_dir is None:
        # Try to find project root by looking for LICENSE in current and parent dirs
        cwd = Path(os.getcwd())
        # First check if we're already in the project dir
        if (cwd / "LICENSE").exists() and _check_license(cwd / "LICENSE"):
            _project_dir = cwd
        else:
            # Check common subdirectories
            for subdir in cwd.iterdir():
                if subdir.is_dir() and (subdir / "LICENSE").exists():
                    if _check_license(subdir / "LICENSE"):
                        _project_dir = subdir
                        break
            else:
                # Fallback: search recursively with limited depth
                license_path = _find_license_recursively(cwd)
                _project_dir = Path(license_path.parent)
    return _project_dir


@typechecked
def get_default_config_path() -> Path:
    project_dir = get_project_dir()
    config_file_path = project_dir.joinpath("resources/config.yaml")
    return config_file_path


@typechecked
def get_config(path: Path | None = None) -> ZerolanLiveRobotConfig:
    global _config
    if _config:
        return _config
    if path is None:
        path = get_default_config_path()
    if path.exists():
        with open(path, mode="r", encoding="utf-8") as f:
            cfg_dict = yaml.safe_load(f)
            _config = ZerolanLiveRobotConfig.model_validate(cfg_dict)
            
            preset_name = cfg_dict.get("character", {}).get("preset")
            if preset_name:
                logger.info(f"Loading character preset: {preset_name}")
                preset_manager = get_preset_manager(
                    str(get_project_dir() / "resources" / "characters")
                )
                _config.character = preset_manager.apply_preset(preset_name, _config.character)
            
            return _config
    else:
        generate_config_file(path)


@typechecked
def save_config(config: ZerolanLiveRobotConfig, path: Path | None = None):
    assert config is not None, f"None can not be saved to config file."
    if path is None:
        path = get_default_config_path()
    # Create dir if not exists
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        logger.warning("Config file already exists. Overwriting...")
    # Generate config file
    gen = ConfigFileGenerator()
    yaml_str = gen.generate_yaml(config)
    with open(path, "w+", encoding="utf-8") as f:
        f.write(yaml_str)
        logger.info(f"Config file was saved: {path}")


get_project_dir()

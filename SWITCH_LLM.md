# ZerolanLiveRobot 启动与 LLM 切换指南

本文档整合了项目启动流程与 LLM 配置一键切换方法，方便在多个大语言模型服务商之间快速切换。

---

## 目录

- [环境要求](#环境要求)
- [一键启动](#一键启动)
- [LLM 一键切换](#llm-一键切换)
  - [支持的模型](#支持的模型)
  - [切换命令](#切换命令)
  - [查看当前配置](#查看当前配置)
- [配置说明](#配置说明)
  - [API Key 填写](#api-key-填写)
- [手动启动（可选）](#手动启动可选)
- [常见问题](#常见问题)

---

## 环境要求

| 项目 | 环境类型 | 环境名/激活方式 |
|------|---------|----------------|
| ZerolanCore | uv/venv | `asr/paraformer/.venv` |
| ZerolanLiveRobot | conda | `ZerolanLiveRobot` |

---

## 一键启动

推荐使用项目提供的 `start_all.ps1` 一键启动两个服务：

```powershell
cd d:\project-server\TraeProject\ZerolanLiveRobot
.\start_all.ps1
```

**效果**：自动打开两个独立 PowerShell 窗口：

| 窗口 | 服务 | 说明 |
|------|------|------|
| 窗口 1 | ZerolanCore ASR | 本地语音识别服务（端口 11001） |
| 窗口 2 | ZerolanLiveRobot | 主控制程序 |

> 若 `conda activate` 在新窗口中不生效，请改用 `conda run -n ZerolanLiveRobot python main.py` 手动启动。

---

## LLM 一键切换

项目内置 `switch_llm.py` 脚本，无需手动编辑 YAML 即可切换 LLM 配置。

### 支持的模型

| 提供商 | 命令参数 | 模型 ID | 接口地址 |
|--------|---------|---------|---------|
| 小米 MiMo | `xiaomi` | `mimo-v2.5` | `token-plan-cn.xiaomimimo.com` |
| 小米 MiMo Pro | `xiaomi-pro` | `mimo-v2.5-pro` | `token-plan-cn.xiaomimimo.com` |
| Kimi | `kimi` | `moonshot-v1-8k` | `api.moonshot.cn` |
| Kimi Coding | `kimi-coding` | `kimi-for-coding` | `api.kimi.com/coding` |
| DeepSeek | `deepseek` | `deepseek-chat` | `api.deepseek.com` |
| 豆包 | `doubao` | `doubao-seed-1-6-flash-250715` | `ark.cn-beijing.volces.com` |
| 智谱 GLM | `glm` | `glm-4.6v-flash` | `open.bigmodel.cn` |

### 切换命令

```powershell
# 切换到小米 MiMo
python switch_llm.py xiaomi

# 切换到 Kimi 标准版
python switch_llm.py kimi

# 切换到 DeepSeek
python switch_llm.py deepseek

# 切换到豆包
python switch_llm.py doubao

# 切换到智谱 GLM
python switch_llm.py glm
```

每次切换后脚本会自动：
1. 显示当前配置
2. 备份原配置到 `./resources/config.yaml.bak.<时间戳>`
3. 写入新配置
4. 提示重启生效

### 查看当前配置

```powershell
python switch_llm.py --show
```

---

## 配置说明

### API Key 填写

API Key 存放在 `resources/secrets.yaml` 中，该文件已被 `.gitignore` 忽略，不会提交到仓库。

首次使用请复制模板：

```powershell
cp resources/secrets.yaml.example resources/secrets.yaml
```

然后编辑 `resources/secrets.yaml`，填入你的 Key：

```yaml
glm:
  api_key: "你的智谱 Key"

xiaomi:
  api_key: "你的小米 Key"

deepseek:
  api_key: "你的 DeepSeek Key"
```

`switch_llm.py` 会自动从 `secrets.yaml` 读取 Key 并写入配置。

> 注意：不要把含 API Key 的文件提交到公共仓库。

---

## 手动启动（可选）

如需分别控制两个服务：

**终端 1 -- ZerolanCore ASR**：

```powershell
cd d:\project-server\TraeProject\zerolan-core\asr\paraformer
.\.venv\Scripts\Activate.ps1
cd ..\..
python starter.py asr
```

**终端 2 -- ZerolanLiveRobot**：

```powershell
conda activate ZerolanLiveRobot
cd d:\project-server\TraeProject\ZerolanLiveRobot
python main.py
```

---

## 常见问题

**Q: 切换后需要做什么？**
> 切换配置后需要重启 ZerolanLiveRobot。如果通过 `start_all.ps1` 启动，关闭两个窗口后重新运行即可。

**Q: 配置备份在哪里？**
> 每次切换都会自动生成备份，位于 `./resources/config.yaml.bak.<时间戳>`。如需回滚，手动复制覆盖 `config.yaml` 即可。

**Q: 切换时报 "配置文件不存在"？**
> 请先运行一次 `python main.py`，程序会自动生成默认配置文件，然后即可使用切换脚本。

**Q: 如何添加新的模型？**
> 编辑 `switch_llm.py` 中的 `PRESETS` 字典，添加新的提供商条目即可。格式参照已有示例。

**Q: 遇到 403 / access_terminated_error？**
> 说明当前 API Key 被服务商拒绝或限制。切换到其他模型即可（如从 Kimi Coding 切换到小米 MiMo）。

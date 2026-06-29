# Agent Light

**仓库地址**：[https://github.com/JiayuK/agent-light](https://github.com/JiayuK/agent-light)

macOS 菜单栏 / Windows 系统托盘 + 悬浮面板，实时监控 **Cursor**、**Claude Code**、**Codex**，以及 **Claude Desktop 编程模式** 的运行状态。

```
🔴 运行中  →  模型正在生成 / 执行工具
🟡 人工确认  →  需要权限确认、Run Command、AskQuestion 等
🟢 结束    →  空闲 / 任务已完成
```

每个卡片对应一个独立实例（一个 Cursor 窗口或一个 CLI 会话）。点击卡片可将对应工具窗口切换到前台。

---

## 快速开始

### 系统要求

| 项目 | macOS | Windows |
|------|-------|---------|
| 系统 | macOS 12.0+（Apple Silicon / Intel） | **Windows 10/11 x64** |
| Python | 独立 app 无需安装；源码版需 3.9+ | 源码版需 3.9+（`run.ps1` 自动建 venv） |
| 权限 | 辅助功能 (Accessibility) | 无额外系统权限（Hook 需写入用户配置目录） |

### 直接下载（macOS 推荐）

无需 Python、无需 `pip install`，解压即用：

1. 打开 **[Releases 页面](https://github.com/JiayuK/agent-light/releases/latest)**
2. 下载 **`agent-light-x.x.x-macos-app.zip`**（独立应用，约 20MB）
3. 解压后进入目录，执行：

```bash
cd <解压后的目录>   # 例如解压到 ~/Applications 后进入对应文件夹

chmod +x run-app.sh
./run-app.sh
```

看到 `✓ Agent Light 已启动` 后，菜单栏会出现监控图标。也可双击 `Agent Light.app` 启动（推荐仍用 `run-app.sh`，便于 `stop` / `status` / 安装 Hook）。

| 命令 | 说明 |
|------|------|
| `./run-app.sh` | 后台启动（默认） |
| `./run-app.sh verbose` | 前台调试并写日志 |
| `./run-app.sh stop` | 停止 |
| `./run-app.sh status` | 查看状态 |
| `./run-app.sh install-hooks` | 安装 Agent Hooks |
| `./run-app.sh paths` | 检测本机 AI 工具路径 |

> **升级**：下载新版 zip，解压覆盖（或新目录），再 `./run-app.sh`；`~/.agent-light/` 设置会保留。

> **架构**：macOS 独立 app 包为 **Apple Silicon (arm64)** 构建。Intel Mac 请用源码版 `./run.sh`。

### Windows x64

**方式一：独立包（推荐）**

从 [Releases](https://github.com/JiayuK/agent-light/releases/latest) 下载 `agent-light-x.x.x-windows-x64.zip`，解压后：

```powershell
cd <解压目录>
.\run-app.ps1
```

**方式二：源码运行**

```powershell
git clone https://github.com/JiayuK/agent-light.git
cd agent-light
.\run.ps1
```

| 命令 | 说明 |
|------|------|
| `.\run-app.ps1` / `.\run.ps1` | 后台启动（托盘 + 悬浮面板） |
| `.\run-app.ps1 verbose` | 前台调试 |
| `.\run-app.ps1 stop` | 停止 |
| `.\run-app.ps1 install-hooks` | 安装 Agent Hooks |
| `.\run-app.ps1 paths` | 检测本机 AI 工具路径 |

功能与 macOS 对齐：交通灯 / 坤坤 / 自定义风格、「我爱发明」风格管理、Hook 安装提醒、Claude Desktop 编程会话检测。路径自动发现：`%APPDATA%\Cursor`、`%USERPROFILE%\.cursor`、`.claude`、`.codex` 等。

> **测试说明**：Windows x64 版已在代码层完成开发与 CI 构建，**尚未在真实 Windows 设备上人工验证**。若在 Windows 上遇到问题，欢迎提 Issue；macOS 版为日常主力平台并已实测。

维护者在本机构建 Windows 包：`.\scripts\build-app-win.ps1`（需在 Windows x64 上运行）；或推送 tag 后由 GitHub Actions `Build Windows x64` 自动构建。

### 源码版（macOS 开发者）

需要本机 Python 3.9+，首次运行会自动 `pip install` 依赖：

```bash
git clone https://github.com/JiayuK/agent-light.git
cd agent-light

chmod +x run.sh
./run.sh
```

首次运行会自动：

1. 检测本机 Python 3.9+
2. 创建 `.venv` 并 `pip install -e .`
3. 后台静默启动（默认不写日志）

看到 `✓ Agent Light 已启动` 后，菜单栏会出现监控图标，屏幕上方出现悬浮面板。

> **不要提交或复制 `.venv`**：虚拟环境与创建它的 Python 绑定，换电脑后删除重建即可：`rm -rf .venv && ./run.sh`

### 手动安装（可选）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
agent-light              # 默认静默
agent-light --verbose    # 启用日志
```

### 辅助功能权限

每台 Mac **只需配置一次**：

**系统设置 → 隐私与安全性 → 辅助功能** → 添加并打开开关：

- 使用 **`./run-app.sh` / `./run.sh`**：添加对应**终端**（Terminal / iTerm / Warp 等）
- **双击 `Agent Light.app`** 启动：添加 **Agent Light**

`run-app.sh` / `run.sh` 启动时会自动检测；若缺失会尝试打开系统设置页面。

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `./run.sh` | 后台静默启动（默认） |
| `./run.sh verbose` | 前台启动并写日志（调试） |
| `./run.sh stop` | 停止服务 |
| `./run.sh status` | 查看运行状态 |
| `./run.sh paths` | **检测本机 AI 工具路径**（无需手动配置） |
| `./run.sh install-hooks` | 安装 Agent Hooks（命令行） |
| `./run.sh uninstall-hooks` | 删除 Agent Hooks（命令行） |

菜单栏也提供 **安装 Hook** / **删除 Hook**，支持增量安装（见下文）。

---

## Agent Hooks

三种工具的状态均通过 **Agent Hooks** 获取，比轮询日志更准确。

### 安装方式

**菜单栏 → 安装 Hook**，或：

```bash
./run.sh install-hooks
```

| 工具 | 配置文件 | 中继脚本 |
|------|----------|----------|
| Cursor | `~/.cursor/hooks.json` | `~/.cursor/hooks/agent-light-signal.sh` |
| Claude Code | `~/.claude/settings.json` | `~/.claude/hooks/agent-light-claude-signal.sh` |
| Codex | `~/.codex/hooks.json` | `~/.codex/hooks/agent-light-codex-signal.sh` |

Claude Desktop **编程模式**与 Claude Code CLI **共用** `~/.claude/settings.json` 中的 Hook；安装 Claude Code Hook 后，Desktop 编程会话也会写入同一状态目录。

状态信号目录：`~/.agent-light/agent-hooks/states/`

### 增量安装

- **只检测本机已安装的工具**（不必三个都有）
- 首次只有 Cursor → 只装 Cursor
- 之后安装了 Codex → 再次点「安装 Hook」会校验 Cursor 是否完整，并新装 Codex
- 已完整配置的工具显示「已安装且配置完整」，不会重复写入
- 安装/删除时**合并写入**，不会覆盖你原有的其他 Hook

安装后请**重启对应 AI 工具**，再执行一次 Agent 任务。

### Claude Desktop 注意点

Agent Light 会单独显示 **Claude Desktop** 卡片（与 **Claude Code · 终端** 区分）。状态读取顺序：

1. **Hook 信号**（与 CLI 同源，需已安装 Claude Code Hook）
2. **会话日志 fallback**（`~/.claude/projects/` 下的 JSONL）
3. 无法识别为编程会话时 → 显示 🟢，原因 `desktop: 非编程模式（无 Hook）`

| 场景 | 行为 |
|------|------|
| Desktop 编程模式 + 已装 Hook | 与 CLI 一样准确（🔴🟡🟢） |
| Desktop 编程模式 + 未装 Hook | 尝试读会话日志；仍可能长期 🟢 |
| Desktop 普通聊天（非编程） | **不监控**，固定 🟢 |
| 同时开 Desktop 编程 + CLI | 可能出现两张卡片（同一项目），属正常 |
| 同一项目多个 Desktop 窗口 | 按窗口标题匹配会话；标题相近可能串台 |
| 同一项目多个 CLI 终端 | 仍按目录共享 Hook 状态（已知限制） |

编程会话的工作目录来自 Claude Desktop 元数据：

`~/Library/Application Support/Claude/claude-code-sessions/`

若 Desktop 卡片长期 🟢，请确认：已在 **编程模式** 下运行任务、窗口标题与会话标题一致、且 Claude Code Hook 已安装并重启 Claude Desktop。

> **从旧版本升级**：若曾使用其他命名的 Hook 脚本，请在菜单栏执行一次「删除 Hook」再「安装 Hook」，或运行 `./run.sh uninstall-hooks && ./run.sh install-hooks`。

### 删除 Hook

菜单栏 **删除 Hook** 会移除**所有已安装的 Agent Light Hook**（例如 Cursor + Codex），不影响其他 Hook 配置。

---

## 路径自动发现

工具配置目录默认**自动发现**，新用户克隆后一般**无需手动配置**：

| 工具 | 默认检测 |
|------|----------|
| Cursor | `~/Library/Application Support/Cursor`、`~/.cursor`、Cursor.app |
| Claude Code | `~/.claude`、`which claude`、常见 CLI 路径 |
| Codex | `~/.codex`、`which codex`、Homebrew Cask |
| Claude Desktop 会话 | `~/Library/Application Support/Claude/claude-code-sessions` |

**软件未启动时**也会根据上述路径与可执行文件判断是否存在，不会盲目创建目录。

验证本机路径是否自动识别成功：

```bash
./run.sh paths
```

输出中 `✓` 表示目录/文件已存在；`○` 为预期默认路径（工具首次运行后会创建）。只要「工具检测详情」里显示已安装对应工具，即可直接启动并安装 Hook。

### 自定义路径（可选）

仅在非标准安装位置时需要。优先级：

**`~/.agent-light/settings.json`** > **环境变量** > **自动发现** > **默认路径**

`settings.json` 示例：

```json
{
  "display_mode": "traffic",
  "tool_paths": {
    "cursor_user_data_dir": "/path/to/Cursor",
    "cursor_config_dir": "/path/to/.cursor",
    "cursor_projects_dir": "/path/to/.cursor/projects",
    "codex_home": "/path/to/.codex",
    "claude_config_dir": "/path/to/.claude",
    "claude_desktop_sessions_dir": "/path/to/claude-code-sessions"
  }
}
```

环境变量（可选）：

| 变量 | 说明 |
|------|------|
| `AGENT_LIGHT_CURSOR_USER_DATA_DIR` | Cursor 用户数据目录 |
| `AGENT_LIGHT_CURSOR_CONFIG_DIR` | Cursor `~/.cursor` 等价目录 |
| `AGENT_LIGHT_CURSOR_PROJECTS_DIR` | Cursor agent transcripts |
| `AGENT_LIGHT_CODEX_HOME` / `CODEX_HOME` | Codex 配置根目录 |
| `AGENT_LIGHT_CLAUDE_CONFIG_DIR` / `CLAUDE_CONFIG_DIR` | Claude Code 配置目录 |
| `AGENT_LIGHT_CLAUDE_DESKTOP_SESSIONS_DIR` | Claude Desktop 编程会话元数据 |

---

## 菜单栏与面板

| 菜单项 | 功能 |
|--------|------|
| 显示面板 | 将悬浮面板置于最前 |
| 🚦 交通灯 | 经典三灯样式 |
| 我爱坤坤💗💗 | 内置 GIF 样式 |
| {emoji} 风格名 | 自定义风格 |
| 我爱发明 | 管理自定义图片/GIF |
| 安装 Hook / 删除 Hook | 增量安装或移除 Hooks |
| 退出 Agent Light | 完全退出 |

- 拖动面板空白区域可移动位置
- 点击实例卡片可聚焦对应 AI 工具窗口

---

## 用户数据目录

所有运行时数据在 `~/.agent-light/`（**不会**随仓库分发）：

```
~/.agent-light/
├── settings.json       # 显示模式、可选路径覆盖
├── custom_styles.json  # 自定义风格
├── styles/{id}/        # 风格图片资源
├── agent-hooks/        # Hook 状态信号
├── logs/               # 日志（verbose 模式）
└── agent-light.pid     # 进程 ID
```

### 卸载

```bash
./run.sh stop
rm -rf .venv
rm -rf ~/.agent-light   # 可选：删除配置与自定义风格
```

---

## 开机自启（可选）

将 `/path/to/agent-light` 替换为你的克隆路径：

```bash
PLIST=~/Library/LaunchAgents/com.agent.light.plist
REPO=/path/to/agent-light

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.agent.light</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>cd $REPO && ./run.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

launchctl load "$PLIST"
```

---

## 常见问题

### 悬浮窗不显示

```bash
./run.sh status          # 确认在运行
./run.sh verbose         # 查看错误输出
```

菜单栏图标 → **显示面板**。

### 状态始终绿灯

1. 菜单栏 **安装 Hook**（或 `./run.sh install-hooks`）
2. 重启 Cursor / Claude Code / Codex / **Claude Desktop**
3. 运行一次 Agent 任务（Desktop 需在**编程模式**）
4. 确认已授予**辅助功能**权限

### 只装了部分 AI 工具

正常。未检测到的工具会跳过，菜单显示如 `安装 Hook (1/2)`。

### 虚拟环境报错

```bash
rm -rf .venv
./run.sh
```

### 调试日志

```bash
./run.sh stop
./run.sh verbose
```

日志路径：`~/.agent-light/logs/agent-light.log`

---

## 项目结构

```
agent-light/
├── run.sh / run.ps1       # macOS / Windows 入口
├── agent_light/
│   ├── main.py            # 平台分发入口
│   ├── platform/          # darwin / win32 应用壳
│   ├── ui/                # macOS AppKit UI
│   ├── ui_win/            # Windows Tk UI
│   ├── agent_hooks/       # Hook 安装与中继
│   └── detector/          # 实例扫描与状态分析
└── packaging/             # PyInstaller spec（mac / win）
```

完整功能说明与问题检测见 **[FEATURES.md](FEATURES.md)**。

## License

MIT — 见 [LICENSE](LICENSE)。

## 隐私与数据

Agent Light **完全本地运行**，不向任何远程服务器上传数据，**无遥测、无分析、无自动更新检查**（代码中无 HTTP 网络请求）。

### 存储位置

| 平台 | 用户数据目录 |
|------|----------------|
| macOS | `~/.agent-light/` |
| Windows | `%USERPROFILE%\.agent-light\` |

### 收集与用途

| 数据 | 位置 | 说明 |
|------|------|------|
| Hook 状态信号 | `agent-hooks/states/` | 仅保存工具名、工作区路径、状态、事件类型；**不保存** prompt / 代码内容 |
| 用户设置与自定义风格 | `settings.json`、`styles/` | 仅在本机，不随仓库分发 |
| 日志（verbose 模式） | `logs/` | 可能包含路径、进程信息；**默认不启用** |
| Hook 运行时路径 | `agent-hooks/python.txt`、`relay.txt` | 记录本机 Python 或 relay 可执行文件路径，供 Hook 脚本调用 |
| macOS 辅助功能 | 内存中临时使用 | 窗口枚举与聚焦；Claude Desktop 编程模式优先读 Hook，普通聊天不解析窗口正文 |
| Windows 窗口信息 | 内存中临时使用 | 通过 Win32 API 读取窗口标题以匹配实例；不持久化窗口内容 |

### Hook 写入的第三方配置

安装 Hook 时会在本机 AI 工具配置目录写入中继脚本并合并 Hook 配置（**不覆盖**你已有的其他 Hook）：

| 工具 | macOS | Windows |
|------|-------|---------|
| Cursor | `~/.cursor/hooks/` | `%USERPROFILE%\.cursor\hooks\` |
| Claude Code | `~/.claude/` | `%USERPROFILE%\.claude\` |
| Codex | `~/.codex/` | `%USERPROFILE%\.codex\` |

卸载可从菜单栏 / 托盘选择「删除 Hook」，或通过 `run.sh` / `run.ps1 uninstall-hooks` 移除。

**请勿提交**：`.venv/`、`*.egg-info/`、`.env`、本机 `~/.agent-light/` 或 `%USERPROFILE%\.agent-light\` 目录。

## 发布 Release（维护者）

```bash
# 1. 更新 pyproject.toml 与 agent_light/__init__.py 中的版本号
# 2. 构建 macOS 发布包（本机 Apple Silicon）
chmod +x scripts/build-release.sh scripts/build-app.sh
./scripts/build-release.sh

# 3. Windows x64 包：在 Windows 上运行 .\scripts\build-app-win.ps1
#    或推送 tag 后由 GitHub Actions 构建 artifact

# 4. 打 tag 并发布
git tag v1.1.0
git push origin v1.1.0
gh release create v1.1.0 \
  dist/agent-light-1.1.0-macos-app.zip \
  dist/agent-light-1.1.0-macos-source.zip \
  dist/agent-light-1.1.0-macos-source.tar.gz \
  dist/agent-light-1.1.0-windows-x64.zip \
  --title "v1.1.0" \
  --notes "macOS: ./run-app.sh | Windows x64: ./run-app.ps1（未经真机测试）"
```

仅构建 macOS 独立 app：`./scripts/build-app.sh`

Windows x64 独立包（需在 Windows 上执行）：

```powershell
.\scripts\build-app-win.ps1
# 产出 dist/agent-light-x.x.x-windows-x64.zip
```

或通过 GitHub Actions `Build Windows x64` workflow 自动构建 artifact。

发布前检查：

- [ ] 确认未 `git add .venv` 或 `*.egg-info`
- [ ] 内置 `assets/kun.*` 为娱乐向 GIF/图片，公开仓库请自行确认版权/肖像权是否可分发

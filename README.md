# Dungeon Master Studio

供地下城主使用的离线战斗工具，采用 Tauri 2 + React 工作区界面，支持角色管理、怪物图鉴和完整内存战斗。项目仅保留重构后的版本；结构、验证记录与后续工作见 [项目说明](docs/migration.md)。

## 安装与启动

技术栈：Tauri 2、React、TypeScript strict、Vite、Zustand、CSS Modules / Design Tokens、VS Code Codicons。目前不提供存档读写或自动恢复，也不使用 localStorage。参战者、草稿、复制副本和最近使用只存在于本次会话；关闭或刷新后丢失。

安装 Node.js（建议 22.12+ 的受支持 LTS）后，在本目录运行：

```bash
npm ci
npm run dev
```

在浏览器打开 `http://127.0.0.1:1420/`。依赖安装需要网络；运行资源、图标和字体均随工程本地提供。`npm run dev` 仅监听本机。

桌面版还需要 Rust stable / Cargo，以及对应平台工具链；macOS 需要 Xcode Command Line Tools。详见 [Tauri 前置要求](https://v2.tauri.app/start/prerequisites/)。

```bash
npm run tauri -- dev
npm run tauri -- build --bundles app
```

macOS `.app` 产物位于 `src-tauri/target/release/bundle/macos/`，默认窗口为 1240×780，最小 1080×580，使用原生标题栏。当前仅将 macOS 作为首个桌面验收平台。

本次验证使用了隔离安装于 `/private/tmp` 的 Rust 工具链，未修改 shell 配置；若这台机器尚未永久安装 Rust，可在当前终端临时启用它（临时目录清理后需要重新安装）：

```bash
export RUSTUP_HOME=/private/tmp/dm-studio-rustup
export CARGO_HOME=/private/tmp/dm-studio-cargo
export PATH="$CARGO_HOME/bin:$PATH"
```

新界面支持战斗 / 角色 / 怪物图鉴视图切换、档案显隐与档案面板调宽。档案默认隐藏、展开宽度 320px；分隔条支持鼠标拖动、左右方向键每次 8px、Shift+方向键每次 32px，Home / End 调整到最小 / 最大宽度。

工作区快捷键统一通过 Command Registry 执行：

| 快捷键 | 操作 |
| --- | --- |
| `Cmd/Ctrl+Shift+I` | 切换参战者档案 |
| `Cmd/Ctrl+1 / 2 / 3` | 战斗 / 角色 / 怪物图鉴 |
| `Cmd/Ctrl+C / V` | 复制所选角色 / 粘贴为新角色 |
| macOS `Cmd+Backspace / Delete` | 快速删除所选角色，无确认 |
| 其他平台 `Ctrl+Delete` | 快速删除所选角色，无确认 |

输入框、可编辑内容、输入法组合期间以及确认框或怪物选择弹窗打开时，不会拦截这些快捷键。浏览器预览可能由浏览器优先处理部分组合，桌面版使用相同注册表。

```bash
npm run typecheck
npm test
npm run build
cargo check --manifest-path src-tauri/Cargo.toml --locked
```

43 项前端测试覆盖纯业务规则、命令与交互、图鉴、快捷键和退出保护。已通过类型检查、构建、Cargo 检查及 macOS release 打包；桌面视觉检查和真实关闭 / Quit 交互因桌面自动化连接不可用尚未完成，详见项目说明。

## 操作流程

1. 点击添加玩家、添加 NPC，或添加怪物。怪物弹窗支持中英文搜索、上下键、Enter 选用、双击选用、最近使用和手动添加；图鉴不可用时仍可手动添加。
2. 在档案里填写名称、先攻、最大 HP 和当前 HP；新增时当前 HP 留空等于最大 HP。怪物填基础名称，编号自动分配。数字须为 JavaScript 安全范围内的整数。
3. 确认添加后，在列表中选择角色可编辑、复制或移除。普通移除先确认，快捷删除不确认；删除后选下一位，末尾选上一位。角色视图与战斗视图共享同一遭遇，角色视图可按类型筛选。
4. 按先攻排序，同先攻箭头仅与相邻同先攻角色换位；点击开始战斗自动排序并从第 1 轮开始。下一位会选择并显示新的行动者。
5. 选中血量操作对象，填写非负整数并点击受到伤害 / 接受治疗；也可在档案里直接修改当前 HP。选中对象可以不是当前行动者。0 HP 不自动删除、跳过或结束战斗。
6. 战斗中可以增删、编辑和排序；这些操作不增加轮数。删除本轮最后一名待行动者后显示“本轮已结束”，点击下一位才进入下一轮。
7. 结束战斗保留全部角色、顺序和 HP；清空战斗需要确认，会移除全部参战者和轮次。

已有参战者时，浏览器正常刷新 / 关闭由浏览器提供退出提示；Tauri 窗口关闭与 macOS 正常 Quit 接入 React 确认框。取消继续保留会话，清空战斗后解除保护。浏览器提示受用户交互和浏览器策略限制；强制退出、系统故障不能保证拦截。本阶段没有保存功能。

图鉴数据按需作为本地资源加载，构建会报告该数据 chunk 大于 500 kB；约 2.49 MB 的数据未放进初始应用代码，也不从外部网站请求。

## 项目结构

```text
src/          React 界面、命令、业务规则、Zustand 状态与测试
src-tauri/    Rust 桌面宿主、退出保护与应用图标
resources/    本地怪物图鉴及来源许可
docs/         项目结构、验证记录与后续工作
```

依赖锁文件为 `package-lock.json` 和 `src-tauri/Cargo.lock`。项目开发和运行不需要 Python。

怪物图鉴包含 503 条资料，来源信息保留在 JSON 元数据中；原资料库附带的许可见 [monster_handbook.LICENSE](resources/monster_handbook.LICENSE)。当前保留生成后的 JSON，不再包含资料库或旧生成脚本。

退役代码、旧存档和原始资料库已移至项目外备份，位置见 [清理记录](docs/migration.md#清理记录)。它们不属于当前工程，也不会被应用读取。

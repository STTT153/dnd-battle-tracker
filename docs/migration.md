# Dungeon Master Studio 项目说明

## 当前版本

项目已统一为 Tauri 2 + React + TypeScript 应用，无 Python 启动入口或运行时依赖。已完成工作区、角色与图鉴、完整内存战斗以及退出确认；存档功能尚未实现。

- Workbench 提供 Activity Bar、Toolbar、Main Content、可隐藏和调宽的 Inspector，以及状态栏。
- 支持玩家、NPC、怪物增删改、复制粘贴、同名怪物自动编号、角色类型筛选。
- 本地图鉴包含 503 条怪物，支持中英文搜索、键盘选择、最近使用 6 项、资料回填和手动添加。
- 支持稳定先攻排序、同先攻换位、回合推进、战斗中增删、伤害、治疗、直接修正 HP、结束与确认清空。
- 选择对象和当前行动者独立；0 HP 不自动跳过、删除或结束战斗。排序和删除不自行增加轮数。
- 全部会话数据仅在内存中，关闭或刷新后丢失。已有参战者时启用正常退出确认，强制结束进程不保证拦截。

## 结构与接口

| 目录 | 职责 |
| --- | --- |
| `src/app` | 应用组装及浏览器 / 桌面退出保护 |
| `src/workbench` | 工作区布局与面板 |
| `src/characters` | 角色模型、纯规则、表单、列表及图鉴适配 |
| `src/combat` | 回合、先攻与 HP 纯规则及战斗视图 |
| `src/commands` | 类型化 Command Registry、命令处理和快捷键 |
| `src/stores` | Encounter、布局、草稿、选择、复制和图鉴会话状态 |
| `src/components` | IconButton、空状态、弹窗与确认框 |
| `src/theme`、`src/icons` | Design Tokens、CSS、Codicons 与统一 D&D SVG |
| `src/types`、`src/test` | 共享接口和测试基础设施 |
| `src-tauri` | 原生窗口、退出事件、能力配置和应用图标 |
| `resources` | 本地图鉴 JSON 和来源许可 |

组件通过命令入口执行业务操作；应用操作调用纯规则，再将结果提交至 Zustand。表单字符串草稿、选择和复制副本与 Encounter 分离。校验失败不修改战斗数据，数值使用 JavaScript 安全整数校验。

CommandIds 定义参数类型，execute 支持异步确认并检查可执行状态。CommandButton 订阅状态以更新可用性；确认期间阻止其他命令。注册返回注销函数，为未来扩展保留入口，不实现插件加载器或 Command Palette。

`combat.stop` 保留角色、显示顺序和 HP，仅清空行动进度；`combat.reset` 确认后清空参战者和轮次。

Rust 只提供窗口和退出保护。session_set_close_guard 同步“是否有参战者”，session_confirm_exit 在确认后退出；不传输 Encounter，不处理战斗规则。仅启用事件监听及注销能力，无文件或 shell 权限。

图鉴按需从现有 JSON 加载，保留 503 条怪物内容；适配后的 MonsterStats 只保留实际展示资料。原始 source / source_file 元数据用于记录来源，不指向应用运行时依赖。来源许可保留为 `resources/monster_handbook.LICENSE`。

## 验证

```bash
npm run typecheck
npm test
npm run build
cargo check --manifest-path src-tauri/Cargo.toml --locked
npm run tauri -- build --bundles app
```

43 项前端测试覆盖角色校验与编号、图鉴适配和搜索、最近使用、战斗规则、表单及列表交互、命令保护、快捷键、面板调宽和退出保护。已通过类型检查、生产构建、Cargo 检查、原生开发启动和 macOS release 打包。

图鉴数据 chunk 约 2.49 MB，按需加载，不属于初始应用 JS；Vite 会提示该 chunk 大于 500 kB。应用运行不从外部网站请求图鉴。

桌面自动化连接不可用，默认与最小窗口、档案面板最大宽度、真实关闭 / macOS Quit、弹窗焦点尚未完成本轮目视验收，不计为通过。退出保护的浏览器事件及原生桥逻辑已有自动化测试覆盖。

## 清理记录

2026-10-26 按要求移除旧版本，仅保留当前工程：

- 旧程序、旧生成脚本、旧图形 / 逻辑测试、6 个旧 SVG 图标已移出项目。
- 已移出独立原始资料库，移除本地虚拟环境与编译缓存。
- 删除旧启动、保存及回归测试说明，更新界面中指向旧入口的提示；移除 JSON 中指向旧生成器的元数据，503 条怪物内容不变。
- 旧战斗存档与备份一并移到项目外，未删除或覆盖。

备份目录：`/Users/stevenyin/workspace/battle_tracker_legacy_backup_20261026`。目录中的 manifest.json 记录了移动清单及旧存档校验值；备份不被当前应用引用。

## 后续工作

实现 Rust 存储、旧存档显式导入、原子写入、损坏备份、自动恢复和写入失败重试。导入时保留原文件，禁止静默覆盖项目外备份。补齐桌面视觉与真实退出交互验收后再扩大平台范围。

## 界面简化

按截图标注移除主侧栏及其切换按钮、快捷键和宽度状态；移除活动栏顶部品牌骰子、标题栏右侧内存提示和标签栏重复产品名。主内容直接占用腾出的宽度，保留视图切换、档案面板、状态栏和退出保护。

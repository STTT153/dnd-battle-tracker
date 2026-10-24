#!/usr/bin/env python3
"""启动中文 Tkinter 战斗追踪器：python3 battle_tracker.py。"""

from pathlib import Path
import sys

try:
    import tkinter as tk
    from tkinter import font, messagebox, ttk
except ImportError:
    print("此 Python 没有安装 Tkinter，暂时无法打开图形界面。\n"
          "请查看同目录 README.md 的安装说明，并为当前 Python 安装匹配的 Tkinter。\n"
          "安装后运行 python3 -m tkinter 检查，再重新启动本程序。", file=sys.stderr)
    sys.exit(1)

from battle_logic import Battle, BattleError, JsonStore


SAVE_PATH = Path(__file__).resolve().with_name("battle_save.json")


class BattleApp:
    def __init__(self, root, save_path=SAVE_PATH):
        self.root = root
        self.store = JsonStore(save_path)
        self.battle = Battle()
        self.dirty = False
        self.protect_original = False
        self.refreshing = False
        self.status = tk.StringVar(value="")
        self.heading = tk.StringVar()
        self.form_title = tk.StringVar(value="添加参战者")
        self.fields = {key: tk.StringVar() for key in ("name", "kind", "initiative", "max_hp", "hp")}
        self.amount = tk.StringVar(value="1")
        self._build_ui()
        self.clear_form()
        self._load()
        self.refresh()
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        self.root.title("D&D 战斗追踪器 · 地下城主助手")
        self.root.geometry("1240x780")
        self.root.minsize(1080, 680)

        # 参考图的中古奇幻插画以低饱和蓝绿、羊皮纸和烛火金为主。
        # 将其转译为高对比度的桌面工具配色，避免装饰干扰战斗信息。
        self.colors = {
            "ink": "#1E2A26",
            "pine": "#243A33",
            "pine_hover": "#304B41",
            "moss": "#46604F",
            "sky": "#6F8FA8",
            "sky_dark": "#45677F",
            "parchment": "#EEE7D8",
            "paper": "#FAF7EF",
            "paper_alt": "#F4EFE3",
            "line": "#C8BDA8",
            "line_dark": "#9E927E",
            "gold": "#C18A43",
            "gold_hover": "#D19A50",
            "rust": "#A14F3E",
            "rust_hover": "#B75D49",
            "sage": "#DDE6DA",
            "mist": "#E1E9EC",
            "muted": "#68716B",
            "white": "#FFFDF8",
        }
        self.root.configure(background=self.colors["parchment"])

        families = set(font.families(self.root))
        ui_family = next((name for name in ("PingFang SC", "SF Pro Text", "Helvetica Neue", "Arial")
                          if name in families), "TkDefaultFont")
        display_family = next((name for name in ("Songti SC", "STSong", "Georgia", ui_family)
                               if name in families), ui_family)
        font.nametofont("TkDefaultFont").configure(family=ui_family, size=12)
        font.nametofont("TkTextFont").configure(family=ui_family, size=12)
        font.nametofont("TkMenuFont").configure(family=ui_family, size=12)
        font.nametofont("TkHeadingFont").configure(family=ui_family, size=12, weight="bold")
        self.body_font = font.Font(self.root, family=ui_family, size=12)
        self.small_font = font.Font(self.root, family=ui_family, size=10)
        self.caption_font = font.Font(self.root, family=ui_family, size=9, weight="bold")
        self.bold_font = font.Font(self.root, family=ui_family, size=12, weight="bold")
        self.title_font = font.Font(self.root, family=display_family, size=22, weight="bold")
        self.section_font = font.Font(self.root, family=display_family, size=15, weight="bold")

        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        c = self.colors
        style.configure("App.TFrame", background=c["parchment"])
        style.configure("Header.TFrame", background=c["pine"])
        style.configure("Card.TFrame", background=c["paper"], relief="solid", borderwidth=1)
        style.configure("CardBody.TFrame", background=c["paper"])
        style.configure("Toolbar.TFrame", background=c["paper_alt"])
        style.configure("HeaderTitle.TLabel", background=c["pine"], foreground=c["white"], font=self.title_font)
        style.configure("HeaderMeta.TLabel", background=c["pine"], foreground="#D9E2DC", font=self.small_font)
        style.configure("Eyebrow.TLabel", background=c["paper"], foreground=c["sky_dark"], font=self.caption_font)
        style.configure("Section.TLabel", background=c["paper"], foreground=c["ink"], font=self.section_font)
        style.configure("Body.TLabel", background=c["paper"], foreground=c["ink"], font=self.body_font)
        style.configure("Muted.TLabel", background=c["paper"], foreground=c["muted"], font=self.small_font)
        style.configure("Toolbar.TLabel", background=c["paper_alt"], foreground=c["ink"], font=self.body_font)
        style.configure("ToolbarMuted.TLabel", background=c["paper_alt"], foreground=c["muted"], font=self.small_font)
        style.configure("Status.TLabel", background=c["parchment"], foreground=c["muted"], font=self.small_font)
        style.configure("EmptyTitle.TLabel", background=c["paper"], foreground=c["ink"], font=self.section_font)
        style.configure("EmptyBody.TLabel", background=c["paper"], foreground=c["muted"], font=self.small_font)

        button_base = dict(font=self.bold_font, padding=(15, 9), relief="flat", borderwidth=0)
        style.configure("Primary.TButton", background=c["gold"], foreground=c["ink"], **button_base)
        style.map("Primary.TButton",
                  background=[("disabled", "#D8C8AA"), ("pressed", "#A87538"), ("active", c["gold_hover"])],
                  foreground=[("disabled", "#847B6B")])
        style.configure("Secondary.TButton", background=c["sky_dark"], foreground=c["white"], **button_base)
        style.map("Secondary.TButton",
                  background=[("disabled", "#AEBBC0"), ("pressed", "#38566A"), ("active", c["sky"])],
                  foreground=[("disabled", "#EEF1F0")])
        style.configure("HeaderGhost.TButton", background=c["pine"], foreground=c["white"],
                        font=self.bold_font, padding=(13, 8), relief="solid", borderwidth=1)
        style.map("HeaderGhost.TButton",
                  background=[("pressed", "#1C2E28"), ("active", c["pine_hover"])],
                  bordercolor=[("!disabled", "#70857A")])
        style.configure("HeaderDanger.TButton", background=c["rust"], foreground=c["white"],
                        font=self.bold_font, padding=(13, 8), relief="flat", borderwidth=0)
        style.map("HeaderDanger.TButton",
                  background=[("disabled", "#6D7069"), ("pressed", "#873E31"), ("active", c["rust_hover"])],
                  foreground=[("disabled", "#D4D6D2")])
        style.configure("Quiet.TButton", background=c["paper_alt"], foreground=c["ink"],
                        font=self.body_font, padding=(11, 7), relief="flat", borderwidth=0)
        style.map("Quiet.TButton", background=[("pressed", "#DED5C5"), ("active", "#E7DFD0")])
        style.configure("Danger.TButton", background=c["paper_alt"], foreground=c["rust"],
                        font=self.bold_font, padding=(11, 7), relief="flat", borderwidth=0)
        style.map("Danger.TButton", background=[("pressed", "#E7CFC8"), ("active", "#F1DDD7")],
                  foreground=[("active", c["rust_hover"])])
        style.configure("Damage.TButton", background=c["rust"], foreground=c["white"], **button_base)
        style.map("Damage.TButton", background=[("pressed", "#873E31"), ("active", c["rust_hover"])])
        style.configure("Heal.TButton", background=c["moss"], foreground=c["white"], **button_base)
        style.map("Heal.TButton", background=[("pressed", "#35493C"), ("active", "#587563")])
        style.configure("Field.TEntry", fieldbackground=c["white"], foreground=c["ink"],
                        bordercolor=c["line"], lightcolor=c["line"], darkcolor=c["line"],
                        insertcolor=c["ink"], padding=(9, 8))
        style.map("Field.TEntry", bordercolor=[("focus", c["sky_dark"])], lightcolor=[("focus", c["sky_dark"])])
        style.configure("Field.TCombobox", fieldbackground=c["white"], background=c["white"],
                        foreground=c["ink"], bordercolor=c["line"], arrowcolor=c["pine"], padding=(9, 7))
        style.map("Field.TCombobox", bordercolor=[("focus", c["sky_dark"])],
                  fieldbackground=[("readonly", c["white"])], foreground=[("readonly", c["ink"])])
        style.configure("Treeview", background=c["paper"], fieldbackground=c["paper"], foreground=c["ink"],
                        bordercolor=c["line"], lightcolor=c["line"], darkcolor=c["line"],
                        rowheight=42, font=self.body_font)
        style.map("Treeview", background=[("selected", "#CAD9DC")], foreground=[("selected", c["ink"])])
        style.configure("Treeview.Heading", background=c["pine"], foreground=c["white"],
                        bordercolor=c["pine"], relief="flat", padding=(8, 10), font=self.bold_font)
        style.map("Treeview.Heading", background=[("active", c["pine_hover"])])
        style.configure("Vertical.TScrollbar", background=c["line"], troughcolor=c["paper_alt"],
                        bordercolor=c["paper_alt"], arrowcolor=c["pine"])

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, style="Header.TFrame", padding=(24, 18))
        top.grid(row=0, column=0, sticky="ew")
        brand = ttk.Frame(top, style="Header.TFrame")
        brand.pack(side="left", fill="y")
        ttk.Label(brand, text="战斗纪事", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(brand, textvariable=self.heading, style="HeaderMeta.TLabel").pack(anchor="w", pady=(3, 0))
        actions = ttk.Frame(top, style="Header.TFrame")
        actions.pack(side="right", fill="y")
        self.end_button = ttk.Button(actions, text="结束战斗", style="HeaderDanger.TButton",
                                     command=self.end_battle)
        self.end_button.pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="新建战斗", style="HeaderGhost.TButton", command=self.new_battle).pack(side="right", padx=(8, 0))
        self.next_button = ttk.Button(actions, text="下一位", style="Secondary.TButton",
                                      command=lambda: self.perform(self.battle.next_turn))
        self.next_button.pack(side="right", padx=(8, 0))
        self.start_button = ttk.Button(actions, text="开始战斗", style="Primary.TButton",
                                       command=lambda: self.perform(self.battle.start))
        self.start_button.pack(side="right")

        middle = ttk.Frame(self.root, style="App.TFrame", padding=(18, 18, 18, 0))
        middle.grid(row=1, column=0, sticky="nsew")
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(0, weight=1)
        listing = ttk.Frame(middle, style="Card.TFrame", padding=(14, 14))
        listing.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        listing.columnconfigure(0, weight=1)
        listing.rowconfigure(2, weight=1)
        ttk.Label(listing, text="INITIATIVE ORDER  ·  行动序列", style="Eyebrow.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(listing, text="参战者", style="Section.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 12))
        columns = ("turn", "kind", "name", "initiative", "hp", "condition")
        self.tree = ttk.Treeview(listing, columns=columns, show="headings", selectmode="browse")
        for key, title, width in zip(columns,
                                     ("本轮", "类型", "名称", "先攻", "当前 / 最大 HP", "状态"),
                                     (86, 60, 205, 58, 132, 72)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=width if key != "name" else 110,
                             anchor="w" if key == "name" else "center", stretch=key == "name")
        self.tree.grid(row=2, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(listing, orient="vertical", style="Vertical.TScrollbar", command=self.tree.yview)
        scroll.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure("玩家", foreground="#315F4A")
        self.tree.tag_configure("NPC", foreground="#566484")
        self.tree.tag_configure("怪物", foreground="#8A5A2F")
        self.tree.tag_configure("zero", foreground=c["rust"], background="#F7E8E2")
        self.tree.tag_configure("current", foreground=c["ink"], background=c["sage"], font=self.bold_font)
        self.tree.tag_configure("current_zero", foreground="#84372D", background="#ECDDD3", font=self.bold_font)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.empty_state = ttk.Frame(listing, style="CardBody.TFrame")
        ttk.Label(self.empty_state, text="尚未集结队伍", style="EmptyTitle.TLabel").pack()
        ttk.Label(self.empty_state, text="在右侧填写资料，添加第一名参战者。", style="EmptyBody.TLabel").pack(pady=(6, 0))

        controls = ttk.Frame(listing, style="Toolbar.TFrame", padding=(10, 9))
        controls.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(controls, text="按先攻排序", style="Quiet.TButton",
                   command=lambda: self.perform(self.battle.sort)).pack(side="left")
        ttk.Button(controls, text="同先攻上移", style="Quiet.TButton", command=lambda: self.move(-1)).pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="同先攻下移", style="Quiet.TButton", command=lambda: self.move(1)).pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="移除所选", style="Danger.TButton", command=self.remove).pack(side="right")

        form = ttk.Frame(middle, style="Card.TFrame", padding=(16, 14))
        form.grid(row=0, column=1, sticky="ns")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="COMBATANT  ·  参战者档案", style="Eyebrow.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(form, textvariable=self.form_title, style="Section.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 12))
        for row, (key, title) in enumerate((("name", "名称"), ("kind", "类型"), ("initiative", "先攻值"),
                                           ("max_hp", "最大 HP"), ("hp", "当前 HP")), start=2):
            ttk.Label(form, text=title, style="Body.TLabel").grid(row=row, column=0, sticky="w", pady=7)
            if key == "kind":
                widget = ttk.Combobox(form, textvariable=self.fields[key], values=("玩家", "NPC", "怪物"),
                                      state="readonly", width=15, style="Field.TCombobox")
            else:
                widget = ttk.Entry(form, textvariable=self.fields[key], width=17, style="Field.TEntry")
            widget.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=7)
        ttk.Label(form, text="新增时当前 HP 留空 = 最大 HP\n怪物名称自动加编号（从 1 开始）\n编辑名称时无需输入自动编号。",
                  style="Muted.TLabel", justify="left").grid(row=7, column=0, columnspan=2, sticky="w", pady=(12, 14))
        ttk.Button(form, text="添加为新参战者", style="Primary.TButton", command=self.add).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 7))
        self.edit_button = ttk.Button(form, text="保存所选角色修改", style="Secondary.TButton", command=self.edit)
        self.edit_button.grid(row=9, column=0, columnspan=2, sticky="ew", pady=7)
        ttk.Button(form, text="清空表单 / 取消选择", style="Quiet.TButton", command=self.clear_form).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(7, 0))

        hp_panel = ttk.Frame(self.root, style="Card.TFrame", padding=(14, 12))
        hp_panel.grid(row=2, column=0, sticky="ew", padx=18, pady=(14, 8))
        ttk.Label(hp_panel, text="HP", style="Eyebrow.TLabel").pack(side="left", padx=(0, 8))
        ttk.Label(hp_panel, text="血量操作", style="Section.TLabel").pack(side="left", padx=(0, 14))
        ttk.Label(hp_panel, text="数值", style="Body.TLabel").pack(side="left", padx=(0, 7))
        ttk.Entry(hp_panel, textvariable=self.amount, width=7, style="Field.TEntry").pack(side="left", padx=(0, 12))
        for title, action, button_style in (("受到伤害", "damage", "Damage.TButton"),
                                            ("接受治疗", "heal", "Heal.TButton")):
            ttk.Button(hp_panel, text=title, style=button_style,
                       command=lambda a=action: self.hp_action(a)).pack(side="left", padx=4)

        bottom = ttk.Frame(self.root, style="App.TFrame", padding=(20, 4, 20, 12))
        bottom.grid(row=3, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        ttk.Label(bottom, textvariable=self.status, style="Status.TLabel", wraplength=920).grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="立即保存 / 重试", style="Quiet.TButton", command=self.save).grid(row=0, column=1, padx=(10, 0))

    def _load(self):
        try:
            self.battle = self.store.load()
            self.status.set(f"已恢复上次战斗；每次修改自动保存。存档：{self.store.path}")
        except FileNotFoundError:
            self.status.set(f"未找到存档，已打开空战斗；首次修改后自动创建：{self.store.path}")
        except BattleError as error:
            try:
                backup = self.store.backup_invalid()
                detail = f"原文件已备份到：\n{backup}\n后续操作会创建新的存档。"
            except OSError as backup_error:
                self.protect_original = True
                detail = f"原文件无法备份，已保护原文件。\n请修复目录读写权限后点击“立即保存 / 重试”。\n{backup_error}"
            self.status.set("存档损坏，已打开空战斗。" + ("原文件受保护，尚不能保存。" if self.protect_original else "原文件已备份。"))
            self.root.after_idle(lambda e=str(error), d=detail: messagebox.showwarning("无法恢复存档", f"{e}\n\n已打开空战斗。\n{d}", parent=self.root))
        except OSError as error:
            self.protect_original = True
            self.status.set("无法读取存档，已打开空战斗；原文件受保护，请检查读写权限。")
            self.root.after_idle(lambda e=str(error): messagebox.showwarning("无法读取存档", f"请检查文件和目录读写权限。\n{self.store.path}\n\n{e}\n原存档不会被直接覆盖。", parent=self.root))

    def save(self):
        try:
            if self.protect_original:
                try:
                    self.store.backup_invalid()
                except FileNotFoundError:
                    pass
                self.protect_original = False
            self.store.save(self.battle)
        except OSError as error:
            self.dirty = True
            self.status.set("保存失败！更改仍在内存中。请检查磁盘空间、文件和目录权限，点击“立即保存 / 重试”。")
            messagebox.showerror("保存失败", f"当前修改尚未保存，请勿直接关闭程序。\n{self.store.path}\n\n{error}", parent=self.root)
            return False
        self.dirty = False
        self.status.set(f"已自动保存 · {self.store.path}")
        return True

    def perform(self, operation, selected_id=None):
        try:
            result = operation()
        except BattleError as error:
            messagebox.showwarning("请检查输入", str(error), parent=self.root)
            return False
        self.dirty = True
        if hasattr(result, "id"):
            selected_id = result.id
        self.refresh(selected_id)
        saved = self.save()
        return saved

    def selected_id(self):
        selection = self.tree.selection()
        if not selection:
            raise BattleError("请先在列表中选择一名参战者。")
        return selection[0]

    @staticmethod
    def parse_number(text, label):
        try:
            return int(text.strip())
        except ValueError:
            raise BattleError(f"{label}请输入整数，例如 0、12 或 -1；不能留空或填写小数。") from None

    def form_values(self, adding=False):
        values = {key: var.get().strip() for key, var in self.fields.items()}
        values["initiative"] = self.parse_number(values["initiative"], "先攻值")
        values["max_hp"] = self.parse_number(values["max_hp"], "最大生命值")
        values["hp"] = (None if adding and not values["hp"] else self.parse_number(values["hp"], "当前生命值"))
        return values

    def add(self):
        self.perform(lambda: self.battle.add(**self.form_values(adding=True)))

    def edit(self):
        self.perform(lambda: self.battle.edit(self.selected_id(), **self.form_values()))

    def clear_form(self):
        if self.tree.selection():
            self.tree.selection_remove(*self.tree.selection())
        for key, value in {"name": "", "kind": "玩家", "initiative": "0", "max_hp": "10", "hp": ""}.items():
            self.fields[key].set(value)
        self.form_title.set("添加参战者")
        self.edit_button.configure(state="disabled")

    def on_select(self, _event=None):
        if self.refreshing:
            return
        if not self.tree.selection():
            self.form_title.set("添加参战者")
            self.edit_button.configure(state="disabled")
            return
        actor = self.battle.get(self.tree.selection()[0])
        for key in self.fields:
            self.fields[key].set(str(getattr(actor, key)))
        self.form_title.set("编辑所选参战者")
        self.edit_button.configure(state="normal")

    def move(self, direction):
        self.perform(lambda: self.battle.move_tied(self.selected_id(), direction))

    def remove(self):
        try:
            actor = self.battle.get(self.selected_id())
        except BattleError as error:
            messagebox.showwarning("未选择角色", str(error), parent=self.root)
            return
        if messagebox.askyesno("移除参战者", f"确定移除“{actor.display_name}”？\n此操作不会增加轮数。", parent=self.root):
            self.perform(lambda: self.battle.remove(actor.id))
            self.clear_form()

    def hp_action(self, action):
        def change():
            actor = self.battle.get(self.selected_id())
            amount = self.parse_number(self.amount.get(), "操作数值")
            if amount < 0:
                raise BattleError("血量操作数值不能小于 0。")
            getattr(self.battle, action)(actor.id, amount)
        self.perform(change)

    def refresh(self, selected_id=None):
        old_selection = self.tree.selection()
        if selected_id is None and old_selection:
            selected_id = old_selection[0]
        yview = self.tree.yview()
        self.refreshing = True
        try:
            children = self.tree.get_children()
            if children:
                self.tree.delete(*children)
            for actor in self.battle.combatants:
                current = actor.id == self.battle.current_id
                turn = ("行动中" if current else "已行动" if actor.id in self.battle.acted_ids
                        else "待行动" if self.battle.active else "未开始")
                tag = ("current_zero" if current and actor.hp == 0 else "current" if current
                       else "zero" if actor.hp == 0 else actor.kind)
                self.tree.insert("", "end", iid=actor.id, values=(turn, actor.kind, actor.display_name,
                                 actor.initiative, f"{actor.hp} / {actor.max_hp}",
                                 "0 HP" if actor.hp == 0 else "—"), tags=(tag,))
            if selected_id and self.tree.exists(selected_id):
                self.tree.selection_set(selected_id)
            if yview:
                self.tree.yview_moveto(yview[0])
        finally:
            self.refreshing = False
        if self.battle.combatants:
            self.empty_state.place_forget()
        else:
            self.empty_state.place(relx=0.5, rely=0.48, anchor="center")
            self.empty_state.lift()
        self.on_select()
        if not self.battle.active:
            self.heading.set(f"准备战斗 · {len(self.battle.combatants)} 名参战者")
        elif self.battle.current_id:
            actor = self.battle.get(self.battle.current_id)
            short_name = actor.display_name if len(actor.display_name) <= 22 else actor.display_name[:21] + "…"
            self.heading.set(f"第 {self.battle.round} 轮 · 当前：{short_name}")
            self.tree.see(actor.id)
        else:
            self.heading.set(f"第 {self.battle.round} 轮已结束 · 点击下一位进入下一轮")
        self.start_button.configure(state="disabled" if self.battle.active else "normal")
        self.next_button.configure(state="normal" if self.battle.active else "disabled")
        self.end_button.configure(state="normal" if self.battle.active else "disabled")

    def end_battle(self):
        if self.perform(self.battle.end):
            self.status.set("战斗已结束；参战者、顺序与当前 HP 均已保留，可以再次开始战斗。")

    def new_battle(self):
        if messagebox.askyesno("新建战斗", "确定清空所有参战者和轮次，开始一场新战斗？\n当前存档也会被新的空战斗替换。", parent=self.root):
            self.battle = Battle()
            self.dirty = True
            self.clear_form()
            self.refresh()
            self.save()

    def close(self):
        if self.dirty and not self.save():
            if not messagebox.askyesno("仍有未保存的更改", "保存仍然失败。确定放弃本次未保存的更改并退出？", parent=self.root):
                return
        self.root.destroy()


def main():
    if sys.platform == "darwin" and tk.TkVersion < 8.6:
        print("当前 Python 使用 macOS 旧版 Tk 8.5，可能只显示空白窗口。\n"
              "请安装带 Tk 8.6 或更高版本的 Python，并运行 python3 -m tkinter 检查。\n"
              "详细安装方式请参阅同目录 README.md。", file=sys.stderr)
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"无法启动图形界面：{error}\n请在有桌面的本地系统中运行，并用 python3 -m tkinter 检查 Tkinter。", file=sys.stderr)
        return 1
    BattleApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

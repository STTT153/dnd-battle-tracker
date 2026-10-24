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
from svg_icons import SvgIconButton


SAVE_PATH = Path(__file__).resolve().with_name("battle_save.json")
RESOURCES_DIR = Path(__file__).resolve().with_name("resources")


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
        self.form_mode = "add"
        self._form_resize_job = None
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
        self.root.minsize(1080, 580)

        # 接近 VS Code Dark Modern 的深色分层；焦点使用蓝色，运行状态使用绿色。
        self.colors = {
            "ink": "#CCCCCC",
            "pine": "#181818",
            "pine_hover": "#2A2D2E",
            "moss": "#2D7D46",
            "sky": "#3794FF",
            "sky_dark": "#0E639C",
            "parchment": "#181818",
            "paper": "#1F1F1F",
            "paper_alt": "#252526",
            "line": "#3E3E42",
            "line_dark": "#555555",
            "gold": "#0E639C",
            "gold_hover": "#1177BB",
            "rust": "#C74E39",
            "rust_hover": "#DA5A45",
            "sage": "#20382B",
            "mist": "#2A2D2E",
            "muted": "#9D9D9D",
            "white": "#F0F0F0",
            "input": "#313131",
            "selection": "#094771",
            "focus": "#007FD4",
        }
        self.root.configure(background=self.colors["parchment"])
        self.root.option_add("*TCombobox*Listbox.background", self.colors["input"])
        self.root.option_add("*TCombobox*Listbox.foreground", self.colors["ink"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.colors["selection"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.colors["white"])

        families = set(font.families(self.root))
        ui_family = next((name for name in ("PingFang SC", "SF Pro Text", "Helvetica Neue", "Arial")
                          if name in families), "TkDefaultFont")
        display_family = ui_family
        font.nametofont("TkDefaultFont").configure(family=ui_family, size=12)
        font.nametofont("TkTextFont").configure(family=ui_family, size=12)
        font.nametofont("TkMenuFont").configure(family=ui_family, size=12)
        font.nametofont("TkHeadingFont").configure(family=ui_family, size=12, weight="bold")
        self.body_font = font.Font(self.root, family=ui_family, size=12)
        self.small_font = font.Font(self.root, family=ui_family, size=10)
        self.caption_font = font.Font(self.root, family=ui_family, size=9, weight="bold")
        self.bold_font = font.Font(self.root, family=ui_family, size=12, weight="bold")
        self.title_font = font.Font(self.root, family=display_family, size=18, weight="bold")
        self.section_font = font.Font(self.root, family=display_family, size=14, weight="bold")

        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        c = self.colors
        style.configure("App.TFrame", background=c["parchment"])
        style.configure("Header.TFrame", background=c["pine"])
        style.configure("Card.TFrame", background=c["paper"], relief="solid", borderwidth=1,
                        bordercolor=c["line"])
        style.configure("CardBody.TFrame", background=c["paper"])
        style.configure("App.TPanedwindow", background=c["parchment"])
        style.configure("Toolbar.TFrame", background=c["paper_alt"])
        style.configure("HeaderTitle.TLabel", background=c["pine"], foreground=c["white"], font=self.title_font)
        style.configure("HeaderMeta.TLabel", background=c["pine"], foreground=c["muted"], font=self.small_font)
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
        style.configure("Primary.TButton", background=c["gold"], foreground=c["white"], **button_base)
        style.map("Primary.TButton",
                  background=[("disabled", "#3A3D41"), ("pressed", "#094E7A"), ("active", c["gold_hover"])],
                  foreground=[("disabled", "#808080")])
        style.configure("Secondary.TButton", background=c["sky_dark"], foreground=c["white"], **button_base)
        style.map("Secondary.TButton",
                  background=[("disabled", "#3A3D41"), ("pressed", "#094E7A"), ("active", c["gold_hover"])],
                  foreground=[("disabled", "#808080")])
        style.configure("HeaderGhost.TButton", background=c["pine"], foreground=c["white"],
                        font=self.bold_font, padding=(13, 8), relief="solid", borderwidth=1)
        style.map("HeaderGhost.TButton",
                  background=[("pressed", "#333333"), ("active", c["pine_hover"])],
                  bordercolor=[("focus", c["focus"]), ("!focus", c["line_dark"])])
        style.configure("HeaderDanger.TButton", background=c["rust"], foreground=c["white"],
                        font=self.bold_font, padding=(13, 8), relief="flat", borderwidth=0)
        style.map("HeaderDanger.TButton",
                  background=[("disabled", "#3A3D41"), ("pressed", "#973D2C"), ("active", c["rust_hover"])],
                  foreground=[("disabled", "#808080")])
        style.configure("Quiet.TButton", background=c["paper_alt"], foreground=c["ink"],
                        font=self.body_font, padding=(11, 7), relief="flat", borderwidth=0)
        style.map("Quiet.TButton", background=[("pressed", "#333333"), ("active", c["pine_hover"])],
                  bordercolor=[("focus", c["focus"])])
        style.configure("Danger.TButton", background=c["paper_alt"], foreground=c["rust"],
                        font=self.bold_font, padding=(11, 7), relief="flat", borderwidth=0)
        style.map("Danger.TButton", background=[("pressed", "#3A2927"), ("active", "#342522")],
                  foreground=[("active", c["rust_hover"])])
        style.configure("FormFooter.TFrame", background=c["paper"])
        style.configure("Damage.TButton", background=c["rust"], foreground=c["white"], **button_base)
        style.map("Damage.TButton", background=[("pressed", "#973D2C"), ("active", c["rust_hover"])])
        style.configure("Heal.TButton", background=c["moss"], foreground=c["white"], **button_base)
        style.map("Heal.TButton", background=[("pressed", "#245F37"), ("active", "#379354")])
        style.configure("Field.TEntry", fieldbackground=c["input"], foreground=c["white"],
                        bordercolor=c["line"], lightcolor=c["line"], darkcolor=c["line"],
                        insertcolor=c["white"], padding=(9, 8))
        style.map("Field.TEntry", bordercolor=[("focus", c["focus"])], lightcolor=[("focus", c["focus"])])
        style.configure("Field.TCombobox", fieldbackground=c["input"], background=c["input"],
                        foreground=c["ink"], bordercolor=c["line"], arrowcolor=c["ink"], padding=(9, 7))
        style.map("Field.TCombobox", bordercolor=[("focus", c["focus"])],
                  fieldbackground=[("readonly", c["input"])], foreground=[("readonly", c["ink"])])
        style.configure("Treeview", background=c["paper"], fieldbackground=c["paper"], foreground=c["ink"],
                        bordercolor=c["line"], lightcolor=c["line"], darkcolor=c["line"],
                        rowheight=42, font=self.body_font)
        style.map("Treeview", background=[("selected", c["selection"])], foreground=[("selected", c["white"])])
        style.configure("Treeview.Heading", background=c["paper_alt"], foreground=c["ink"],
                        bordercolor=c["line"], relief="flat", padding=(8, 10), font=self.bold_font)
        style.map("Treeview.Heading", background=[("active", c["pine_hover"])])
        style.configure("Vertical.TScrollbar", background="#424242", troughcolor=c["paper"],
                        bordercolor=c["paper"], lightcolor="#424242", darkcolor="#424242",
                        arrowcolor=c["ink"], relief="flat", borderwidth=0)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 11))
        top.grid(row=0, column=0, sticky="ew")
        brand = ttk.Frame(top, style="Header.TFrame")
        brand.pack(side="left", fill="y")
        ttk.Label(brand, text="战斗纪事", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(brand, textvariable=self.heading, style="HeaderMeta.TLabel").pack(anchor="w", pady=(3, 0))
        actions = ttk.Frame(top, style="Header.TFrame")
        actions.pack(side="right", fill="y")
        self.end_button = SvgIconButton(
            actions, RESOURCES_DIR / "Stop.svg", c["white"],
            command=self.end_battle, icon_name="Stop", disabled_color=c["white"])
        self.end_button.pack(side="right", padx=(2, 0))
        self.next_button = SvgIconButton(
            actions, RESOURCES_DIR / "Next.svg", c["white"],
            command=lambda: self.perform(self.battle.next_turn), icon_name="Next",
            disabled_color=c["white"])
        self.next_button.pack(side="right", padx=(2, 0))
        self.start_button = SvgIconButton(
            actions, RESOURCES_DIR / "Play.svg", c["white"],
            command=lambda: self.perform(self.battle.start), icon_name="Play",
            disabled_color=c["white"])
        self.start_button.pack(side="right", padx=(2, 0))

        middle = ttk.Frame(self.root, style="App.TFrame", padding=(18, 18, 18, 0))
        middle.grid(row=1, column=0, sticky="nsew")
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(0, weight=1)
        self.main_pane = ttk.Panedwindow(middle, orient="horizontal", style="App.TPanedwindow")
        self.main_pane.grid(row=0, column=0, sticky="nsew")
        listing = ttk.Frame(self.main_pane, style="Card.TFrame", padding=(14, 14))
        listing.columnconfigure(0, weight=1)
        listing.rowconfigure(1, weight=1)
        listing_header = ttk.Frame(listing, style="CardBody.TFrame")
        listing_header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.add_monster_button = SvgIconButton(
            listing_header, RESOURCES_DIR / "AddMonster.svg", c["white"],
            command=lambda: self.prepare_add("怪物"), icon_name="添加怪物",
            bg=c["paper"], hover_bg=c["pine_hover"], disabled_color=c["white"])
        self.add_monster_button.pack(side="right")
        self.add_player_button = SvgIconButton(
            listing_header, RESOURCES_DIR / "AddPlayer.svg", c["white"],
            command=lambda: self.prepare_add("玩家"), icon_name="添加玩家",
            bg=c["paper"], hover_bg=c["pine_hover"], disabled_color=c["white"])
        self.add_player_button.pack(side="right", padx=(0, 2))
        columns = ("turn", "kind", "name", "initiative", "hp", "condition")
        self.tree = ttk.Treeview(listing, columns=columns, show="headings", selectmode="browse")
        for key, title, width in zip(columns,
                                     ("本轮", "类型", "名称", "先攻", "当前 / 最大 HP", "状态"),
                                     (86, 60, 205, 58, 132, 72)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=width if key != "name" else 110,
                             anchor="w" if key == "name" else "center", stretch=key == "name")
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        scroll = ttk.Scrollbar(listing, orient="vertical", style="Vertical.TScrollbar", command=self.tree.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(10, 0))
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure("玩家", foreground="#89D185")
        self.tree.tag_configure("NPC", foreground="#9CDCFE")
        self.tree.tag_configure("怪物", foreground="#DCDCAA")
        self.tree.tag_configure("zero", foreground="#F48771", background="#3A2323")
        self.tree.tag_configure("current", foreground=c["ink"], background=c["sage"], font=self.bold_font)
        self.tree.tag_configure("current_zero", foreground="#F48771", background="#412828", font=self.bold_font)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click, add="+")
        self.empty_state = ttk.Frame(listing, style="CardBody.TFrame")
        ttk.Label(self.empty_state, text="尚未集结队伍", style="EmptyTitle.TLabel").pack()
        ttk.Label(self.empty_state, text="使用列表右上角的玩家或怪物图标开始。", style="EmptyBody.TLabel").pack(pady=(6, 0))

        controls = ttk.Frame(listing, style="Toolbar.TFrame", padding=(10, 9))
        controls.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(controls, text="按先攻排序", style="Quiet.TButton",
                   command=lambda: self.perform(self.battle.sort)).pack(side="left")
        ttk.Button(controls, text="同先攻上移", style="Quiet.TButton", command=lambda: self.move(-1)).pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="同先攻下移", style="Quiet.TButton", command=lambda: self.move(1)).pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="移除所选", style="Danger.TButton", command=self.remove).pack(side="right")

        self.form_shell = ttk.Frame(self.main_pane, style="Card.TFrame")
        self.form_shell.columnconfigure(0, weight=1)
        self.form_shell.rowconfigure(1, weight=1)
        form_header = ttk.Frame(self.form_shell, style="CardBody.TFrame", padding=(16, 12, 8, 10))
        form_header.grid(row=0, column=0, columnspan=2, sticky="ew")
        form_header.columnconfigure(0, weight=1)
        self.form_close_button = SvgIconButton(
            form_header, RESOURCES_DIR / "Close.svg", c["white"],
            command=self.hide_form, icon_name="关闭档案",
            bg=c["paper"], hover_bg=c["pine_hover"], disabled_color=c["white"])
        self.form_close_button.grid(row=0, column=1, sticky="ne")
        ttk.Label(form_header, textvariable=self.form_title, style="Section.TLabel").grid(
            row=0, column=0, sticky="w")
        self.form_canvas = tk.Canvas(self.form_shell, width=300, background=c["paper"],
                                     highlightthickness=0, borderwidth=0)
        self.form_canvas.grid(row=1, column=0, sticky="nsew")
        self.form_scrollbar = ttk.Scrollbar(self.form_shell, orient="vertical", style="Vertical.TScrollbar",
                                            command=self.form_canvas.yview)
        self.form_scrollbar.grid(row=1, column=1, sticky="ns")
        self.form_canvas.configure(yscrollcommand=self.form_scrollbar.set)
        form = ttk.Frame(self.form_canvas, style="CardBody.TFrame", padding=(16, 14))
        form_window = self.form_canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _event: self.form_canvas.configure(
            scrollregion=self.form_canvas.bbox("all")))
        self.form_canvas.bind("<Configure>", lambda event: self.form_canvas.itemconfigure(
            form_window, width=event.width))
        form.columnconfigure(1, weight=1)
        for row, (key, title) in enumerate((("name", "名称"), ("kind", "类型"), ("initiative", "先攻值"),
                                           ("max_hp", "最大 HP"), ("hp", "当前 HP")), start=0):
            ttk.Label(form, text=title, style="Body.TLabel").grid(row=row, column=0, sticky="w", pady=7)
            if key == "kind":
                widget = ttk.Combobox(form, textvariable=self.fields[key], values=("玩家", "NPC", "怪物"),
                                      state="readonly", width=15, style="Field.TCombobox")
            else:
                widget = ttk.Entry(form, textvariable=self.fields[key], width=17, style="Field.TEntry")
            widget.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=7)
        form_footer = ttk.Frame(self.form_shell, style="FormFooter.TFrame", padding=(16, 10, 16, 14))
        form_footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.form_action_button = ttk.Button(form_footer, text="确认添加", style="Primary.TButton",
                                             command=self.commit_form)
        self.form_action_button.pack(fill="x")
        self.main_pane.add(listing, weight=4)
        self.main_pane.add(self.form_shell, weight=1)
        self.form_visible = True
        self.form_width = 360
        self._schedule_form_width()

        hp_panel = ttk.Frame(self.root, style="Card.TFrame", padding=(14, 12))
        hp_panel.grid(row=2, column=0, sticky="ew", padx=18, pady=(14, 8))
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
        self.prepare_add("玩家")

    def prepare_add(self, kind):
        if self.tree.selection():
            self.tree.selection_remove(*self.tree.selection())
        for key, value in {"name": "", "kind": kind, "initiative": "0", "max_hp": "10", "hp": ""}.items():
            self.fields[key].set(value)
        self.form_mode = "add"
        self.form_title.set(f"添加{kind}")
        self.form_action_button.configure(text="确认添加", style="Primary.TButton")
        self.show_form()

    def commit_form(self):
        if self.form_mode == "edit":
            self.edit()
        else:
            self.add()

    def hide_form(self):
        if not self.form_visible:
            return
        if self._form_resize_job is not None:
            try:
                self.root.after_cancel(self._form_resize_job)
            except tk.TclError:
                pass
            self._form_resize_job = None
        self.main_pane.forget(self.form_shell)
        self.form_visible = False

    def show_form(self):
        if not self.form_visible:
            self.main_pane.add(self.form_shell, weight=1)
            self.form_visible = True
        # 先同步完成 pane 的几何计算，让侧栏在本次点击中就展开；再在空闲时
        # 校正一次，兼容 macOS/Tk 在重新插入 pane 后延迟分配尺寸的行为。
        try:
            self.root.update_idletasks()
        except tk.TclError:
            return
        self._restore_form_width()
        self._schedule_form_width()

    def _schedule_form_width(self):
        if self._form_resize_job is not None:
            try:
                self.root.after_cancel(self._form_resize_job)
            except tk.TclError:
                return
        try:
            self._form_resize_job = self.root.after_idle(self._restore_form_width)
        except tk.TclError:
            self._form_resize_job = None

    def _restore_form_width(self):
        self._form_resize_job = None
        try:
            if (not self.form_visible or not self.main_pane.winfo_exists()
                    or len(self.main_pane.panes()) < 2):
                return
            self.main_pane.update_idletasks()
            total = self.main_pane.winfo_width()
            if total <= 1:
                return
            panel_width = min(self.form_width, max(280, total - 520))
            position = total - panel_width
            self.main_pane.sashpos(0, position)
        except tk.TclError:
            pass

    def on_tree_click(self, event):
        if self.tree.identify_row(event.y):
            self.root.after_idle(self.on_select)

    def on_select(self, _event=None):
        if self.refreshing:
            return
        if not self.tree.selection():
            return
        actor = self.battle.get(self.tree.selection()[0])
        for key in self.fields:
            self.fields[key].set(str(getattr(actor, key)))
        self.form_mode = "edit"
        self.form_title.set(actor.display_name)
        self.form_action_button.configure(text="保存修改", style="Secondary.TButton")
        self.show_form()

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

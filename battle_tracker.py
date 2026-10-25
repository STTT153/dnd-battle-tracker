#!/usr/bin/env python3
"""启动中文 Tkinter 战斗追踪器：python3 battle_tracker.py。"""

import copy
import json
import sys
from pathlib import Path

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


class CompactPanedWindow(tk.PanedWindow):
    """A two-pixel sash with the position API used by ttk.Panedwindow."""

    def add(self, child, **options):
        options.pop("weight", None)
        super().add(child, **options)

    def sashpos(self, index, position=None):
        if position is None:
            return self.sash_coord(index)[0]
        self.sash_place(index, position, 0)
        return self.sash_coord(index)[0]


class BattleApp:
    def __init__(self, root, save_path=SAVE_PATH):
        self.root = root
        self.store = JsonStore(save_path)
        self.battle = Battle()
        self.dirty = False
        self.protect_original = False
        self.refreshing = False
        self.status = tk.StringVar(value="")
        self.combatant_count = tk.StringVar(value="参战人数: 0")
        self.round_count = tk.StringVar(value="回合数: 0")
        self.form_title = tk.StringVar(value="添加参战者")
        self.form_mode = "add"
        self._form_resize_job = None
        self._drag_resize_job = None
        self._drag_pointer_x = None
        self._drag_grab_offset = 0
        self._form_wheel_remainder = 0.0
        self._list_wheel_remainder = 0.0
        self._handbook_monsters = None
        self._monster_picker = None
        self._recent_monsters = []
        self.fields = {key: tk.StringVar() for key in ("name", "initiative", "max_hp", "hp")}
        self.form_kind = "玩家"
        self.form_monster_stats = None
        self.amount = tk.StringVar(value="1")
        self._copied_combatant = None
        self._build_ui()
        self.clear_form()
        self._load()
        self.refresh()
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        self.root.title("Dungeon Master Studio")
        self.root.geometry("1240x780")
        self.root.minsize(1080, 580)

        # 接近 VS Code Dark Modern 的深色分层；焦点使用蓝色，运行状态使用绿色。
        self.colors = {
            "ink": "#CCCCCC",
            "pine": "#3C3C3C",
            "pine_hover": "#2A2D2E",
            "moss": "#2D7D46",
            "sky": "#3794FF",
            "sky_dark": "#0E639C",
            "parchment": "#3C3C3C",
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
            "status_blue": "#007ACC",
        }
        self.root.configure(background=self.colors["parchment"])
        self.root.option_add("*TCombobox*Listbox.background", self.colors["input"])
        self.root.option_add("*TCombobox*Listbox.foreground", self.colors["ink"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.colors["selection"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.colors["white"])

        families = set(font.families(self.root))
        ui_family = next((name for name in ("PingFang SC", "SF Pro Text", "Helvetica Neue", "Arial")
                          if name in families), "TkDefaultFont")
        font.nametofont("TkDefaultFont").configure(family=ui_family, size=12)
        font.nametofont("TkTextFont").configure(family=ui_family, size=12)
        font.nametofont("TkMenuFont").configure(family=ui_family, size=12)
        font.nametofont("TkHeadingFont").configure(family=ui_family, size=12, weight="bold")
        self.body_font = font.Font(self.root, family=ui_family, size=12)
        self.small_font = font.Font(self.root, family=ui_family, size=10)
        self.caption_font = font.Font(self.root, family=ui_family, size=9, weight="bold")
        self.bold_font = font.Font(self.root, family=ui_family, size=12, weight="bold")
        self.section_font = font.Font(self.root, family=ui_family, size=14, weight="bold")

        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        c = self.colors
        style.configure("App.TFrame", background=c["parchment"])
        style.configure("Header.TFrame", background=c["pine"])
        style.configure("Card.TFrame", background=c["paper"], relief="solid", borderwidth=1,
                        bordercolor=c["line"])
        style.configure("HP.TFrame", background=c["paper"], relief="flat", borderwidth=0)
        style.configure("List.TFrame", background=c["paper"], relief="flat", borderwidth=0)
        style.configure("CardBody.TFrame", background=c["paper"])
        style.configure("StatusBar.TFrame", background=c["status_blue"])
        style.configure("StatusBar.TLabel", background=c["status_blue"], foreground="#FFFFFF",
                        font=self.small_font)
        style.configure("Toolbar.TFrame", background=c["paper_alt"])
        style.configure("Eyebrow.TLabel", background=c["paper"], foreground=c["sky_dark"], font=self.caption_font)
        style.configure("Section.TLabel", background=c["paper"], foreground=c["ink"], font=self.section_font)
        style.configure("Body.TLabel", background=c["paper"], foreground=c["ink"], font=self.body_font)
        style.configure("Muted.TLabel", background=c["paper"], foreground=c["muted"], font=self.small_font)
        style.configure("Toolbar.TLabel", background=c["paper_alt"], foreground=c["ink"], font=self.body_font)
        style.configure("ToolbarMuted.TLabel", background=c["paper_alt"], foreground=c["muted"], font=self.small_font)
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
                        borderwidth=0, relief="flat", rowheight=42, font=self.body_font)
        style.layout("Treeview", [
            ("Treeview.padding", {"sticky": "nswe", "children": [
                ("Treeview.treearea", {"sticky": "nswe"})
            ]})
        ])
        style.map("Treeview", background=[("selected", c["selection"])], foreground=[("selected", c["white"])])
        style.configure("Treeview.Heading", background=c["paper_alt"], foreground=c["ink"],
                        bordercolor=c["line"], relief="flat", padding=(8, 10), font=self.bold_font)
        style.map("Treeview.Heading", background=[("active", c["pine_hover"])])
        style.configure("Vertical.TScrollbar", background="#424242", troughcolor=c["paper"],
                        bordercolor=c["paper"], lightcolor="#424242", darkcolor="#424242",
                        arrowcolor=c["ink"], relief="flat", borderwidth=0)
        style.layout("Form.Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
            ]})
        ])
        style.configure("Form.Vertical.TScrollbar", background="#505050", troughcolor=c["paper"],
                        bordercolor=c["paper"], lightcolor="#505050", darkcolor="#505050",
                        relief="flat", borderwidth=0, width=8)
        style.map("Form.Vertical.TScrollbar", background=[("active", "#626262")],
                  lightcolor=[("active", "#626262")], darkcolor=[("active", "#626262")])
        style.layout("List.Vertical.TScrollbar", style.layout("Form.Vertical.TScrollbar"))
        style.configure("List.Vertical.TScrollbar", background="#363636", troughcolor=c["paper"],
                        bordercolor=c["paper"], lightcolor="#363636", darkcolor="#363636",
                        relief="flat", borderwidth=0, width=8)
        style.map("List.Vertical.TScrollbar", background=[("active", "#505050")],
                  lightcolor=[("active", "#505050")], darkcolor=[("active", "#505050")])

        layout_gap = 4
        self.layout_gap = layout_gap
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, style="Header.TFrame",
                        padding=(layout_gap, layout_gap, layout_gap, 0))
        top.grid(row=0, column=0, sticky="ew")
        actions = ttk.Frame(top, style="Header.TFrame")
        actions.pack(side="right", fill="y")
        self.end_button = SvgIconButton(
            actions, RESOURCES_DIR / "Stop.svg", c["white"],
            command=self.end_battle, icon_name="Stop", disabled_color=c["white"],
            bg=c["pine"], hover_bg="#505050", pressed_bg="#5A5A5A")
        self.end_button.pack(side="right", padx=(2, 0))
        self.next_button = SvgIconButton(
            actions, RESOURCES_DIR / "Next.svg", c["white"],
            command=lambda: self.perform(self.battle.next_turn), icon_name="Next",
            disabled_color=c["white"], bg=c["pine"], hover_bg="#505050",
            pressed_bg="#5A5A5A")
        self.next_button.pack(side="right", padx=(2, 0))
        self.start_button = SvgIconButton(
            actions, RESOURCES_DIR / "Play.svg", c["white"],
            command=lambda: self.perform(self.battle.start), icon_name="Play",
            disabled_color=c["white"], bg=c["pine"], hover_bg="#505050",
            pressed_bg="#5A5A5A")
        self.start_button.pack(side="right", padx=(2, 0))

        middle = ttk.Frame(self.root, style="App.TFrame",
                           padding=(layout_gap, layout_gap, layout_gap, 0))
        middle.grid(row=1, column=0, sticky="nsew")
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(0, weight=1)
        self.main_pane = CompactPanedWindow(
            middle, orient="horizontal", background=c["parchment"],
            sashwidth=layout_gap, sashpad=0, borderwidth=0,
            relief="flat", sashrelief="flat", showhandle=False)
        self.main_pane.grid(row=0, column=0, sticky="nsew")
        listing = ttk.Frame(self.main_pane, style="List.TFrame", padding=(14, 14))
        self.listing = listing
        listing.columnconfigure(0, weight=1)
        listing.rowconfigure(1, weight=1)
        listing_header = ttk.Frame(listing, style="CardBody.TFrame")
        listing_header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.add_monster_button = SvgIconButton(
            listing_header, RESOURCES_DIR / "AddMonster.svg", c["white"],
            command=self.open_monster_picker, icon_name="添加怪物",
            bg=c["paper"], hover_bg=c["pine_hover"], disabled_color=c["white"])
        self.add_monster_button.pack(side="right")
        self.add_player_button = SvgIconButton(
            listing_header, RESOURCES_DIR / "AddPlayer.svg", c["white"],
            command=lambda: self.prepare_add("玩家"), icon_name="添加玩家",
            bg=c["paper"], hover_bg=c["pine_hover"], disabled_color=c["white"])
        self.add_player_button.pack(side="right", padx=(0, 2))
        columns = ("turn", "kind", "name", "initiative", "hp", "condition")
        self.tree_columns = columns
        self.tree_headings = ("本轮", "类型", "名称", "先攻", "当前 / 最大 HP", "状态")
        list_view = ttk.Frame(listing, style="CardBody.TFrame")
        list_view.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        list_view.columnconfigure(0, weight=1)
        list_view.rowconfigure(1, weight=1)
        self.list_heading = tk.Canvas(list_view, height=42, background=c["paper_alt"],
                                      highlightthickness=0, borderwidth=0)
        self.list_heading.grid(row=0, column=0, sticky="ew")
        self.list_canvas = tk.Canvas(list_view, background=c["paper"],
                                     highlightthickness=0, borderwidth=0)
        self.list_canvas.grid(row=1, column=0, sticky="nsew")
        self.tree = ttk.Treeview(self.list_canvas, columns=columns, show="", height=1,
                                 selectmode="browse")
        for key, title, width in zip(columns,
                                     self.tree_headings,
                                     (86, 60, 205, 58, 132, 72)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=width if key != "name" else 110,
                             anchor="w" if key == "name" else "center", stretch=key == "name")
        self.list_tree_window = self.list_canvas.create_window((0, 0), window=self.tree, anchor="nw")
        self.list_canvas.bind("<Configure>", self._resize_list_canvas)
        self.tree.bind("<Configure>", self._update_list_scrollregion)
        self.list_scrollbar = ttk.Scrollbar(listing, orient="vertical", style="List.Vertical.TScrollbar",
                                            command=self.list_canvas.yview)
        self.list_scrollbar.grid(row=1, column=1, sticky="ns", pady=(10, 0))
        self.list_canvas.configure(yscrollcommand=self.list_scrollbar.set)
        self.tree.tag_configure("玩家", foreground="#89D185")
        self.tree.tag_configure("NPC", foreground="#9CDCFE")
        self.tree.tag_configure("怪物", foreground="#DCDCAA")
        self.tree.tag_configure("zero", foreground="#F48771", background="#3A2323")
        self.tree.tag_configure("current", foreground=c["ink"], background=c["sage"], font=self.bold_font)
        self.tree.tag_configure("current_zero", foreground="#F48771", background="#412828", font=self.bold_font)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click, add="+")
        # 先于 Treeview 的按行滚动类绑定处理，避免左侧一次手势叠加两种滚动。
        self.tree.bind("<MouseWheel>", self._scroll_list_with_wheel)
        self.tree.bind("<Button-4>", self._scroll_list_with_wheel)
        self.tree.bind("<Button-5>", self._scroll_list_with_wheel)
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
        self.form_scrollbar = ttk.Scrollbar(self.form_shell, orient="vertical", style="Form.Vertical.TScrollbar",
                                            command=self.form_canvas.yview)
        self.form_scrollbar.grid(row=1, column=1, sticky="ns")
        self.form_canvas.configure(yscrollcommand=self.form_scrollbar.set)
        self.root.bind_all("<MouseWheel>", self._scroll_form_with_wheel)
        self.root.bind_all("<Button-4>", self._scroll_form_with_wheel)
        self.root.bind_all("<Button-5>", self._scroll_form_with_wheel)
        self.root.bind_all("<MouseWheel>", self._scroll_list_with_wheel, add="+")
        self.root.bind_all("<Button-4>", self._scroll_list_with_wheel, add="+")
        self.root.bind_all("<Button-5>", self._scroll_list_with_wheel, add="+")
        form = ttk.Frame(self.form_canvas, style="CardBody.TFrame", padding=(16, 14))
        form_window = self.form_canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _event: self.form_canvas.configure(
            scrollregion=self.form_canvas.bbox("all")))
        self.form_canvas.bind("<Configure>", lambda event: self.form_canvas.itemconfigure(
            form_window, width=event.width))
        form.columnconfigure(1, weight=1)
        for row, (key, title) in enumerate((("name", "名称"), ("initiative", "先攻值"),
                                           ("max_hp", "最大 HP"), ("hp", "当前 HP")), start=0):
            ttk.Label(form, text=title, style="Body.TLabel").grid(row=row, column=0, sticky="w", pady=7)
            widget = ttk.Entry(form, textvariable=self.fields[key], width=17, style="Field.TEntry")
            widget.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=7)
        self.monster_stats_frame = ttk.Frame(form, style="CardBody.TFrame")
        self.monster_stats_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.monster_stats_frame.columnconfigure(0, weight=1)
        self.monster_stats_frame.grid_remove()
        form_footer = ttk.Frame(self.form_shell, style="FormFooter.TFrame", padding=(16, 10, 16, 14))
        form_footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.form_action_button = ttk.Button(form_footer, text="确认添加", style="Primary.TButton",
                                             command=self.commit_form)
        self.form_action_button.pack(fill="x")
        self.main_pane.add(listing, weight=4)
        self.main_pane.add(self.form_shell, weight=1)
        self.form_visible = True
        self.form_width = 360
        self.resize_handle = tk.Frame(self.main_pane, background=c["parchment"],
                                      cursor="sb_h_double_arrow")
        self.resize_handle.bind("<ButtonPress-1>", self._start_panel_resize)
        self.resize_handle.bind("<B1-Motion>", self._drag_panel_resize)
        self.resize_handle.bind("<ButtonRelease-1>", self._finish_panel_resize)
        self.main_pane.bind("<Configure>", self._position_resize_handle)
        self._schedule_form_width()

        self.hp_panel = ttk.Frame(self.root, style="HP.TFrame", padding=(14, 12))
        self.hp_panel.grid(row=2, column=0, sticky="ew", padx=layout_gap,
                           pady=(layout_gap, layout_gap))
        ttk.Label(self.hp_panel, text="数值", style="Body.TLabel").pack(side="left", padx=(0, 7))
        ttk.Entry(self.hp_panel, textvariable=self.amount, width=7, style="Field.TEntry").pack(side="left", padx=(0, 12))
        for title, action, button_style in (("受到伤害", "damage", "Damage.TButton"),
                                            ("接受治疗", "heal", "Heal.TButton")):
            ttk.Button(self.hp_panel, text=title, style=button_style,
                       command=lambda a=action: self.hp_action(a)).pack(side="left", padx=4)

        self.status_bar = ttk.Frame(self.root, style="StatusBar.TFrame", padding=(12, 4))
        self.status_bar.grid(row=3, column=0, sticky="ew")
        ttk.Label(self.status_bar, textvariable=self.combatant_count,
                  style="StatusBar.TLabel").pack(side="left")
        ttk.Label(self.status_bar, textvariable=self.round_count,
                  style="StatusBar.TLabel").pack(side="left", padx=(20, 0))

        self.root.bind("<Command-BackSpace>", self._shortcut_delete)
        self.root.bind("<Command-Delete>", self._shortcut_delete)
        self.root.bind("<Command-c>", self._shortcut_copy)
        self.root.bind("<Command-v>", self._shortcut_paste)

    def _resize_list_canvas(self, event):
        widths = [self.tree.column(key, "width") for key in self.tree_columns]
        fixed_width = sum(widths) - widths[2]
        widths[2] = max(110, event.width - fixed_width)
        self.tree.column("name", width=widths[2])
        self.list_canvas.itemconfigure(self.list_tree_window, width=event.width)
        self.list_heading.delete("all")
        x = 0
        for title, width in zip(self.tree_headings, widths):
            self.list_heading.create_text(x + width / 2, 21, text=title,
                                          fill=self.colors["ink"], font=self.bold_font)
            x += width

    def _update_list_scrollregion(self, _event=None):
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))

    def _pointer_in_widgets(self, event, widgets):
        try:
            target = self.root.winfo_containing(event.x_root, event.y_root)
        except (AttributeError, tk.TclError):
            target = event.widget
        while target is not None:
            if target in widgets:
                return True
            target = target.master
        return False

    def _scroll_form_with_wheel(self, event):
        """按像素滚动右侧档案。"""
        if not self.form_visible or not self._pointer_in_widgets(
                event, (self.form_canvas, self.form_scrollbar)):
            return
        return self._scroll_canvas_with_wheel(self.form_canvas, event, "_form_wheel_remainder")

    def _scroll_list_with_wheel(self, event):
        """按像素滚动参战者列表，表头保持固定。"""
        if not self._pointer_in_widgets(
                event, (self.tree, self.list_canvas, self.list_heading, self.list_scrollbar)):
            return
        return self._scroll_canvas_with_wheel(self.list_canvas, event, "_list_wheel_remainder") or "break"

    def _scroll_canvas_with_wheel(self, canvas, event, remainder_name):
        bounds = canvas.bbox("all")
        if not bounds:
            return
        content_height = bounds[3] - bounds[1]
        viewport_height = canvas.winfo_height()
        if content_height <= viewport_height:
            setattr(self, remainder_name, 0.0)
            return
        if getattr(event, "num", None) in (4, 5):
            pixels = -36 if event.num == 4 else 36
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return
            pixels = (-delta * 6 if sys.platform == "darwin" and abs(delta) < 120
                      else -delta * 54 / 120)
        remainder = getattr(self, remainder_name) + pixels
        whole_pixels = int(remainder)
        setattr(self, remainder_name, remainder - whole_pixels)
        if whole_pixels:
            first, _last = canvas.yview()
            current = round(first * content_height)
            position = max(0, min(content_height - viewport_height, current + whole_pixels))
            if position == current:
                setattr(self, remainder_name, 0.0)
            else:
                canvas.yview_moveto(position / content_height)
        return "break"

    def _load(self):
        try:
            self.battle = self.store.load()
            self.status.set(f"已恢复上次战斗；每次修改自动保存。存档：{self.store.path}")
            if self._enrich_existing_monsters():
                self.dirty = True
                self.save()
        except FileNotFoundError:
            self.status.set(f"未找到存档，已打开空战斗；首次修改后自动创建：{self.store.path}")
        except BattleError as error:
            try:
                backup = self.store.backup_invalid()
                detail = f"原文件已备份到：\n{backup}\n后续操作会创建新的存档。"
            except OSError as backup_error:
                self.protect_original = True
                detail = f"原文件无法备份，已保护原文件。\n请修复目录读写权限；下次修改或退出时会重试保存。\n{backup_error}"
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
            self.status.set("保存失败！更改仍在内存中。请检查磁盘空间、文件和目录权限；下次修改或退出时会重试保存。")
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
    def _editing_text(event):
        return isinstance(event.widget, (tk.Entry, ttk.Entry, tk.Text, tk.Spinbox,
                                         ttk.Combobox))

    def copy_selected(self):
        if not self.tree.selection():
            return False
        actor = self.battle.get(self.selected_id())
        keys = ("name", "kind", "initiative", "max_hp", "hp", "monster_stats")
        self._copied_combatant = {key: copy.deepcopy(getattr(actor, key)) for key in keys}
        return True

    def paste_copied(self):
        if self._copied_combatant is None:
            return False
        return self.perform(lambda: self.battle.add(**copy.deepcopy(self._copied_combatant)))

    def quick_remove_selected(self):
        if not self.tree.selection():
            return False
        return self._remove_combatant(self.selected_id())

    def _remove_combatant(self, combatant_id):
        rows = self.tree.get_children()
        index = rows.index(combatant_id)
        next_id = (rows[index + 1] if index + 1 < len(rows)
                   else rows[index - 1] if index else None)
        result = self.perform(lambda: self.battle.remove(combatant_id), selected_id=next_id)
        if next_id is not None and self.tree.exists(next_id):
            self.tree.focus(next_id)
            self._see_actor(next_id)
        else:
            self.clear_form()
        return result

    def _shortcut_copy(self, event):
        if not self._editing_text(event) and self.copy_selected():
            return "break"

    def _shortcut_paste(self, event):
        if not self._editing_text(event) and self._copied_combatant is not None:
            self.paste_copied()
            return "break"

    def _shortcut_delete(self, event):
        if not self._editing_text(event) and self.tree.selection():
            self.quick_remove_selected()
            return "break"

    @staticmethod
    def parse_number(text, label):
        try:
            return int(text.strip())
        except ValueError:
            raise BattleError(f"{label}请输入整数，例如 0、12 或 -1；不能留空或填写小数。") from None

    def form_values(self, adding=False):
        values = {key: var.get().strip() for key, var in self.fields.items()}
        values["kind"] = self.form_kind
        values["initiative"] = self.parse_number(values["initiative"], "先攻值")
        values["max_hp"] = self.parse_number(values["max_hp"], "最大生命值")
        values["hp"] = (None if adding and not values["hp"] else self.parse_number(values["hp"], "当前生命值"))
        if adding:
            values["monster_stats"] = self.form_monster_stats
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
        self.form_kind = kind
        self.form_monster_stats = None
        self._render_monster_stats()
        for key, value in {"name": "", "initiative": "0", "max_hp": "10", "hp": ""}.items():
            self.fields[key].set(value)
        self.form_mode = "add"
        self.form_title.set(f"添加{kind}")
        self.form_action_button.configure(text="确认添加", style="Primary.TButton")
        self.show_form()

    @staticmethod
    def _handbook_stats(entry):
        """只复制状态栏使用的字段；动作和图鉴 HP 不进入资料副本。"""
        keys = ("english_name", "classification_raw", "armor_class", "speed", "abilities",
                "skills", "damage_vulnerabilities", "damage_resistances", "damage_immunities",
                "condition_immunities", "senses", "languages", "challenge_rating",
                "experience_points", "proficiency_bonus")
        stats = {key: entry.get(key) for key in keys}
        # 当前图鉴的结构化抗性/免疫数组为空，数据卡原文仍包含这些行。
        stats["defenses"] = [line for line in (entry.get("stat_block_text") or "").splitlines()
                             if line.startswith(("易伤", "抗性", "免疫"))]
        stats["traits"] = [section.get("content", "") for section in entry.get("sections", [])
                           if section.get("key") == "traits" and section.get("content")]
        return stats

    def _render_monster_stats(self):
        frame = self.monster_stats_frame
        for child in frame.winfo_children():
            child.destroy()
        stats = self.form_monster_stats
        if not stats or self.form_kind != "怪物":
            frame.grid_remove()
            return
        frame.grid()
        row = 0

        def line(title, value):
            nonlocal row
            if value is None or value == "" or value == []:
                return
            ttk.Label(frame, text=title, style="Eyebrow.TLabel").grid(
                row=row, column=0, sticky="w", pady=(11, 2))
            row += 1
            ttk.Label(frame, text=str(value), style="Body.TLabel", wraplength=290,
                      justify="left").grid(row=row, column=0, sticky="ew")
            row += 1

        line("体型、种类与阵营", stats.get("classification_raw"))
        armor = stats.get("armor_class") or {}
        line("AC", armor.get("raw"))
        speed = stats.get("speed") or {}
        line("速度", speed.get("raw"))
        abilities = stats.get("abilities") or {}
        names = (("strength", "力量"), ("dexterity", "敏捷"), ("constitution", "体质"),
                 ("intelligence", "智力"), ("wisdom", "感知"), ("charisma", "魅力"))
        ability_lines = []
        for key, name in names:
            ability = abilities.get(key) or {}
            if ability.get("score") is not None:
                modifier = ability.get("modifier")
                saving = ability.get("saving_throw")
                ability_lines.append(f"{name} {ability['score']}  调整 {modifier:+d}  豁免 {saving:+d}")
        line("属性 · 调整 · 豁免", "\n".join(ability_lines))
        skills = stats.get("skills") or []
        line("技能", "、".join(f"{skill['name']}{skill['bonus']:+d}" for skill in skills))
        for key, title in (("damage_vulnerabilities", "易伤"), ("damage_resistances", "抗性"),
                           ("damage_immunities", "伤害免疫"), ("condition_immunities", "状态免疫")):
            line(title, "、".join(stats.get(key) or []))
        if not any(stats.get(key) for key in ("damage_vulnerabilities", "damage_resistances",
                                              "damage_immunities", "condition_immunities")):
            line("易伤 · 抗性 · 免疫", "\n".join(stats.get("defenses") or []))
        line("感官", stats.get("senses"))
        line("语言", "、".join(stats.get("languages") or []))
        cr = stats.get("challenge_rating") or ""
        xp = stats.get("experience_points")
        pb = stats.get("proficiency_bonus")
        if cr:
            suffix = []
            if xp is not None:
                suffix.append(f"XP {xp:,}")
            if pb is not None:
                suffix.append(f"PB {pb:+d}")
            line("CR", cr + (f"（{'；'.join(suffix)}）" if suffix else ""))
        line("特质", "\n\n".join(stats.get("traits") or []))

    def _monster_handbook(self):
        """惰性读取图鉴，保留侧栏所需的怪物数据。"""
        if self._handbook_monsters is not None:
            return self._handbook_monsters
        monsters = []
        try:
            with (RESOURCES_DIR / "monster_handbook.JSON").open("r", encoding="utf-8") as stream:
                payload = json.load(stream)
            for entry in payload.get("monsters", []):
                name = (entry.get("name") or "").strip()
                if not name:
                    continue
                hit_points = entry.get("hit_points") or {}
                average = hit_points.get("average")
                monsters.append({
                    "id": entry.get("id") or name,
                    "name": name,
                    "english_name": (entry.get("english_name") or "").strip(),
                    "max_hp": average if isinstance(average, int) and average >= 1 else None,
                    "challenge_rating": (entry.get("challenge_rating") or "").strip(),
                    "creature_type": (entry.get("creature_type") or "").strip(),
                    "stats": self._handbook_stats(entry),
                })
        except (OSError, ValueError):
            monsters = []
        self._handbook_monsters = monsters
        return self._handbook_monsters

    def _enrich_existing_monsters(self):
        """给旧存档中可明确匹配图鉴的怪物补齐状态资料。"""
        by_name = {monster["name"]: monster for monster in self._monster_handbook()}
        changed = False
        for actor in self.battle.combatants:
            monster = by_name.get(actor.name)
            if (actor.kind == "怪物" and actor.monster_stats is None and monster
                    and actor.max_hp == monster["max_hp"]):
                actor.monster_stats = monster["stats"]
                changed = True
        return changed

    def _apply_handbook_monster(self, monster):
        """把图鉴里的怪物及其状态资料填入右侧表单。"""
        self.prepare_add("怪物")
        self.fields["name"].set(monster["name"])
        if isinstance(monster.get("max_hp"), int) and monster["max_hp"] >= 1:
            self.fields["max_hp"].set(str(monster["max_hp"]))
        self.fields["hp"].set("")
        self.form_monster_stats = monster.get("stats")
        self._render_monster_stats()
        self._record_recent_monster(monster)

    def _record_recent_monster(self, monster):
        """LRU 缓存：把刚选用的怪物放到“最近使用”最前，最多保留 6 个。"""
        self._recent_monsters = [m for m in self._recent_monsters if m["id"] != monster["id"]]
        self._recent_monsters.insert(0, monster)
        del self._recent_monsters[6:]

    def open_monster_picker(self):
        monsters = self._monster_handbook()
        if not monsters:
            messagebox.showwarning(
                "怪物图鉴不可用",
                "无法读取 resources/monster_handbook.JSON，或其中没有怪物。\n"
                "请先运行 build_monster_handbook.py 生成图鉴，再重试。",
                parent=self.root)
            self.prepare_add("怪物")
            return None

        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("选择怪物")
        dialog.transient(self.root)
        dialog.configure(background=self.colors["paper"])
        dialog.resizable(False, False)
        self._monster_picker = dialog

        header = ttk.Frame(dialog, style="CardBody.TFrame", padding=(14, 12))
        header.pack(fill="x")
        ttk.Label(header, text="搜索怪物名（中文或英文）", style="Muted.TLabel").pack(anchor="w")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(header, textvariable=search_var, style="Field.TEntry")
        search_entry.pack(fill="x", pady=(6, 0))

        def pick_recent(monster):
            self._apply_handbook_monster(monster)
            dialog.destroy()

        if self._recent_monsters:
            recent_frame = ttk.Frame(dialog, style="CardBody.TFrame", padding=(14, 8, 14, 0))
            recent_frame.pack(fill="x")
            ttk.Label(recent_frame, text="最近使用", style="Eyebrow.TLabel").pack(anchor="w")
            chips = ttk.Frame(recent_frame, style="CardBody.TFrame")
            chips.pack(fill="x", pady=(4, 0))
            for index, monster in enumerate(self._recent_monsters):
                row, column = divmod(index, 3)
                ttk.Button(chips, text=monster["name"], style="Quiet.TButton",
                           command=lambda m=monster: pick_recent(m)).grid(
                               row=row, column=column, sticky="ew", pady=(0, 4),
                               padx=(0 if column == 2 else 4, 0))
            for column in range(3):
                chips.columnconfigure(column, weight=1)

        body = ttk.Frame(dialog, style="CardBody.TFrame", padding=(14, 0))
        body.pack(fill="both", expand=True)
        listbox = tk.Listbox(body, height=16, width=38, font=self.body_font,
                             bg=self.colors["input"], fg=self.colors["ink"],
                             selectbackground=self.colors["selection"],
                             selectforeground=self.colors["white"],
                             highlightthickness=0, borderwidth=0, relief="flat",
                             activestyle="none")
        scrollbar = ttk.Scrollbar(body, orient="vertical", style="Vertical.TScrollbar",
                                  command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        detail_var = tk.StringVar()
        ttk.Label(dialog, textvariable=detail_var, style="Muted.TLabel",
                  padding=(14, 8), wraplength=380).pack(fill="x")

        filtered = list(monsters)

        def repopulate(_name=None, _index=None, _op=None):
            query = search_var.get().strip().lower()
            filtered.clear()
            for monster in monsters:
                if query and query not in monster["name"].lower() \
                        and query not in monster["english_name"].lower():
                    continue
                filtered.append(monster)
            listbox.delete(0, "end")
            for monster in filtered:
                listbox.insert("end", monster["name"])
            detail_var.set("")

        def on_select(_event=None):
            selection = listbox.curselection()
            if not selection:
                return
            monster = filtered[selection[0]]
            parts = []
            if monster["creature_type"]:
                parts.append(monster["creature_type"])
            if monster["max_hp"] is not None:
                parts.append(f"生命值 {monster['max_hp']}")
            if monster["challenge_rating"]:
                parts.append(f"挑战等级 {monster['challenge_rating']}")
            detail_var.set(" · ".join(parts))

        def choose(_event=None):
            selection = listbox.curselection()
            if not selection and filtered:
                listbox.selection_set(0)
                listbox.activate(0)
                selection = (0,)
            if not selection:
                return
            self._apply_handbook_monster(filtered[selection[0]])
            dialog.destroy()

        footer = ttk.Frame(dialog, style="CardBody.TFrame", padding=(14, 12))
        footer.pack(fill="x")
        ttk.Button(footer, text="取消", style="Quiet.TButton",
                   command=dialog.destroy).pack(side="right")
        ttk.Button(footer, text="选择", style="Primary.TButton",
                   command=choose).pack(side="right", padx=(0, 8))

        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<Double-Button-1>", choose)
        search_entry.bind("<Return>", choose)
        search_entry.bind("<Escape>", lambda _event: dialog.destroy())
        search_var.trace_add("write", repopulate)

        repopulate()
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - dialog.winfo_reqwidth()) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - dialog.winfo_reqheight()) // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        search_entry.focus_set()
        try:
            dialog.grab_set()
        except tk.TclError:
            pass
        return dialog

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
        if self._drag_resize_job is not None:
            self.root.after_cancel(self._drag_resize_job)
            self._drag_resize_job = None
        self._drag_pointer_x = None
        self.resize_handle.place_forget()
        self.main_pane.forget(self.form_shell)
        self.form_visible = False

    def show_form(self):
        if self.form_visible:
            self._position_resize_handle()
            return
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

    def _position_resize_handle(self, _event=None):
        if not self.form_visible or len(self.main_pane.panes()) < 2:
            self.resize_handle.place_forget()
            return
        position = self.main_pane.sashpos(0)
        self.resize_handle.place(x=position, y=0, width=self.layout_gap, relheight=1)
        self.resize_handle.lift()

    def _start_panel_resize(self, event):
        if self._form_resize_job is not None:
            self.root.after_cancel(self._form_resize_job)
            self._form_resize_job = None
        self._drag_pointer_x = None
        self._drag_grab_offset = (event.x_root - self.main_pane.winfo_rootx()
                                  - self.main_pane.sashpos(0))
        self.resize_handle.configure(background=self.colors["line_dark"])
        return "break"

    def _drag_panel_resize(self, event):
        self._drag_pointer_x = event.x_root
        if self._drag_resize_job is None:
            self._drag_resize_job = self.root.after(16, self._flush_panel_resize)
        return "break"

    def _flush_panel_resize(self):
        self._drag_resize_job = None
        if self._drag_pointer_x is None or not self.form_visible:
            return
        total = self.main_pane.winfo_width()
        position = self._drag_pointer_x - self.main_pane.winfo_rootx() - self._drag_grab_offset
        position = max(520, min(total - 280, position))
        self.main_pane.sashpos(0, position)
        self.form_width = total - self.main_pane.sashpos(0)
        self._position_resize_handle()

    def _finish_panel_resize(self, event):
        if event is not None:
            self._drag_pointer_x = event.x_root
        if self._drag_resize_job is not None:
            self.root.after_cancel(self._drag_resize_job)
            self._drag_resize_job = None
        self._flush_panel_resize()
        self._drag_pointer_x = None
        self.resize_handle.configure(background=self.colors["parchment"])
        return "break"

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
            self._position_resize_handle()
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
        self.form_kind = actor.kind
        self.form_monster_stats = actor.monster_stats
        self._render_monster_stats()
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
            self._remove_combatant(actor.id)

    def hp_action(self, action):
        def change():
            actor = self.battle.get(self.selected_id())
            amount = self.parse_number(self.amount.get(), "操作数值")
            if amount < 0:
                raise BattleError("血量操作数值不能小于 0。")
            getattr(self.battle, action)(actor.id, amount)
        self.perform(change)

    def _see_actor(self, actor_id):
        box = self.tree.bbox(actor_id)
        bounds = self.list_canvas.bbox("all")
        if not box or not bounds:
            return
        viewport_top = self.list_canvas.canvasy(0)
        viewport_height = self.list_canvas.winfo_height()
        row_top, row_bottom = box[1], box[1] + box[3]
        if row_top < viewport_top:
            target = row_top
        elif row_bottom > viewport_top + viewport_height:
            target = row_bottom - viewport_height
        else:
            return
        content_height = bounds[3] - bounds[1]
        if content_height > 0:
            self.list_canvas.yview_moveto(max(0, target) / content_height)

    def refresh(self, selected_id=None):
        self.combatant_count.set(f"参战人数: {len(self.battle.combatants)}")
        self.round_count.set(f"回合数: {self.battle.round}")
        old_selection = self.tree.selection()
        if selected_id is None and old_selection:
            selected_id = old_selection[0]
        yview = self.list_canvas.yview()
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
            self.tree.configure(height=max(1, len(self.battle.combatants)))
            self.tree.update_idletasks()
            self._update_list_scrollregion()
            if selected_id and self.tree.exists(selected_id):
                self.tree.selection_set(selected_id)
            if yview:
                self.list_canvas.yview_moveto(yview[0])
        finally:
            self.refreshing = False
        if self.battle.combatants:
            self.empty_state.place_forget()
        else:
            self.empty_state.place(relx=0.5, rely=0.48, anchor="center")
            self.empty_state.lift()
        self.on_select()
        if self.battle.active and self.battle.current_id:
            self._see_actor(self.battle.current_id)
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

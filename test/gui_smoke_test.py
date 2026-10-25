"""真实 Tk 控件集成测试：PYTHONPATH=. python3 test/gui_smoke_test.py。"""

from pathlib import Path
from types import SimpleNamespace
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from battle_tracker import BattleApp


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 同一进程只创建一个 Tk 根窗口，兼容 macOS 自带的旧版 Tk。
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "battle_save.json"
        self.root.withdraw()
        self.addCleanup(self.destroy)
        self.warning = self.enterContextCompat(patch("battle_tracker.messagebox.showwarning"))
        self.error = self.enterContextCompat(patch("battle_tracker.messagebox.showerror"))
        self.confirm = self.enterContextCompat(patch("battle_tracker.messagebox.askyesno", return_value=True))
        self.app = BattleApp(self.root, self.path)
        self.root.update()

    def enterContextCompat(self, context):
        result = context.start()
        self.addCleanup(context.stop)
        return result

    def destroy(self):
        for child in self.root.winfo_children():
            child.destroy()

    def widget_texts(self, widget=None):
        texts = []
        for child in (widget or self.root).winfo_children():
            try:
                texts.append(str(child.cget("text")))
            except tk.TclError:
                pass
            texts.extend(self.widget_texts(child))
        return texts

    def add_actor(self, name="哥布林", initiative=10, kind="怪物", max_hp=10, hp=""):
        self.app.clear_form()
        self.app.fields["name"].set(name)
        self.app.form_kind = kind
        self.app.fields["initiative"].set(str(initiative))
        self.app.fields["max_hp"].set(str(max_hp))
        self.app.fields["hp"].set(str(hp))
        self.app.add()
        self.root.update()
        return self.app.battle.combatants[-1]

    def test_add_edit_sort_turn_remove_and_restore(self):
        a, b = self.add_actor(initiative=20), self.add_actor()
        self.assertEqual(a.hp, a.max_hp)
        self.assertEqual(self.app.tree.item(b.id, "values")[2], "哥布林 2")
        self.app.start_button.invoke()
        self.app.tree.selection_set(a.id)
        self.app.next_button.invoke()
        self.assertEqual(self.app.battle.current_id, b.id)
        self.assertEqual(self.app.tree.selection(), (b.id,))
        self.app.fields["initiative"].set("30")
        self.app.form_action_button.invoke()
        self.app.perform(self.app.battle.sort)
        self.assertEqual(self.app.battle.current_id, b.id)
        self.assertEqual(self.app.tree.get_children()[0], b.id)
        self.assertIn("行动中", self.app.tree.item(b.id, "values")[0])
        self.assertEqual(self.app.store.load().to_dict(), self.app.battle.to_dict())
        self.app.remove()
        self.assertIsNone(self.app.battle.current_id)
        self.assertEqual(self.app.tree.selection(), (a.id,))
        self.assertEqual(self.app.battle.round, 1)
        self.app.next_button.invoke()
        self.assertEqual(self.app.battle.round, 2)
        self.assertEqual(self.app.combatant_count.get(), "参战人数: 1")
        self.assertEqual(self.app.round_count.get(), "回合数: 2")
        self.assertEqual(self.app.tree.selection(), (a.id,))
        self.app.tree.selection_set(a.id)
        self.app.remove()
        self.assertEqual(self.app.tree.get_children(), ())
        self.assertEqual(self.app.tree.selection(), ())
        self.assertFalse(self.app.battle.active)

    def test_delete_selects_next_then_previous_at_list_end(self):
        first = self.add_actor("甲", kind="玩家")
        middle = self.add_actor("乙", kind="玩家")
        last = self.add_actor("丙", kind="玩家")
        self.app.tree.selection_set(middle.id)
        self.app.remove()
        self.assertEqual(self.app.tree.selection(), (last.id,))
        self.assertEqual(self.app.tree.focus(), last.id)
        self.assertEqual(self.app.form_title.get(), last.display_name)
        self.app.remove()
        self.assertEqual(self.app.tree.selection(), (first.id,))
        self.assertEqual(self.app.tree.focus(), first.id)
        self.assertEqual(self.app.form_title.get(), first.display_name)
        self.app.remove()
        self.assertEqual(self.app.tree.selection(), ())
        self.assertEqual(self.app.battle.combatants, [])

    def test_damage_healing_and_zero_marker_without_automatic_end(self):
        monster = self.add_actor()
        self.add_actor("勇者", initiative=20, kind="玩家", max_hp=20)
        self.app.start_button.invoke()
        self.app.tree.selection_set(monster.id)
        self.app.amount.set("5")
        self.app.hp_action("damage")
        self.assertEqual(monster.hp, 5)
        self.assertTrue(self.app.battle.active)
        self.app.amount.set("999")
        self.app.hp_action("heal")
        self.assertEqual(monster.hp, 10)
        self.app.amount.set("999")
        self.app.hp_action("damage")
        self.assertIn("0 HP", self.app.tree.item(monster.id, "values")[-1])
        self.assertTrue(self.app.battle.active)
        self.assertEqual(self.app.battle.round, 1)
        self.assertEqual(str(self.app.start_button["state"]), "disabled")
        self.assertEqual(str(self.app.end_button["state"]), "normal")

    def test_copy_paste_and_quick_delete_shortcuts(self):
        monster = self.add_actor("哥布林", initiative=17, max_hp=25, hp=4)
        monster.monster_stats = {"traits": ["原始特质"]}
        self.app.tree.selection_set(monster.id)
        tree_event = SimpleNamespace(widget=self.app.tree)
        self.assertTrue(self.root.bind("<Command-BackSpace>"))
        self.assertTrue(self.root.bind("<Command-Delete>"))
        self.assertTrue(self.root.bind("<Command-c>"))
        self.assertTrue(self.root.bind("<Command-v>"))
        self.assertEqual(self.app._shortcut_copy(tree_event), "break")
        monster.monster_stats["traits"][0] = "修改后的特质"

        self.assertEqual(self.app._shortcut_paste(tree_event), "break")
        copy_two = self.app.battle.combatants[-1]
        self.assertNotEqual(copy_two.id, monster.id)
        self.assertEqual(copy_two.display_name, "哥布林 2")
        self.assertEqual((copy_two.kind, copy_two.initiative, copy_two.max_hp, copy_two.hp),
                         (monster.kind, 17, 25, 4))
        self.assertEqual(copy_two.monster_stats, {"traits": ["原始特质"]})
        self.assertEqual(self.app._shortcut_paste(tree_event), "break")
        copy_three = self.app.battle.combatants[-1]
        self.assertEqual(copy_three.display_name, "哥布林 3")
        self.assertEqual(self.app.store.load().to_dict(), self.app.battle.to_dict())

        editor = tk.Entry(self.root)
        self.app.tree.selection_set(copy_three.id)
        self.assertIsNone(self.app._shortcut_copy(SimpleNamespace(widget=editor)))
        self.assertIsNone(self.app._shortcut_paste(SimpleNamespace(widget=editor)))
        self.assertIsNone(self.app._shortcut_delete(SimpleNamespace(widget=editor)))
        self.assertEqual(len(self.app.battle.combatants), 3)

        self.assertEqual(self.app._shortcut_delete(tree_event), "break")
        self.assertFalse(self.app.tree.exists(copy_three.id))
        self.assertEqual(self.app.tree.selection(), (copy_two.id,))
        self.assertEqual(len(self.app.battle.combatants), 2)
        self.confirm.assert_not_called()
        self.assertEqual(self.app.store.load().to_dict(), self.app.battle.to_dict())

    def test_end_button_preserves_combatants_hp_and_order(self):
        monster = self.add_actor(initiative=10)
        player = self.add_actor("勇者", initiative=20, kind="玩家", max_hp=20)
        self.app.start_button.invoke()
        self.app.tree.selection_set(monster.id)
        self.app.amount.set("3")
        self.app.hp_action("damage")
        before = [(actor.id, actor.hp) for actor in self.app.battle.combatants]
        self.app.end_button.invoke()
        self.assertEqual((self.app.battle.active, self.app.battle.round,
                          self.app.battle.current_id), (False, 0, None))
        self.assertEqual([(actor.id, actor.hp) for actor in self.app.battle.combatants], before)
        self.assertEqual(before, [(player.id, 20), (monster.id, 7)])
        self.assertIn("均已保留", self.app.status.get())
        self.assertEqual(self.app.store.load().to_dict(), self.app.battle.to_dict())

    def test_resizable_hideable_contextual_combatant_panel(self):
        actor = self.add_actor("勇者", kind="玩家")
        self.assertEqual(self.app.form_title.get(), actor.display_name)
        self.assertEqual(str(self.app.form_action_button["text"]), "保存修改")
        self.assertEqual(self.app.form_close_button.icon_name, "关闭档案")
        self.assertEqual(len(self.app.main_pane.panes()), 2)
        self.root.update()
        old_position = self.app.main_pane.sashpos(0)
        self.assertEqual(str(self.app.resize_handle.cget("cursor")), "sb_h_double_arrow")
        self.app._start_panel_resize(SimpleNamespace(
            x_root=self.app.main_pane.winfo_rootx() + old_position))
        self.app._drag_panel_resize(SimpleNamespace(
            x_root=self.app.main_pane.winfo_rootx() + old_position - 70))
        self.app._finish_panel_resize(None)
        self.root.update()
        self.assertNotEqual(self.app.main_pane.sashpos(0), old_position)
        resized_width = self.app.form_shell.winfo_width()
        self.app.show_form()
        self.root.update()
        self.assertAlmostEqual(self.app.form_shell.winfo_width(), resized_width, delta=10)
        self.app.hide_form()
        self.assertEqual(len(self.app.main_pane.panes()), 1)
        self.app.tree.selection_set(actor.id)
        self.app.tree.event_generate("<<TreeviewSelect>>")
        self.root.update()
        self.assertTrue(self.app.form_visible)
        self.assertEqual(len(self.app.main_pane.panes()), 2)
        self.assertEqual(self.app.form_title.get(), actor.display_name)
        self.assertAlmostEqual(self.app.form_shell.winfo_width(), resized_width, delta=10)
        self.assertLessEqual(self.app.form_close_button.winfo_width(), 28)
        self.assertLessEqual(self.app.form_close_button.winfo_height(), 24)
        self.assertGreaterEqual(self.app.form_action_button.winfo_rooty(),
                                self.app.form_canvas.winfo_rooty() + self.app.form_canvas.winfo_height())
        self.app.add_monster_button.invoke()
        picker = self.app._monster_picker
        self.assertIsNotNone(picker)
        self.assertTrue(picker.winfo_exists())
        self.addCleanup(picker.destroy)
        monsters = self.app._monster_handbook()
        self.assertGreater(len(monsters), 0)
        monster = next(m for m in monsters if m["max_hp"])
        self.app._apply_handbook_monster(monster)
        self.assertEqual(self.app._recent_monsters[0]["id"], monster["id"])
        self.assertEqual(len(self.app._recent_monsters), 1)
        self.assertEqual(self.app.form_mode, "add")
        self.assertEqual(self.app.form_kind, "怪物")
        self.assertEqual(self.app.fields["name"].get(), monster["name"])
        self.assertEqual(self.app.fields["max_hp"].get(), str(monster["max_hp"]))
        self.assertEqual(self.app.form_title.get(), "添加怪物")
        self.assertEqual(str(self.app.form_action_button["text"]), "确认添加")
        # 记录最近使用后再次打开，会渲染“最近使用”区块。
        self.app.open_monster_picker()
        self.assertIsNotNone(self.app._monster_picker)
        self.addCleanup(self.app._monster_picker.destroy)

    def test_monster_recent_cache_keeps_latest_six(self):
        monsters = self.app._monster_handbook()
        chosen = [m for m in monsters if m["max_hp"]][:7]
        self.assertGreaterEqual(len(chosen), 7)
        for monster in chosen:
            self.app._apply_handbook_monster(monster)
        self.assertEqual(len(self.app._recent_monsters), 6)
        self.assertEqual(self.app._recent_monsters[0]["id"], chosen[6]["id"])
        self.assertNotIn(chosen[0]["id"], [m["id"] for m in self.app._recent_monsters])
        self.app._apply_handbook_monster(chosen[3])
        self.assertEqual(len(self.app._recent_monsters), 6)
        self.assertEqual(self.app._recent_monsters[0]["id"], chosen[3]["id"])

    def test_list_scrolls_without_moving_heading(self):
        for number in range(25):
            self.add_actor(f"参战者 {number}", kind="玩家")
        self.root.deiconify()
        self.root.update()
        self.assertIs(self.app.tree.master, self.app.list_canvas)
        self.assertLess(self.app.list_canvas.yview()[1], 1.0)
        heading_y = self.app.list_heading.winfo_rooty()
        self.app.list_canvas.yview_moveto(0.01)
        self.root.update()
        self.assertGreater(self.app.list_canvas.canvasy(0), 0)
        self.assertEqual(self.app.list_heading.winfo_rooty(), heading_y)

    def test_invalid_input_and_no_selection_show_chinese_warning(self):
        self.app.add()
        self.warning.assert_called()
        self.assertEqual(len(self.app.battle.combatants), 0)
        self.add_actor()
        self.app.amount.set("abc")
        self.app.hp_action("damage")
        self.assertIn("整数", self.warning.call_args[0][1])
        self.app.clear_form()
        self.app.hp_action("damage")
        self.assertIn("选择", self.warning.call_args[0][1])

    def test_new_battle_requires_confirmation(self):
        self.add_actor()
        self.confirm.return_value = False
        self.app.new_battle()
        self.assertEqual(len(self.app.battle.combatants), 1)
        self.confirm.return_value = True
        self.app.new_battle()
        self.assertEqual(self.app.battle.combatants, [])
        self.assertEqual(self.app.store.load().combatants, [])

    def test_missing_and_corrupt_save_are_explained(self):
        self.assertIn("未找到存档", self.app.status.get())
        self.path.write_bytes(b"broken JSON")
        self.app._load()
        self.root.update()
        self.warning.assert_called()
        self.assertIn("损坏", self.app.status.get())
        self.assertEqual(len(list(self.path.parent.glob("*.bak"))), 1)
        self.app.save()
        self.assertEqual(self.app.store.load().combatants, [])

    def test_save_failure_keeps_changes_and_retry_works(self):
        a = self.add_actor()
        with patch.object(self.app.store, "save", side_effect=PermissionError("只读目录")):
            self.app.amount.set("5")
            self.app.hp_action("damage")
            self.assertTrue(self.app.dirty)
            self.assertEqual(a.hp, 5)
            self.assertIn("保存失败", self.app.status.get())
            self.error.assert_called()
            self.confirm.return_value = False
            self.app.close()
            self.assertTrue(self.root.winfo_exists())
        self.assertTrue(self.app.save())
        self.assertFalse(self.app.dirty)
        self.assertEqual(self.app.store.load().get(a.id).hp, 5)

    def test_layout_widgets_fit_default_window(self):
        self.root.deiconify()
        self.root.after(300, self.root.quit)
        self.root.mainloop()
        width, height = self.root.winfo_width(), self.root.winfo_height()
        self.assertGreaterEqual(width, 1000)
        def check_children(widget):
            if isinstance(widget, tk.Canvas):
                return
            for child in widget.winfo_children():
                x = child.winfo_rootx() - self.root.winfo_rootx()
                y = child.winfo_rooty() - self.root.winfo_rooty()
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + child.winfo_width(), width)
                self.assertLessEqual(y + child.winfo_height(), height)
                check_children(child)
        check_children(self.root)
        texts = self.widget_texts()
        self.assertNotIn("战斗纪事", texts)
        self.assertNotIn("立即保存 / 重试", texts)
        self.assertEqual(self.app.status_bar.winfo_rooty() + self.app.status_bar.winfo_height(),
                         self.root.winfo_rooty() + self.root.winfo_height())
        self.assertEqual(self.app.combatant_count.get(), "参战人数: 0")
        self.assertEqual(self.app.round_count.get(), "回合数: 0")
        self.assertEqual(self.app.status_bar.cget("style"), "StatusBar.TFrame")
        tree_style = ttk.Style(self.root)
        self.assertNotIn("Treeview.field", str(tree_style.layout("Treeview")))
        self.assertEqual(tree_style.lookup("Treeview", "background", ("selected",)),
                         self.app.colors["selection"])
        self.assertLess(self.app.hp_panel.winfo_rooty() + self.app.hp_panel.winfo_height(),
                        self.app.status_bar.winfo_rooty())
        self.assertEqual(self.root.title(), "Dungeon Master Studio")
        edge = self.root.winfo_rootx() + self.root.winfo_width()
        top = self.root.winfo_rooty()
        button_bottom = max(button.winfo_rooty() + button.winfo_height() for button in
                            (self.app.start_button, self.app.next_button, self.app.end_button))
        self.assertEqual(self.app.start_button.winfo_rooty() - top, 4)
        self.assertEqual(edge - self.app.end_button.winfo_rootx()
                         - self.app.end_button.winfo_width(), 4)
        self.assertEqual(edge - self.app.form_shell.winfo_rootx()
                         - self.app.form_shell.winfo_width(), 4)
        self.assertEqual(self.app.listing.winfo_rootx() - self.root.winfo_rootx(), 4)
        self.assertEqual(self.app.form_shell.winfo_rootx()
                         - self.app.listing.winfo_rootx() - self.app.listing.winfo_width(), 4)
        self.assertEqual(self.app.resize_handle.winfo_rootx(),
                         self.app.listing.winfo_rootx() + self.app.listing.winfo_width())
        self.assertEqual(self.app.resize_handle.winfo_width(), self.app.layout_gap)
        self.assertEqual(self.app.form_shell.winfo_rooty() - button_bottom, 4)
        self.assertEqual(self.app.hp_panel.winfo_rooty()
                         - self.app.main_pane.winfo_rooty() - self.app.main_pane.winfo_height(), 4)
        self.assertEqual(self.app.status_bar.winfo_rooty()
                         - self.app.hp_panel.winfo_rooty() - self.app.hp_panel.winfo_height(), 4)
        self.assertEqual(self.app.start_button.icon_name, "Play")
        self.assertEqual(self.app.next_button.icon_name, "Next")
        self.assertEqual(self.app.end_button.icon_name, "Stop")
        for button in (self.app.start_button, self.app.next_button, self.app.end_button):
            self.assertEqual(button._color, "#F0F0F0")
            self.assertEqual(button._disabled_color, "#F0F0F0")
            self.assertEqual(button._bg, "#3C3C3C")
        self.assertEqual(self.app.add_player_button.icon_name, "添加玩家")
        self.assertEqual(self.app.add_monster_button.icon_name, "添加怪物")
        player_icon_items = self.app.add_player_button.find_withtag("icon")
        self.assertIn("oval", [self.app.add_player_button.type(item) for item in player_icon_items])
        self.assertFalse(hasattr(self.app, "new_button"))
        self.assertEqual(str(self.root.cget("background")), "#3C3C3C")
        self.assertNotIn("INITIATIVE ORDER  ·  行动序列", texts)
        self.assertNotIn("参战者", texts)
        self.assertNotIn("COMBATANT  ·  参战者档案", texts)
        self.assertNotIn("HP", texts)
        self.assertNotIn("血量操作", texts)
        self.assertNotIn("修正当前 HP", texts)
        self.assertNotIn("添加为新参战者", texts)
        self.assertNotIn("保存所选角色修改", texts)
        self.assertNotIn("清空表单 / 取消选择", texts)
        self.assertNotIn("当前行动者以绿色高亮；0 HP 角色仍会保留回合。单击一行可编辑。", texts)
        self.assertNotIn("作用于列表中选中的角色", texts)
        self.assertFalse(any(text.startswith("新增时当前 HP 留空") for text in texts))
        self.root.geometry("1080x580")
        self.root.update()
        first, last = self.app.form_canvas.yview()
        self.assertGreaterEqual(first, 0.0)
        self.assertLessEqual(last, 1.0)
        if last < 1.0:
            self.app.form_canvas.yview_moveto(1.0)
            self.root.update()
            self.assertGreater(self.app.form_canvas.yview()[0], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

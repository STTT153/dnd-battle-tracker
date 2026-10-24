"""真实 Tk 控件集成测试：PYTHONPATH=. python3 test/gui_smoke_test.py。"""

from pathlib import Path
import tempfile
import tkinter as tk
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
        self.app.fields["kind"].set(kind)
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
        self.app.edit_button.invoke()
        self.app.perform(self.app.battle.sort)
        self.assertEqual(self.app.battle.current_id, b.id)
        self.assertEqual(self.app.tree.get_children()[0], b.id)
        self.assertIn("行动中", self.app.tree.item(b.id, "values")[0])
        self.assertEqual(self.app.store.load().to_dict(), self.app.battle.to_dict())
        self.app.remove()
        self.assertIsNone(self.app.battle.current_id)
        self.assertEqual(self.app.battle.round, 1)
        self.app.next_button.invoke()
        self.assertEqual(self.app.battle.round, 2)
        self.assertEqual(self.app.tree.selection(), (a.id,))
        self.app.tree.selection_set(a.id)
        self.app.remove()
        self.assertEqual(self.app.tree.get_children(), ())
        self.assertFalse(self.app.battle.active)

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
        self.assertNotIn("修正当前 HP", texts)
        self.assertNotIn("当前行动者以绿色高亮；0 HP 角色仍会保留回合。单击一行可编辑。", texts)
        self.assertNotIn("作用于列表中选中的角色", texts)


if __name__ == "__main__":
    unittest.main(verbosity=2)

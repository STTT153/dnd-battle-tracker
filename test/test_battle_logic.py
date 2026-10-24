"""运行：python3 -m unittest discover -s test -p 'test_*.py' -v。"""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from battle_logic import Battle, BattleError, JsonStore


class BattleTests(unittest.TestCase):
    def setUp(self):
        self.b = Battle()

    def add(self, name="角色", initiative=10, kind="玩家", max_hp=20, hp=None):
        return self.b.add(name, kind, initiative, max_hp, hp)

    def test_defaults_and_independent_ids(self):
        a, b = self.add(), self.add()
        self.assertEqual(a.hp, 20)
        self.assertNotEqual(a.id, b.id)

    def test_monster_numbering_and_rename(self):
        a = self.add("哥布林", kind="怪物")
        b = self.add("哥布林", kind="怪物")
        self.assertEqual([a.display_name, b.display_name], ["哥布林 1", "哥布林 2"])
        c = self.add("兽人", kind="怪物")
        self.b.edit(c.id, "哥布林", "怪物", 10, 20, 20)
        self.assertEqual(c.display_name, "哥布林 3")
        self.b.edit(a.id, a.name, a.kind, 12, 20, 20)
        self.assertEqual(a.display_name, "哥布林 1")

    def test_stable_sort_and_manual_tie_order(self):
        a, b, c = self.add("甲", 10), self.add("乙", 20), self.add("丙", 10)
        self.b.sort()
        self.assertEqual(self.b.combatants, [b, a, c])
        self.b.move_tied(c.id, -1)
        self.b.sort()
        self.assertEqual(self.b.combatants, [b, c, a])
        with self.assertRaises(BattleError):
            self.b.move_tied(c.id, -1)

    def test_sort_preserves_current_and_round(self):
        a, b, c = self.add("甲", 30), self.add("乙", 20), self.add("丙", 10)
        self.b.start()
        self.b.next_turn()
        self.b.edit(b.id, b.name, b.kind, -5, 20, 20)
        self.b.sort()
        self.assertEqual(self.b.current_id, b.id)
        self.assertEqual(self.b.round, 1)
        self.b.next_turn()
        self.assertEqual(self.b.current_id, c.id)
        self.b.next_turn()
        self.assertEqual((self.b.round, self.b.current_id), (2, a.id))

    def test_damage_reduces_hp_and_floors_at_zero(self):
        a = self.add()
        self.b.damage(a.id, 5)
        self.assertEqual(a.hp, 15)
        self.b.damage(a.id, 7)
        self.assertEqual(a.hp, 8)
        self.b.damage(a.id, 999)
        self.assertEqual(a.hp, 0)
        self.assertIn(a, self.b.combatants)

    def test_healing_cap_and_direct_hp(self):
        a = self.add(hp=3)
        self.b.heal(a.id, 999)
        self.assertEqual(a.hp, 20)
        self.b.correct_hp(a.id, 0)
        self.assertEqual(a.hp, 0)
        with self.assertRaises(BattleError):
            self.b.correct_hp(a.id, 21)

    def test_manual_end_preserves_combatants_order_and_hp(self):
        a = self.add("甲", 10, hp=7)
        b = self.add("乙", 20, kind="怪物", max_hp=15, hp=11)
        self.b.start()
        self.b.next_turn()
        before = [(actor.id, actor.hp, actor.initiative) for actor in self.b.combatants]
        self.b.end()
        self.assertEqual((self.b.active, self.b.round, self.b.current_id), (False, 0, None))
        self.assertEqual(self.b.acted_ids, set())
        self.assertEqual([(actor.id, actor.hp, actor.initiative) for actor in self.b.combatants], before)
        self.b.start()
        self.assertEqual((self.b.active, self.b.round, self.b.current_id), (True, 1, b.id))
        with self.assertRaises(BattleError):
            Battle().end()

    def test_all_monsters_at_zero_do_not_automatically_end_battle(self):
        player = self.add("勇者", 20, kind="玩家")
        m1 = self.add("哥布林", 10, kind="怪物", max_hp=6)
        m2 = self.add("兽人", 5, kind="怪物", max_hp=8)
        self.b.start()
        self.b.damage(m1.id, 99)
        self.assertTrue(self.b.active)
        self.b.correct_hp(m2.id, 0)
        self.assertEqual((self.b.active, self.b.round, self.b.current_id), (True, 1, player.id))
        self.assertEqual((player.hp, m1.hp, m2.hp), (20, 0, 0))

    def test_all_players_at_zero_do_not_automatically_end_battle(self):
        p1 = self.add("战士", 20, kind="玩家", max_hp=12)
        p2 = self.add("法师", 15, kind="玩家", max_hp=8)
        monster = self.add("巨魔", 5, kind="怪物", max_hp=30)
        self.b.start()
        self.b.damage(p1.id, 12)
        self.assertTrue(self.b.active)
        self.b.edit(p2.id, p2.name, p2.kind, p2.initiative, p2.max_hp, 0)
        self.assertTrue(self.b.active)
        self.assertEqual(self.b.round, 1)
        self.assertEqual(monster.hp, 30)

    def test_zero_hp_npcs_do_not_change_battle_state(self):
        player = self.add("勇者", 20, kind="玩家")
        npc = self.add("向导", 10, kind="NPC", hp=0)
        self.b.start()
        self.assertTrue(self.b.active)
        self.b.correct_hp(npc.id, 0)
        self.assertTrue(self.b.active)
        self.assertEqual(player.hp, 20)

    def test_zero_hp_still_gets_turn(self):
        a, b = self.add("甲", 20), self.add("乙", 10, hp=0)
        self.b.start()
        self.b.next_turn()
        self.assertEqual((self.b.current_id, self.b.round), (b.id, 1))

    def test_single_actor_rounds(self):
        a = self.add()
        self.b.start()
        self.b.next_turn()
        self.assertEqual((self.b.current_id, self.b.round), (a.id, 2))

    def test_remove_current_selects_pending_without_advancing_round(self):
        a, b, c = self.add("甲", 30), self.add("乙", 20), self.add("丙", 10)
        self.b.start()
        self.b.next_turn()
        self.b.remove(b.id)
        self.assertEqual((self.b.current_id, self.b.round), (c.id, 1))
        self.assertEqual(self.b.acted_ids, {a.id})

    def test_remove_last_current_defers_round_increment(self):
        a, b = self.add("甲", 20), self.add("乙", 10)
        self.b.start()
        self.b.next_turn()
        self.b.remove(b.id)
        self.assertEqual((self.b.current_id, self.b.round), (None, 1))
        recovered = Battle.from_dict(self.b.to_dict())
        recovered.next_turn()
        self.assertEqual((recovered.current_id, recovered.round), (a.id, 2))

    def test_remove_other_does_not_move_current(self):
        a, b, c = self.add("甲", 30), self.add("乙", 20), self.add("丙", 10)
        self.b.start()
        self.b.next_turn()
        self.b.remove(a.id)
        self.b.remove(c.id)
        self.assertEqual((self.b.current_id, self.b.round), (b.id, 1))

    def test_remove_all_returns_to_preparation(self):
        a = self.add()
        self.b.start()
        self.b.remove(a.id)
        self.assertEqual(self.b.to_dict(), Battle().to_dict())

    def test_new_higher_initiative_actor_gets_this_round(self):
        a, b = self.add("甲", 20), self.add("乙", 10)
        self.b.start()
        self.b.next_turn()
        c = self.add("新角色", 40)
        self.b.sort()
        self.assertEqual(self.b.current_id, b.id)
        self.b.next_turn()
        self.assertEqual((self.b.current_id, self.b.round), (c.id, 1))
        self.b.next_turn()
        self.assertEqual((self.b.current_id, self.b.round), (c.id, 2))

    def test_add_after_current_removed_at_round_end(self):
        a, b = self.add("甲", 20), self.add("乙", 10)
        self.b.start()
        self.b.next_turn()
        self.b.remove(b.id)
        c = self.add("新角色", 30)
        self.assertEqual((self.b.current_id, self.b.round), (c.id, 1))

    def test_empty_battle_operations_and_missing_selection(self):
        self.b.sort()
        for operation in (self.b.start, self.b.next_turn,
                          lambda: self.b.remove(None), lambda: self.b.damage(None, 5)):
            with self.assertRaises(BattleError):
                operation()

    def test_invalid_inputs_do_not_mutate(self):
        for args in ((" ", "玩家", 1, 10), ("甲", "其他", 1, 10),
                     ("甲", "玩家", 1.5, 10), ("甲", "玩家", True, 10),
                     ("甲", "玩家", 1, 0), ("甲", "玩家", 1, 10, 11),
                     ("甲", "玩家", 1, 10, -1)):
            with self.subTest(args=args), self.assertRaises(BattleError):
                self.b.add(*args)
        self.assertEqual(self.b.combatants, [])
        a = self.add()
        before = self.b.to_dict()
        for operation in (lambda: self.b.edit(a.id, "", "玩家", 10, 20, 20),
                          lambda: self.b.damage(a.id, -1), lambda: self.b.heal(a.id, 1.5)):
            with self.assertRaises(BattleError):
                operation()
            self.assertEqual(self.b.to_dict(), before)

    def test_cannot_start_twice_or_next_before_start(self):
        self.add()
        with self.assertRaises(BattleError):
            self.b.next_turn()
        self.b.start()
        self.b.next_turn()
        with self.assertRaises(BattleError):
            self.b.start()
        self.assertEqual(self.b.round, 2)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = JsonStore(Path(self.directory.name) / "battle_save.json")

    def test_round_trip_order_ids_hp_current_and_acted(self):
        b = Battle()
        a = b.add("法师", "玩家", 20, 20)
        g = b.add("哥布林", "怪物", 10, 8)
        b.add("向导", "NPC", 10, 12)
        b.start()
        b.next_turn()
        b.damage(g.id, 3)
        b.edit(g.id, "哥布林", "怪物", 30, 8, g.hp)
        b.sort()
        self.store.save(b)
        loaded = self.store.load()
        self.assertEqual(loaded.to_dict(), b.to_dict())
        self.assertEqual(loaded.current_id, g.id)
        self.assertEqual(loaded.acted_ids, {a.id})
        loaded.next_turn()
        self.assertEqual(loaded.get(loaded.current_id).name, "向导")

    def test_loads_version_one_save_and_discards_legacy_temp_hp(self):
        legacy = {
            "version": 1,
            "combatants": [{"id": "p1", "name": "战士", "kind": "玩家",
                              "initiative": 10, "max_hp": 20, "hp": 12,
                              "temp_hp": 99, "monster_number": None}],
            "active": False, "round": 0, "current_id": None, "acted_ids": [],
        }
        loaded = Battle.from_dict(legacy)
        self.assertEqual(loaded.get("p1").hp, 12)
        self.assertNotIn("temp_hp", loaded.to_dict()["combatants"][0])
        self.assertEqual(loaded.to_dict()["version"], 2)

    def test_empty_round_trip(self):
        b = Battle()
        self.store.save(b)
        self.assertEqual(self.store.load().to_dict(), b.to_dict())

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            self.store.load()

    def test_corrupt_file_preserved_in_backup(self):
        for payload in (b'{broken', b'\xff\xfe', b'[]', b'{"version": 99}'):
            with self.subTest(payload=payload):
                self.store.path.write_bytes(payload)
                with self.assertRaises(BattleError):
                    self.store.load()
                backup = self.store.backup_invalid()
                self.assertEqual(backup.read_bytes(), payload)
                self.assertEqual(self.store.path.read_bytes(), payload)

    def test_failed_replace_preserves_previous_save_and_cleans_temp(self):
        b = Battle()
        self.store.save(b)
        original = self.store.path.read_bytes()
        b.add("玩家", "玩家", 10, 20)
        with patch("battle_logic.os.replace", side_effect=OSError("磁盘写入失败")):
            with self.assertRaises(OSError):
                self.store.save(b)
        self.assertEqual(self.store.path.read_bytes(), original)
        self.assertEqual(list(self.store.path.parent.glob("*.tmp")), [])

    def test_reject_semantically_invalid_saves(self):
        b = Battle()
        a = b.add("玩家", "玩家", 10, 20)
        b.start()
        valid = b.to_dict()
        corruptions = [
            {"round": True}, {"round": 0}, {"active": "yes"}, {"current_id": "missing"},
            {"current_id": None}, {"acted_ids": [a.id]}, {"acted_ids": ["missing"]},
            {"acted_ids": [a.id, a.id]}, {"acted_ids": [{}]}, {"combatants": {}},
            {"combatants": [valid["combatants"][0]] * 2},
            {"combatants": [dict(valid["combatants"][0], hp=99)]},
            {"combatants": [dict(valid["combatants"][0], id="")]},
            {"combatants": [dict(valid["combatants"][0], initiative=1.5)]},
            {"combatants": [dict(valid["combatants"][0], kind="怪物", monster_number=0)]},
        ]
        for changes in corruptions:
            with self.subTest(changes=changes), self.assertRaises(BattleError):
                Battle.from_dict(dict(copy.deepcopy(valid), **changes))
        del valid["acted_ids"]
        with self.assertRaises(BattleError):
            Battle.from_dict(valid)


if __name__ == "__main__":
    unittest.main()

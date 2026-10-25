"""离线 D&D 战斗模型及 JSON 保存；不依赖 Tkinter。"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Optional
from uuid import uuid4


KINDS = ("玩家", "NPC", "怪物")


class BattleError(ValueError):
    """可以直接展示给用户的输入或存档错误。"""


def integer(value, label, minimum=None):
    # bool 是 int 的子类，但不能作为存档中的数字。
    if type(value) is not int:
        raise BattleError(f"{label}必须是整数。")
    if minimum is not None and value < minimum:
        raise BattleError(f"{label}不能小于 {minimum}。")
    return value


def validate_fields(name, kind, initiative, max_hp, hp):
    if not isinstance(name, str) or not name.strip():
        raise BattleError("请输入参战者名称。")
    if kind not in KINDS:
        raise BattleError("类型必须是玩家、NPC 或怪物。")
    integer(initiative, "先攻值")
    integer(max_hp, "最大生命值", 1)
    integer(hp, "当前生命值", 0)
    if hp > max_hp:
        raise BattleError("当前生命值不能超过最大生命值。")


@dataclass
class Combatant:
    id: str
    name: str
    kind: str
    initiative: int
    max_hp: int
    hp: int
    monster_number: Optional[int] = None
    monster_stats: Optional[dict] = None

    @property
    def display_name(self):
        if self.kind == "怪物":
            return f"{self.name} {self.monster_number}"
        return self.name


class Battle:
    def __init__(self):
        self.combatants = []
        self.active = False
        self.round = 0
        self.current_id = None
        self.acted_ids = set()

    def get(self, combatant_id):
        for actor in self.combatants:
            if actor.id == combatant_id:
                return actor
        raise BattleError("请先在列表中选择一名参战者。")

    def _number(self, name, excluded_id=None):
        numbers = [c.monster_number for c in self.combatants
                   if c.kind == "怪物" and c.name == name and c.id != excluded_id]
        return max(numbers, default=0) + 1

    def add(self, name, kind, initiative, max_hp, hp=None, monster_stats=None):
        if hp is None:
            hp = max_hp
        validate_fields(name, kind, initiative, max_hp, hp)
        name = name.strip()
        actor = Combatant(str(uuid4()), name, kind, initiative, max_hp, hp,
                          self._number(name) if kind == "怪物" else None,
                          monster_stats if kind == "怪物" else None)
        self.combatants.append(actor)
        if self.active and self.current_id is None:
            self._choose_pending()
        return actor

    def edit(self, combatant_id, name, kind, initiative, max_hp, hp):
        actor = self.get(combatant_id)
        validate_fields(name, kind, initiative, max_hp, hp)
        name = name.strip()
        number = None
        if kind == "怪物":
            number = (actor.monster_number if actor.kind == kind and actor.name == name
                      else self._number(name, actor.id))
        actor.name, actor.kind, actor.initiative = name, kind, initiative
        actor.max_hp, actor.hp, actor.monster_number = max_hp, hp, number

    def _choose_pending(self):
        self.current_id = next((c.id for c in self.combatants
                                if c.id not in self.acted_ids), None)

    def remove(self, combatant_id):
        actor = self.get(combatant_id)
        self.combatants.remove(actor)
        self.acted_ids.discard(combatant_id)
        if not self.combatants:
            self.active, self.round, self.current_id = False, 0, None
            self.acted_ids.clear()
        elif self.current_id == combatant_id:
            # 删除不会增加轮数；必要时停留在本轮结束状态。
            self._choose_pending()

    def sort(self):
        # Python 的排序稳定，独立 ID 使当前行动者不依赖列表索引。
        self.combatants.sort(key=lambda c: c.initiative, reverse=True)

    def move_tied(self, combatant_id, direction):
        actor = self.get(combatant_id)
        if direction not in (-1, 1):
            raise BattleError("移动方向无效。")
        index = self.combatants.index(actor)
        target = index + direction
        if not 0 <= target < len(self.combatants):
            raise BattleError("已到列表边界，无法继续移动。")
        if self.combatants[target].initiative != actor.initiative:
            raise BattleError("只能与相邻且先攻相同的角色交换顺序；请先点击排序。")
        self.combatants[index], self.combatants[target] = (
            self.combatants[target], self.combatants[index])

    def start(self):
        if not self.combatants:
            raise BattleError("战斗列表为空，请先添加参战者。")
        if self.active:
            raise BattleError("战斗已经开始，请使用“下一位”。")
        self.sort()
        self.active, self.round = True, 1
        self.acted_ids.clear()
        self._choose_pending()

    def end(self):
        if not self.active:
            raise BattleError("当前没有进行中的战斗。")
        self.active, self.round, self.current_id = False, 0, None
        self.acted_ids.clear()

    def next_turn(self):
        if not self.combatants:
            raise BattleError("战斗列表为空，请先添加参战者。")
        if not self.active:
            raise BattleError("请先点击“开始战斗”。")
        if self.current_id is not None:
            self.acted_ids.add(self.current_id)
        self._choose_pending()
        if self.current_id is None:
            self.round += 1
            self.acted_ids.clear()
            self._choose_pending()
        return self.get(self.current_id)

    def damage(self, combatant_id, amount):
        actor = self.get(combatant_id)
        integer(amount, "伤害值", 0)
        actor.hp = max(0, actor.hp - amount)

    def heal(self, combatant_id, amount):
        actor = self.get(combatant_id)
        integer(amount, "治疗值", 0)
        actor.hp = min(actor.max_hp, actor.hp + amount)

    def correct_hp(self, combatant_id, value):
        actor = self.get(combatant_id)
        integer(value, "当前生命值", 0)
        if value > actor.max_hp:
            raise BattleError("当前生命值不能超过最大生命值。")
        actor.hp = value

    def to_dict(self):
        return {"version": 2, "combatants": [vars(c).copy() for c in self.combatants],
                "active": self.active, "round": self.round,
                "current_id": self.current_id,
                "acted_ids": [c.id for c in self.combatants if c.id in self.acted_ids]}

    @classmethod
    def from_dict(cls, data):
        if (not isinstance(data, dict) or type(data.get("version")) is not int
                or data["version"] not in (1, 2)):
            raise BattleError("存档格式或版本不受支持。")
        try:
            battle = cls()
            if not isinstance(data["combatants"], list):
                raise BattleError("存档中的参战者列表无效。")
            ids, monster_names = set(), set()
            for entry in data["combatants"]:
                if not isinstance(entry, dict):
                    raise BattleError("存档中的参战者数据无效。")
                entry = entry.copy()
                if data["version"] == 1:
                    # v1 存档兼容迁移：旧字段不再进入模型或新存档。
                    entry.pop("temp_hp", None)
                c = Combatant(**entry)
                validate_fields(c.name, c.kind, c.initiative, c.max_hp, c.hp)
                if not isinstance(c.id, str) or not c.id.strip() or c.id in ids:
                    raise BattleError("存档中的角色 ID 为空或重复。")
                c.name = c.name.strip()
                if c.kind == "怪物":
                    integer(c.monster_number, "怪物编号", 1)
                    key = (c.name, c.monster_number)
                    if key in monster_names:
                        raise BattleError("存档中的同名怪物编号重复。")
                    monster_names.add(key)
                elif c.monster_number is not None:
                    raise BattleError("非怪物角色不应有怪物编号。")
                ids.add(c.id)
                battle.combatants.append(c)
            active, round_number = data["active"], data["round"]
            current, acted = data["current_id"], data["acted_ids"]
            if type(active) is not bool:
                raise BattleError("存档中的战斗状态无效。")
            integer(round_number, "轮数", 0)
            if current is not None and (not isinstance(current, str) or current not in ids):
                raise BattleError("存档中的当前行动者不存在。")
            if (not isinstance(acted, list) or any(not isinstance(i, str) for i in acted)
                    or len(set(acted)) != len(acted) or not set(acted) <= ids):
                raise BattleError("存档中的已行动名单无效。")
            if active:
                if not ids or round_number < 1 or current in acted:
                    raise BattleError("存档中的轮次状态不一致。")
                if current is None and set(acted) != ids:
                    raise BattleError("存档缺少当前行动者。")
            elif round_number != 0 or current is not None or acted:
                raise BattleError("未开始战斗的存档包含无效轮次。")
            battle.active, battle.round, battle.current_id = active, round_number, current
            battle.acted_ids = set(acted)
            return battle
        except (KeyError, TypeError, RecursionError) as error:
            raise BattleError("存档字段缺失或格式不正确。") from error


class JsonStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except (ValueError, UnicodeError, RecursionError) as error:
            raise BattleError("存档不是有效的 UTF-8 JSON 文件。") from error
        return Battle.from_dict(data)

    def save(self, battle):
        # 临时文件和目标文件位于同一目录，避免半份 JSON 覆盖原存档。
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=self.path.parent,
                                             prefix=self.path.name + ".", suffix=".tmp",
                                             delete=False) as stream:
                temporary = stream.name
                json.dump(battle.to_dict(), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def backup_invalid(self):
        """独占创建备份；失败时调用方必须停止覆盖原存档。"""
        backup = self.path.with_name(self.path.name + ".invalid-" + uuid4().hex + ".bak")
        with self.path.open("rb") as source, backup.open("xb") as target:
            target.write(source.read())
        return backup

#!/usr/bin/env python3
"""将 2025 怪物图鉴 HTML 转换为结构化 JSON；仅使用 Python 标准库。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Optional


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / ".dnd5e" / "怪物图鉴2025"
OUTPUT = ROOT / "resources" / "monster_handbook.JSON"


@dataclass
class AbilityScore:
    score: int
    modifier: int
    saving_throw: int


@dataclass
class ArmorClass:
    value: int
    details: Optional[str]
    raw: str


@dataclass
class HitPoints:
    average: int
    formula: Optional[str]
    raw: str


@dataclass
class Initiative:
    modifier: int
    score: Optional[int]
    raw: str


@dataclass
class Speed:
    raw: str
    modes: dict[str, int] = field(default_factory=dict)


@dataclass
class NamedBonus:
    name: str
    bonus: int


@dataclass
class RuleSection:
    key: str
    name: str
    english_name: Optional[str]
    content: str


@dataclass
class Monster:
    """怪物图鉴中一个可直接用于战斗与详情展示的怪物数据结构。"""

    id: str
    name: str
    english_name: str
    category_path: list[str]
    source_file: str
    summary: Optional[str]
    habitats: list[str]
    treasure: list[str]
    description: Optional[str]
    size: Optional[str]
    creature_type: str
    alignment: Optional[str]
    classification_raw: str
    armor_class: ArmorClass
    initiative: Initiative
    hit_points: HitPoints
    speed: Speed
    abilities: dict[str, AbilityScore]
    skills: list[NamedBonus]
    damage_vulnerabilities: list[str]
    damage_resistances: list[str]
    damage_immunities: list[str]
    condition_immunities: list[str]
    senses: Optional[str]
    passive_perception: Optional[int]
    languages: list[str]
    challenge_rating: str
    experience_points: Optional[int]
    proficiency_bonus: Optional[int]
    sections: list[RuleSection]
    stat_block_text: str


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    children: list[Node | str] = field(default_factory=list)
    parent: Optional[Node] = None


class TreeParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), {key.lower(): value or "" for key, value in attrs}, parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if node.tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def descendants(node: Node, tag: Optional[str] = None):
    for child in node.children:
        if isinstance(child, Node):
            if tag is None or child.tag == tag:
                yield child
            yield from descendants(child, tag)


def first(node: Node, tag: str, class_name: Optional[str] = None) -> Optional[Node]:
    for child in descendants(node, tag):
        if class_name is None or class_name in child.attrs.get("class", "").split():
            return child
    return None


def inline_text(node: Node) -> str:
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag == "br":
            parts.append("\n")
        else:
            parts.append(inline_text(child))
    return clean_text("".join(parts))


def block_text(node: Node) -> str:
    block_tags = {"p", "div", "table", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag == "br":
            parts.append("\n")
        else:
            parts.append(block_text(child))
            if child.tag in block_tags:
                parts.append("\n")
    return clean_text("".join(parts), preserve_lines=True)


def clean_text(value: str, preserve_lines: bool = False) -> str:
    value = value.replace("\xa0", " ").replace("\u3000", " ")
    if not preserve_lines:
        return " ".join(value.split())
    lines = [" ".join(line.split()) for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def inside(node: Node, ancestor: Node) -> bool:
    current = node.parent
    while current is not None:
        if current is ancestor:
            return True
        current = current.parent
    return False


def parse_signed(value: str) -> int:
    return int(value.replace("＋", "+").replace("−", "-").strip())


def split_list(value: Optional[str]) -> list[str]:
    if not value or value in {"无", "—", "-"}:
        return []
    return [part.strip() for part in re.split(r"[，,；;、]", value) if part.strip() and part.strip() != "无"]


def labeled_values(stat: Node) -> dict[str, str]:
    values = {}
    for cell in descendants(stat, "td"):
        strong = first(cell, "strong")
        if strong is None:
            continue
        label = inline_text(strong).strip().rstrip("：:")
        full = inline_text(cell)
        if full.startswith(label):
            values.setdefault(label, full[len(label):].strip().lstrip("：:"))
    # 少量宽版数据卡把次要属性放在同一个段落中，以 BR 而非 TR 分隔。
    stat_labels = {"技能", "伤害易伤", "伤害抗性", "伤害免疫", "状态免疫", "感官", "语言", "CR"}
    for strong in descendants(stat, "strong"):
        label = inline_text(strong).strip().rstrip("：:")
        if label not in stat_labels or label in values or strong.parent is None:
            continue
        siblings = strong.parent.children
        try:
            start = siblings.index(strong) + 1
        except ValueError:
            continue
        parts = []
        for sibling in siblings[start:]:
            if isinstance(sibling, Node) and sibling.tag in {"br", "strong"}:
                break
            parts.append(sibling if isinstance(sibling, str) else inline_text(sibling))
        value = clean_text("".join(parts)).strip().lstrip("：:")
        if value:
            values[label] = value
    return values


def parse_armor(raw: str) -> ArmorClass:
    match = re.match(r"(\d+)(?:[（(](.*?)[）)])?", raw)
    if not match:
        raise ValueError(f"无法解析 AC：{raw}")
    return ArmorClass(int(match.group(1)), match.group(2) or None, raw)


def parse_hp(raw: str) -> HitPoints:
    match = re.match(r"(\d+)(?:[（(]([^）)]+)[）)])?", raw)
    if not match:
        raise ValueError(f"无法解析 HP：{raw}")
    return HitPoints(int(match.group(1)), match.group(2) or None, raw)


def parse_initiative(raw: str) -> Initiative:
    match = re.match(r"([+\-−＋]?\d+)(?:[（(](\d+)[）)])?", raw)
    if not match:
        raise ValueError(f"无法解析先攻：{raw}")
    return Initiative(parse_signed(match.group(1)), int(match.group(2)) if match.group(2) else None, raw)


def parse_speed(raw: str) -> Speed:
    modes = {}
    names = {"步行": "walk", "掘穴": "burrow", "攀爬": "climb", "飞行": "fly", "游泳": "swim"}
    for index, part in enumerate(re.split(r"[，,]", raw)):
        match = re.search(r"(\d+)\s*尺", part)
        if not match:
            continue
        mode = "walk" if index == 0 else None
        for chinese, key in names.items():
            if chinese in part:
                mode = key
                break
        if mode:
            modes[mode] = int(match.group(1))
    return Speed(raw, modes)


def parse_abilities(stat: Node) -> dict[str, AbilityScore]:
    table = next((node for node in descendants(stat, "table")
                  if "stat-abilities" in node.attrs.get("class", "").split()), None)
    if table is None:
        return {}
    names = {"力量": "strength", "敏捷": "dexterity", "体质": "constitution",
             "智力": "intelligence", "感知": "wisdom", "魅力": "charisma"}
    result = {}
    for row in descendants(table, "tr"):
        cells = [cell for cell in row.children if isinstance(cell, Node) and cell.tag in {"td", "th"}]
        for index, cell in enumerate(cells):
            chinese = inline_text(cell)
            if chinese not in names:
                continue
            values = []
            for following in cells[index + 1:]:
                text = inline_text(following)
                if text:
                    values.append(text)
                if len(values) == 3:
                    break
            if len(values) == 3:
                result[names[chinese]] = AbilityScore(int(values[0]), parse_signed(values[1]), parse_signed(values[2]))
    return result


def parse_skills(raw: Optional[str]) -> list[NamedBonus]:
    result = []
    for item in split_list(raw):
        match = re.match(r"(.+?)([+\-−＋]\d+)$", item)
        if match:
            result.append(NamedBonus(match.group(1).strip(), parse_signed(match.group(2))))
    return result


def split_bilingual(value: str) -> tuple[str, Optional[str]]:
    match = re.search(r"[A-Za-z]", value)
    if not match:
        return value.strip().rstrip("。"), None
    return value[:match.start()].strip().rstrip("。"), value[match.start():].strip().rstrip("。")


def section_key(name: str) -> str:
    for prefix, key in (("特质", "traits"), ("附赠动作", "bonus_actions"),
                        ("反应", "reactions"), ("传奇动作", "legendary_actions"), ("动作", "actions")):
        if name.startswith(prefix):
            return key
    return "other"


def parse_sections(stat: Node) -> list[RuleSection]:
    sections = []
    for heading in descendants(stat, "h6"):
        parent = heading.parent
        if parent is None:
            continue
        try:
            start = parent.children.index(heading) + 1
        except ValueError:
            continue
        content_nodes = []
        for sibling in parent.children[start:]:
            if isinstance(sibling, Node) and sibling.tag == "h6":
                break
            content_nodes.append(sibling)
        container = Node("section", {}, content_nodes)
        content = block_text(container)
        name, english = split_bilingual(inline_text(heading))
        sections.append(RuleSection(section_key(name), name, english, content))
    return sections


def parse_classification(raw: str) -> tuple[Optional[str], str, Optional[str]]:
    parts = re.split(r"[，,]", raw, maxsplit=1)
    descriptor = parts[0].strip()
    alignment = parts[1].strip() if len(parts) > 1 else None
    sizes = ("超巨型", "超微型", "微型", "小型", "中型", "大型", "巨型")
    size = next((item for item in sizes if descriptor.startswith(item)), None)
    creature_type = descriptor[len(size):].strip() if size else descriptor
    return size, creature_type, alignment


def parse_habitat(body: Node) -> tuple[list[str], list[str]]:
    node = first(body, "div", "HT")
    if node is None:
        return [], []
    value = inline_text(node)
    match = re.search(r"栖息地[：:]\s*(.*?)(?:[；;]\s*)?宝藏[：:]\s*(.*)$", value)
    if not match:
        return [], []
    return split_list(match.group(1)), split_list(match.group(2))


def parse_monster(path: Path) -> Optional[Monster]:
    parser = TreeParser()
    parser.feed(path.read_bytes().decode("gb18030"))
    h5 = first(parser.root, "h5")
    if h5 is None:
        return None
    stat = h5.parent
    while stat is not None and "stat-block" not in stat.attrs.get("class", "").split():
        stat = stat.parent
    if stat is None:
        return None
    identifier = h5.attrs["id"]
    english_name = identifier.replace("_", " ")
    visible_name = inline_text(h5)
    name = visible_name[:-len(english_name)].strip() if visible_name.lower().endswith(english_name.lower()) else split_bilingual(visible_name)[0]
    sub_line = first(stat, "div", "sub-line")
    classification = inline_text(sub_line) if sub_line else ""
    size, creature_type, alignment = parse_classification(classification)
    fields = labeled_values(stat)
    cr_raw = fields.get("CR", "")
    cr_match = re.match(r"([^（(]+)", cr_raw)
    if cr_match is None:
        raise ValueError(f"无法解析 CR：{path}: {cr_raw}")
    xp_match = re.search(r"(?:XP\s*([\d,]+)|([\d,]+)\s*XP)", cr_raw, re.IGNORECASE)
    pb_match = re.search(r"PB\s*([+\-]?\d+)", cr_raw, re.IGNORECASE)
    senses = fields.get("感官")
    passive = re.search(r"被动察觉\s*(\d+)", senses or "")
    body = first(parser.root, "body") or parser.root
    summary_node = first(body, "p", "sum")
    habitats, treasure = parse_habitat(body)
    lore = []
    for paragraph in descendants(body, "p"):
        if inside(paragraph, stat) or "sum" in paragraph.attrs.get("class", "").split():
            continue
        value = block_text(paragraph)
        if value:
            lore.append(value)
    relative = path.relative_to(SOURCE)
    return Monster(
        id=identifier,
        name=name,
        english_name=english_name,
        category_path=list(relative.parts[:-1]),
        source_file=relative.as_posix(),
        summary=inline_text(summary_node) if summary_node else None,
        habitats=habitats,
        treasure=treasure,
        description="\n\n".join(lore) or None,
        size=size,
        creature_type=creature_type,
        alignment=alignment,
        classification_raw=classification,
        armor_class=parse_armor(fields["AC"]),
        initiative=parse_initiative(fields["先攻"]),
        hit_points=parse_hp(fields["HP"]),
        speed=parse_speed(fields["速度"]),
        abilities=parse_abilities(stat),
        skills=parse_skills(fields.get("技能")),
        damage_vulnerabilities=split_list(fields.get("伤害易伤")),
        damage_resistances=split_list(fields.get("伤害抗性")),
        damage_immunities=split_list(fields.get("伤害免疫")),
        condition_immunities=split_list(fields.get("状态免疫")),
        senses=senses,
        passive_perception=int(passive.group(1)) if passive else None,
        languages=split_list(fields.get("语言")),
        challenge_rating=cr_match.group(1).strip(),
        experience_points=(int((xp_match.group(1) or xp_match.group(2)).replace(",", ""))
                           if xp_match else None),
        proficiency_bonus=parse_signed(pb_match.group(1)) if pb_match else None,
        sections=parse_sections(stat),
        stat_block_text=block_text(stat),
    )


def validate(monsters: list[Monster], expected_count: int):
    if len(monsters) != expected_count:
        raise ValueError(f"数据卡数量不一致：HTML 中 {expected_count} 个，生成 {len(monsters)} 个")
    ids = [monster.id for monster in monsters]
    if len(ids) != len(set(ids)):
        raise ValueError("怪物 ID 重复")
    for monster in monsters:
        if not monster.name or monster.armor_class.value < 0 or monster.hit_points.average < 0:
            raise ValueError(f"怪物必填字段无效：{monster.source_file}")
        if set(monster.abilities) != {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}:
            raise ValueError(f"怪物六维不完整：{monster.source_file}")


def main():
    html_files = sorted(SOURCE.rglob("*.htm"), key=lambda path: path.relative_to(SOURCE).as_posix())
    expected_count = 0
    monsters = []
    for path in html_files:
        text = path.read_bytes().decode("gb18030")
        expected_count += len(re.findall(r"<h5\b", text, re.IGNORECASE))
        monster = parse_monster(path)
        if monster is not None:
            monsters.append(monster)
    validate(monsters, expected_count)
    payload = {
        "schema_version": 1,
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "encoding": "UTF-8",
        "monster_struct": {
            "python_type": "Monster",
            "definition_file": Path(__file__).name,
            "primary_key": "id",
            "fields": list(Monster.__dataclass_fields__),
        },
        "source_html_count": len(html_files),
        "monster_count": len(monsters),
        "monsters": [asdict(monster) for monster in monsters],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"已生成 {OUTPUT}：{len(monsters)} 个怪物，来自 {len(html_files)} 个 HTML。")


if __name__ == "__main__":
    main()

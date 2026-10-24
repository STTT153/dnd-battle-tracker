"""把 resources/ 下的 SVG 图标渲染成可着色的 Tkinter 画布按钮（仅用标准库）。"""

import math
import re
import tkinter as tk
import xml.etree.ElementTree as ET

# SVG 里的 stroke="currentColor" 会替换成调用方传入的颜色。
_TOKEN_RE = re.compile(r"([A-Za-z])|([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")
_ARG_COUNTS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "S": 4, "T": 2, "A": 7, "Z": 0}


def _tokenize_path(d):
    tokens = []
    for match in _TOKEN_RE.finditer(d):
        if match.group(1) is not None:
            tokens.append((match.group(1), None))
        else:
            tokens.append((None, float(match.group(2))))
    return tokens


def _parse_commands(d):
    tokens = _tokenize_path(d)
    commands = []
    index = 0
    while index < len(tokens):
        cmd, _ = tokens[index]
        if cmd is None:
            index += 1
            continue
        index += 1
        args = []
        arg_count = _ARG_COUNTS.get(cmd.upper(), 0)
        while index < len(tokens) and len(args) < arg_count:
            next_cmd, next_val = tokens[index]
            if next_cmd is not None:
                break
            args.append(next_val)
            index += 1
        commands.append((cmd, args))
    return commands


def _arc_points(p0, p1, rx, ry, large_arc, sweep, samples=48):
    """把圆弧离散成折线点（只处理 rx == ry 的正圆，足够本项目使用）。"""
    x0, y0 = p0
    x1, y1 = p1
    if math.hypot(x1 - x0, y1 - y0) < 1e-9:
        return []
    radius = (rx + ry) / 2.0
    dx, dy = x1 - x0, y1 - y0
    chord = math.hypot(dx, dy)
    if chord / 2.0 > radius:
        radius = chord / 2.0
    mid_x = (x0 + x1) / 2.0
    mid_y = (y0 + y1) / 2.0
    height = math.sqrt(max(0.0, radius * radius - (chord / 2.0) ** 2))
    ux, uy = dx / chord, dy / chord
    nx, ny = -uy, ux
    if sweep == 0:
        cx, cy = mid_x + height * nx, mid_y + height * ny
    else:
        cx, cy = mid_x - height * nx, mid_y - height * ny
    start_angle = math.atan2(y0 - cy, x0 - cx)
    end_angle = math.atan2(y1 - cy, x1 - cx)
    delta = end_angle - start_angle
    while delta > 2 * math.pi:
        delta -= 2 * math.pi
    while delta < -2 * math.pi:
        delta += 2 * math.pi
    if sweep == 0 and delta > 0:
        delta -= 2 * math.pi
    elif sweep == 1 and delta < 0:
        delta += 2 * math.pi
    if large_arc == 1 and abs(delta) < math.pi:
        delta += 2 * math.pi if delta > 0 else -2 * math.pi
    elif large_arc == 0 and abs(delta) > math.pi:
        delta -= 2 * math.pi if delta > 0 else -2 * math.pi
    points = []
    for step in range(1, samples + 1):
        angle = start_angle + delta * step / samples
        points += [cx + radius * math.cos(angle), cy + radius * math.sin(angle)]
    return points


def _path_subpaths(d):
    commands = _parse_commands(d)
    subpaths = []
    current = [0.0, 0.0]
    points = []
    closed = False

    def flush():
        nonlocal points, closed
        if points:
            subpaths.append((points, closed))
        points = []
        closed = False

    for cmd, args in commands:
        upper = cmd.upper()
        relative = cmd.islower()
        if upper == "M":
            flush()
            x, y = args[0], args[1]
            if relative:
                x += current[0]
                y += current[1]
            current = [x, y]
            points = [x, y]
        elif upper == "L":
            for j in range(0, len(args), 2):
                x, y = args[j], args[j + 1]
                if relative:
                    x += current[0]
                    y += current[1]
                points += [x, y]
                current = [x, y]
        elif upper == "H":
            for value in args:
                x = value + current[0] if relative else value
                points += [x, current[1]]
                current = [x, current[1]]
        elif upper == "V":
            for value in args:
                y = value + current[1] if relative else value
                points += [current[0], y]
                current = [current[0], y]
        elif upper == "A":
            rx, ry = args[0], args[1]
            large_arc, sweep = args[3], args[4]
            x, y = args[5], args[6]
            if relative:
                x += current[0]
                y += current[1]
            points += _arc_points(current, (x, y), rx, ry, large_arc, sweep)
            current = [x, y]
        elif upper == "Z":
            closed = True
    flush()
    return subpaths


def _load_svg_icon(svg_path):
    root = ET.parse(str(svg_path)).getroot()
    width = float(root.get("width", "20"))
    height = float(root.get("height", "20"))
    viewbox = (root.get("viewBox") or "0 0 24 24").split()
    view_w = float(viewbox[2])
    view_h = float(viewbox[3])
    root_fill = root.get("fill", "none")
    root_stroke = root.get("stroke", "none")
    primitives = []
    for element in root.iter():
        tag = element.tag.split("}")[-1]
        fill = element.get("fill", root_fill)
        stroke = element.get("stroke", root_stroke)
        filled = fill == "currentColor"
        stroked = stroke == "currentColor"
        if tag == "path":
            d = element.get("d")
            if not d:
                continue
            stroke_width = float(element.get("stroke-width", "1.0"))
            for points, closed in _path_subpaths(d):
                primitives.append(("polygon" if closed else "line", points, stroke_width,
                                   filled, stroked))
        elif tag == "rect":
            x = float(element.get("x", "0"))
            y = float(element.get("y", "0"))
            w = float(element.get("width", "0"))
            h = float(element.get("height", "0"))
            stroke_width = float(element.get("stroke-width", "1.0"))
            primitives.append(("rect", (x, y, x + w, y + h), stroke_width,
                               filled, stroked))
        elif tag == "circle":
            cx = float(element.get("cx", "0"))
            cy = float(element.get("cy", "0"))
            radius = float(element.get("r", "0"))
            stroke_width = float(element.get("stroke-width", "1.0"))
            primitives.append(("oval", (cx - radius, cy - radius,
                                         cx + radius, cy + radius), stroke_width,
                               filled, stroked))
    return width, height, view_w, view_h, primitives


class SvgIconButton(tk.Canvas):
    """用 Canvas 画的图标按钮，支持 hover / 按下 / 禁用与 invoke()，替代文字图标。"""

    def __init__(self, master, svg_path, color, command=None, icon_name="",
                 bg="#181818", hover_bg="#2A2D2E", pressed_bg="#333333",
                 disabled_color="#666666", focus_color="#007FD4", **kwargs):
        width, height, view_w, view_h, primitives = _load_svg_icon(svg_path)
        self._icon_size = min(width, height)
        self._scale = self._icon_size / max(view_w, view_h) if max(view_w, view_h) else 1.0
        pad = 4
        self._canvas_w = int(self._icon_size) + pad * 2
        self._canvas_h = int(self._icon_size) + pad * 2
        super().__init__(master, width=self._canvas_w, height=self._canvas_h,
                         background=bg, highlightthickness=1,
                         highlightbackground=bg, highlightcolor=focus_color,
                         borderwidth=0, cursor="pointinghand", takefocus=1, **kwargs)
        self._primitives = primitives
        self._color = color
        self._bg = bg
        self._hover_bg = hover_bg
        self._pressed_bg = pressed_bg
        self._disabled_color = disabled_color
        self.command = command
        self.icon_name = icon_name
        self._enabled = True
        self._state = "normal"
        self._render(color)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Return>", lambda _event: self.invoke())
        self.bind("<space>", lambda _event: self.invoke())

    def _render(self, color):
        self.delete("icon")
        scale = self._scale
        offset_x = (self._canvas_w - self._icon_size) / 2.0
        offset_y = (self._canvas_h - self._icon_size) / 2.0
        for kind, data, stroke_width, filled, stroked in self._primitives:
            width = max(1.0, stroke_width * scale)
            if kind == "line":
                if not stroked:
                    continue
                points = [offset_x + value * scale for value in data]
                self.create_line(*points, fill=color, width=width,
                                 capstyle="round", joinstyle="round", tags="icon")
            elif kind == "polygon":
                points = [offset_x + value * scale for value in data]
                self.create_polygon(*points, outline=color if stroked else "",
                                    fill=color if filled else "", width=width,
                                    joinstyle="round", tags="icon")
            elif kind == "rect":
                x0, y0, x1, y1 = data
                self.create_rectangle(offset_x + x0 * scale, offset_y + y0 * scale,
                                      offset_x + x1 * scale, offset_y + y1 * scale,
                                      outline=color if stroked else "",
                                      fill=color if filled else "", width=width, tags="icon")
            elif kind == "oval":
                x0, y0, x1, y1 = data
                self.create_oval(offset_x + x0 * scale, offset_y + y0 * scale,
                                 offset_x + x1 * scale, offset_y + y1 * scale,
                                 outline=color if stroked else "",
                                 fill=color if filled else "", width=width, tags="icon")

    def _set_enabled(self, enabled):
        self._enabled = enabled
        self._state = "normal" if enabled else "disabled"
        self._render(self._color if enabled else self._disabled_color)
        self.configure(background=self._bg)
        super().configure(cursor="pointinghand" if enabled else "arrow")

    def configure(self, cnf=None, **kwargs):
        if cnf is not None:
            kwargs.update(cnf)
        state = kwargs.pop("state", None)
        if state is not None:
            self._set_enabled(state != "disabled")
        if kwargs:
            super().configure(**kwargs)

    def cget(self, key):
        if key == "state":
            return self._state
        if key == "text":
            return self.icon_name
        return super().cget(key)

    def __getitem__(self, key):
        return self.cget(key)

    def invoke(self):
        if self._enabled and self.command is not None:
            self.command()

    def _on_enter(self, _event):
        if self._enabled:
            self.configure(background=self._hover_bg)

    def _on_leave(self, _event):
        if self._enabled:
            self.configure(background=self._bg)

    def _on_press(self, _event):
        if self._enabled:
            self.configure(background=self._pressed_bg)

    def _on_release(self, _event):
        if self._enabled:
            self.configure(background=self._hover_bg)
            self.invoke()


"""UI界面管理 - 修复版"""
from dataclasses import dataclass, field


@dataclass
class UIWindow:
    wid: str
    visible: bool = False
    modal: bool = False
    z_order: int = 0
    focus: bool = False
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
    collapsed: bool = False
    parent: str = None

    def contains_point(self, x: float, y: float) -> bool:
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


@dataclass
class UIEvent:
    name: str
    source: str
    stopped: bool = False

    def stop_propagation(self) -> None:
        self.stopped = True


class UIManager:
    def __init__(self):
        self.windows: dict[str, UIWindow] = {}
        self.focused: str = None
        self.keyboard_visible: bool = False
        self._z_counter: int = 0
        self._handlers: dict[tuple[str, str], list] = {}

    # ---- 窗口单例 + 层级管理 ----
    def open_window(self, wid: str) -> bool:
        if wid not in self.windows:
            self.windows[wid] = UIWindow(wid)
        w = self.windows[wid]
        if w.visible:
            self.raise_window(wid)
            return False
        w.visible = True
        self.raise_window(wid)
        return True

    def close_window(self, wid: str) -> bool:
        w = self.windows.get(wid)
        if w is None:
            return False
        was_visible = w.visible
        w.visible = False
        if self.focused == wid:
            self.blur()
        return was_visible

    def raise_window(self, wid: str) -> None:
        w = self.windows.get(wid)
        if w is None:
            return
        self._z_counter += 1
        w.z_order = self._z_counter

    def top_window(self):
        visible = [w for w in self.windows.values() if w.visible]
        return max(visible, key=lambda w: w.z_order, default=None)

    # ---- 模态窗口：阻止所有后台交互 ----
    def set_modal(self, wid: str, modal: bool) -> None:
        if wid in self.windows:
            self.windows[wid].modal = modal
            if modal:
                self.raise_window(wid)

    def active_modal(self):
        modals = [w for w in self.windows.values() if w.visible and w.modal]
        return max(modals, key=lambda w: w.z_order, default=None)

    def is_interactive(self, wid: str) -> bool:
        modal = self.active_modal()
        return modal is None or modal.wid == wid

    def handle_click(self, wid: str, x: float = None, y: float = None) -> bool:
        w = self.windows.get(wid)
        if w is None or not w.visible or not self.is_interactive(wid):
            return False
        return True

    def click_outside_closes(self, wid: str) -> bool:
        return False

    # ---- 事件分发：可阻止冒泡 + 优先级 ----
    def on(self, wid: str, event: str, handler, priority: int = 0) -> None:
        key = (wid, event)
        self._handlers.setdefault(key, []).append((priority, handler))
        self._handlers[key].sort(key=lambda item: -item[0])

    def dispatch_event(self, wid: str, event: str) -> bool:
        if not self.is_interactive(wid):
            return False
        ui_event = UIEvent(event, wid)
        current = wid
        bubbled = False
        while current is not None:
            for _, handler in self._handlers.get((current, event), []):
                handler(ui_event)
            if ui_event.stopped:
                return False
            w = self.windows.get(current)
            current = w.parent if w else None
            if current is not None:
                bubbled = True
        return bubbled

    dispatch_ui_event = dispatch_event

    # ---- 焦点唯一 + 丢失焦点关闭虚拟键盘 ----
    def set_focus(self, wid: str) -> None:
        if wid not in self.windows:
            return
        for w in self.windows.values():
            w.focus = False
        self.windows[wid].focus = True
        self.focused = wid
        self.keyboard_visible = True

    def blur(self) -> None:
        if self.focused is not None and self.focused in self.windows:
            self.windows[self.focused].focus = False
        self.focused = None
        self.keyboard_visible = False

    # ---- 界面状态完整保存 / 恢复 ----
    def save_ui_state(self) -> dict:
        return {
            wid: {
                "visible": w.visible,
                "position": (w.x, w.y),
                "size": (w.width, w.height),
                "collapsed": w.collapsed,
                "z_order": w.z_order,
            }
            for wid, w in self.windows.items()
        }

    def restore_ui_state(self, state: dict) -> None:
        for wid, saved in state.items():
            w = self.windows.setdefault(wid, UIWindow(wid))
            w.visible = saved.get("visible", w.visible)
            position = saved.get("position")
            if position is not None:
                w.x, w.y = position
            size = saved.get("size")
            if size is not None:
                w.width, w.height = size
            w.collapsed = saved.get("collapsed", w.collapsed)
            w.z_order = saved.get("z_order", w.z_order)

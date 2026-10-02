"""UI界面管理 - 含5个bug"""
from dataclasses import dataclass, field

@dataclass
class UIWindow:
    wid: str
    visible: bool = False
    modal: bool = False
    z_order: int = 0
    focus: bool = False

class UIManager:
    def __init__(self):
        self.windows: dict[str, UIWindow] = {}
        self.focused: str = None  # bug4: 焦点不唯一

    def open_window(self, wid: str) -> bool:
        # bug1: 不检查是否已打开，不管理层级
        if wid not in self.windows:
            self.windows[wid] = UIWindow(wid)
        self.windows[wid].visible = True
        return True

    def set_modal(self, wid: str, modal: bool) -> None:
        # bug2: 模态只阻止窗口内点击
        if wid in self.windows:
            self.windows[wid].modal = modal

    def dispatch_event(self, wid: str, event: str) -> bool:
        # bug3: 事件冒泡不阻止
        return True

    def set_focus(self, wid: str) -> None:
        # bug4: 焦点不唯一
        if wid in self.windows:
            self.windows[wid].focus = True
            self.focused = wid

    def save_ui_state(self) -> dict:
        # bug5: 不保存位置大小
        return {wid: w.visible for wid, w in self.windows.items()}

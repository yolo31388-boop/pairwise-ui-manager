"""UI界面管理 - 窗口单例/层级/模态/事件/焦点/状态持久化"""
from dataclasses import dataclass, field


@dataclass
class UIWindow:
    wid: str
    visible: bool = False
    modal: bool = False
    z_order: int = 0
    focus: bool = False
    position: tuple[int, int] | None = None
    size: tuple[int, int] | None = None
    collapsed: bool = False


@dataclass
class UIEvent:
    name: str
    target: str
    stopped: bool = False

    def stop_propagation(self) -> None:
        self.stopped = True


class UIManager:
    def __init__(self):
        self.windows: dict[str, UIWindow] = {}
        self.focused: str | None = None
        self.keyboard_visible: bool = False
        self.priorities: dict[str, int] = {}
        self.handlers: dict[str, list] = {}
        self._z_counter: int = 0

    def _next_z(self) -> int:
        self._z_counter += 1
        return self._z_counter

    def open_window(self, wid: str) -> bool:
        """单例打开：已打开则拒绝重复实例并置顶，新窗口分配最高层级。"""
        if wid in self.windows and self.windows[wid].visible:
            self._bring_to_front(wid)
            return False
        if wid not in self.windows:
            self.windows[wid] = UIWindow(wid)
        win = self.windows[wid]
        win.visible = True
        win.z_order = self._next_z()
        return True

    def close_window(self, wid: str) -> None:
        win = self.windows.get(wid)
        if win is None:
            return
        win.visible = False
        win.modal = False
        if self.focused == wid:
            self.clear_focus()

    def _bring_to_front(self, wid: str) -> None:
        self.windows[wid].z_order = self._next_z()

    def bring_to_front(self, wid: str) -> bool:
        if wid not in self.windows or not self.windows[wid].visible:
            return False
        self._bring_to_front(wid)
        return True

    def top_window(self) -> str | None:
        visible = (w for w in self.windows.values() if w.visible)
        top = max(visible, key=lambda w: (self.priorities.get(w.wid, 0), w.z_order),
                  default=None)
        return top.wid if top else None

    def _active_modal(self) -> UIWindow | None:
        """当前实际生效的模态窗口：必须是模态窗口自身之上没有其它可见窗口。"""
        top = self.top_window()
        if top is None:
            return None
        win = self.windows[top]
        return win if win.modal else None

    def set_modal(self, wid: str, modal: bool = True) -> None:
        if wid in self.windows:
            self.windows[wid].modal = modal
            if modal:
                self._bring_to_front(wid)

    def can_interact(self, wid: str) -> bool:
        """模态窗口存在时，只有模态窗口自身可交互，背景UI全部被阻止。"""
        modal = self._active_modal()
        if modal is None:
            return True
        return modal.wid == wid

    def register_handler(self, wid: str, handler) -> None:
        self.handlers.setdefault(wid, []).append(handler)

    def dispatch_event(self, wid: str, event: str,
                       bubble_path: list[str] | None = None) -> bool:
        """派发UI事件。

        返回True表示事件成功投递给目标UI；返回False表示被模态拦截
        或目标不存在（事件被消费，不会穿透到背景/游戏层）。
        处理器返回False或调用event.stop_propagation()可阻止冒泡。
        """
        if not self.can_interact(wid):
            return False

        path = list(bubble_path) if bubble_path else [wid]
        ev = UIEvent(name=event, target=wid)
        for target in path:
            if ev.stopped:
                break
            for handler in self.handlers.get(target, []):
                ret = handler(ev)
                if ret is False:
                    ev.stop_propagation()
                    break

        # 事件只投递给已注册的UI元素；未知目标视为被消费
        return wid in self.windows or wid in self.handlers

    def set_priority(self, wid: str, priority: int) -> None:
        self.priorities[wid] = priority

    def set_focus(self, wid: str) -> None:
        """焦点唯一：设置新焦点前清除旧焦点，并弹出虚拟键盘。"""
        if wid not in self.windows:
            return
        if self.focused is not None and self.focused != wid:
            old = self.windows.get(self.focused)
            if old is not None:
                old.focus = False
        self.windows[wid].focus = True
        self.focused = wid
        self.keyboard_visible = True

    def clear_focus(self) -> None:
        """清除焦点并收起虚拟键盘，避免键盘一直遮挡屏幕。"""
        if self.focused is not None:
            old = self.windows.get(self.focused)
            if old is not None:
                old.focus = False
            self.focused = None
        self.keyboard_visible = False

    def save_ui_state(self) -> dict:
        """保存完整界面状态：可见性、位置、大小、展开/折叠、层级。"""
        state = {}
        for wid, w in self.windows.items():
            state[wid] = {
                "visible": w.visible,
                "modal": w.modal,
                "position": tuple(w.position) if w.position else None,
                "size": tuple(w.size) if w.size else None,
                "collapsed": w.collapsed,
                "z_order": w.z_order,
            }
        return state

    def load_ui_state(self, state: dict) -> None:
        """恢复界面状态，未保存过的窗口保持默认。"""
        for wid, saved in state.items():
            if isinstance(saved, dict):
                win = self.windows.setdefault(wid, UIWindow(wid))
                win.visible = saved.get("visible", win.visible)
                win.modal = saved.get("modal", win.modal)
                win.position = tuple(saved["position"]) if saved.get("position") else None
                win.size = tuple(saved["size"]) if saved.get("size") else None
                win.collapsed = saved.get("collapsed", win.collapsed)
                win.z_order = saved.get("z_order", win.z_order)
                self._z_counter = max(self._z_counter, win.z_order)
            else:
                # 兼容旧版仅存 bool 的格式
                self.windows.setdefault(wid, UIWindow(wid, visible=bool(saved)))

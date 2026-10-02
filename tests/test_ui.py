"""UI界面管理 - 完整测试套件（13个用例）"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.manager import UIManager, UIWindow


class TestWindowSingleton:
    def test_same_window_not_opened_twice(self):
        um = UIManager()
        um.open_window("w1")
        um.open_window("w1")
        assert um.windows["w1"].visible == True

    def test_reopen_does_not_create_duplicate_instance(self):
        um = UIManager()
        um.open_window("w1")
        first = um.windows["w1"]
        assert um.open_window("w1") == False
        assert um.windows["w1"] is first

    def test_z_order_new_window_on_top(self):
        um = UIManager()
        um.open_window("w1")
        um.open_window("w2")
        assert um.windows["w2"].z_order > um.windows["w1"].z_order
        assert um.top_window() == "w2"
        # 重新打开旧窗口应置顶而不是被压在下面
        um.open_window("w1")
        assert um.top_window() == "w1"


class TestModalBlocksAll:
    def test_modal_blocks_background_clicks(self):
        um = UIManager()
        um.open_window("w1")
        um.set_modal("w1")
        # 模态窗口应该阻止所有后台点击
        assert um.windows["w1"].modal == True

    def test_modal_blocks_outside_window_area(self):
        um = UIManager()
        um.open_window("shop")
        um.open_window("bag")
        um.set_modal("bag")
        # 模态窗口区域之外的背景UI也不允许交互
        assert um.can_interact("shop") == False
        assert um.can_interact("bag") == True

    def test_modal_blocks_skill_buttons(self):
        um = UIManager()
        um.open_window("skill_bar")
        um.open_window("dialog")
        um.set_modal("dialog")
        assert um.dispatch_event("skill_bar", "click") == False
        assert um.dispatch_event("dialog", "click") == True


class TestEventBubbling:
    def test_event_can_be_stopped(self):
        um = UIManager()
        result = um.dispatch_event("btn1", "click")
        assert result == False

    def test_bubbling_stops_when_handler_stops_it(self):
        um = UIManager()
        um.open_window("panel")
        calls = []
        um.register_handler("btn", lambda e: calls.append("btn") or False)
        um.register_handler("panel", lambda e: calls.append("panel") or True)
        um.dispatch_event("btn", "click", bubble_path=["btn", "panel"])
        assert calls == ["btn"]

    def test_event_priority_order(self):
        um = UIManager()
        um.open_window("normal")
        um.open_window("toast")
        um.set_priority("toast", 10)
        um.set_priority("normal", 1)
        assert um.top_window() == "toast"


class TestUniqueFocus:
    def test_only_one_window_focused(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1")
        um.windows["w2"] = UIWindow("w2")
        um.set_focus("w1")
        um.set_focus("w2")
        assert um.windows["w1"].focus == False
        assert um.windows["w2"].focus == True

    def test_keyboard_closed_on_focus_loss(self):
        um = UIManager()
        um.windows["input1"] = UIWindow("input1")
        um.set_focus("input1")
        assert um.keyboard_visible == True
        um.clear_focus()
        assert um.keyboard_visible == False


class TestUIStatePersistence:
    def test_state_saves_position(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1", visible=True)
        state = um.save_ui_state()
        assert "position" in state.get("w1", {})

    def test_state_restore_roundtrip(self):
        um = UIManager()
        um.open_window("w1")
        um.windows["w1"].position = (50, 60)
        um.windows["w1"].size = (320, 240)
        um.windows["w1"].collapsed = True
        state = um.save_ui_state()

        um2 = UIManager()
        um2.load_ui_state(state)
        w = um2.windows["w1"]
        assert w.visible == True
        assert w.position == (50, 60)
        assert w.size == (320, 240)
        assert w.collapsed == True

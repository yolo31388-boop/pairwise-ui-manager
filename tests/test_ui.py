"""UI界面管理 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.manager import UIManager, UIWindow

class TestWindowSingleton:
    def test_same_window_not_opened_twice(self):
        um = UIManager()
        um.open_window("w1")
        um.open_window("w1")
        assert um.windows["w1"].visible == True

    def test_reopen_returns_false_without_duplicate(self):
        um = UIManager()
        assert um.open_window("bag") == True
        assert um.open_window("bag") == False
        assert list(um.windows).count("bag") == 1

    def test_new_window_is_raised_on_top(self):
        um = UIManager()
        um.open_window("w1")
        um.open_window("w2")
        assert um.windows["w2"].z_order > um.windows["w1"].z_order
        assert um.top_window().wid == "w2"

class TestModalBlocksAll:
    def test_modal_blocks_background_clicks(self):
        um = UIManager()
        um.open_window("w1")
        um.set_modal("w1", True)
        # 模态窗口应该阻止所有后台点击
        assert um.windows["w1"].modal == True

    def test_modal_blocks_clicks_anywhere_outside_window(self):
        um = UIManager()
        um.open_window("hud")
        um.open_window("dialog")
        um.set_modal("dialog", True)
        assert um.is_interactive("dialog") == True
        assert um.is_interactive("hud") == False
        assert um.handle_click("hud", 9999, 9999) == False

class TestEventBubbling:
    def test_event_can_be_stopped(self):
        um = UIManager()
        result = um.dispatch_event("btn1", "click")
        assert result == False

    def test_bubbling_stops_before_parent_handler(self):
        um = UIManager()
        um.windows["panel"] = UIWindow("panel", visible=True)
        um.windows["btn"] = UIWindow("btn", visible=True, parent="panel")
        calls = []
        um.on("panel", "click", lambda e: calls.append("panel"))
        def stop_handler(e):
            calls.append("btn")
            e.stop_propagation()
        um.on("btn", "click", stop_handler)
        assert um.dispatch_ui_event("btn", "click") == False
        assert calls == ["btn"]

    def test_handlers_follow_priority_order(self):
        um = UIManager()
        um.windows["w"] = UIWindow("w", visible=True)
        calls = []
        um.on("w", "click", lambda e: calls.append("low"), priority=0)
        um.on("w", "click", lambda e: calls.append("high"), priority=10)
        um.dispatch_event("w", "click")
        assert calls == ["high", "low"]

class TestUniqueFocus:
    def test_only_one_window_focused(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1")
        um.windows["w2"] = UIWindow("w2")
        um.set_focus("w1")
        um.set_focus("w2")
        assert um.windows["w1"].focus == False
        assert um.windows["w2"].focus == True

    def test_blur_closes_virtual_keyboard(self):
        um = UIManager()
        um.windows["input"] = UIWindow("input")
        um.set_focus("input")
        assert um.keyboard_visible == True
        um.blur()
        assert um.keyboard_visible == False
        assert um.focused is None

class TestUIStatePersistence:
    def test_state_saves_position(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1", visible=True)
        state = um.save_ui_state()
        assert "position" in state.get("w1", {})

    def test_state_saves_size_and_collapsed(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1", visible=True, collapsed=True)
        state = um.save_ui_state()
        assert state["w1"]["collapsed"] == True
        assert "size" in state["w1"]

    def test_restore_roundtrips_full_geometry(self):
        um = UIManager()
        um.windows["w1"] = UIWindow(
            "w1", visible=True, x=10, y=20, width=300, height=200, collapsed=True
        )
        state = um.save_ui_state()
        um2 = UIManager()
        um2.restore_ui_state(state)
        w = um2.windows["w1"]
        assert w.visible == True
        assert (w.x, w.y) == (10, 20)
        assert (w.width, w.height) == (300, 200)
        assert w.collapsed == True

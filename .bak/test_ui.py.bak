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

class TestModalBlocksAll:
    def test_modal_blocks_background_clicks(self):
        um = UIManager()
        um.open_window("w1")
        um.set_modal("w1", True)
        # 模态窗口应该阻止所有后台点击
        assert um.windows["w1"].modal == True

class TestEventBubbling:
    def test_event_can_be_stopped(self):
        um = UIManager()
        result = um.dispatch_event("btn1", "click")
        assert result == False

class TestUniqueFocus:
    def test_only_one_window_focused(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1")
        um.windows["w2"] = UIWindow("w2")
        um.set_focus("w1")
        um.set_focus("w2")
        assert um.windows["w1"].focus == False
        assert um.windows["w2"].focus == True

class TestUIStatePersistence:
    def test_state_saves_position(self):
        um = UIManager()
        um.windows["w1"] = UIWindow("w1", visible=True)
        state = um.save_ui_state()
        assert "position" in state.get("w1", {})

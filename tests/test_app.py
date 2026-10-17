import os
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


APP = Path(os.environ.get("AI_COMPANION_APP", Path(__file__).resolve().parents[1] / "app.py")).resolve()


class CompanionAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {"AI_COMPANION_SESSION_DIR": self.temp.name,
                                      "DEEPSEEK_API_KEY": ""})
        env.start()
        self.addCleanup(env.stop)

    def app(self):
        app = AppTest.from_file(str(APP), default_timeout=10).run()
        self.assertFalse(app.exception)
        return app

    def test_first_visit_explains_how_to_start_without_api_key(self):
        app = self.app()
        self.assertIn("把今天的心事", " ".join(item.value for item in app.title))
        self.assertTrue(app.chat_input[0].disabled)
        self.assertEqual([], list(Path(self.temp.name).glob("*.json")))

    def test_failed_reply_can_retry_without_duplicating_the_user_message(self):
        from openai import APIConnectionError

        app = self.app()
        app.text_input(key="api_key").set_value("test-key-never-sent").run()
        with patch("openai.OpenAI") as factory:
            client = factory.return_value.__enter__.return_value
            client.chat.completions.create.side_effect = APIConnectionError(request=None)
            app.chat_input[0].set_value("今天有点累").run()
            self.assertFalse(app.exception)
            self.assertIn("连接暂时中断", app.warning[0].value)
            self.assertEqual([{"role": "user", "content": "今天有点累"}], app.session_state.messages)

            client.chat.completions.create.side_effect = None
            chunks = [SimpleNamespace(choices=[])] + [
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=word))])
                for word in (None, "愿意听你说。", "慢慢来。")
            ]
            client.chat.completions.create.return_value.__enter__.return_value = iter(chunks)
            app.button(key="retry").click().run()
        self.assertFalse(app.exception)
        self.assertEqual([{"role": "user", "content": "今天有点累"},
                          {"role": "assistant", "content": "愿意听你说。慢慢来。"}],
                         app.session_state.messages)
        saved = next(Path(self.temp.name).glob("*.json")).read_text(encoding="utf-8")
        self.assertNotIn("test-key-never-sent", saved)

    def seed_session(self, name, nick_name, content):
        path = Path(self.temp.name) / f"{name}.json"
        path.write_text(json.dumps({"nick_name": nick_name, "nature": f"{nick_name}很开朗",
                                    "messages": [{"role": "user", "content": content},
                                                 {"role": "assistant", "content": "我在听。"}]}),
                        encoding="utf-8")
        return path

    def test_loading_history_updates_both_profile_fields(self):
        self.seed_session("2026-10-15_10-00-00", "小竹", "昨天的散步")
        self.seed_session("2026-10-16_10-00-00", "小荷", "今天的午饭")
        app = self.app()
        for name, nickname in (("2026-10-15_10-00-00", "小竹"),
                               ("2026-10-16_10-00-00", "小荷")):
            app.button(key=f"session_{name}").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(nickname, app.text_input(key="profile_name").value)
            self.assertEqual(f"{nickname}很开朗", app.text_area(key="profile_nature").value)

    def test_rapid_new_chats_are_unique_and_do_not_create_empty_history(self):
        app = self.app()
        identifiers = {app.session_state.current_session}
        for _ in range(3):
            app.button(key="new_chat").click().run()
            identifiers.add(app.session_state.current_session)
        self.assertEqual(4, len(identifiers))
        self.assertEqual([], list(Path(self.temp.name).glob("*.json")))

    def test_deleting_current_chat_preserves_companion_settings(self):
        path = self.seed_session("2026-10-16_10-00-00", "小竹", "一件开心的事")
        app = self.app()
        app.button(key=f"session_{path.stem}").click().run()
        app.button(key=f"delete_{path.stem}").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(path.exists())
        self.assertEqual([], app.session_state.messages)
        self.assertEqual("小竹", app.session_state.nick_name)

    def test_corrupt_history_does_not_crash_or_replace_current_chat(self):
        path = Path(self.temp.name) / "broken.json"
        path.write_text('{"messages":', encoding="utf-8")
        app = self.app()
        identifier = app.session_state.current_session
        app.button(key="session_broken").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(identifier, app.session_state.current_session)
        self.assertTrue(path.exists())

    def test_profile_changes_persist_and_blank_values_keep_previous_settings(self):
        app = self.app()
        app.text_input(key="profile_name").set_value("小竹")
        app.text_area(key="profile_nature").set_value("开朗，喜欢散步")
        next(b for b in app.button if b.label == "保存设定").click().run()
        self.assertFalse(app.exception)
        identifier = app.session_state.current_session
        app.text_input(key="profile_name").set_value("   ")
        next(b for b in app.button if b.label == "保存设定").click().run()
        self.assertEqual("小竹", app.session_state.nick_name)
        fresh_app = self.app()
        fresh_app.button(key=f"session_{identifier}").click().run()
        self.assertFalse(fresh_app.exception)
        self.assertEqual("小竹", fresh_app.text_input(key="profile_name").value)
        self.assertEqual("开朗，喜欢散步", fresh_app.text_area(key="profile_nature").value)

    def test_whitespace_does_not_send_or_create_a_session(self):
        app = self.app()
        app.text_input(key="api_key").set_value("test-key-never-sent").run()
        with patch("openai.OpenAI") as factory:
            app.chat_input[0].set_value("   \n ").run()
        self.assertFalse(app.exception)
        self.assertEqual([], app.session_state.messages)
        factory.assert_not_called()

    def test_empty_stream_keeps_the_user_message_and_offers_retry(self):
        app = self.app()
        app.text_input(key="api_key").set_value("test-key-never-sent").run()
        with patch("openai.OpenAI") as factory:
            client = factory.return_value.__enter__.return_value
            client.chat.completions.create.return_value.__enter__.return_value = iter([])
            app.chat_input[0].set_value("想聊聊天").run()
        self.assertFalse(app.exception)
        self.assertIn("没有收到回复", app.warning[0].value)
        self.assertEqual([{"role": "user", "content": "想聊聊天"}], app.session_state.messages)
        self.assertFalse(app.button(key="retry").disabled)

    def test_partial_stream_failure_does_not_store_an_incomplete_reply(self):
        from openai import APIConnectionError

        def interrupted_stream():
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="不完整的回复"))])
            raise APIConnectionError(request=None)

        app = self.app()
        app.text_input(key="api_key").set_value("test-key-never-sent").run()
        with patch("openai.OpenAI") as factory:
            client = factory.return_value.__enter__.return_value
            client.chat.completions.create.return_value.__enter__.return_value = interrupted_stream()
            app.chat_input[0].set_value("今天下雨了").run()
        self.assertFalse(app.exception)
        self.assertEqual([{"role": "user", "content": "今天下雨了"}], app.session_state.messages)
        self.assertIn("连接暂时中断", app.warning[0].value)

    def test_unwritable_storage_does_not_lose_current_chat_when_switching(self):
        path = self.seed_session("2026-10-16_10-00-00", "小竹", "一件开心的事")
        app = self.app()
        app.button(key=f"session_{path.stem}").click().run()
        identifier = app.session_state.current_session
        with patch.object(Path, "write_text", side_effect=PermissionError):
            app.button(key="new_chat").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(identifier, app.session_state.current_session)
        self.assertEqual("一件开心的事", app.session_state.messages[0]["content"])
        self.assertIn("未能保存", app.error[0].value)

    def test_clicking_active_history_keeps_unsaved_messages(self):
        path = self.seed_session("2026-10-16_10-00-00", "小竹", "一件开心的事")
        app = self.app()
        app.button(key=f"session_{path.stem}").click().run()
        app.text_input(key="api_key").set_value("test-key-never-sent").run()
        with patch.object(Path, "write_text", side_effect=PermissionError), patch("openai.OpenAI") as factory:
            factory.return_value.__enter__.return_value.chat.completions.create.return_value.__enter__.return_value = iter([])
            app.chat_input[0].set_value("刚刚想到的另一件事").run()
        app.button(key=f"session_{path.stem}").click().run()
        self.assertFalse(app.exception)
        self.assertEqual("刚刚想到的另一件事", app.session_state.messages[-1]["content"])



if __name__ == "__main__":
    unittest.main()

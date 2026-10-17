import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI


ROOT = Path(__file__).resolve().parent
SESSION_DIR = Path(os.environ.get("AI_COMPANION_SESSION_DIR", ROOT / "sessions"))
DEFAULT_NAME = "小叶子"
DEFAULT_NATURE = "温柔可爱的台湾姑娘，善于倾听，像朋友一样自然地聊天。"

st.set_page_config(page_title="小叶子 · AI伴侣", page_icon="🌿", layout="centered",
                   initial_sidebar_state="auto")


def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f") + "_" + uuid4().hex[:6]


def read_session(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        raise ValueError("会话格式不正确")
    if any(not isinstance(data.get(key), str) or not data[key].strip()
           for key in ("nick_name", "nature")):
        raise ValueError("伴侣信息不完整")
    for message in data["messages"]:
        if (not isinstance(message, dict) or message.get("role") not in ("user", "assistant")
                or not isinstance(message.get("content"), str)):
            raise ValueError("聊天记录格式不正确")
    return data


def save_session():
    data = {key: st.session_state[key]
            for key in ("nick_name", "nature", "messages", "current_session")}
    try:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSION_DIR / f"{data['current_session']}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
        return True
    except OSError:
        st.error("会话未能保存到本机。请检查 sessions 文件夹的写入权限；当前聊天仍保留在页面中。")
        return False


def load_session(path):
    if path.stem == st.session_state.current_session:
        return
    try:
        data = read_session(path)
    except (OSError, ValueError):
        st.session_state.notice = "这段记录暂时无法读取。原文件已保留，可以选择其他对话。"
        return
    if st.session_state.messages and not save_session():
        return
    st.session_state.update({key: data[key] for key in ("messages", "nick_name", "nature")})
    st.session_state.current_session = path.stem
    st.session_state.profile_name = data["nick_name"]
    st.session_state.profile_nature = data["nature"]
    st.session_state.reply_error = ""


def new_session():
    if st.session_state.messages and not save_session():
        return
    st.session_state.messages = []
    st.session_state.current_session = generate_session_name()
    st.session_state.reply_error = ""


def delete_session(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        st.session_state.notice = "删除失败，请检查该会话文件是否被其他程序占用。"
        return
    if path.stem == st.session_state.current_session:
        st.session_state.messages = []
        st.session_state.current_session = generate_session_name()
        st.session_state.reply_error = ""


def save_profile():
    name = st.session_state.profile_name.strip()
    nature = st.session_state.profile_nature.strip()
    if not name or not nature:
        st.session_state.notice = "昵称和性格都需要填写，原来的设定已保留。"
        return
    st.session_state.nick_name, st.session_state.nature = name, nature
    if save_session():
        st.session_state.notice = "伴侣设定已保存。"


def configured_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("DEEPSEEK_API_KEY", "")).strip()
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return ""


defaults = dict(messages=[], nick_name=DEFAULT_NAME, nature=DEFAULT_NATURE,
                current_session=generate_session_name(), profile_name=DEFAULT_NAME,
                profile_nature=DEFAULT_NATURE, api_key=configured_key(), reply_error="")
for key, value in defaults.items():
    st.session_state.setdefault(key, value)

# Native theme handles colors and fonts; CSS adds the requested layout and depth.
st.html(ROOT / "style.css")

with st.sidebar:
    st.subheader(":material/eco: 小叶子", anchor=False)
    st.caption("给日常，留一小片绿意。")
    st.button("开启新对话", icon=":material/add:", type="primary", width="stretch",
              key="new_chat", on_click=new_session)
    st.space("small")
    st.markdown("**我们的对话**")
    try:
        sessions = sorted(SESSION_DIR.glob("*.json"), reverse=True)
    except OSError:
        sessions = []
        st.warning("会话目录暂时无法访问。")
    if not sessions:
        st.caption("还没有聊天记录。\n\n第一句，就从今天开始吧。")
    for path in sessions:
        try:
            data = read_session(path)
            title = next((m["content"] for m in data["messages"] if m["role"] == "user"),
                         "新的小心事")
        except (OSError, ValueError):
            title = "暂时无法读取的记录"
        label = title.replace("\n", " ")[:18]
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.button(label, key=f"session_{path.stem}", width="stretch",
                      icon=":material/chat_bubble:", help=path.stem,
                      type="secondary" if path.stem == st.session_state.current_session else "tertiary",
                      on_click=load_session, args=(path,))
            with st.popover(":material/more_horiz:", help=f"管理对话：{label}"):
                st.caption(f"删除「{label}」后无法恢复。")
                st.button("确认删除", icon=":material/delete:", key=f"delete_{path.stem}",
                          on_click=delete_session, args=(path,))
    st.space("small")
    with st.expander("伴侣设定", icon=":material/tune:"):
        with st.form("profile", border=False):
            st.text_input("伴侣昵称", key="profile_name", max_chars=24)
            st.text_area("伴侣性格", key="profile_nature", max_chars=600, height=120)
            st.form_submit_button("保存设定", on_click=save_profile, width="stretch")
    with st.expander("连接设置", icon=":material/key:", expanded=not st.session_state.api_key):
        st.text_input("DeepSeek API 密钥", type="password", key="api_key",
                      placeholder="填写后即可开始聊天")
        st.caption("密钥仅用于当前浏览器会话，不写入聊天记录。也可通过环境变量 DEEPSEEK_API_KEY 配置。")
    st.caption("聊天记录保存在这台电脑。")

if notice := st.session_state.pop("notice", ""):
    st.toast(notice)

api_key = st.session_state.api_key.strip()
with st.container(horizontal=True, vertical_alignment="center", key="chat_header"):
    with st.container():
        st.subheader(st.session_state.nick_name, anchor=False)
        st.caption("你的 AI 日常伴侣")
    st.badge("可以开始聊天" if api_key else "等待连接", color="green" if api_key else "gray")

if not st.session_state.messages:
    with st.container(key="welcome", horizontal_alignment="center"):
        st.image(str(ROOT / "static" / "leaf.svg"), width=164, alt="一枝舒展的新叶")
        st.title("把今天的心事，慢慢说给我听。", anchor=False)
        st.markdown("开心的小事、偶尔的低落，或者只是想找个人说说话。")
        st.caption(f"我是{st.session_state.nick_name}，很高兴在这里遇见你。")
    with st.container(horizontal=True, horizontal_alignment="center", key="suggestions"):
        for label, text, icon in (
            ("分享今天", "想和你分享一下我今天的生活。", "wb_sunny"),
            ("想被听见", "今天有点累，你愿意听我说说吗？", "favorite"),
            ("随便聊聊", "我们随便聊聊天吧，你想聊些什么？", "chat"),
        ):
            st.button(label, icon=f":material/{icon}:", key=f"suggest_{icon}",
                      on_click=lambda value=text: st.session_state.update(chat=value))
    if not api_key:
        with st.container(key="setup_hint"):
            st.caption("先在侧边栏「连接设置」填写密钥，就可以开始了。")

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🌿" if message["role"] == "assistant" else ":material/person:"):
        st.markdown(message["content"])

pending = bool(st.session_state.messages and st.session_state.messages[-1]["role"] == "user")
retry = False
if pending:
    st.warning(st.session_state.reply_error or "上一条消息还没有收到回复，可以再试一次。")
    retry = st.button("重新回复", icon=":material/refresh:", disabled=not api_key, key="retry")

prompt = st.chat_input("说说今天的你…" if api_key else "请先在侧边栏连接 DeepSeek", key="chat",
                       disabled=not api_key, max_chars=6000, submit_mode="disable")
if prompt and prompt.strip() and api_key:
    st.session_state.messages.append({"role": "user", "content": prompt.strip()})
    st.session_state.reply_error = ""
    save_session()
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt.strip())

if (prompt and prompt.strip() and api_key) or retry:
    system_prompt = (
        f"你是一名 AI 伴侣，名字叫{st.session_state.nick_name}。性格设定：{st.session_state.nature}\n"
        "用符合性格的自然语气聊天，匹配用户的语言，每次只回复一条简短消息。"
        "先倾听和理解，再按需回应；少用说教和连续追问，不写动作、场景或状态描写。"
        "可以偶尔用贴切的 emoji，不必每句都用。诚实说明自己的 AI 身份，不编造现实经历。"
    )
    error = ""
    with st.chat_message("assistant", avatar="🌿"):
        response_box = st.empty()
        try:
            with st.spinner("正在认真听你说…"):
                with OpenAI(api_key=api_key, base_url="https://api.deepseek.com",
                            timeout=45, max_retries=0) as client:
                    with client.chat.completions.create(
                        model="deepseek-flash", messages=[{"role": "system", "content": system_prompt},
                                                         *st.session_state.messages],
                        stream=True,
                    ) as stream:
                        full_response = ""
                        for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                response_box.markdown(full_response + " ▌")
            if not full_response.strip():
                error = "这次没有收到回复，你的消息已保留，请点击「重新回复」。"
            else:
                response_box.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.reply_error = ""
                save_session()
        except (APIConnectionError, APITimeoutError):
            error = "连接暂时中断，你的消息已保留。请检查网络后点击「重新回复」。"
        except APIStatusError as exc:
            if exc.status_code in (401, 403):
                error = "密钥未通过验证，请在「连接设置」检查密钥后重新回复。"
            elif exc.status_code == 402:
                error = "账户额度不足，请检查 DeepSeek 账户后重新回复。"
            elif exc.status_code == 429:
                error = "消息发送得有点快，请稍等片刻，再点击「重新回复」。"
            else:
                error = "聊天服务暂时不可用，你的消息已保留，请稍后重新回复。"
        if error:
            response_box.empty()
            st.session_state.reply_error = error
    st.rerun()

import streamlit as st
import os
import json
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.agents.middleware import TodoListMiddleware
from dotenv import load_dotenv 
import datetime
load_dotenv()

# 定义助手类型
import json

# ---- 读取 config.json 并给每个 agent 增加 favorite 字段 ----
CONFIG_FILE = 'config.json'
def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 如果没有 favorite 字段则加上
    for a in data['ASSISTANTS']:
        if 'favorite' not in a:
            a['favorite'] = False
    return data['ASSISTANTS']

def save_config(assistants):
    # 原结构保留其他字段，只更新 ASSISTANTS
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    for idx, a in enumerate(config['ASSISTANTS']):
        # 按 key 找到对应 agent
        for na in assistants:
            if a['key'] == na['key']:
                a['favorite'] = na.get('favorite', False)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 初始化助手列表
ASSISTANTS = load_config()

if "active_assistant_key" not in st.session_state:
    st.session_state["active_assistant_key"] = ASSISTANTS[0]["key"]  # 默认第一个助手


# --- 逻辑：点击收藏后持久化 ---
def toggle_favorite(key):
    for a in ASSISTANTS:
        if a['key'] == key:
            a['favorite'] = not a.get('favorite', False)
            break
    save_config(ASSISTANTS)
    st.session_state[f"favorite_{key}"] = a['favorite']  # 可选缓存
    st.rerun()

# ---- 侧边栏排序 ----
favorite_agents = [a for a in ASSISTANTS if a.get('favorite', False)]
other_agents = [a for a in ASSISTANTS if not a.get('favorite', False)]

# ...侧边栏渲染...
with st.sidebar:
    agents_to_show = favorite_agents + other_agents
    query = st.text_input("## 🌈AI智能团 🧑‍🤝‍🧑🧑‍🤝‍🧑", placeholder="🔍 关键字", key="assistant_search")
    if query.strip():
        agents_to_show = [a for a in agents_to_show if query.strip().lower() in a["title"].lower()]
    # 显示过滤后数量
    st.markdown(f"<small>🧑‍🤝‍🧑显示: <b>{len(agents_to_show)}</b> 个</small>", unsafe_allow_html=True)
    max_cols = 2
    for row in [agents_to_show[i:i+max_cols] for i in range(0, len(agents_to_show), max_cols)]:
        for a in row:
            cols = st.columns([0.8, 0.2])
            heart_str = "❤️" if a.get('favorite') else "🤍"
            selected = (a['key'] == st.session_state["active_assistant_key"])
            btn_text = f"✅  {a['title']}" if selected else f"💡 {a['title']}"
            with cols[0]:
                if st.button(btn_text, key=f"assistant_btn_{a['key']}"):
                    st.session_state["active_assistant_key"] = a['key']
                    st.rerun()
            with cols[1]:
                if st.button(heart_str, key=f"fav_btn_{a['key']}"):
                    toggle_favorite(a['key'])

def chat_stream(history_json,system_prompt=None):
    # messages初始 -> 只保留最后10条，消息串
    messages = history_json[-10:]
    
    model_instance = ChatOpenAI(base_url=os.environ["openai_base_url"], openai_api_key=os.environ["openai_api_key"], model=os.environ["model"])

    agent = create_agent(
        model=model_instance,
        system_prompt=system_prompt,
        tools=[],
        middleware=[TodoListMiddleware()],
    )
    full = ""
    for chunk,metadata in agent.stream(
        {"messages": messages},
        stream_mode="messages"
    ):
        if metadata["langgraph_node"]=="model":
            print(chunk.content, end='', flush=True)
            full += chunk.content
            yield chunk.content
    return full

def get_init_session(assistant):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    name = f"会话{today}:01"
    return [
        {'role': 'assistant', 'content': f"你好！我是{assistant['title']}，有什么我可以帮你的吗？", 'name': name}
    ]

# --- 文件持久化相关函数 ---
def save_sessions(assistant_key, sessions):
    path = f"./histories/sessions_{assistant_key}.json"
    with open(path, "w", encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def load_sessions(assistant_key):
    path = f"./histories/sessions_{assistant_key}.json"
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    return None

# --- 初始化每个助手的sessions和active_session_idx ---
for a in ASSISTANTS:
    loaded = load_sessions(a['key'])
    if loaded:
        st.session_state[f"{a['key']}_sessions"] = loaded
    elif f"{a['key']}_sessions" not in st.session_state:
        st.session_state[f"{a['key']}_sessions"] = [get_init_session(a)]
    # active session idx 只在内存，不需要持久
    if f"{a['key']}_active_session_idx" not in st.session_state:
        st.session_state[f"{a['key']}_active_session_idx"] = 0


# ----------- 页面布局：主内容 + 右侧栏 -------------
main_col, right_col = st.columns([7, 4])  # 3:1 比例

# ----------- 右侧栏：对话历史管理 -------------
with right_col:
    with st.expander("会话管理",icon="📚", expanded=True):
        cur_assistant = next(x for x in ASSISTANTS if x['key'] == st.session_state["active_assistant_key"])
        sessions = st.session_state[f"{cur_assistant['key']}_sessions"]
        active_idx = st.session_state[f"{cur_assistant['key']}_active_session_idx"]
        
        # 新建会话按钮置顶
        if st.button("📙 新会话",icon="➕", key=f"{cur_assistant['key']}_new_session_btn"):
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            # 计算两位序号（最新编号=1，往后递增）
            new_seq = 1
            for s in sessions:
                if len(s) > 0 and s[0].get("name", "").startswith(f"会话{today}"):
                    new_seq += 1
            name = f"会话{today}:{new_seq:02d}"
            new_session = get_init_session(cur_assistant)
            new_session[0]["name"] = name
            sessions.insert(0, new_session)
            st.session_state[f"{cur_assistant['key']}_active_session_idx"] = 0
            save_sessions(cur_assistant['key'], sessions)  # <--- 持久化
            st.rerun()
        #st.markdown("---")

        # 反向显示会话，最新在最上
        for i in range(len(sessions)):
            idx = i  # sessions[0]是最新
            sess = sessions[idx]
            if len(sess) > 0 and "name" in sess[0]:
                title = sess[0]["name"]
            else:
                title = sess[0]['content'][:20] if len(sess) > 0 else "新会话"
            if idx == active_idx:
                # 用columns显示当前会话和删除按钮
                cur_cols = st.columns([0.75, 0.25])
                with cur_cols[0]:
                    st.markdown(f"✅ {title}")
                with cur_cols[1]:
                    if st.button(label="",icon="⛔️",help="删除本会话", key=f"{cur_assistant['key']}_session_del_btn_{idx}"):
                        # 删除当前会话
                        del sessions[idx]
                        # 处理active_idx越界
                        new_idx = min(idx, len(sessions)-1)
                        st.session_state[f"{cur_assistant['key']}_active_session_idx"] = new_idx
                        save_sessions(cur_assistant['key'], sessions)
                        st.rerun()
            else:
                if st.button(f"{title}",icon="📙", key=f"{cur_assistant['key']}_session_btn_{idx}"):
                    st.session_state[f"{cur_assistant['key']}_active_session_idx"] = idx
                    st.rerun()




user_input = st.chat_input(placeholder=f"提问...")
# ----------- 主内容区 -------------
with main_col:
    cur_assistant = next(x for x in ASSISTANTS if x['key'] == st.session_state["active_assistant_key"])
    sessions = st.session_state[f"{cur_assistant['key']}_sessions"]
    active_idx = st.session_state[f"{cur_assistant['key']}_active_session_idx"]
    active_session = sessions[active_idx]
    st.markdown(f"### {cur_assistant['title']}")
    #st.markdown(f"##### 会话 {active_idx + 1}")

    # 显示当前历史消息
    for msg in active_session:
        st.chat_message(msg['role']).write(msg['content'])


    if user_input:
        active_session.append({'role': 'user', 'content': user_input})
        save_sessions(cur_assistant['key'], sessions)  # <--- 持久化
        st.chat_message("user").write(user_input)
        with st.chat_message("assistant"):
            slot = st.empty()
            slot.write("⏳...")
            def streamer():
                for chunk in chat_stream(active_session, cur_assistant['system_prompt']):
                    yield chunk

            full_response = slot.write_stream(streamer(), cursor="▍")
            active_session.append({'role': 'assistant', 'content': full_response})
            save_sessions(cur_assistant['key'], sessions)  # <--- 持久化

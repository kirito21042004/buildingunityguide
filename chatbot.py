import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response
import os, time, uuid
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers.run_collector import RunCollectorCallbackHandler
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from streamlit_feedback import streamlit_feedback
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=pcsk_3xKM8U_MsKJHPK9WiD2t8fmozDr7ukFxsNTvMWtEw6PboJxPLhzXoZ3pDb5UL1QZmANYjX)

# Cấu hình trang
st.set_page_config(page_title="Gamebuilding Guide Chatbot", page_icon="🎮", layout="wide")
load_dotenv()

# Thêm CSS tùy chỉnh
st.markdown(
    """
    <style>
        /* Tổng quan giao diện */
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #ffffff;
            font-family: 'Roboto', sans-serif;
        }
        .main {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #00d4ff;
            text-shadow: 0px 0px 20px #00d4ff;
        }
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
        }
        input, select, textarea {
            background: #203a43;
            color: #ffffff;
            border: 1px solid #00d4ff;
            border-radius: 5px;
        }
        button {
            background: linear-gradient(45deg, #00d4ff, #00ffab);
            color: #000000;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        button:hover {
            background: linear-gradient(45deg, #00ffab, #00d4ff);
            transform: scale(1.1);
        }
        .stMarkdown > div {
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Tiêu đề ứng dụng
st.title("🎮 Gamebuilding Guide Chatbot")
st.caption("Your futuristic assistant for Unity Game Development 🚀")

def check_if_key_exists(key):
    return key in st.session_state

@st.cache_data(ttl="2h", show_spinner=False)
def get_run_url(run_id):
    time.sleep(1)
    return client.read_run(run_id).url

# API Key Section
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "UNITY_GAME_DEVELOPMENT"

if "query" not in st.session_state:
    st.session_state.query = None

with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("🔑 **Get your API Key: [Click Here](https://example.com)**")
    api_provider = st.selectbox("API Provider", ["OpenAI", "Upstage"], key="api_provider_selection")
    openai_api_key = st.text_input("OpenAI API KEY", type="password") if api_provider == "OpenAI" else None
    upstage_api_key = st.text_input("Upstage API KEY", type="password") if api_provider == "Upstage" else None
    langchain_api_key = st.text_input("LangSmith API KEY (Optional)", type="password")

    if openai_api_key:
        st.session_state["openai_api_key"] = openai_api_key
        os.environ["OPENAI_API_KEY"] = st.session_state["openai_api_key"]
    else:
        st.session_state.pop("openai_api_key", None)
        os.environ.pop("OPENAI_API_KEY", None)

    if upstage_api_key:
        st.session_state["upstage_api_key"] = upstage_api_key
        os.environ["UPSTAGE_API_KEY"] = st.session_state["upstage_api_key"]
    else:
        st.session_state.pop("upstage_api_key", None)
        os.environ.pop("UPSTAGE_API_KEY", None)

    if langchain_api_key:
        st.session_state["langchain_api_key"] = langchain_api_key
    else:
        st.session_state.pop("langchain_api_key", None)
        os.environ.pop("LANGCHAIN_API_KEY", None)

    project_name = st.text_input("LangSmith Project (Optional)", value="UNITY_GAME_DEV")
    session_id = st.text_input("Session ID (Optional)")

if not check_if_key_exists("langchain_api_key"):
    st.info(
        "⚠️ Add your LangSmith API key to enable response tracking."
    )
    cfg = RunnableConfig()
    cfg["configurable"] = {"session_id": "default_session"}
else:
    langchain_endpoint = "https://api.smith.langchain.com"
    client = Client(
        api_url=langchain_endpoint, api_key=st.session_state["langchain_api_key"]
    )
    ls_tracer = LangChainTracer(project_name=project_name, client=client)
    run_collector = RunCollectorCallbackHandler()
    cfg = RunnableConfig()
    cfg["callbacks"] = [ls_tracer, run_collector]
    if session_id:
        cfg["configurable"] = {"session_id": session_id}
    else:
        cfg["configurable"] = {"session_id": str(uuid.uuid4())}

if not check_if_key_exists("openai_api_key") and api_provider == "OpenAI":
    st.info(
        "⚠️ Please add your OpenAI API key."
    )
elif not check_if_key_exists("upstage_api_key") and api_provider == "Upstage":
    st.info(
        "⚠️ Please add your Upstage API key."
    )

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_question := st.chat_input(placeholder="Ask your Unity Game Development questions here!"):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append({"role": "user", "content": user_question})

    with st.spinner("Generating response..."):
        ai_response = get_ai_response(user_question, cfg, api_provider)
        with st.chat_message("ai"):
            ai_message = st.write_stream(ai_response)
            st.session_state.message_list.append({"role": "ai", "content": ai_message})
        if check_if_key_exists("langchain_api_key"):
            wait_for_all_tracers()
            st.session_state.last_run = run_collector.traced_runs[0].id

if st.session_state.get("last_run"):
    run_url = get_run_url(st.session_state.last_run)
    st.sidebar.markdown(f"[LangSmith Trace 🛠️]({run_url})")
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label=None,
        key=f"feedback_{st.session_state.last_run}",
    )
    if feedback:
        scores = {"👍": 1, "👎": 0}
        client.create_feedback(
            st.session_state.last_run,
            feedback["type"],
            score=scores[feedback["score"]],
            comment=st.session_state.query,
        )
        st.toast("Feedback saved!", icon="📝")

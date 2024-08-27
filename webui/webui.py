import streamlit as st
from api import SearchSSE, SearchVideo
import ast
import requests
from io import BytesIO
import time
from typing import List, Any

# 侧边栏配置
with st.sidebar:
    st.markdown("## 配置")
    base_url = st.text_input(
        "LangChain-SearXNG服务地址",
        value="http://127.0.0.1:8002",
        key="langchain_searxng_base_url",
    )
    search_model_options = ["SearXNG搜索", "智谱搜索"]
    search_model_index = st.selectbox(
        "LangChain-SearXNG搜索方式",
        options=range(len(search_model_options)),
        format_func=lambda x: search_model_options[x],
        key="search_modelssearxng_search_model",
    )
    llm_model = ""
    retriever_model = ""
    if search_model_index == 0:
        llm_model = st.selectbox(
            "LangChain-SearXNG搜索模型",
            options=["zhipuai", "deepseek", "openai"],
            key="langchain_searxng_llm_model",
        )
        retriever_model = "searx"
    elif search_model_index == 1:
        llm_model = "zhipuwebsearch"
        retriever_model = "zhipuwebsearch"

    network_flag = st.toggle(
        "是否联网搜索",
        value=True,
        key="network_search",
    )
    "[View the source code](https://github.com/ptonlix/LangChain-SearXNG)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ptonlix/LangChain-SearXNG?quickstart=1)"

# 页面标题
st.title("🔍 LangChain-SearXNG")
st.caption("🚀 基于LangChain和SearXNG打造的开源AI搜索引擎")


def initialize_session_state():
    """初始化会话状态，确保必要的变量存在"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "您好！我是AI搜索助手，有什么可以帮您的吗？",
                "video_sources": [],
                "sources_markdown": "",
            }
        ]
    st.session_state.setdefault("video_sources", None)
    st.session_state.setdefault("sources_markdown", "**搜索来源：**\n\n")


def display_chat_history():
    """显示聊天历史记录"""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            display_video_sources(msg["video_sources"])
            if msg["sources_markdown"]:
                st.markdown(msg["sources_markdown"])
            st.write(msg["content"])


def display_video_sources(video_sources: List[Any]):
    """显示视频来源"""
    if not video_sources:
        return

    st.markdown("**相关视频：**")
    cols = st.columns(len(video_sources))
    for idx, video in enumerate(video_sources):
        with cols[idx]:
            try:
                response = requests.get(video.pic.replace("////", "//"))
                img = BytesIO(response.content)
                st.image(img, use_column_width=True)
            except Exception as e:
                st.error(f"无法加载图片: {str(e)}")
            st.markdown(f"[{video.author}]({video.arcurl})")
            st.caption(f"{video.description[:50]}...")


def update_progress(progress_bar, timer_text, progress: float, elapsed_time: float):
    """更新进度条和计时器"""
    progress_bar.progress(progress)
    timer_text.text(f"耗时: {elapsed_time:.2f} 秒")


def process_user_input(
    prompt: str, base_url: str, network_flag: bool, llm_model: str, retriever_model: str
):
    """处理用户输入并进行搜索"""
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "video_sources": [], "sources_markdown": ""}
    )
    st.chat_message("user").write(prompt)

    chat_history = [
        (msg["role"], msg["content"]) for msg in st.session_state.messages[1:]
    ]
    chat_history = [
        ("ai" if role == "assistant" else "human", content)
        for role, content in chat_history
    ]

    with st.chat_message("assistant"):
        video_placeholder = st.empty()
        sources_placeholder = st.empty()
        content_placeholder = st.empty()
        progress_bar = st.empty()
        timer_text = st.empty()

        start_time = time.time()
        update_progress(progress_bar, timer_text, 0, 0)

        sse_client = SearchSSE(base_url)
        video_client = SearchVideo(base_url)

        data = {
            "question": prompt,
            "chat_history": chat_history,
            "network": network_flag,
            "conversation_id": "",
            "llm": llm_model,
            "retriever": retriever_model,
        }
        headers = {"Accept": "text/event-stream; charset=utf-8"}

        full_response, sources_markdown = process_sse_events(
            sse_client,
            data,
            headers,
            video_client,
            prompt,
            video_placeholder,
            sources_placeholder,
            content_placeholder,
            progress_bar,
            timer_text,
            start_time,
        )

        total_time = time.time() - start_time
        update_progress(progress_bar, timer_text, 1.0, total_time)

        full_response_with_time = f"{full_response}\n\n*总耗时: {total_time:.2f} 秒*"
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_response_with_time,
                "video_sources": (
                    st.session_state.video_sources.video_list
                    if st.session_state.video_sources
                    else []
                ),
                "sources_markdown": sources_markdown,
            }
        )


def process_sse_events(
    sse_client,
    data,
    headers,
    video_client,
    prompt,
    video_placeholder,
    sources_placeholder,
    content_placeholder,
    progress_bar,
    timer_text,
    start_time,
):
    """处理服务器发送的事件（SSE）"""
    full_response = ""
    sources_markdown = "**搜索来源：**\n\n"

    video_sources = video_client.search_video(
        endpoint="/v1/search/video",
        data={"query": prompt, "conversation_id": ""},
        headers=headers,
    ).data

    update_progress(progress_bar, timer_text, 0.1, time.time() - start_time)

    if video_sources:
        display_video_sources_in_placeholder(
            video_placeholder, video_sources, progress_bar, timer_text, start_time
        )

    st.session_state.video_sources = video_sources

    source_idx = 1
    for event in sse_client.connect("/v2/search/sse", data, headers):
        if event.event == "source":
            source_data = ast.literal_eval(event.data)
            sources_markdown += f"{source_idx}. [{source_data.get('title','')}]({source_data.get('url','')})\n"
            source_idx += 1
            sources_placeholder.markdown(sources_markdown)
        elif event.event == "message":
            full_response += event.data
            content_placeholder.markdown(full_response + "▌")
            progress = min(0.2 + len(full_response) / 1000, 0.9)
            update_progress(
                progress_bar, timer_text, progress, time.time() - start_time
            )
        elif event.event == "error":
            st.error(f"错误: {event.data}")

    content_placeholder.markdown(full_response)
    return full_response, sources_markdown


def display_video_sources_in_placeholder(
    video_placeholder, video_sources, progress_bar, timer_text, start_time
):
    """在占位符中显示视频来源"""
    with video_placeholder.container():
        st.markdown("**相关视频：**\n\n")
        cols = st.columns(len(video_sources.video_list))
        for idx, video in enumerate(video_sources.video_list):
            with cols[idx]:
                try:
                    response = requests.get(video.pic.replace("////", "//"))
                    response.raise_for_status()  # 检查请求是否成功
                    img = BytesIO(response.content)
                    st.image(img, use_column_width=True)
                except requests.RequestException as e:
                    print(f"无法加载图片: {str(e)}")
                    st.image(
                        "https://via.placeholder.com/150?text=图片加载失败",
                        use_column_width=True,
                        caption="加载图片失败",
                    )
                except Exception as e:
                    print(f"处理图片时出错: {str(e)}")
                    st.image(
                        "https://via.placeholder.com/150?text=图片处理失败",
                        use_column_width=True,
                        caption="加载图片失败",
                    )
                st.markdown(f"[{video.author}]({video.arcurl})")
                st.caption(f"{video.description[:50]}...")
            update_progress(
                progress_bar,
                timer_text,
                0.1 + (idx + 1) / (10 * len(video_sources.video_list)),
                time.time() - start_time,
            )


def main():
    """主函数，初始化会话状态并处理用户输入"""
    initialize_session_state()
    display_chat_history()

    if prompt := st.chat_input():
        process_user_input(prompt, base_url, network_flag, llm_model, retriever_model)


if __name__ == "__main__":
    main()

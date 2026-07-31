import asyncio
import os
import sys
from typing import Dict, List, Optional
from contextvars import ContextVar

stream_queues: Dict[str, asyncio.Queue] = {}

def get_stream_queue(session_id: str) -> asyncio.Queue:
    if session_id not in stream_queues:
        stream_queues[session_id] = asyncio.Queue()
    return stream_queues[session_id]

def close_stream_queue(session_id: str):
    if session_id in stream_queues:
        del stream_queues[session_id]


# === 输入命令队列：给线程输入 prompt / tool_call 指令 ===
input_queues: Dict[str, asyncio.Queue] = {}

def get_input_queue(session_id: str) -> asyncio.Queue:
    if session_id not in input_queues:
        input_queues[session_id] = asyncio.Queue()
    return input_queues[session_id]

def close_input_queue(session_id: str):
    if session_id in input_queues:
        del input_queues[session_id]


# === 当前“异步上下文”绑定的 session_id，适用于无参数传递情况 ===
_session_ctx: ContextVar[str] = ContextVar("_session_ctx")

def set_current_session(session_id: str):
    _session_ctx.set(session_id)
    print(f"设置当前 session_id: {session_id}")

def get_current_session() -> str:
    session_id = _session_ctx.get(None)
    if session_id is None:
        raise ValueError("No session_id set for current context")
    return session_id


# === 快捷获取当前 session 的输入/输出队列 ===
def get_session_queue() -> asyncio.Queue:
    session_id = get_current_session()
    return get_stream_queue(session_id)

def get_session_input_queue() -> asyncio.Queue:
    session_id = get_current_session()
    return get_input_queue(session_id)


# === agent 实例管理 ===
agent_instances: Dict[str, object] = {}

def get_agent(session_id: str, images: List[Dict] = None) -> object:
    if session_id not in agent_instances:
        from deepwind_app.agent.twoStageAgent import TwoStageAgent  # 避免循环引用
        agent_instances[session_id] = TwoStageAgent(session_id=session_id, images=images)
    return agent_instances[session_id]

def close_agent(session_id: str):
    if session_id in agent_instances:
        del agent_instances[session_id]

# === 文件会话管理 ===
_file_sessions: Dict[str, List[Dict]] = {}
_file_lock = asyncio.Lock()  # 异步锁保证线程安全

async def add_files_to_session(session_id: str, files_info: List[Dict]):
    """异步添加文件到会话"""
    async with _file_lock:
        if session_id not in _file_sessions:
            _file_sessions[session_id] = []
        _file_sessions[session_id].extend(files_info)

async def get_session_files(session_id: str) -> List[Dict]:
    """异步获取会话文件列表"""
    async with _file_lock:
        return _file_sessions.get(session_id, []).copy()

async def clear_session_files(session_id: str):
    """异步清除会话文件"""
    async with _file_lock:
        if session_id in _file_sessions:
            del _file_sessions[session_id]

# 更新reset函数
async def reset():
    async with _file_lock:
        stream_queues.clear()
        input_queues.clear()
        agent_instances.clear()
        _file_sessions.clear()
    
async def clear_asyncio_queue(q: asyncio.Queue):
    while not q.empty():
        try:
            q.get_nowait()
            # q.task_done()  # 可选：如果你使用了 join()
        except asyncio.QueueEmpty:
            break
        

"""Fyno Library Git Sync WebSocket API。

一个 WebSocket 连接对应一次 Sync Modal Session，并绑定连接建立时的
Workspace。Receiver 独立监听消息和断开事件；阻塞的 Git workflow 通过
``asyncio.to_thread`` 执行，避免阻塞 asyncio event loop。
"""

import asyncio
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
import threading

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)

from ..sync.sync import (
    get_sync,
    sync as run_sync,
)
from .dependencies import require_workspace


router = APIRouter(
    prefix="/sync",
)

_DISCONNECTED = object()


@router.websocket("/ws")
async def sync_websocket(
    websocket: WebSocket,
    workspace: Path = Depends(
        require_workspace
    ),
) -> None:
    """运行绑定当前 Workspace 的 Git Sync Session。"""
    await websocket.accept()

    cancel_event = threading.Event()
    messages: asyncio.Queue[object] = (
        asyncio.Queue()
    )
    receiver = asyncio.create_task(
        _receive_messages(
            websocket,
            messages,
            cancel_event,
        )
    )

    try:
        info = await asyncio.to_thread(
            get_sync,
            workspace,
            cancel_event=cancel_event,
        )

        if cancel_event.is_set():
            return

        await websocket.send_json(
            {
                "type": "info",
                "data": asdict(info),
            }
        )

        while True:
            message = await messages.get()

            if message is _DISCONNECTED:
                return

            if not isinstance(message, dict):
                await websocket.send_json(
                    {
                        "type": "error",
                        "reason": (
                            "Unsupported sync action"
                        ),
                    }
                )
                continue

            action = message.get("action")

            if action == "refresh":
                info = await asyncio.to_thread(
                    get_sync,
                    workspace,
                    cancel_event=cancel_event,
                )

                if cancel_event.is_set():
                    return

                await websocket.send_json(
                    {
                        "type": "info",
                        "data": asdict(info),
                    }
                )
                continue

            if action != "sync":
                await websocket.send_json(
                    {
                        "type": "error",
                        "reason": (
                            "Unsupported sync action"
                        ),
                    }
                )
                continue

            remote = message.get("remote")

            if (
                remote is not None
                and not isinstance(remote, str)
            ):
                await websocket.send_json(
                    {
                        "type": "error",
                        "reason": (
                            "Invalid sync remote"
                        ),
                    }
                )
                continue

            result = await asyncio.to_thread(
                run_sync,
                workspace,
                remote,
                cancel_event=cancel_event,
            )

            # Receiver 可能在 Git 执行期间观察到 disconnect。此时底层返回的
            # cancelled 结果只用于结束线程，不再发送给已经关闭的客户端。
            if cancel_event.is_set():
                return

            await websocket.send_json(
                {
                    "type": "result",
                    "data": asdict(result),
                }
            )

            info = await asyncio.to_thread(
                get_sync,
                workspace,
                cancel_event=cancel_event,
            )

            if cancel_event.is_set():
                return

            await websocket.send_json(
                {
                    "type": "info",
                    "data": asdict(info),
                }
            )
    except WebSocketDisconnect:
        cancel_event.set()
    finally:
        cancel_event.set()
        receiver.cancel()

        with suppress(
            asyncio.CancelledError
        ):
            await receiver


async def _receive_messages(
    websocket: WebSocket,
    messages: asyncio.Queue[object],
    cancel_event: threading.Event,
) -> None:
    """独占 WebSocket receive，并将命令或断开信号交给主 Session。

    Receiver 与 ``to_thread`` 中的 Git workflow 并行存在，因此客户端在 Git
    执行期间断开时，不必等待命令结束就能 set cancellation Event。
    """
    try:
        while True:
            message = await websocket.receive_json()
            await messages.put(message)
    except WebSocketDisconnect:
        pass
    finally:
        cancel_event.set()
        await messages.put(
            _DISCONNECTED
        )

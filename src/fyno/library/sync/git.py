"""Fyno Sync 使用的基础 Git 操作。

该模块保持为 Git CLI 的薄封装。所有公开函数均返回 ``GitResult``：
命令成功时 ``success`` 为 True 且 ``reason`` 为空字符串；命令失败时
``success`` 为 False，并在 ``reason`` 中返回 Git 提供的错误原因。
"""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import threading
import time
from typing import Generic, TypeVar


T = TypeVar("T")

_GIT_TIMEOUT_SECONDS = 30
_GIT_POLL_SECONDS = 0.1
_GIT_STOP_GRACE_SECONDS = 1.0


@dataclass(frozen=True, slots=True)
class GitResult(Generic[T]):
    """Git 操作结果。

    Attributes:
        success: 操作是否成功。
        reason: 失败原因；操作成功时固定为空字符串。
        data: 查询操作返回的数据；没有数据或操作失败时为 None。
    """

    success: bool
    reason: str
    data: T | None = None


def git_available() -> GitResult[bool]:
    """判断当前系统能否从 PATH 中找到 Git 可执行文件。"""
    available = shutil.which("git") is not None

    if not available:
        return _failure(
            "Git executable was not found"
        )

    return _success(True)


def is_repository(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[bool]:
    """判断 Workspace 本身是否为 Git 仓库根目录。

    Git 仓库中的普通子目录不会被视为独立仓库，避免后续 add、commit 等操作
    意外作用于 Workspace 之外的父级仓库。
    """
    result = _run(
        workspace,
        "rev-parse",
        "--show-toplevel",
        cancel_event=cancel_event,
    )

    if not result.success:
        if _is_not_repository_reason(
            result.reason
        ):
            return _success(False)

        return _failure(
            result.reason
        )

    try:
        is_root = (
            Path(result.data or "").resolve()
            == Path(workspace).resolve()
        )
    except OSError as exc:
        return _failure(str(exc))

    return _success(is_root)


def init(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """在 Workspace 中初始化以 main 为初始分支的 Git 仓库。"""
    return _run_without_data(
        workspace,
        "init",
        "--initial-branch",
        "main",
        cancel_event=cancel_event,
    )


def get_current_branch(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[str]:
    """获取当前分支名称；Detached HEAD 时返回空字符串。"""
    return _run(
        workspace,
        "branch",
        "--show-current",
        cancel_event=cancel_event,
    )


def get_head(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[str | None]:
    """获取本地 HEAD Commit SHA，尚无 Commit 时返回 None。

    ``--quiet`` 会让不存在的 HEAD 以退出码 1 且无错误信息结束。该状态表示
    unborn repository，不是 Git 执行错误。
    """
    result = _run(
        workspace,
        "rev-parse",
        "--verify",
        "--quiet",
        "HEAD",
        cancel_event=cancel_event,
        success_returncodes=(0, 1),
    )

    if not result.success:
        return _failure(
            result.reason
        )

    return _success(
        result.data or None
    )


def get_remote_head(
    workspace: str | Path,
    remote: str,
    branch: str,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[str | None]:
    """直接查询远程 Branch 的 Commit SHA，不存在时返回 None。

    使用 ``git ls-remote`` 而不是本地 ``refs/remotes``。Fyno 不执行 fetch，
    因此本地 tracking ref 可能过期，不能代表远程仓库的真实状态。
    """
    result = _run(
        workspace,
        "ls-remote",
        remote,
        f"refs/heads/{branch}",
        cancel_event=cancel_event,
    )

    if not result.success:
        return _failure(
            result.reason
        )

    if not result.data:
        return _success(None)

    commit = result.data.split(
        maxsplit=1
    )[0]

    return _success(commit)


def add_all(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """执行 ``git add -A``，将全部变化加入暂存区。"""
    return _run_without_data(
        workspace,
        "add",
        "-A",
        cancel_event=cancel_event,
    )


def has_staged_changes(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[bool]:
    """判断暂存区中是否存在可以提交的变化。

    Sync 应在 ``add_all`` 成功后调用本函数。返回 False 时应跳过 commit，
    避免用户反复同步且文件没有变化时触发 ``nothing to commit`` 错误。
    """
    result = _run(
        workspace,
        "diff",
        "--cached",
        "--name-only",
        cancel_event=cancel_event,
    )

    if not result.success:
        return _failure(
            result.reason
        )

    return _success(
        bool(result.data)
    )


def commit(
    workspace: str | Path,
    message: str,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """使用给定 message 提交当前暂存区。"""
    return _run_without_data(
        workspace,
        "commit",
        "-m",
        message,
        cancel_event=cancel_event,
    )


def push(
    workspace: str | Path,
    remote: str,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """将当前分支推送到指定 Remote。

    ``--set-upstream`` 可以同时覆盖首次推送和后续推送场景。
    """
    return _run_without_data(
        workspace,
        "push",
        "--set-upstream",
        remote,
        "HEAD",
        cancel_event=cancel_event,
    )


def get_remotes(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[dict[str, str]]:
    """获取全部 Remote，返回 Remote 名称到 URL 的映射。"""
    names_result = _run(
        workspace,
        "remote",
        cancel_event=cancel_event,
    )

    if not names_result.success:
        return _failure(
            names_result.reason
        )

    remotes: dict[str, str] = {}

    for name in (
        names_result.data or ""
    ).splitlines():
        url_result = _run(
            workspace,
            "remote",
            "get-url",
            name,
            cancel_event=cancel_event,
        )

        if not url_result.success:
            return _failure(
                url_result.reason
            )

        remotes[name] = (
            url_result.data or ""
        )

    return _success(remotes)


def add_remote(
    workspace: str | Path,
    name: str,
    url: str,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """使用给定名称和 URL 添加一个 Remote。"""
    return _run_without_data(
        workspace,
        "remote",
        "add",
        name,
        url,
        cancel_event=cancel_event,
    )


def set_remote_url(
    workspace: str | Path,
    name: str,
    url: str,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """将指定 Remote 的 URL 修改为给定值。"""
    return _run_without_data(
        workspace,
        "remote",
        "set-url",
        name,
        url,
        cancel_event=cancel_event,
    )


def get_changes(
    workspace: str | Path,
    *,
    cancel_event: threading.Event | None = None,
) -> GitResult[list[str]]:
    """返回 ``git status --short`` 的逐行结果。

    每一项保留 Git 的两字符状态码和文件路径，可区分新增、修改、删除等变化；
    没有变化时 data 为空列表。Git 不会在该结果中列出未发生变化的文件。
    """
    result = _run(
        workspace,
        "status",
        "--short",
        cancel_event=cancel_event,
    )

    if not result.success:
        return _failure(
            result.reason
        )

    return _success(
        (result.data or "").splitlines()
    )


def _run_without_data(
    workspace: str | Path,
    *args: str,
    cancel_event: threading.Event | None = None,
) -> GitResult[None]:
    """执行不需要向调用方返回标准输出的 Git 命令。"""
    result = _run(
        workspace,
        *args,
        cancel_event=cancel_event,
    )

    if not result.success:
        return _failure(
            result.reason
        )

    return _success()


def _run(
    workspace: str | Path,
    *args: str,
    cancel_event: threading.Event | None = None,
    success_returncodes: tuple[int, ...] = (0,),
) -> GitResult[str]:
    """在 Workspace 中执行短生命周期 Git 命令并返回标准输出。

    每次调用只持有一个独立 Git 子进程。短周期 ``communicate`` 同时排空
    stdout/stderr 并检查 cancel/timeout，避免 PIPE 填满后 Git 与父进程互相
    等待。结束、取消或超时后都会回收子进程。
    """
    if (
        cancel_event is not None
        and cancel_event.is_set()
    ):
        return _failure(
            "Git command was cancelled"
        )

    started_at = time.monotonic()

    try:
        process = subprocess.Popen(
            [
                "git",
                "-C",
                str(workspace),
                *args,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        return _failure(
            f"Unable to execute Git: {exc}"
        )

    while True:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            break

        if (
            cancel_event is not None
            and cancel_event.is_set()
        ):
            _stop_process(process)
            return _failure(
                "Git command was cancelled"
            )

        elapsed = (
            time.monotonic()
            - started_at
        )
        remaining = (
            _GIT_TIMEOUT_SECONDS
            - elapsed
        )

        if remaining <= 0:
            _stop_process(process)
            return _failure(
                "Git command timed out after "
                f"{_GIT_TIMEOUT_SECONDS} seconds"
            )

        try:
            stdout, stderr = process.communicate(
                timeout=min(
                    _GIT_POLL_SECONDS,
                    remaining,
                )
            )
            break
        except subprocess.TimeoutExpired:
            continue

    if (
        process.returncode
        not in success_returncodes
    ):
        reason = (
            (stderr or "").strip()
            or (stdout or "").strip()
            or "Git command failed"
        )
        return _failure(reason)

    # status --short 的第一列可能以空格开头，不能使用 strip()，否则会破坏
    # Git 的两字符状态码。这里只移除命令输出末尾的换行。
    output = (stdout or "").rstrip(
        "\r\n"
    )

    return _success(output)


def _stop_process(
    process: subprocess.Popen[str],
) -> None:
    """终止并回收尚未结束的 Git 子进程。

    先给予 terminate 一个很短的退出窗口；进程仍存活时再 kill。无论走哪条
    路径，最终都调用 communicate，确保进程和 stdout/stderr PIPE 被回收。
    """
    if process.poll() is None:
        try:
            process.terminate()
        except OSError:
            # 进程可能在 poll 与 terminate 之间自然退出。
            pass

    try:
        process.communicate(
            timeout=_GIT_STOP_GRACE_SECONDS
        )
        return
    except subprocess.TimeoutExpired:
        pass

    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            # kill 前进程自然退出时，后续 communicate 仍负责最终回收。
            pass

    process.communicate()


def _success(
    data: T | None = None,
) -> GitResult[T]:
    """创建成功结果，并保证 reason 为空字符串。"""
    return GitResult(
        success=True,
        reason="",
        data=data,
    )


def _failure(
    reason: str,
) -> GitResult[T]:
    """创建失败结果。"""
    return GitResult(
        success=False,
        reason=reason,
        data=None,
    )


def _is_not_repository_reason(
    reason: str,
) -> bool:
    """判断 Git 失败原因是否表示当前目录不是仓库。"""
    normalized_reason = reason.lower()

    return (
        "not a git repository"
        in normalized_reason
    )

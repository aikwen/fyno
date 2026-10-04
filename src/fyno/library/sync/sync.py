"""Library Git Sync Service。

该模块将 ``git.py`` 的基础操作编排为无状态的查询与单向同步流程。Workspace
由 API 层校验后传入；本模块不读取应用配置、不维护请求间缓存，也不实现并发
任务管理。

每次请求直接执行所需的短生命周期 Git CLI 子进程。Fyno 不持有 Git process，
也不执行 Pull、Fetch、合并、冲突解决或 Force Push。
"""

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Literal

from . import git


_BRANCH = "main"
_REMOTE = "origin"
_COMMIT_MESSAGE = ":fountain_pen: sync notes"


SyncStatus = Literal[
    "success",
    "clean",
    "error",
]


@dataclass(frozen=True, slots=True)
class SyncInfo:
    """当前 Workspace 的 Git Sync 信息。"""

    success: bool
    reason: str
    git_available: bool
    repository: bool
    remote: str | None
    changes: list[str]
    synced: bool


@dataclass(frozen=True, slots=True)
class SyncResult:
    """一次同步请求的结果。"""

    status: SyncStatus
    reason: str = ""
    stage: str | None = None


def get_sync(
    workspace: str | Path,
    cancel_event: threading.Event | None = None,
) -> SyncInfo:
    """真实查询 Workspace 当前的 Git Sync 状态。

    本函数不使用请求间缓存，也不产生 Git 修改。存在 origin 时通过 ls-remote
    查询远程 main 的真实 HEAD；不依赖可能因未 Fetch 而过期的 tracking ref。
    """
    available_result = git.git_available()

    if (
        not available_result.success
        or not available_result.data
    ):
        return _info_error(
            reason=(
                available_result.reason
                or "Git executable was not found"
            ),
            git_available=False,
        )

    repository_result = git.is_repository(
        workspace,
        cancel_event=cancel_event,
    )

    if not repository_result.success:
        return _info_error(
            reason=repository_result.reason,
            git_available=True,
        )

    if not repository_result.data:
        return SyncInfo(
            success=True,
            reason="",
            git_available=True,
            repository=False,
            remote=None,
            changes=[],
            synced=False,
        )

    branch_result = git.get_current_branch(
        workspace,
        cancel_event=cancel_event,
    )

    if not branch_result.success:
        return _info_error(
            reason=branch_result.reason,
            git_available=True,
            repository=True,
        )

    remotes_result = git.get_remotes(
        workspace,
        cancel_event=cancel_event,
    )

    if not remotes_result.success:
        return _info_error(
            reason=remotes_result.reason,
            git_available=True,
            repository=True,
        )

    origin = (
        remotes_result.data or {}
    ).get(_REMOTE)

    changes_result = git.get_changes(
        workspace,
        cancel_event=cancel_event,
    )

    if not changes_result.success:
        return _info_error(
            reason=changes_result.reason,
            git_available=True,
            repository=True,
            remote=origin,
        )

    changes = changes_result.data or []

    local_head_result = git.get_head(
        workspace,
        cancel_event=cancel_event,
    )

    if not local_head_result.success:
        return _info_error(
            reason=local_head_result.reason,
            git_available=True,
            repository=True,
            remote=origin,
            changes=changes,
        )

    local_head = local_head_result.data
    remote_head: str | None = None

    if origin is not None:
        remote_head_result = git.get_remote_head(
            workspace,
            _REMOTE,
            _BRANCH,
            cancel_event=cancel_event,
        )

        if not remote_head_result.success:
            return _info_error(
                reason=remote_head_result.reason,
                git_available=True,
                repository=True,
                remote=origin,
                changes=changes,
            )

        remote_head = remote_head_result.data

    # 没有本地 HEAD 的新仓库尚未建立任何有效同步关系，即使远程 main 同样
    # 不存在，也不能仅因两个 None 相等就视为已同步。
    synced = (
        branch_result.data == _BRANCH
        and origin is not None
        and not changes
        and local_head is not None
        and local_head == remote_head
    )

    return SyncInfo(
        success=True,
        reason="",
        git_available=True,
        repository=True,
        remote=origin,
        changes=changes,
        synced=synced,
    )


def sync(
    workspace: str | Path,
    remote: str | None = None,
    cancel_event: threading.Event | None = None,
) -> SyncResult:
    """将当前 Workspace 提交并推送到固定的 origin/main。"""
    available_result = git.git_available()

    if (
        not available_result.success
        or not available_result.data
    ):
        return _error(
            stage="git",
            reason=(
                available_result.reason
                or "Git executable was not found"
            ),
        )

    repository_result = git.is_repository(
        workspace,
        cancel_event=cancel_event,
    )

    if not repository_result.success:
        return _error(
            stage="repository",
            reason=repository_result.reason,
        )

    remote_url = (
        remote.strip()
        if remote is not None
        else ""
    )

    # 初始化会在 Workspace 中创建 .git。新仓库没有可复用的 origin，因此
    # 请求未提供 Remote 时应在任何 Git 修改之前失败，避免留下无用副作用。
    if (
        not repository_result.data
        and not remote_url
    ):
        return _error(
            stage="remote",
            reason="Git remote origin is not configured",
        )

    if repository_result.data:
        branch_result = git.get_current_branch(
            workspace,
            cancel_event=cancel_event,
        )

        if not branch_result.success:
            return _error(
                stage="repository",
                reason=branch_result.reason,
            )

        current_branch = (
            branch_result.data or ""
        )

        # Fyno 固定使用 main。自动切换分支可能改变用户当前工作上下文，因此
        # 其他分支和 Detached HEAD 都只返回错误。
        if current_branch != _BRANCH:
            branch_name = (
                current_branch
                or "detached HEAD"
            )
            return _error(
                stage="repository",
                reason=(
                    "Fyno Sync requires branch main; "
                    f"current branch is {branch_name}"
                ),
            )
    else:
        init_result = git.init(
            workspace,
            cancel_event=cancel_event,
        )

        if not init_result.success:
            return _error(
                stage="repository",
                reason=init_result.reason,
            )

    remotes_result = git.get_remotes(
        workspace,
        cancel_event=cancel_event,
    )

    if not remotes_result.success:
        return _error(
            stage="remote",
            reason=remotes_result.reason,
        )

    origin = (
        remotes_result.data or {}
    ).get(_REMOTE)

    if origin is None:
        # 空字符串不表示删除 Remote。首次同步尚无 origin 时，必须由请求提供
        # 一个非空 URL 才能创建固定的 origin。
        if not remote_url:
            return _error(
                stage="remote",
                reason="Git remote origin is not configured",
            )

        add_remote_result = git.add_remote(
            workspace,
            _REMOTE,
            remote_url,
            cancel_event=cancel_event,
        )

        if not add_remote_result.success:
            return _error(
                stage="remote",
                reason=add_remote_result.reason,
            )
    elif remote_url and remote_url != origin:
        # Fyno 只允许更新固定 origin 的 URL，不删除或重命名其他 Remote。
        set_remote_result = git.set_remote_url(
            workspace,
            _REMOTE,
            remote_url,
            cancel_event=cancel_event,
        )

        if not set_remote_result.success:
            return _error(
                stage="remote",
                reason=set_remote_result.reason,
            )

    add_result = git.add_all(
        workspace,
        cancel_event=cancel_event,
    )

    if not add_result.success:
        return _error(
            stage="add",
            reason=add_result.reason,
        )

    staged_result = git.has_staged_changes(
        workspace,
        cancel_event=cancel_event,
    )

    if not staged_result.success:
        return _error(
            stage="commit",
            reason=staged_result.reason,
        )

    # Staged changes 只决定本轮是否需要 Commit，不能证明旧 Commit 已经 Push。
    if staged_result.data:
        commit_result = git.commit(
            workspace,
            _COMMIT_MESSAGE,
            cancel_event=cancel_event,
        )

        if not commit_result.success:
            return _error(
                stage="commit",
                reason=commit_result.reason,
            )

    local_head_result = git.get_head(
        workspace,
        cancel_event=cancel_event,
    )

    if not local_head_result.success:
        return _error(
            stage="repository",
            reason=local_head_result.reason,
        )

    local_head = local_head_result.data

    # 新仓库没有变化时不存在 HEAD，也就没有可以 Push 的 source ref。
    if local_head is None:
        return SyncResult(
            status="clean",
        )

    remote_head_result = git.get_remote_head(
        workspace,
        _REMOTE,
        _BRANCH,
        cancel_event=cancel_event,
    )

    if not remote_head_result.success:
        # ls-remote 的认证、网络和 Remote 错误直接返回；Fyno 不尝试 fallback、
        # Pull、Fetch 或修复远程历史。
        return _error(
            stage="remote",
            reason=remote_head_result.reason,
        )

    # Local/Remote HEAD 是否相同才决定 Push。即使本轮没有新 Commit，只要 SHA
    # 不一致，也必须重试之前可能失败的 Push。
    if local_head == remote_head_result.data:
        return SyncResult(
            status="clean",
        )

    push_result = git.push(
        workspace,
        _REMOTE,
        cancel_event=cancel_event,
    )

    if not push_result.success:
        return _error(
            stage="push",
            reason=push_result.reason,
        )

    return SyncResult(
        status="success",
    )


def _info_error(
    reason: str,
    git_available: bool,
    repository: bool = False,
    remote: str | None = None,
    changes: list[str] | None = None,
) -> SyncInfo:
    """构造失败的 SyncInfo，并保留已成功读取的部分状态。"""
    return SyncInfo(
        success=False,
        reason=reason,
        git_available=git_available,
        repository=repository,
        remote=remote,
        changes=changes or [],
        synced=False,
    )


def _error(
    stage: str,
    reason: str,
) -> SyncResult:
    """构造带失败阶段和 Git 原因的 SyncResult。"""
    return SyncResult(
        status="error",
        reason=reason,
        stage=stage,
    )

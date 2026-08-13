from __future__ import annotations

from typing import Any

from .action_authority import build_action_authority_matrix


def run_action_authority_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    return build_action_authority_matrix(suite)

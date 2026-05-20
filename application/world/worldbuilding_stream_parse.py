"""世界观 SSE 流式 JSON 增量解析（单次 LLM 输出，按维度/字段推送）。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from application.world.worldbuilding_merge import (
    WORLD_BUILDING_FIELDS_BY_DIMENSION,
    filter_dimension_fields,
)

WORLDBUILDING_DIM_KEYS: Tuple[str, ...] = (
    "core_rules",
    "geography",
    "society",
    "culture",
    "daily_life",
)

DIM_LABELS: Dict[str, str] = {
    "core_rules": "核心法则",
    "geography": "地理生态",
    "society": "社会结构",
    "culture": "历史文化",
    "daily_life": "沉浸感细节",
}

_FIELD_PAIR_RE = re.compile(r'"(\w+)"\s*:\s*"((?:[^"\\]|\\.)*)"')


def _unescape_json_string(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\\\", "\\")
    )


def _json_working_copy(text: str) -> str:
    raw = text or ""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if m:
        raw = m.group(1)
    start = raw.find("{")
    return raw[start:] if start >= 0 else raw


def _dimension_slice(buffer: str, dim_key: str) -> str:
    keys = list(WORLDBUILDING_DIM_KEYS)
    if dim_key not in keys:
        return ""
    start = buffer.find(f'"{dim_key}"')
    if start < 0:
        return ""
    end = len(buffer)
    for other in keys[keys.index(dim_key) + 1 :]:
        pos = buffer.find(f'"{other}"', start + 1)
        if pos > 0:
            end = min(end, pos)
    return buffer[start:end]


def _extract_completed_string_fields(
    text: str, *, allowed_keys: Optional[Set[str]] = None
) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in _FIELD_PAIR_RE.finditer(text):
        key = m.group(1)
        if allowed_keys is not None and key not in allowed_keys:
            continue
        val = _unescape_json_string(m.group(2)).strip()
        if val:
            out[key] = val
    return out


class WorldbuildingStreamParser:
    """消费 LLM 流式 token，产出 style / dim_chunk / field 事件。"""

    def __init__(self) -> None:
        self.buffer = ""
        self.emitted_fields: Set[Tuple[str, str]] = set()
        self.announced_dims: Set[str] = set()
        self.style_emitted = False
        self.last_active_dim = WORLDBUILDING_DIM_KEYS[0]
        self.accumulated: Dict[str, Dict[str, str]] = {k: {} for k in WORLDBUILDING_DIM_KEYS}

    def active_dimension(self) -> str:
        last = self.last_active_dim
        for dk in WORLDBUILDING_DIM_KEYS:
            if f'"{dk}"' in self.buffer:
                last = dk
        self.last_active_dim = last
        return last

    def feed(self, chunk: str) -> List[Dict[str, Any]]:
        if not chunk:
            return []
        self.buffer += chunk
        events: List[Dict[str, Any]] = []
        active = self.active_dimension()

        events.append({"kind": "dim_chunk", "dimension": active, "chunk": chunk})

        if not self.style_emitted:
            m = re.search(r'"style"\s*:\s*"((?:[^"\\]|\\.)*)"', self.buffer)
            if m:
                self.style_emitted = True
                events.append(
                    {"kind": "style", "content": _unescape_json_string(m.group(1))}
                )

        for dim in WORLDBUILDING_DIM_KEYS:
            if dim not in self.announced_dims and f'"{dim}"' in self.buffer:
                self.announced_dims.add(dim)
                events.append({"kind": "phase_dim", "dimension": dim})

            slice_text = _dimension_slice(_json_working_copy(self.buffer), dim)
            if not slice_text:
                continue
            allowed = frozenset(WORLD_BUILDING_FIELDS_BY_DIMENSION.get(dim, ()))
            for field, value in _extract_completed_string_fields(
                slice_text, allowed_keys=allowed
            ).items():
                dedupe = (dim, field)
                if dedupe in self.emitted_fields:
                    continue
                self.emitted_fields.add(dedupe)
                self.accumulated[dim][field] = value
                events.append(
                    {
                        "kind": "field",
                        "dimension": dim,
                        "field": field,
                        "value": value,
                    }
                )
        return events

    def finalize(self) -> Dict[str, Dict[str, str]]:
        """流结束后的兜底：完整 JSON 修复解析，补全未流式识别的字段。"""
        if not self.buffer.strip():
            return self.accumulated

        try:
            from application.world.services.auto_bible_generator import (
                _parse_llm_json_to_dict,
                _repair_json_string,
                _sanitize_llm_json_output,
            )

            content = _sanitize_llm_json_output(self.buffer)
            try:
                parsed = _parse_llm_json_to_dict(content)
            except json.JSONDecodeError:
                parsed = _parse_llm_json_to_dict(_repair_json_string(content))

            wb = parsed.get("worldbuilding") if isinstance(parsed, dict) else None
            if not isinstance(wb, dict):
                wb = {
                    k: parsed.get(k)
                    for k in WORLDBUILDING_DIM_KEYS
                    if isinstance(parsed.get(k), dict)
                }
            for dim in WORLDBUILDING_DIM_KEYS:
                blk = wb.get(dim) if isinstance(wb, dict) else None
                if not isinstance(blk, dict):
                    continue
                for k, v in blk.items():
                    s = str(v).strip() if v is not None else ""
                    if s:
                        self.accumulated[dim][k] = s
        except Exception:
            pass

        filtered = {
            dim: filter_dimension_fields(dim, fields)
            for dim, fields in self.accumulated.items()
        }
        return {dim: dict(fields) for dim, fields in filtered.items() if fields}

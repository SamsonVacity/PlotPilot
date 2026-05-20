"""世界观 SSE 流式解析：字段白名单过滤。"""
from application.world.worldbuilding_stream_parse import WorldbuildingStreamParser


def test_parser_ignores_nested_custom_keys():
    parser = WorldbuildingStreamParser()
    chunk = '''```json
{
  "style": "第三人称",
  "worldbuilding": {
    "core_rules": {
      "world_name": "破劫纪元",
      "name": "血劫大法",
      "essence": "劫气残渣",
      "power_system": "吸收劫气突破，每次突破引发天劫反噬",
      "physics_rules": "劫气来自宇宙崩坏残渣"
    }
  }
}
```'''
    events = parser.feed(chunk)
    field_events = [e for e in events if e.get("kind") == "field" and e.get("dimension") == "core_rules"]
    fields = {e["field"]: e["value"] for e in field_events}
    assert "power_system" in fields
    assert "physics_rules" in fields
    assert "world_name" not in fields
    assert "name" not in fields
    assert "essence" not in fields

    finalized = parser.finalize()
    cr = finalized.get("core_rules") or {}
    assert "power_system" in cr
    assert "name" not in cr


def test_parser_geography_only_allowed_keys():
    parser = WorldbuildingStreamParser()
    text = (
        '{"worldbuilding":{"geography":{"terrain":"高原","effect":"不应出现",'
        '"climate":"干燥"}}}'
    )
    parser.feed(text)
    finalized = parser.finalize()
    geo = finalized.get("geography") or {}
    assert geo.get("terrain") == "高原"
    assert "effect" not in geo

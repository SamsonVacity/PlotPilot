/** 世界观五维字段白名单（与后端 WORLD_BUILDING_FIELDS_BY_DIMENSION 对齐） */
export const WB_FIELDS_BY_DIM: Record<string, readonly string[]> = {
  core_rules: [
    'power_system',
    'physics_rules',
    'magic_tech',
    'cost_and_limitation',
    'resource_scarcity',
  ],
  geography: [
    'terrain',
    'climate',
    'resources',
    'ecology',
    'forbidden_zones',
    'urban_core',
    'hidden_realms',
  ],
  society: [
    'politics',
    'economy',
    'class_system',
    'power_structure',
    'oppression_mechanism',
    'class_division',
  ],
  culture: ['history', 'religion', 'taboos', 'worship', 'oaths_and_curses'],
  daily_life: [
    'food_clothing',
    'language_slang',
    'entertainment',
    'survival_tactics',
    'market_reality',
    'food_and_drink',
    'slang_and_profanity',
  ],
} as const

export function filterWorldbuildingFields(
  dimension: string,
  fields: Record<string, string>
): Record<string, string> {
  const allowed = new Set(WB_FIELDS_BY_DIM[dimension] ?? [])
  if (!allowed.size) return {}
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(fields)) {
    if (allowed.has(k) && String(v).trim()) out[k] = v
  }
  return out
}

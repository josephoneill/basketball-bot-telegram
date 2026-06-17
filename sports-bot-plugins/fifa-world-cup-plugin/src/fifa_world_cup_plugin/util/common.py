import difflib
import re
from functools import wraps
from datetime import datetime
from zoneinfo import ZoneInfo


def cached(key, expire=None):
  """Decorator to cache async function results by key."""
  def decorator(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
      if key in self.cache:
        return self.cache[key]

      result = await func(self, *args, **kwargs)
      self.cache.set(key, result, expire=expire)
      return result
    return wrapper
  return decorator

def normalize_team_name(value):
  if not value:
    return ''
  normalized = re.sub(r'[^a-z0-9\s]', ' ', value.lower())
  return ' '.join(normalized.split())

def timestamp_to_eastern(value):
  if not value:
    return ''

  eastern = ZoneInfo('America/New_York')

  # Football API returns unix timestamps; ESPN returns ISO strings.
  if isinstance(value, str):
    cleaned = value.strip()
    if not cleaned:
      return ''

    if cleaned.replace('.', '', 1).isdigit():
      dt = datetime.fromtimestamp(float(cleaned), tz=eastern)
    else:
      iso_value = cleaned.replace('Z', '+00:00')
      parsed = datetime.fromisoformat(iso_value)
      if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo('UTC'))
      dt = parsed.astimezone(eastern)
  else:
    dt = datetime.fromtimestamp(float(value), tz=eastern)

  return dt.strftime('%m-%d %H:%M:%S %Z')


def find_team_id_with_match_fallback(
  team_name,
  entries,
  extract_team=lambda entry: entry,
  id_key='id',
  name_key='name',
  code_key='code',
  min_fuzzy_ratio=0.6,
):
  search_name = normalize_team_name(team_name)
  if not search_name:
    return None

  candidates = []
  for entry in entries or []:
    team = extract_team(entry) or {}
    team_id = team.get(id_key)
    if team_id is None:
      continue

    normalized_name = normalize_team_name(team.get(name_key, ''))
    normalized_code = normalize_team_name(team.get(code_key, ''))
    candidates.append((team_id, normalized_name, normalized_code))

  if not candidates:
    return None

  # Prefer exact normalized name/code match first.
  for team_id, normalized_name, normalized_code in candidates:
    if search_name in {normalized_name, normalized_code}:
      return team_id

  # Then allow partial team-name match.
  for team_id, normalized_name, _ in candidates:
    if search_name in normalized_name:
      return team_id

  # Finally choose the strongest fuzzy match when confidence is high enough.
  scored = []
  for team_id, normalized_name, _ in candidates:
    if not normalized_name:
      continue
    ratio = difflib.SequenceMatcher(None, search_name, normalized_name).ratio()
    scored.append((ratio, team_id))

  if not scored:
    return None

  best_ratio, best_id = max(scored, key=lambda item: item[0])
  if best_ratio < min_fuzzy_ratio:
    return None
  return best_id
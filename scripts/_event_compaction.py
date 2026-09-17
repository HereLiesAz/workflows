from __future__ import annotations


def generic_event_compaction_script() -> str:
    return r'''DISPATCH_EVENT_JSON="$(jq -c '\''
  def strip_noise:
    if type == "object" then
      with_entries(
        select(.key as $k | [
          "url", "html_url", "avatar_url", "followers_url", "following_url",
          "gists_url", "starred_url", "subscriptions_url", "organizations_url",
          "repos_url", "events_url", "received_events_url", "node_id", "_links"
        ] | index($k) | not)
      ) | map_values(strip_noise)
    elif type == "array" then map(strip_noise)
    else . end;
  strip_noise
'\'' <<<"$EVENT_JSON")"
'''

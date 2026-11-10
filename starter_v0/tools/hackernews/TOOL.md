---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, limit]
outputs: [query, count, items, error]
side_effect: false
description: Search tech discussions, stories, and comments on Hacker News via Algolia API. Use this for tech trends and startup discussions.
parameters:
  type: object
  properties:
    query:
      type: string
      description: Keyword to search on Hacker News.
    limit:
      type: integer
      description: Maximum number of stories (default 5, max 10).
  required:
    - query
---

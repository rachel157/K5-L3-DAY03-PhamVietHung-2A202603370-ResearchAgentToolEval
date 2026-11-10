---
name: github_search
description: Search for open-source repositories on GitHub by query string. Use this when the user asks for code repositories, libraries, or open-source projects.
parameters:
  type: object
  properties:
    query:
      type: string
      description: Search keywords for repositories.
    sort:
      type: string
      description: Sort field (stars, forks, updated). Default is stars.
      enum: [stars, forks, updated]
    limit:
      type: integer
      description: Maximum number of results (default 5, max 10).
  required:
    - query
---
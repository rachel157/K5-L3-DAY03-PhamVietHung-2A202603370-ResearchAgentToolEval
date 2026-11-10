---
name: wikipedia
description: Look up summary definitions and explanations of concepts or entities on Wikipedia. Use this for general knowledge lookup.
parameters:
  type: object
  properties:
    title:
      type: string
      description: The article title or concept to look up.
  required:
    - title
---
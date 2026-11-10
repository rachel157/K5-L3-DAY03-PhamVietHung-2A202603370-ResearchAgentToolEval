---
name: save_note
description: Save a research summary or markdown note to a local file. ONLY execute when confirmed is true.
parameters:
  type: object
  properties:
    filename:
      type: string
      description: Name of the file to save.
    content:
      type: string
      description: Markdown text content to save.
    confirmed:
      type: boolean
      description: Must be set to true after explicit user confirmation.
  required:
    - filename
    - content
    - confirmed
---
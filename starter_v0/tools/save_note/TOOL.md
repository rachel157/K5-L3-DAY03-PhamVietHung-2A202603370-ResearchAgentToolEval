---
name: save_note
track: bonus
kind: action
provider: local filesystem
requires_env: []
inputs: [filename, content, confirmed]
outputs: [success, filename, path, awaiting_user, question, response_type, error]
side_effect: local_file_write
requires_confirmation: true
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

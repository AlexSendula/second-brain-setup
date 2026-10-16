---
type: type
created: {{today}}
name: inbox
folder: ["02 Inbox"]
filename: "<YYYY-MM-DD HHMM> <title>"
fields:
  source: {format: text}
  received: {format: datetime}
  question: {format: text}
---
An inbox item: something that arrived and is not sorted yet. It records where it came from, when it arrived, and an open question if the agent has one. A note you drop in by hand needs none of this; the agent fills it in.

Rules:
- source is chat, note, phone, email, or a feed's name.

## Template
```
---
type: inbox
created:
source:
received:
---
```

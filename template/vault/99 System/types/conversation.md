---
type: type
created: {{today}}
name: conversation
folder: ["06 Conversations/<year>"]
filename: "<YYYY-MM-DD> <who> about <what>"
fields:
  date: {format: date, required: true}
  with: {format: [link, text], required: true}
  about: {format: [link, list]}
  source: {values: [chat, transcript, notes], required: true}
---
A conversation: a talk with someone. It has the date, who it was with, what it was about (any notes it touched, or none), and where it came from. The body is light by default: whatever you said, even one line. A summary, discussion points and action points are only for a transcript or notes, and each action point links to what it became.

## Template
```
---
type: conversation
created:
date:
with:
source:
---
```

---
type: type
created: {{today}}
name: appointment
folder: ["03 Projects/<project>", "04 Areas/<area>"]
filename: "<YYYY-MM-DD> <what>"
fields:
  date: {format: date, required: true}
  repeat: {format: repeat}
  time: {format: time}
  length: {format: duration}
  where: {format: text}
  with: {format: [link, text]}
  calendar: {format: boolean, default: false}
---
An appointment: something you would put in a calendar. It has a date (for a repeating one, when it starts and how it repeats), optionally a time or a length, where it is, who it is with, and whether to export it to a calendar, only on your word. A missed occurrence of a repeating appointment just passes.

## Template
```
---
type: appointment
created:
date:
---
```

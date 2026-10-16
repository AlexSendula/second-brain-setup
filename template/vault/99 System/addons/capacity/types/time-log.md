---
type: type
created: {{today}}
name: time-log
folder: ["09 Logs/time"]
filename: "<YYYY-MM> time"
fields: {}
---
A time log: the time you spent on things, one file per month. Each line has the date, how long, what it was for, and optionally a note. Part of the Capacity add-on.

## Template
```
---
type: time-log
created:
---

- <YYYY-MM-DD> <duration> [[<project>]] <what it was for>
```

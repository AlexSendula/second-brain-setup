---
type: type
created: {{today}}
name: project
folder: ["03 Projects/<project>"]
filename: "<project>"
fields:
  status: {values: [active, paused, someday, done, dropped], required: true}
  area: {format: link}
  due: {format: date}
  done: {format: date, required_when: "status is done or dropped"}
---
A project: something with an end. It has a state (active, paused, someday, done or dropped), the area it serves, an optional deadline, and the date it was finished. Its body holds the Goal, the Now, the tasks as lines, and the Log.

## Template
```
---
type: project
created:
status: active
---

## Goal

## Now

## Tasks

## Log
```

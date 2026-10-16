---
type: type
created: {{today}}
name: task
folder: ["03 Projects/<project>", "04 Areas/<area>"]
filename: "<title>"
fields:
  status: {values: [open, doing, waiting, someday, done, dropped], required: true}
  due: {format: date}
  lead: {format: duration}
  scheduled: {format: date}
  start: {format: date}
  repeat: {format: repeat}
  repeat_from: {values: [due, done], default: due}
  if_missed: {values: [carry, lapse], default: carry}
  estimate: {format: duration}
  context: {values_from: contexts}
  waiting_on: {format: [link, text], required_when: "status is waiting"}
  chase: {format: date, required_when: "status is waiting"}
  done: {format: date, required_when: "status is done or dropped"}
  points: {values: [1, 2, 3, 5, 8]}
---
A task: one thing to do. It has a state (open, doing, waiting, someday, done or dropped). It can also have a deadline, a lead time, a planned day, a repeat, an estimate, a context, and who it is waiting on, with a chase date. It is a line in its project or area note, or its own note when it needs more.

Rules:
- A repeat requires due.
- if_missed applies only to fixed-date repeats (repeat_from: due).
- points applies only to stories: task notes inside a project.
- done is not written when a repeating task note completes an occurrence.

## Template
```
---
type: task
created:
status: open
---

## Now

## Log
```

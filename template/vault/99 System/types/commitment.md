---
type: type
created: {{today}}
name: commitment
folder: ["04 Areas/<area>"]
filename: "<title>"
fields:
  when: {format: when, required: true}
  length: {format: duration}
  from: {format: date}
  until: {format: date}
  calendar: {format: boolean, default: false}
---
A commitment: how your week normally runs. It has the days, optionally the times or a rough length, and optionally a season it runs in (from and until). The agent treats commitments as your baseline and never reminds you of a missed one.

Rules:
- length is required when `when` has no times.

## Template
```
---
type: commitment
created:
when:
---
```

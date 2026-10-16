---
type: type
created: {{today}}
name: week-plan
folder: ["08 Weeks/<year>"]
filename: "<YYYY-Www>"
fields:
  week: {format: week, required: true}
  focus: {format: text}
  updated: {format: date}
  frozen: {format: date}
  points_planned: {format: number}
  points_done: {format: number}
---
A week plan: your focus for one week, your budgets for it (with the Capacity add-on), and an overview built from the items in that week. It is named for the week it plans.

## Template
```
---
type: week-plan
created:
week:
---

## Budgets

- <time> [[<project>]]
```

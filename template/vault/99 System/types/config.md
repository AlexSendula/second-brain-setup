---
type: type
created: {{today}}
name: config
folder: ["99 System"]
filename: "config"
fields:
  system_version: {format: text}
  format_version: {format: number}
  update_source: {format: text}
  agent_tools: {format: list}
  addons: {format: list}
  contexts: {format: list}
  weekly_review: {format: weekdays}
  daily_briefing: {format: boolean}
  week_plan: {format: boolean, default: true}
  timezone: {format: text}
  points_per_week: {format: number, default: 8}
  available: {format: duration, default: 16h}
  available_days: {format: weekdays, default: mon-sun}
---
Config: the settings for this vault. It holds your contexts, which add-ons are on, your weekly review day, whether you want the daily briefing and week plans, your timezone, and the versions of the system and the format. With Capacity, it also holds how many hours a day you have, and on which days.

Rules:
- each agent_tools item is claude-code, codex or vscode.

## Template
```
---
type: config
created:
system_version:
format_version: 1
update_source:
agent_tools:
addons: []
contexts: [home, out, computer, phone]
weekly_review: sun
daily_briefing: false
week_plan: true
timezone: ""
---
```

---
type: type
created: {{today}}
name: type
folder: ["99 System/types"]
filename: "<name>"
fields:
  name: {format: text}
  folder: {format: list}
  filename: {format: text}
---
A type definition: one kind of note. It gives the kind's folder and file name, its fields with their formats and allowed values, and a Template: the frontmatter and sections a new note of the kind starts with. A required_when reads "<field> is <value>", with several values joined by " or " (for example "status is done or dropped").

## Template
```
---
type: type
created:
name:
folder:
filename:
fields:
---

One short paragraph: what this kind is.

## Template

(The frontmatter and sections a new note of this kind starts with, in a fenced block.)
```

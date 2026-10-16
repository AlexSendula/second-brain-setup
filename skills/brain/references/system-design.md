# Second Brain: system design

Names: the vault is called `second-brain`; the system's skills use the prefix `brain`. Generic on purpose: clear, obvious and easy.

| | |
|---|---|
| Status | 2026-10-12. All sections agreed in brainstorming; the six-lens review is applied. 2026-10-13: agent memory decided after research (6.7). **System v1 is agreed and frozen**: it changes only through an explicit decision of the author, recorded in section 7. |
| Scope | The **system**: the idea, independent of technology. How it runs (agent tools, where routines live, scripts, the exact file format, updates, sync, UI) belongs to the implementation spec, [Implementation](https://alexsendula.github.io/second-brain/implementation/) (section 8). |
| Research | [Landscape survey](https://alexsendula.github.io/second-brain/research/2026-10-11-landscape-survey/); agent memory: [Agent memory research](https://alexsendula.github.io/second-brain/research/2026-10-13-agent-memory-research/) |

Built for one person's private life first. The same system should work for a work vault (a separate vault, same system). The system is published on GitHub so others can read it and try it; a person's vault is private and never part of that repo.

**Where the line between system and implementation runs:** the system says what has to happen and why: the kinds of things, what each records (in plain words), where things live, the routines, the rules and the boundaries. The implementation says how it runs, including the exact file format: field names, value syntax and file-name patterns. Every vault documents its own exact format (section 5.8), so any agent can read any vault.

---

## 1. Definition

> A second brain is a trusted place outside your head for what you know, what happened, and what you've committed to. It gives these back when you ask, and before you need to ask, so your mind is free to think and to live.

The system's take, kept separate from the definition:

> In this system, an AI agent maintains the second brain. It files, links, reminds and reviews, so the upkeep that killed earlier second brains is no longer your job.

Three tests, used for every design decision:

1. **Can you forget it?** If you still have to remember to check, you haven't offloaded it.
2. **Would you trust it with something important?** If not, you'll keep it in your head anyway.
3. **Does it come back by itself?** Something that only stores is an archive, not a second brain.

Why it brings peace of mind: an unfinished goal stops intruding on your thoughts once you've made a concrete plan for it, even before you've done it (Masicampo & Baumeister, 2011). Capture it, plan it, trust it to come back.

Why structure and not only search (RAG): similarity search is good at "find something like this", but commitments, current state, complete lists and dates are not similarity questions. Search over a pile of documents cannot remind you unasked, cannot tell which of three notes is current, cannot list *all* of something, and cannot add hours up. The agent structures each item once, when it writes; search guesses again on every read. What isn't a fact yet, such as a preference you've mentioned once, lives in agent memory (section 6.7).

---

## 2. Principles

1. **Get it out of your head.** Every choice is judged by whether it reduces what you have to remember or decide.
2. **The vault is the truth.** Plain markdown. The index, exports and any UI are built from it; memory only holds what you haven't confirmed yet. All of them can be thrown away without losing anything you've confirmed.
3. **Readable and fixable by hand.** Every file follows a documented format that you can read, check and edit yourself. Running the system is the agent's job. Some features only exist with AI, and that's fine.
4. **Any agent, any model.** Instructions and rules are markdown. Calculations are plain scripts.
5. **Strict where machines read, free where you write.** Metadata follows a checked format. The body of a note is yours.
6. **Many ways in, one place to land.** Capturing is instant. Organizing is the agent's job.
7. **The system starts the review; you make the decisions.** Personal life has no manager, so the agent brings things up.
8. **Corrections become rules.** The agent's autonomy grows only through rules you've confirmed, stored in the vault.
9. **Small core, everything else is an add-on.** Add-ons come and go as definition files, not changes to the core.
10. **Forgiving.** Skipping a day, a review or a few weeks loses nothing. When you come back, the system sorts what it can, shows only what matters, and lets you handle the rest in small steps.
11. **Feeds are untrusted.** Automated sources only add to the inbox. They never act or give instructions.
12. **Reliability before features.** A small system that never misses beats a big one that sometimes does.
13. **Goals over thresholds.** Where a decision needs judgment, the system gives the agent the goal and examples, not fixed numbers. Numbers in this design are starting defaults the agent reasons around, and your corrections become rules. The exception is definitions that tools must calculate the same way every time (section 3.4).

---

## 3. Building blocks

### 3.1 Core and add-ons

| Core (every user) | Add-ons (optional) |
|---|---|
| Inbox | Capacity: available hours, budgets, time log, uncommitted hours |
| Areas and projects | Agent memory: what you haven't confirmed yet (the system works without it; on from the start in the author's implementation) |
| Tasks: deadlines, planned days, repeats, waiting-for, someday | Habits (parked; measure a rolling rate such as "4 of the last 7 days", never streaks) |
| Appointments and commitments | Calendar export (later) |
| Lists | Anyone's own: health, finance, workouts, keeping in touch, … |
| Notes (reference) | |
| Conversations | |
| People | |
| Rules | |
| Catch-up, reviews and the week plan | |
| Archive | |

### 3.2 Kinds of things in a life

| Kind | Example | What makes it different |
|---|---|---|
| Area | health, home, money, car, dance | Usually never ends. Holds standards and repeating items. |
| Project | plan the vacation, a website for Sam | Has an end and a goal. Splits into tasks. |
| Task | call the plumber | One action. |
| List item | milk, light bulbs | Grouped by where you buy it, not by project. |
| Repeating, fixed date | rent on the 1st; bins every Tuesday | Tied to the calendar. A missed one either **carries over** (rent: it still has to be paid) or **lapses** (bins: the next one replaces it). |
| Repeating, from last time | dentist 6 months after the last visit | The timer restarts when you do it. |
| Waiting for | a parcel, a reply from the landlord | Someone else has to act. Always has a date to chase it. |
| Someday | places to visit | Set aside. Comes back in the weekly review. |
| Appointment | dentist 14 Nov 10:00; dance every Tuesday 20:15 | A moment you have to be somewhere, one-off or repeating. Belongs in a calendar; often needs preparation. |
| Date to remember | birthdays | Comes back ahead of time, so there's time for a gift. |
| Conversation | doctor visit, a talk with a friend | What was said and what came of it. |
| Person | Sam, your neighbour, your dentist | Who someone is and how you know them. A line in the people list; their own note when there's enough to remember. |
| Reference | insurance policy, recipes | No action. Must be easy to find. |
| Commitment | work 08:30–17:00 on weekdays (a baseline); fitness every Monday (an intention) | How your week normally runs, not a calendar entry. The agent plans around it. Missing one just passes. |
| Habit *(Habits, parked)* | read 20 min a day | Measured over time. A missed day just passes. |

### 3.3 Storage kinds

| Kind | For | Example |
|---|---|---|
| Notes | anything that needs context | a task, project, conversation, reference note |
| Logs | many identical entries, one line each, one file per month | tracked time, gym sessions |
| Cache | speed only; optional, rebuildable | only if lookups ever get slow |

No database. Rough scale with heavy use: ~3,000 files a year, ~30,000 after 10 years, 50–100 MB of text; text search stays under a second, and archiving keeps the active set to a few hundred files.

### 3.4 Time words
The routines, views and tools use these words with one meaning each. They are exact on purpose, so a lookup always gives the same answer (principle 13); the agent may still mention something that is getting close, such as a project that looks like it's stalling.

| Word | Meaning |
|---|---|
| **Overdue** | Open, and its deadline has passed. |
| **Today** | Its deadline or planned day is today, or an appointment or commitment is today. |
| **Lead window** | It has a deadline and a lead time, and today is within that lead time before the deadline. A birthday is in its lead window from 2 weeks before. |
| **Chase due** | Waiting, and its chase date has passed. |
| **Stalled** | An active project with no log activity for 3 weeks or more (the time away during a break doesn't count). |
| **Coming up** | Deadlines, appointments and birthdays in the next 2 weeks. |
| **Away** | No session for more than a week. |

---

## 4. Routines (CORD)

### 4.1 Capture
- Talking to the agent is the main way in: captured and filed in one step.
- The inbox takes anything that arrives while nobody is organizing: notes you drop in by hand (no format needed; the agent completes them), and later phone capture and feeds.
- You never say where something goes. One sentence is enough.
- **An explicit capture the agent can't place** ("remind me to call the plumber", but it's unclear for what) goes into the inbox right away, with its open question, so it can't vanish when the session ends.
- **Brainstorms, open chats and unfinished discussions are not captures.** They are never saved unless you ask.

### 4.2 Organize (the agent's job)
- **When:** chat captures are filed immediately. The inbox is organized when you ask, at the start of the weekly review, or when the catch-up offers it.
- **Per item:** decide what kind of thing it is and check the rules (section 6.8). Then file it as a new note, update an existing note (its Now and Log), or keep it in the inbox with a question.
- **Questions** come together at the end, followed by one summary of what moved where. An unanswered question stays with its inbox item.
- **Traceable:** processed inbox items move to the archive, and whatever they became links back to them.
- **Upkeep:** adding anyone mentioned by name to the people list (section 5.4), turning a task line into its own note when it needs one (section 5.6), linking items to their project or area, proposing a rule when you give the same answer more than once.
- **One agent at a time.** An interrupted batch is noticed by the next catch-up, which runs the check and finishes or reports what's half done.

### 4.3 Conversations
When you mention a conversation ("talked to Sam, the website deadline moved to 1 December") or give a transcript or notes, the agent:
1. saves a conversation note in `Conversations/<year>/` (always, even for one line; a transcript is saved before it's processed);
2. updates the Now section of every note it touched (project, area or task) and adds a Log line linking the conversation;
3. sorts the rest:

| What was said | Where it goes |
|---|---|
| A change to a topic | That topic's Now section, plus a Log line linking the conversation |
| Something you need to do | A task in the right area, or a new project |
| A fact about the person | Their line in the people list, or their note |
| A date | An appointment, a deadline, or the person's birthday |
| An idea or tip worth keeping | A note, or Someday |
| Just chat, nothing to keep | Stays only in the conversation note |
| Unclear | The agent asks; repeated answers become rules |

A conversation is with people as named in the people list (a link once they have their own note), or with someone unnamed ("the plumber"). A theme that keeps coming up without a topic gets proposed as a new project in the weekly review.

### 4.4 Catch-up
Automatic at the start of every session. A few lines at most, grouped by count, silent when nothing needs you:
- what's waiting in the inbox;
- what's overdue;
- what's in its lead window, including birthdays within 2 weeks;
- waiting-fors whose chase date has passed;
- what's on today;
- that the weekly review is due, once the review day has passed without one;
- anything the check found that only you can resolve.

The first catch-up of a week also freezes last week's plan and builds this week's (section 4.6). When you've been away or many things are past their date, the catch-up hands over to coming back (section 4.7).

Memory may change the catch-up's wording and order, but never drop an item it's meant to show.

### 4.5 Reviews
- **Daily briefing:** optional, mornings. Today, the next few days, what needs preparing; with Capacity, uncommitted hours and a suggested focus. Not stored.
- **Weekly review:** optional, about 20 minutes, led by the agent. The catch-up says when it's due; skipping it loses nothing.
  1. Empty the inbox. *(short version)*
  2. Look back: what got done; with Capacity, planned against tracked.
  3. Projects: active ones still active and with a clear next step? Stalled ones get flagged. Paused ones: still paused? Done or dropped ones get archived.
  4. Waiting-for: chase anything past its chase date.
  5. Coming up: the next 2 weeks. *(short version)*
  6. Someday: anything ready to start? Plus a few items set aside during a break (section 4.7).
  7. Plan the week (optional): add tasks to the week, set a focus; with Capacity, set budgets.
  8. Tidy: clear ticked list items; turn finished task lines in areas into Log entries; archive finished task notes and past appointments in areas (section 4.9).
- **Short version:** steps 1 and 5, about 5 minutes.

### 4.6 The week plan
- **Builds itself.** At the start of each week, the first catch-up creates the week plan, pre-filled with everything already known: repeating tasks that fall in the week, deadlines, planned tasks, appointments, commitments and birthdays.
- **Planning is optional.** You can add tasks to the week ("this week I want to do X" gives that task a planned day this week), set a focus, and with Capacity set budgets. If you don't, the plan is simply your overview of the week.
- **One place.** The week plan is the This week view. Items stay the truth; the plan holds only your decisions for the week (focus, budgets) and an overview built from the items, refreshed whenever an item changes.
- **Frozen at the end of the week**, as it stood, whether or not you reviewed it. Afterwards it is the record of that week.
- **Missing weeks are normal.** A week without a session has no plan, nothing is filled in afterwards, and nothing depends on every week having one.
- **Can be switched off.** Then the This week view is built on the fly, no week notes are kept, and there is no focus or budgets.
- **No time slots.** Things show up in the week, not at an hour.

### 4.7 Coming back after a break
When you've been away, or more than about 10 things are past their date, the catch-up doesn't show a list. It gives one calm line ("Welcome back. 3 things need you now; 14 others can wait.") and three choices:

| Choice | What happens |
|---|---|
| **Just what matters** (default) | Only things with consequences: overdue deadlines, repeats that carry over (bills), things someone else is waiting on, appointments and birthdays in the next few days. Everything else is set aside as "from your break" (marked on the item itself, so later sessions and reviews find it). |
| **Small batches** | The rest, 5 at a time, with quick answers: done, new date, drop, keep. Stop any time; the next session continues. |
| **Not now** | Only the urgent items, then carry on. |

What the system sorts by itself, because no decision is needed:
- past one-off appointments are archived and marked unconfirmed (you can say "that one didn't happen" later); repeating appointments and commitments just move on;
- repeats that lapse move to their next date;
- planned days that passed lapse: the task goes back to your open tasks without a planned day (a deadline, if any, stays);
- stalled flags pause for the length of the break;
- missed weeks have no plan, or the plan they had stays frozen; there are no reviews to catch up on.

Never sorted silently: deadlines, repeats that carry over, and anything someone else is waiting on. Every change is listed in the summary and can be undone. Items set aside come back a few at a time in later weekly reviews until they're sorted; you can also say "drop them all". The system never counts what you "missed" and never uses guilt language.

### 4.8 Do
- Views: Today, This week (the week plan), Active projects with their next step, Lists, Waiting for.
- Or ask: "I've got an hour and I'm at home, what can I do?" The agent filters by context and estimate.
- Done: tick it off or tell the agent. **A task line and its note always agree**, wherever you mark it done. **Marking a repeating task done always schedules the next one** (section 5.4).

### 4.9 Pausing, archiving and reviving
- **Archiving is a state first.** Done or dropped projects, areas that end, finished task notes, past one-off appointments and stopped repeats get that state; moving them into the archive just keeps the active folders tidy. Lookups, views and reviews go by state.
- **Nothing open disappears with an archive.** Before a project is marked done or dropped, or an area ends, the agent lists what's still open and asks what happens to each: tasks and waiting-fors are done, dropped along with it, or moved to another project or area; future appointments are kept (moving to the relevant area) or cancelled; commitments and repeats are stopped or moved. For a dropped project, "drop everything open" is the suggested default, and the agent says what that includes; for a done project, any leftover is a question.
- **Dropped with the project:** what was dropped along with a project is marked as such, and the project's Log lists it ("2026-10-12 Dropped. Dropped with it: Buy the domain, Build the site, Ask Sam for photos").
- **Out of active tracking:** the week plan, Today, the catch-up, reviews and lookups skip the archive, unless you ask about the past. If something new turns out to be about an archived project, the agent asks whether to revive it or file it there as reference.
- **Pausing** is not archiving: a paused project stays where it is and leaves planning (week plan, Today), but its deadlines and chase dates still come up in the catch-up.
- **Reviving:** the project moves back, becomes active, and its Log gets a line ("2027-01-10 Revived: planning a second trip"). The agent offers to bring back only what was dropped with it: deadlines or planned days that passed in the meantime become questions, waiting-fors get a fresh chase date or a question, past appointments stay archived, and items moved elsewhere stay where they went. A project revived after being done simply reopens. Archiving it again moves it back to the same spot.
- **Finished task lines:** in an area, the weekly review turns them into Log entries ("2026-10-15 Called the plumber"); in a project, they stay ticked until the project is archived.

### 4.10 Judgment calls
- The catch-up runs every session, even when you came for something else (a few lines, silent when nothing needs you).
- No monthly or quarterly area review in the core; it can come later as an add-on.

---

## 5. The vault

This section says where things live and what each kind records, in plain words. The exact field names and value syntax are the implementation's choice; every vault documents its own (section 5.8). The implementation spec holds the reference format the author's implementation starts from.

### 5.1 Layout
The vault is one folder, called `second-brain` by default.

```
Inbox/                          waiting to be organized
Projects/
  Website for Sam/
    Website for Sam.md          project note; most tasks live here as lines
    Choose hosting for Sam's site.md   a task with its own note
Areas/
  Health/
    Health.md
    Dentist checkup.md          repeating task
    2026-11-14 Dentist.md       appointment
  Dance/
    Dance.md
    Dance class.md              repeating appointment
  Work/
    Work.md
    Work hours.md               commitment
  Home/
    Home.md
    Shopping list.md
    Fix the squeaky garden gate.md
People/
  People.md                     everyone you know, one line each
  Robin.md                      someone with their own note
  <your name>.md                your own facts (sizes, allergies, licence plate)
Conversations/
  2026/
    2026-10-12 Sam about the website.md
Resources/
  Recipes/
    Lasagne.md
Weeks/
  2026/
    2026-W42.md                 week plan
Logs/
  time/
    2026-10 time.md             Capacity add-on
Archive/                        mirrors the vault (section 4.9)
  Projects/
    Vacation Italy/
  Areas/
    Health/
      2026-03-02 Dentist.md     past appointment
  Inbox/
    2026/                       processed inbox items
_system/
  config.md
  rules.md
  types/                        one definition per kind
  addons/capacity/              the Capacity add-on's own types
```

File names in the layout follow the author's reference format (implementation spec). Plus the vault's entry point for agents and the system's routines and tools (section 6). Their names and locations are set by the implementation.

### 5.2 Conventions
1. **The folder is the parent.** A task, list, appointment or commitment lives in its project or area folder; moving it means moving the file. Every task, list, appointment and commitment lives in a project or an area.
2. **People and conversations get their own folders.** Both belong to several topics at once. Conversations are records: written once and never moved, not even when a project is archived.
3. **Outcomes go into the topic.** After a conversation, every project, area or task it touched gets an updated Now section and a Log line linking the conversation (other notes it's about get just the Log line); the conversation links back. You follow the topic; the conversation is the record.
4. **Every project and area is a folder** with a note of the same name inside, even a tiny project.
5. **Names make sense on their own.** "Book flights for Italy", not "Book flights". Names are unique across the whole vault, archive included; on a clash the agent adds a distinguishing word or year.
6. **Dated things start with the date:** inbox items, conversations, one-off appointments, week plans.
7. **Links are by name:** `[[Website for Sam]]`.
8. **Renames update every link**, in records too. Updating a link is not rewriting a record; neither is turning a person's name into a link when they get their own note.
9. **The archive mirrors the vault:** `Archive/Projects/<Name>/`, `Archive/Areas/<Area>/…`, so an item always has the same spot, however often it's revived and archived again. No year folders, except for processed inbox items (`Archive/Inbox/<year>/`). What moves when: section 4.9.
10. **Busy folders split by year:** conversations and week plans.
11. **Notes live in Resources, or next to what they belong to:** a hotel comparison sits in the vacation project's folder.
12. **Task lines stay simple.** A task line carries at most a deadline, a planned day or a waiting-for; anything more is a task with its own note (section 5.6).

### 5.3 What every note records
Its kind, the date it was created, and optionally tags.

### 5.4 Core kinds and what they record

**Inbox item** · `Inbox/`, name starts with date and time. Where it came from (chat, a note you dropped in, phone, email, a feed), when it arrived, and an open question if the agent has one. A note you drop in by hand needs none of this; the agent completes it.

**Area** · `Areas/<Area>/<Area>.md`. Optionally what "OK" looks like for this area; Now; Tasks (as lines); Log.

**Project** · `Projects/<Name>/<Name>.md`. Its state (active, paused, someday, done, dropped), the area it serves, an optional deadline, and when it was finished. Body: Goal, Now, Tasks (as lines), Log.

**Task** · a line in its project or area note, or its own note in that folder (section 5.6). Its state (open, waiting, someday, done, dropped) and optionally:
- a **deadline**, and a **lead time** that brings it up that long before the deadline;
- a **planned day**;
- a **repeat**: fixed date or from last time; for fixed-date repeats, whether a missed one **carries over** or **lapses**;
- an **estimate** and a **context** (from your list of contexts);
- who it's **waiting on** (a person or a name) and a **chase date**;
- when it was finished.

A task line can hold a deadline, a planned day and a waiting-for; the rest needs a note. A task note's body: Now, sub-tasks as plain checkboxes, Log.

Rules for tasks:
- Waiting always has a chase date; the agent sets one week out unless you say otherwise.
- A repeat always has a next date, and that date is its deadline (for overdue, the lead window and the catch-up).
- Completing a repeating task uses the day it actually happened (you can tell the agent later), adds a Log line naming which occurrence it closed, clears its planned day, and sets the next date (the task stays open): from that day for "from last time" repeats; for fixed-date repeats, the next occurrence. A missed occurrence that **carries over** stays due until it is done or you skip it; one that **lapses** simply moves to the next occurrence. A day a month doesn't have becomes that month's last day.
- When the agent creates a fixed-date repeat, it picks carry over or lapse by what's obvious (a bill carries over; bins lapse) and asks when unclear.
- A booked visit for a repeating task (the dentist) is an appointment; the repeat completes when the visit happens.
- Stopping a repeat means dropping the task.

**Appointment** · in its area or project folder; a one-off appointment's name starts with its date, a repeating one is named for what it is ("Dance class"). The date (for a repeating one: when it starts and how it repeats), optionally a time (a start, or a start and end) or a length, where, with whom, and whether to export it to a calendar (only on your word, later). A missed occurrence of a repeating appointment simply passes.

**Commitment** · in its area folder. Which days, optionally the times or a rough length, optionally a season it runs in (from, until), and whether to export it to a calendar (only on your word, later). The agent treats commitments as your baseline: it plans around them, shows them in the week plan and the daily briefing, and never reminds you of a missed one.

**Appointment or commitment?** Would you put it in a calendar? Then it's an appointment. If it's how your week normally runs, it's a commitment. The agent asks when it's unclear.

**List** · in its project or area folder. A heading per place, plain checkboxes. Ticked items can be removed any time; the weekly review clears them.

**Note** · in Resources or next to what it belongs to. Anything to keep that isn't a task.

**Person** · by default a line in `People/People.md`: their name (told apart when two people share one, e.g. "Sam (work)"), how you know them, and optionally a birthday (with or without the year) and small facts. A person gets their own note (`People/<Name>.md`, linked from their line) when there's enough to remember: several facts, or conversations you'll want to look back on. The agent decides, with the same goal as for tasks (section 5.6). A person note's body: who they are, things worth remembering as dated lines; conversations show up through backlinks. Everyone in your life who is mentioned by name (family, friends, colleagues, neighbours, the plumber you deal with; not authors or public figures) is added to the list, and the agent asks when it's unclear who is meant. A birthday comes back in its lead window (from 2 weeks before), which is when the gift task is created. Other dates to remember (an anniversary) are yearly repeating tasks with a lead time.

**Conversation** · `Conversations/<year>/`, name starts with the date. When it was, with whom (as named in the people list, a link once they have their own note; or someone unnamed), what it was about (any notes it touched; may be none), and where it came from (chat, transcript, notes). Body: light by default, whatever you said, even one line. Summary, discussion points and action points only for a transcript or notes; each action point links what it became.

**Week plan** · `Weeks/<year>/`, named for the week it plans. Your focus, your budgets (with Capacity), and an overview built from the items. See section 4.6.

**Config** · `_system/config.md`. Your contexts, which add-ons are on, your weekly review day, whether you want the daily briefing and week plans, your timezone, and which version of the system and format the vault uses. With Capacity: how many hours a day you have available, and on which days.

**Rules** · `_system/rules.md`. Confirmed rules, one per line, with the date you confirmed them. Permissions for outside actions under their own heading (section 6.5).

Every kind may have a Log.

### 5.5 Capacity add-on
How much time you have against how much you've planned. Entirely optional; budgeting and tracking are also optional within it.

**Available hours** · roughly how many hours a day you have to plan, and on which days (config).

**Budget** · how much time something gets this week, set in the week plan.

**Time log** · `Logs/time/`, one file per month, one line per entry: the date, how long, what it was for, optionally a note.

**Uncommitted hours:** your available hours a day times the days you count, minus commitments with a time or length and appointments that week (overlaps count once). A rough number, not a schedule: it still includes meals, chores and rest. Its job is a reality check ("you planned 14h of 30 uncommitted hours"), not a target. **Planned** = the week's budgets, plus estimates of tasks with a deadline or planned day that week that aren't inside something with a budget. **Tracked** = time log entries that week. Untracked time is shown as untracked, never nagged about.

### 5.6 How things change over time

Overwrite the current state, add to the history. Every version is kept anyway (the implementation saves versions), so rewriting state loses nothing.

| Content | How it changes |
|---|---|
| **State:** the note's properties plus a short **Now** section at the top (where it stands, the next step) | Rewritten; always current. The agent reads it first. |
| **History:** the **Log** section | One dated entry per change, newest first. Never rewritten. |
| **Records:** conversations, frozen week plans | Written once. |
| **Logs:** time log and other add-on logs | Only new lines are added. |
| **Reference:** notes | Edited freely. |

**When an update is too big:** a log entry that grows long (more than a few lines), or something that will be updated on its own (a comparison, a quote), becomes its own note in the same folder; the Log gets one line linking it. A task that needs several notes of its own, or takes weeks, becomes a project.

**Tasks: lines or notes.** The goal is that each task lives in one place, and that things stay together until splitting makes them easier to follow. This is a judgment the agent makes with that goal in mind, not a threshold:
- **Keep it a line** when it's quick to state. A line can carry a deadline, a planned day or a waiting-for (who, and when to chase). Its small updates go into the parent note's Log ("2026-10-12 Buy the domain: Sam prefers .nl").
- **Give it its own note** when it has substance: it repeats (it needs its repeat rule and a record of each time it was done), or it develops its own story (updates over time, sub-tasks, material like a quote or a comparison), so its updates would crowd the parent's Log.
- **When unsure, keep it together.** Splitting later is easy. The agent mentions a split in its summary; if you'd rather keep something together, it changes it, and your correction can become a rule.
- **Once a line becomes a note,** the line becomes a link to it, and the two always agree.

Task lines don't carry estimates; a budget, if any, covers them.

### 5.7 Example

Written in the author's reference format (implementation spec):

```
Areas/Home/Fix the squeaky garden gate.md
---
type: task
created: 2026-10-05
status: waiting
waiting_on: the joiner
chase: 2026-10-16
---
## Now
Joiner comes Thu 16 Oct. Nothing to do until then.

## Log
- 2026-10-12 Joiner booked for Thu 16 Oct. [[2026-10-12 The joiner about the gate]]
  Quote: [[Joiner quote for the gate]]
- 2026-10-08 Oiling the hinges didn't help. The sag is at the post, probably the latch.
- 2026-10-05 Dragging on the ground since the weekend. Tightening the hinges changed nothing.
```

### 5.8 The vault describes itself
- Each kind has a type definition in `_system/types/`: its folder, naming, exact fields, their formats or allowed values, which are required (also "required when", e.g. a chase date when waiting), defaults, and a template. The agent reads these, the check enforces them, and you can open them in any markdown reader. This is how any agent can work in any vault, whatever field names its implementation chose.
- Core type definitions belong to the system's version: written when a vault is created and changed only by a format change you approved (section 6.4). You don't edit them.
- An add-on is a folder in `_system/addons/<name>/` with its own type definitions, plus the routines it adds (section 6.2). It may add new kinds and optional fields to core kinds and config (Capacity adds budgets and available hours). Switching it on is one line in config. When it's switched off, its notes and fields stay valid; they just aren't used.
- Fields no type defines are allowed (your own); the agent leaves them alone.

### 5.9 The check
The check tool (section 6.3) verifies that:
- every note has a known kind and its required properties (a note dropped in the inbox gets these when it's organized);
- values are valid;
- files are in the right folder for their kind, and dated files start with their date;
- no two files share a name;
- there are no broken links;
- conversation links go both ways;
- task lines and their notes agree;
- task lines carry only what a line may carry, written in the vault's format.

It only reports. The agent fixes mechanical problems (a value's format, a misplaced file with an obvious parent). Anything that would change meaning becomes a question and stays in the catch-up until it's resolved. Exactly which files it covers and how is part of the format (implementation spec).

---

## 6. The agent and memory

### 6.1 A session
1. **Starts at the vault's entry point:** one file that explains the vault to any agent: what it is, where things are, the boundaries, and that every session starts with the catch-up.
2. **Reads** the config, the rules and the type definitions, and agent memory when it's on.
3. **Does the work** with a routine: the catch-up first, then whatever you asked.
4. **Finishes each batch of changes** with the check, a saved version you can undo, and a summary of what changed. When memory is on, it also saves what it learned that you haven't confirmed yet.

### 6.2 Routines
| Routine | Does |
|---|---|
| catch-up | Start of every session (section 4.4); builds and freezes week plans (4.6). |
| return | Coming back after a break (section 4.7), started by the catch-up. |
| organize | Processes the inbox (section 4.2). |
| conversation | Saves a conversation and everything that comes out of it (section 4.3). |
| daily | The optional morning briefing. |
| weekly | The optional weekly review, full and short. |
| setup | Creates a new vault; switches add-ons on and off. |
| log-time | Added by the Capacity add-on. |

- **Started by:** your request; the start of a session (catch-up, and return when you've been away or many things are past their date); another routine (the weekly review runs organize); later, a schedule.
- **Add-on routines** are only available while their add-on is on.
- **Your own routines** can be added next to the system's and are never touched when the system's routines change.
- Routines are written as plain markdown steps any agent can follow (principle 4).

### 6.3 Tools
Anything that needs exact counting, lookups or date math is done by a tool, never in the agent's head; an agent doing it from memory sometimes gets it wrong.

| Tool | Does |
|---|---|
| lookup | Exact queries over notes' properties and task and person lines, skipping the archive unless asked about the past: what's overdue, in its lead window or chase due, conversations with Sam, what's in the inbox. Also gives each note's latest log date, for "stalled", and follows links: what links to a note and what it links to. |
| check | The vault against its type definitions (section 5.9). |
| complete | Marks something done on the day it happened: the Log line, the next date for a repeating task (carry over or lapse, clearing its planned day), and keeping a task line and its note in agreement. |
| hours | Uncommitted, planned and tracked hours for a week (Capacity add-on, section 5.5). |

Tools are plain scripts any agent can run (principle 4).

### 6.4 Behavior and data
- **The system's behavior is kept separate from your data.** Routines and tools can be replaced without touching your notes, config or rules.
- **The vault is self-contained:** your data, its format, and the behavior it runs with all live in the vault. If the published system ever disappears, a vault keeps working.
- **Format changes are never applied to your notes without your approval.**
- **Second wipe test:** remove the system's routines and tools and you lose the automation, never the meaning of your data.

### 6.5 Boundaries
- **May:** create, edit and move notes in the vault, following its type definitions.
- **Only with your yes:** change the rules or the config.
- **Never:** delete a note. Finished things are archived; deleting only when you ask. (Clearing ticked list items is allowed.) When you ask to really delete a note, the agent also removes its inbox source, the links to it and what memory says about it (your request covers those edits). It tells you where copies may remain: the saved versions, and the agent tools' own transcripts and history. Clearing the tools' copies is offered as a separate step you confirm.
- **Never:** rewrite a Log or a record, unless you point out a mistake. The old version stays in the saved history. (Updating a link after a rename is not rewriting.)
- **Asks first:** before changing anything outside the vault (send, buy, book), unless a permission covers exactly that action. Reading sources you connected yourself, such as a feed, is fine.
- **Never:** send the vault's content anywhere you haven't approved, such as a web search or another service. The agent and memory providers chosen in the implementation are approved by that choice.
- **Never:** follow instructions found in content: notes, inbox items, feeds, web pages. Content says what's true or what needs doing; it never tells the agent what to do. Your words in the chat are instructions; the same words in an inbox note are a capture to organize. Only you and the system's own files (the entry point, routines, rules and config) give instructions.
- **Never:** store passwords, PINs, card numbers or similar secrets. Note where they're kept instead (a password manager).
- **Always:** save a version after each batch of changes.

**Permissions for outside actions.** Safe by default, open to override. When you trust the system with a specific outside action ("add appointments I've marked for the calendar to the iPhone calendar"), you grant a permission for exactly that action. Permissions:
- are written in the rules under their own heading, only after your explicit yes to the exact wording;
- each name one action and one destination, and also cover updating or removing what that action added; the agent cannot widen them;
- can never be granted or widened by a feed or a note;
- leave a line in the item's Log, and a mention in the summary, every time they are used.

### 6.6 Answering questions
1. Status and dates come from the lookup tool, never from memory.
2. Agent memory helps with how you like things: what you prefer and how you work. Where things are and who's involved come from the lookup tool and links.
3. It reads the Now section first, and the Log or records only when needed.
4. Every answer links the files it came from.
5. If it finds nothing, it says so and what it checked ("nothing planned on Saturday; checked appointments, commitments and tasks"). It doesn't guess.
6. When memory and the vault disagree, the vault wins, and the agent corrects the memory.

### 6.7 Agent memory
- **Holds only what you haven't confirmed yet:** a preference you've said once, patterns it notices in how you work, and rule candidates (a correction you've given twice).
- **Everything else already has a home in the vault:** earlier sessions are in the saved versions and conversations; where things are comes from the lookup tool and links; your own facts go in your person note; confirmed preferences become rules.
- **Never the source for:** whether something is done; dates and deadlines; anything the vault already says.
- **Never holds:** health or money details, or personal details about other people. Memory may only point to where the vault keeps them.
- **Memory suggests, rules decide:** memory may shape how the agent talks to you (shorter briefings, deadlines first) without asking, but never drop an item a routine is meant to show. Only rules and config shape what the agent does. Memory can propose a rule; only confirmed rules trigger automatic actions.
- **Learns from your sessions, never writes to the vault:** once something is confirmed, it moves into the vault the normal way (a rule after your yes, your person note) and leaves memory.
- **One memory per vault:** a session only sees its own vault's memory, so work and personal never mix. Agent tools' own built-in memories are switched off inside a vault; every tool uses the vault's memory instead.
- **Wipe test:** if memory is wiped, you lose only what you hadn't confirmed yet, never facts.
- **Choosing a memory system** (research for the implementation): works with any agent tool; never writes to the vault; forgets what's deleted from the vault; newer facts replace older ones; one memory per vault; runs locally or with a provider acceptable for private data; acceptable cost per use; can be wiped safely.

### 6.8 Rules
- **Where they come from:** you give the same answer more than once (within a session, or across sessions when memory is on), or you say "always do this".
- **Confirmed:** a rule is added, changed or removed only after your yes to its exact wording.
- **Corrections:** when you correct something a rule did, the agent proposes changing that rule.
- **Conflicts:** the more specific rule wins; when that's unclear, the agent asks.
- **Limits:** rules can never override the "Never" list in section 6.5.

### 6.9 Judgment calls
- Date math goes through a tool.
- Memory never triggers anything on its own; it may only change how the agent talks to you.
- The agent never deletes a note unless you ask.
- Outside actions ask by default; you can open specific ones up with explicit, narrow permissions.
- The system's behavior lives in the vault, not in one agent tool.

---

## 7. Decisions that replaced earlier proposals
- **No size field** (S/M/L): an optional estimate covers it.
- **Story points and sprints dropped:** capacity comes from real hours (Capacity add-on) and the week plan.
- **Conversations:** first proposed as an add-on, then stored inside their main topic; settled as core, in one `Conversations/` folder of records with outcomes written into each topic. The work exception for client data was dropped.
- **Principle 3:** "the whole system can be run by hand" was considered and rejected for an AI-first system; settled as "readable and fixable by hand".
- **Routines:** first proposed as plain files in `_system/routines/`; settled as skills installed in the vault (implementation spec).
- **Updating and the skills details** moved out of the system into the implementation. The system keeps one promise: format changes need your approval.
- **The exact file format** (field names, value syntax, file-name patterns, check rules) moved to the implementation spec. The system keeps what each kind records, in plain words, and requires every vault to document its own format.
- **Waking hours:** a clock range, then `awake: 16h`; settled as available hours per day plus which days count, so a work vault works too. The result is called uncommitted hours, not free time.
- **Weekly review note → week plan:** builds itself each week, planning optional, frozen at week end; the weekly review became optional.
- **Budgets:** first a field on projects and areas; settled as part of the week plan.
- **Archive:** sorting by year replaced by a mirror of the vault, so revived and re-archived items keep one spot; nothing open disappears with an archive; what was dropped with a project is offered back when it's revived.
- **People:** a note per person replaced by a line in the people list by default, with a note when there's enough to remember; everyone mentioned by name is added.
- **Appointments and commitments:** both moved from the Time add-on into the core, as separate kinds ("would you put it in a calendar?"); appointments can repeat. The add-on kept only capacity and was renamed **Capacity**.
- **Missed repeats:** "jump to the next future date" replaced by carry over or lapse, per repeat.
- **Task lines:** "a line never carries metadata" (every dated task a note) was replaced by lines that may carry a deadline, a planned day or a waiting-for; a task gets its own note when it repeats or develops its own story, decided by the agent with the goal in mind. "Steps" are now called tasks.
- **Unfinished chats:** saving every unanswered question to the inbox was rejected; only explicit captures the agent can't place go there.
- **Names:** the vault is called `second-brain` and the skills use the prefix `brain`: clear and obvious over distinctive (Tend, Cairn and Steward were considered).
- **Agent memory:** first tied to Hindsight, then chosen after research (2026-10-13). Memory holds only what you haven't confirmed yet, learned from sessions; it no longer learns from the vault or holds history and "where things are". A memory service that extracts facts from the vault was rejected: it copies status and dates into memory, sends every note to a model and adds a server per vault. Agent tools' own memories are off inside vaults. Principle 2 and section 6.7 changed to match.
- **Goals over thresholds** (principle 13) added: numbers are defaults the agent reasons around, except the exact time words.
- **Outside actions:** first proposed as "always ask, a rule can never automate this"; settled as ask by default, with explicit, narrow permissions the user can grant.

---

## 8. Implementation
The author's implementation is its own document: [Implementation](https://alexsendula.github.io/second-brain/implementation/). It implements this system and never changes it. A change to this system needs the author's explicit yes and is recorded in section 7.

## 9. Open questions
None at the system level. Questions about running the system are in the implementation spec.

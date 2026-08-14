# faculty-tools Repo

Sarah's own teaching tools, served from GitHub Pages at `skarlis3.github.io/faculty-tools/`. Not a class website and not student-facing.

## Read these first, before doing any work in this repo

The rules governing this work are deliberately not kept in this repo, because this repo is public. Nothing here repeats them, so skipping these files means working without them. **Read each one in full — do not skim for the sections that look relevant.**

1. `~/MEGA/work-with-claude-code/CLAUDE.md` — how Sarah wants the work done.
2. `~/MEGA/work-with-claude-code/classes/CLAUDE.md` — shared class rules. Relevant here because the podium app reads the class calendars, and the calendar conventions are documented there.

Everything below this point is about this repo's own files, and belongs here.

## The podium app: `podium/podium.html` is the live one

This is the screen Sarah puts up at the classroom podium. It shows the day's agenda and pulls that day's events from the class Google Calendar.

- **Live at** `https://skarlis3.github.io/faculty-tools/podium/podium.html`, linked from the hub page in the `skarlis` repo at `instructor-resources.html` under "Daily Welcome Screen."
- **It is a plain web page.** HTML, CSS and JavaScript in one file, opened in a browser. Nothing to install and nothing to run.
- **It reads calendars through the Google Calendar API.** It used to go through a CORS proxy; that was replaced on 2026-02-08.

**`podium/podium.py` and `podium/podium_config.py` are the retired Streamlit version.** They still sit in the same folder and still contain their own copy of the calendar list, so a search for a calendar ID returns hits in files nobody runs. Before editing anything podium-related, check you are in `podium.html`.

## The calendar list

`CLASS_CALENDARS` near the top of the script block in `podium/podium.html` maps a display name to a Google Calendar ID. Adding or renaming a section means editing that object.

**The IDs outlive the labels.** A calendar's name in Google can be wrong while its ID stays correct, so the label in this file is not evidence of which section a calendar holds. `~/MEGA/work-with-claude-code/classes/ENGL-1181/CLAUDE.md` records which calendar belongs to which section for that course; check there rather than trusting a label.

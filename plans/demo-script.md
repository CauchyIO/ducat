# Demo script

An outline, not a finished script. The Demo phase fleshes it out; this fixes the shape so nobody
rebuilds it from scratch.

**One sentence:** it asks before it looks, shows its evidence, and will not act on its own.

Everything shown is a **replay of a real session**, never a simulation. The skill's whole claim is
that it does not invent numbers; a demo built on invented ones contradicts the pitch the moment
anyone looks closely — and audiences are good at spotting a canned demo.

## The four beats

**1. What happens without it.** Someone types "optimize our Databricks costs" into an ordinary
assistant. It goes rummaging — around twenty queries across every workspace, every job, months of
billing — and returns a confident report on what is wrong with everything. Like asking a consultant
to look at cloud spend and finding them hours later having read every file in the building, with
opinions about departments nobody mentioned. The report is good. Nobody asked for it.

**2. The same question, with the skill.** It stops and asks what to look at. It offers a survey to
help choose, says that running it costs a little money, and waits. Given a yes, it returns a
shortlist — the biggest costs, and which would you like assessed? Candidates, not verdicts.

**3. What it produces.** One scope is chosen. Out comes a page: what this costs, the evidence, what
changing it would save, what you would give up, how confident it is and why — and what it cannot
tell you, because it does not have the invoice.

**4. The last move.** "Great, go and change it." It declines. Here are the exact steps for whoever
does have that access, but it does not touch anything.

Roughly ten minutes.

## Two audiences, two readiness points

**The team** cares about beats 2 and 3: how an agent is made to show its working, and how it knows
what it is not allowed to claim. That is reusable in anything else built here. Ready once a real
assessment exists; real names and real numbers are fine in the room.

**A client** cares about beats 1 and 4: it will not rummage through their data uninvited, and it
will not change anything. Beat 3 then proves it is still worth having. This version needs the
identifiers anonymised — the recordings carry internal cost data — and the strongest form is not a
replay at all but a short assessment against the client's own estate, which needs the onboarding
work first.

## Practical constraints

- Replay recordings; do not run live. A cold warehouse is a minute of silence and a throttled cost
  API is an error on screen.
- Scrub every transcript before it leaves the machine. They capture whole sessions, credentials
  included.
- Capture the feedback as issues on the day. Demo criticism is the most useful a project gets and it
  evaporates by the next morning.

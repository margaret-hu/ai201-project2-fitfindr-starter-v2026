# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three 
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** `search_listings` scores matches by plain keyword overlap 
with the description, not meaning. Some phrasings share no keywords with a 
listing that actually fits, so a real match can score zero and get dropped.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling 
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** This path doesn't depend on keyword luck — it's the 
branch itself. An empty results list is a plain `if`, not a judgment call, so 
there's no fuzziness left to excuse a miss.

---

## 3. Something about state

For 5 different matching queries, each selecting a different item, the item 
named in the `search_listings` trace step matches the item named in the 
following `suggest_outfit` trace step — in 5 of 5 tries.

**Why this target:** Varying the item rules out a cached or hardcoded item 
passing by coincidence. 5 of 5 because passing a value from 
`session["selected_item"]` into a tool call is deterministic plumbing, not 
model generation — any miss is a real bug, not noise.

---

## 4. Something about the fit card

For 5 different items, the fit card names the item's exact price — in at least 
4 of 5 tries.

**Why this target:** `create_fit_card` calls the model, and asking it to 
mention a number in a caption doesn't guarantee it will — it can round, omit, 
or describe the price in words instead. 4 of 5 catches a card that routinely 
drops the price while leaving room for the same kind of occasional miss 
criterion 1 already tolerates.

---

## 5. Your choice

Given an invalid API key, the agent catches `ModelUnavailable` and returns a 
session with `session["error"]` set to a readable message — instead of letting 
the exception crash the run — in 5 of 5 tries.

**Why this target:** Catching a specific exception type is a fixed branch, not 
model generation — the same bad key should fail the same safe way every time. 
5 of 5 because any crash reaching the user here is a real bug, not variance to
tolerate.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

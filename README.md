# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a second-hand shopping assistant. A user describes what they want, such as "vintage graphic tee under $30, size M", and the agent finds the best-matching resale listing. It then suggests one or two outfits around that item, using the user's saved wardrobe if they have one, and writes a short social-media caption with the price and platform. If nothing matches, it stops and says what to change in the search.



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the local clothing catalogue by description keywords, with optional size and maximum-price filters. A listing counts as a match when at least one word from the search query appears, case-insensitively, in its `title`, `description`, or `style_tags`; the price limit is inclusive.
- **Inputs:** `description` (str), `size` (str or None — matched by whole token, case-insensitively, e.g. "m" matches "S/M" but not "us 9"), `max_price` (float or None).
- **Returns:** A list of matching listing dictionaries, capped at `config.SEARCH_RESULT_LIMIT` (10), ranked by score (the count of distinct query words matched) highest first, then by lower price; each includes fields such as `title`, `price`, `size`, and `platform`.
- **When it has nothing:** Returns an empty list [], not None or an exception.

### `suggest_outfit`

- **What it does:** Suggests one or two outfits built around a selected listing, using items from the user’s wardrobe when available.
- **Inputs:** `new_item` (dict) a listing, `wardrobe` (dict) with an items list.
- **Returns:** A non-empty str with one or two outfit suggestions; when the wardrobe has items, each suggestion names specific pieces from `wardrobe['items']` verbatim (using each item's `name` field as stored, not a paraphrase).
- **When it has nothing:** Still returns general outfit ideas and says they are general because no wardrobe is saved.

### `create_fit_card`

- **What it does:** Writes a short social-media-style caption about the selected second-hand find and how it could be worn.
- **Inputs:** `outfit` (str), `new_item` (dict) a listing.
- **Returns:** A str of two to four sentences that includes the price written with digits and the selling platform.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a helpful fallback message instead of calling the model or raising an exception.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message telling the user what to change and return the session without calling `suggest_outfit`. Otherwise take the first result and continue to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::_parse_query`. It pulls the price ("under $30") and size ("size M") out of the query, and what's left becomes the description.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. `wardrobe` is set at the start, and `error` is set only when the search is empty.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit Combination:**
            Pair the Y2K butterfly baby tee with the baggy straight-leg dark wash jeans, chunky white sneakers, and the black crossbody bag.

            **Why it works & how to style it:**
            This look plays on the quintessential Y2K proportion-play by contrasting the fitted, cropped silhouette of the baby tee with the relaxed, low-slung feel of the baggy jeans. To complete the outfit, throw the black cropped zip hoodie on top for easy layering and let the butterfly print pop against the dark indigo denim.

  Fit card: Found the absolute cutest Y2K butterfly baby tee on depop for just $18 and I am never taking it off. I've been styling it with my baggiest dark wash jeans and chunky sneakers for that ultimate 2000s proportion play. Throwing a black zip hoodie over top makes it the easiest everyday fit.

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

The full search result is long, so this one prints only titles and prices.

```
$ python -c "from tools import search_listings; print([(r['title'], r['price']) for r in search_listings('graphic tee', max_price=30)])"
[('Y2K Baby Tee — Butterfly Print', 18.0), ('Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('Mesh Long-Sleeve Top — Black', 15.0), ('Vintage Band Tee — Faded Grey', 19.0), ('Low-Rise Cargo Pants — Khaki', 27.0), ('Vintage Graphic Hoodie — Faded Black', 26.0)]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit Combination:**
Pair the vintage Levi's 501 jeans with the white ribbed tank top, layered under the vintage black denim jacket, and finish with the black combat boots and black crossbody bag. 

**Why it works and how to styling it:**
This look leans into a classic, grunge-inspired Americana aesthetic by pairing medium-wash denim with monochrome black layers. Tucking in the white tank defines the waist against the straight-leg cut of the jeans, while rolling the jacket sleeves and wearing chunky boots adds an effortlessly cool, textured edge.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Found my holy grail vintage Levi's 501s and I'm obsessed with this medium wash. They were only $38, which feels like an absolute steal for how perfectly worn-in they are. Just posted them on depop because they're a bit too big, but they'd look so good styled low-slung with crisp white sneakers for that effortless 90s vibe.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude whether `search_listings` was efficient in memory and runtime.
- *What came back:* It found that `_size_matches` re-tokenized the fixed `size` argument on every listing instead of once.
- *What I changed:* I hoisted `size_tokens = _tokenize(size)` out of the loop, computed once instead of per-listing.

**Moment 2**

- *What I asked for:* I asked Claude whether the `suggest_outfit` prompt wording could be improved further.
- *What came back:* It found no better wording, but caught a bug: each wardrobe item's `colors` is a list, and my summary line put it straight into the f-string, so the prompt would have shown `['black']` instead of `black`.
- *What I changed:* I joined the list with `', '.join(...)` before interpolating, matching how the new item's colors were already formatted in the same function.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

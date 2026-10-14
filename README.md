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
- **Served over MCP:** Registered on the MCP server in `mcp_server.py`, alongside `search_listings`, and called from `agent.py::run_agent` through `call_tool`.

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

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. `wardrobe` is set at the start, and `error` is set when the search is empty or a model or MCP call fails.

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
| 1. A matching query completes all three tools | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. State: the item searched is the item passed to `suggest_outfit` (Try N = item N) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card names the item's exact price (Try N = item N) | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Invalid API key is caught as `ModelUnavailable` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Rows 3 and 4: Try N is item N's Try 1 (Y2K Baby Tee, 90s Track Jacket, 90s
Silk Slip Dress, Platform Sneakers, Denim Jacket). I chose Try 1 before
reading any results.

**Criterion 1, Try 1**, from `run_eval.py::main` calling `agent.py::run_agent`, `scenarios.py` scenario "matching query completes" (`results/run_2026-10-09_2302_before.md` lines 42-80):

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:

**Outfit Combination: Y2K Casual Streetwear**

Pair the Y2K butterfly baby tee with the baggy dark-wash straight-leg jeans and chunky white sneakers, then layer the black cropped zip hoodie on top. This combination works because the slim fit of the baby tee contrasts perfectly with the voluminous, relaxed silhouette of the baggy jeans, while the black hoodie frames the pastel butterfly print and ties the look together with classic Y2K street style.

Fit card:

Still pinching myself over this $18 Y2K butterfly baby tee I just scored on depop. I'm obsessed with how the pastel print pops when you throw a cropped black zip hoodie over it. Paired with some baggy dark-wash jeans and chunky sneakers, it is literally the ultimate off-duty Y2K streetwear fit.

Trace:

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  first search result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: **Outfit Combination: Y2K Casual Streetwear**  Pair the Y2K butterfly baby tee with the baggy dark-wash straig…
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print
      out: Still pinching myself over this $18 Y2K butterfly baby tee I just scored on depop. I'm obsessed with how the p…
```

**Criterion 2, Try 1**, from `run_eval.py::main` calling `agent.py::run_agent`, `scenarios.py` scenario "impossible query stops early" (`results/run_2026-10-09_2302_before.md` lines 256-273):

```
- stopped early: yes — Nothing matched "designer ballgown". Try broader keywords first (e.g. "jacket" instead of a specific style). Your $5 budget and size xxs may also be ruling things out, so loosen one at a time to see which.
- selected_item: (none)
- search_results: 0

Trace:

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch: no results
      →    stopping before suggest_outfit
```

**Criterion 3, Try 1 (item 1)**, from `run_eval.py::main` calling `agent.py::run_agent`, `scenarios.py` scenario "item 1: Y2K Baby Tee" (`results/run_2026-10-09_2302_before.md` lines 565-605):

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:

**Outfit 1: Casual Y2K Streetwear**
Pair the Y2K Butterfly Baby Tee with the baggy straight-leg jeans, vintage black denim jacket, and chunky white sneakers. This combination works because the slim fit of the baby tee contrasts perfectly with the voluminous, relaxed denim for an authentic turn-of-the-millennium silhouette. Layer the black denim jacket loosely over the shoulders and let the bright butterfly print pop against the dark wash.

**Outfit 2: Edgy Contrast**
Style the Y2K Butterfly Baby Tee alongside the wide-leg khaki trousers, black combat boots, and the black crossbody bag. This works by blending the hyper-feminine, playful energy of the butterfly print with the utilitarian, rugged edge of the khaki trousers and combat boots. Cinch the trousers with a cool belt and accessorize with the crossbody bag to tie the effortless, grunge-leaning look together.

Trace:

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  first search result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: **Outfit 1: Casual Y2K Streetwear** Pair the Y2K Butterfly Baby Tee with the baggy straight-leg jeans, vintage…
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print
      out: Obsessed with this Y2K butterfly baby tee I just scored for only $18. I'm thinking it'll look so good either d…
```

**Criterion 4, Try 1 (item 1)**, from `agent.py::run_agent` calling `create_fit_card`, `scenarios.py` scenario "item 1: Y2K Baby Tee" (`results/run_2026-10-09_2302_before.md` lines 581-585, same try as criterion 3):

```
Fit card:

Obsessed with this Y2K butterfly baby tee I just scored for only $18. I'm thinking it'll look so good either dressed down with baggy denim and sneakers for that ultimate Y2K streetwear vibe, or toughened up with combat boots and khakis for a cool grunge contrast. Going to list it on my Depop later today so grab it before I change my mind!
```

**Criterion 5, Try 1**, from `run_eval.py::main` calling `agent.py::run_agent`, `scenarios.py` scenario "invalid API key is caught" (`results/run_2026-10-09_2302_before.md` lines 1638-1658):

```
- stopped early: yes — The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Trace:

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  first search result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] branch: ModelUnavailable
      →    stopping, error set on session
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
| 1 | A matching query completes all three tools | ≥ 4 of 5 | MET (5/5) | All five tries ended with `stopped early: no`, an outfit and a fit card. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All five tries ended at `branch: no results` with 0 results and no outfit or fit card. |
| 3 | The item searched is the item passed to `suggest_outfit` | 5 of 5 | MET (5/5) | For each of the five items, the selected item was the one in the `suggest_outfit` and `create_fit_card` steps. |
| 4 | Fit card names the item's exact price | ≥ 4 of 5 | MET (5/5) | Each card contained the item's price (e.g. "$18" for an $18.0 listing). |
| 5 | Invalid API key is caught as `ModelUnavailable` | 5 of 5 | MET (5/5) | All five tries stopped at `branch: ModelUnavailable` with the readable key message, no crash. |

**Diagnoses**

No criterion missed, so there is nothing to place in a tool, the loop's branch,
the session, or the model's output, and no pattern across rows.

**Were my targets too low?** Yes, for criterion 4. It is the only criterion
that depends on the model's wording, and a target of 4 of 5 left room for a
miss that never came. I'd tighten it to 5 of 5, with the card required to show
the price as `$<price>` and no other dollar figure (added to `criteria.md`).
Criteria 2, 3 and 5 test fixed code paths, so 5 of 5 was right. Criterion 1
allowed one miss and had none.

I re-scored all 25 Before cards (5 items × 5 tries) against the tightened
criterion 4, and all passed, so it wouldn't have changed this run. Limits:
every listing in `data/listings.json` has a whole-dollar price, so cents
formatting is untested, and five items is a small sample.

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
$ python app.py ask 'vintage graphic tee under $30'

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select_item
      in:  first search result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: **Outfit Combination:** Pair the Y2K butterfly baby tee with the baggy straight-leg dark wash jeans, chunky wh…
[5] create_fit_card (via MCP)
      in:  Y2K Baby Tee — Butterfly Print
      out: Found the absolute cutest Y2K butterfly baby tee on depop for just $18 and I am never taking it off. I've been…
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5'

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch: no results
      →    stopping before suggest_outfit
```

The empty trace is three steps against five, and it ends at the branch, so
`suggest_outfit` and `create_fit_card` never run.

**On the MCP move:** `search_listings` and `create_fit_card` are registered on
the MCP server (`mcp_server.py`) with typed inputs and descriptions. `run_agent`
calls them through `call_tool` (`mcp_client.py`), which starts the server over
stdio for each call, instead of importing them from `tools.py`. Only
`suggest_outfit` is still a direct call. Step 2 in both traces and step 5 in the
happy path are MCP calls.

Behavior is unchanged for `search_listings`: for `vintage graphic tee`, max $30,
the direct and MCP calls returned identical lists (10 results each), and the
empty query still comes back as `[]`, so the branch works as before. The
10-result cap lives in the tool itself, not in MCP. For `create_fit_card`, an
empty or whitespace `outfit` still returns the fallback message. One
difference: a model failure inside the server reaches the agent as `MCPError`,
not `ModelUnavailable`, so `run_agent` catches both, sets `session["error"]` and
labels the trace step with whichever it caught.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** No code change, since every criterion was already MET in Before. I tightened criterion 4 to require `$<price>` and no other dollar figure, 5 of 5 (see `criteria.md`), and re-ran the eval unchanged.

**Which failure it was meant to fix:** None. My diagnosis found no miss, only that criterion 4 (≥ 4 of 5) was too loose for the one model-dependent check, so a miss could have slipped through. The tighter version can fail where the old one couldn't.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item searched is the item passed to `suggest_outfit` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card shows `$<price>` and no other dollar figure (tightened) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Invalid API key is caught as `ModelUnavailable` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Evidence, from `results/run_2026-10-13_0145_after.md`:

- Criteria 3 and 4 use five items, five tries each: Y2K Baby Tee ($18), 90s Track Jacket ($45), 90s Silk Slip Dress ($30), Platform Sneakers ($48), Denim Jacket ($42). In all 25 fit cards the only dollar figure was the item's own price (`$18`, `$45`, `$30`, `$48`, `$42`), with no second figure. In every try the item named in the `search_listings` step was the one in `suggest_outfit`.
- Criterion 2: every try ended at `branch: no results` after three steps, with no outfit or fit card.
- Criterion 5: every try ended at `branch: ModelUnavailable` after four steps, with the readable key message.

**Did it help, and how do I know:** No, and it couldn't have, since the agent didn't change. The tighter criterion 4 passed 25 of 25, so the Before result wasn't a loose-target fluke. I counted dollar figures per card with a regex. Limits: whole-dollar prices only, five items, temperature 0.9.

### The Second Improvement

**What I changed:** A bad key inside the MCP `create_fit_card` server came back as `MCPError: unhandled errors in a TaskGroup`, plus a hint to check that the server runs. The message never named the key. `mcp_client.py::call_tool` now unwraps the exception group and raises the server's own error. I added a scenario with a good key for `suggest_outfit` and a bad one in the server, and extended criterion 5 to both paths, 5 of 5 each (see `criteria.md`).

**Which failure it was meant to fix:** The "Model failure over MCP" gap in What's Still Broken, which I reproduced by hand first.

### Run Log — After (second change)

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | ≥ 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item searched is the item passed to `suggest_outfit` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card shows `$<price>` and no other dollar figure | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5a. Bad key in `suggest_outfit` is caught, cause named | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5b. Bad key inside the MCP server is caught, cause named (new) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Evidence, from `results/run_2026-10-13_2048_after2.md`: all ten criterion 5 tries set `session["error"]` to a message containing "The model rejected your API key", and none contained "TaskGroup". The 5b tries stopped at `branch: MCPError` after `suggest_outfit` succeeded, with no fit card. The other rows are scored the same way as the first After log.

**Did it help, and how do I know:** It fixed the message and broke nothing: criteria 1 to 5a match the previous log, and 5b passes 5 of 5. 5b wasn't in the previous log, so it has no before-row. Its before-evidence is one manual run showing "unhandled errors in a TaskGroup". Limits: one failure type (a bad key), five tries, and criterion 3 is scored by matching the item title across trace steps.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is missed, but the criteria leave four gaps:

- **Keyword search:** `search_listings` matches shared words, not meaning, and I only tested queries that share words with a listing. I'd try paraphrases ("retro band shirt") and add synonyms if they fail. Stopped: no run showed a miss.
- **Price with cents:** All listings are whole-dollar, so $24.50 is untested. I'd add such a listing and re-check. Stopped: the current data can't trigger it.
- **Invented details in fit cards:** Some claim things not in the input, e.g. "Going to list it on my Depop later today" (Before, item 1). I'd tell the prompt not to invent actions and add a criterion for it. Stopped: I found it after the criteria were written.
- **Model failure over MCP:** Fixed in the second pass (see The Improvement). Remaining gap: only a bad key was tested inside the server, not other model failures (rate limit, timeout), and `MCPError` still carries the server's "Error executing tool ..." prefix. Stopped: no run showed a miss.

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

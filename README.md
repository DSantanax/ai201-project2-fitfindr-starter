# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

### Tool 1: search_listings

**What it does:**

The agent will be given parsed information such as the string description of the user query, a letter string of common sizes of the item in question, and the max price in decimal if given. This function will query a list of dicts of clothing items from the wardrobe list and filter based on the size/price and return the top matched item of the top 3 matching items sorted by relevance found in the database based on the description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): This is the main item description of the query
- `size` (str): This is the optional sizing of the item from the query 
- `max_price` (float): This is the optional price range of the query, use this as an estimate or none if given.

**What it returns:**
The return will a list of dicts containing the top 3 items based on the relevance of the description with fields (id, title, description, category, style_tags (list), size condition, price (float), colors (list), brand, platform)

**What happens if it fails or returns nothing:**
If no listing is found, prompt the agent to recommend the user to try a different query or expand their query.

---

### Tool 2: suggest_outfit

**What it does:**
    Given the new item dict and the user's wardrobe as a list, ask the LLM to suggest outfits combinations for the user.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The dict of the item the user is interested in
- `wardrobe` (dict): A dict with an items list that contains the keys: id, name, category, colors, style_tags, and notes with their respective values. This can be empty.

**What it returns:**
     This function returns a string with outfit suggestions/combinations matching their new_item with their wardrobe.

**What happens if it fails or returns nothing:**
     If the user's wardrobe is empty recommend general stying advice and recommendations. Do not throw any errors or exceptions and do not return empty strings.

---

### Tool 3: create_fit_card

**What it does:**
    Create a short shareable outfit caption for the item found thrifting! This caption may be shared by the user online and with friends/family.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The recommended outfit description from the suggest_outfit output
- `new_item` (dict): The dict of the item that user is interested in

**What it returns:**
     A string of a few sentences that can be used as an Instagram/TikTok/Subreddit Outfit of the Day caption. Keep it personalized for the user and ensure to mention the brand, item name, price, and platform naturally.

**What happens if it fails or returns nothing:**
     If outfit is empty or missing, return a descriptive error message
     string — do NOT raise an exception during any failure.

---

---

## Interaction Walkthrough

**User query:** I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?

**Step 1 — Tool called:**

- Tool: search_listings
- Input: description of the query, size = None, max_price 30
- Why this tool: This tool was called because the user is looking to thrift a specific item.
- Output: Y2K Baby Tee — Butterfly Print
Price: $18.0 · Platform: depop
Brand: unbranded · Size: S/M
Condition: excellent · Colors: white, pink, purple. Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.

**Step 2 — Tool called:**

- Tool: suggest_outfit
- Input: the new item y2k baby tee dict, example wardrobe list
- Why this tool: This tool was called because an item was found and the user asked how to style it.
- Output: I'd be happy to help you style the Y2K Baby Tee — Butterfly Print. Here are two complete outfit combinations:
**Outfit 1: Casual Streetwear**
Pair the Y2K Baby Tee with the **Baggy straight-leg jeans** and **Chunky white sneakers**. The fitted crop length of the tee will create a nice contrast with the loose-fitting jeans, while the chunky sneakers will add a cool, streetwear touch. You can also add the **Black crossbody bag** to complete the look.
**Outfit 2: Earthy Chic**
Combine the Y2K Baby Tee with the **Wide-leg khaki trousers** and **Black combat boots**. The earthy tones of the trousers will complement the pastel colors of the butterfly print, creating a cute and laid-back look. The black combat boots will add an edgy touch, while the **Brown leather belt** can be added to define your waist.

**Step 3 — Tool called:**

- Tool: create_fit_card
- Input: outfit combinations string, new_item y2k baby tee
- Why this tool: This tool was called because the user asked for a style and outfit combinations were created. As part of the functionality it creates a shareable outfit caption.
- Output: I just scored this adorable Y2K Baby Tee — Butterfly Print on depop for $18.0 and I'm obsessed with how it adds a touch of whimsy to my casual streetwear look. Paired with my baggy straight-leg jeans and chunky white sneakers, this outfit is giving me major laid-back vibes with a cool, edgy twist. The white, pink, and purple butterfly print is so eye-catching and fun, and I love how it contrasts with my black crossbody bag.

**Final output to user:**

---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No results match the query | No listings matched your query. Try broadening your search — use fewer filters or a more general description. |
| `suggest_outfit` | Wardrobe is empty | I'm so excited to help you style this adorable Y2K baby tee. Since your wardrobe is currently empty, we can start from scratch and build a cohesive look around this piece. The butterfly print and pastel colors give off a sweet, playful vibe that's perfect for a cottagecore or vintage-inspired aesthetic. To complement this tee, consider pairing it with: 1. **High-waisted pants or skirts**: A flowy, high-waisted maxi skirt or some distressed high-waisted mom jeans would create a charming, laid-back look. 2. **Comfortable shorts**: ... (trimmed for brevity) Remember, the key to styling this tee is to have fun and be playful! Experiment with different combinations, and don't be afraid to add your own personal touches to create a look that's uniquely yours. |
| `create_fit_card` | Outfit input is missing or incomplete | No outfit suggestion was available — try expanding your wardrobe or refining your search to get a fit card. |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**
The plan helped me visualize the architecture before implementation. This helped when creating the individual functions such as search_listings when specifying the input/output and description. It is also useful for the Coding Agent to have an idea of what is necessary and what the expected outcome is especially during failures.

**One divergence from your spec, and why:**
My plan was originally written sequentially following the input/output for the function calls. However, I had to properly update my spec and reimplement my agent.py to avoid the sequential call and allow the Agent to call the function based on the query. This was also done for the expected outcome for edge cases and errors such as empty wardobes. At first the Agent called the functions and continued without finding an item from the list. I updated the LLM prompt and the search_listings to notify the user that not item was found and to broaden their search.

---

## Where to Start

1. **Read `planning.md` **
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.


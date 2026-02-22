# Kite Goals — Personal Goal Based Mutual Fund Tracker

This is a simple CLI app to organise your Coin mutual funds into buckets as per your goals. Zerodha has long been requested for this feature but they don't seem to progress on this feature.

So, here's a command-line personal finance tracker that connects to your Zerodha account, maps your mutual funds to risk categories, allocates them across your financial goals, and tells you exactly how much SIP to set up — per risk bucket, per goal — to hit your targets on time.

---

## What it does

- Fetches your live MF holdings from Zerodha via KiteConnect
- Groups funds into **low / medium / high** risk buckets using your own `mappings.json`
- Allocates your portfolio across goals in **priority order** (Emergency before Phone, etc.)
- Shows **progress towards each goal** with a visual bar
- Calculates the **monthly SIP per risk bracket** needed to close the gap by your deadline
- Suggests a **rebalance plan** that distributes a given monthly budget across your actual funds

---

## Project structure

```
.
├── main.py          # Orchestrator — runs the full flow
├── auth.py          # Zerodha login and session management
├── portfolio.py     # Groups holdings by risk category
├── goals.py         # Waterfall allocation + SIP calculation
├── rebalance.py     # Distributes monthly budget across funds
├── display.py       # All terminal output / formatting
├── utils.py         # load_json, validate_goals, months_between
│
├── funds.json       # Auto-generated from Zerodha (or mock manually)
├── goals.json       # Your goals — you define these
├── mappings.json    # Which funds belong to which risk tier — you define these
└── .env             # API credentials (never commit this)
```

---

## Setup

**1. Install dependencies**

```bash
pip install kiteconnect python-dotenv
```

**2. Create a `.env` file**

```
zerodha_api_key=your_api_key_here
zerodha_api_secret=your_api_secret_here
```

Get these from [Zerodha's developer console](https://developers.kite.trade/).

**3. Define your risk mappings in `mappings.json`**

Map each fund you hold to a risk tier. Fund names must match exactly what Zerodha returns in `funds.json`.

```json
{
    "high":   ["HDFC SMALL CAP FUND - DIRECT PLAN"],
    "medium": ["HDFC BALANCED ADVANTAGE FUND - DIRECT PLAN"],
    "low":    ["HDFC CORPORATE BOND FUND - DIRECT PLAN"]
}
```

**4. Define your goals in `goals.json`**

```json
[
  {
    "name": "Emergency",
    "priority": 0,
    "target": 150000,
    "deadline": "2026-12-01",
    "allocation": {
      "low": 0.7,
      "medium": 0.2,
      "high": 0.1
    }
  },
  {
    "name": "Phone",
    "priority": 1,
    "target": 15000,
    "deadline": "2026-06-01",
    "allocation": {
      "low": 0.7,
      "medium": 0.2,
      "high": 0.1
    }
  }
]
```

> ⚠️ Each goal's allocation weights **must sum to 1.0** — the app will raise an error if they don't.

---

## Running it

```bash
python main.py
```

You'll be asked:
1. Whether to fetch fresh holdings from Zerodha (opens a browser for login)
2. Your monthly SIP budget for the rebalance plan (optional)

If you want to skip the Zerodha login and test locally, just create a `funds.json` manually with your holdings.

---

## How allocation works

Goals are funded in **priority order** — your Emergency fund (priority 0) gets filled before the Phone goal (priority 1). This means your most critical goals are never starved by aspirational ones.

Within each goal, the `allocation` weights define how much of each risk bucket that goal claims. The pool of available money depletes as each goal is funded. Whatever remains after all goals is shown as **unallocated surplus**.

```
Portfolio (current value)
│
├── [Priority 0] Emergency
│     low   →  claims 70% of ₹150,000  from low bucket
│     medium →  claims 20% of ₹150,000  from medium bucket
│     high  →  claims 10% of ₹150,000  from high bucket
│
└── [Priority 1] Phone
      low   →  claims from whatever low has left
      ...
```

---

## Sample output

```
════════════════════════════════════════════════════════════
  GOAL ALLOCATIONS  (priority order)
════════════════════════════════════════════════════════════

  [0] EMERGENCY
      Target  : ₹150,000.00
      Funded  : ₹33,799.22
      Gap     : ₹116,200.78
      Progress: [██████░░░░░░░░░░░░░░░░░░░░░░░░] 22.5%
      Deadline: 2026-12-01  (10 months away)
      SIP/mo breakdown to close gap by deadline:
        low        ₹ 10,396.61/month
        high       ₹  1,223.47/month
      Risk breakdown:
        low       needed ₹105,000.00  |  funded ₹  1,033.94  |  gap ₹103,966.06
        medium    needed ₹ 30,000.00  |  funded ₹ 30,000.00  |  gap ₹      0.00
        high      needed ₹ 15,000.00  |  funded ₹  2,765.27  |  gap ₹ 12,234.73
```

---

## Adding a new fund

1. Buy the fund on Zerodha
2. Add it to `mappings.json` under the appropriate risk tier
3. Run `main.py` and fetch fresh holdings — it will appear automatically

---

## Roadmap ideas

- [ ] Historical SIP tracking (did you actually invest what was planned last month?)
- [ ] Auto-calculate allocation weights from a target risk profile
- [ ] Export summary to PDF or spreadsheet
- [ ] Multi-currency support
- [ ] Web UI / dashboard
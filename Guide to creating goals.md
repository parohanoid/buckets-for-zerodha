# `goals.json` Guide

Each goal is an object in the array. Fields:

| Field | Required | Description |
|---|---|---|
| `name` | ✓ | Display label. Anything. |
| `target` | ✓ | Amount in ₹ you want saved. |
| `priority` | ✓ | Funding order. `0` is funded first. |
| `allocation` | ✓ | Risk split within the goal. Must sum to `1.0`. |
| `deadline` | — | `YYYY-MM-DD`. Enables SIP/month calculation. |
| `share` | — | Tiebreaker when two goals share a priority. See below. |

---

### `allocation`

How much of this goal comes from each risk tier. Must sum to `1.0`.

```json
"allocation": { "low": 0.7, "medium": 0.2, "high": 0.1 }
```

Rule of thumb: the shorter the timeline, the more you shift toward `low`.

---

### `priority`

Goals are funded in order — priority `0` is fully funded before priority `1` gets anything. Use this to protect critical goals (emergency fund) from being crowded out by aspirational ones (vacation, gadget).

---

### `share`

Only relevant when two goals share the same `priority`. Controls how available funds are split between them before claiming.

```json
{ "name": "Phone",  "priority": 1, "share": 0.6 }  // gets 60%
{ "name": "Laptop", "priority": 1, "share": 0.4 }  // gets 40%
```

- Values are normalised, so `6/4` and `0.6/0.4` are identical.
- Omit on all tied goals for an equal split.
- Either all tied goals define `share` or none do — mixing causes an error.

---

### Common errors

```json
// ❌ allocation sums to 1.1
"allocation": { "low": 0.7, "medium": 0.3, "high": 0.1 }

// ❌ share defined on Phone but not Laptop at same priority
{ "name": "Phone",  "priority": 1, "share": 0.6 }
{ "name": "Laptop", "priority": 1 }
```
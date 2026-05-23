# Tool Design Checklist

Tools are how Claude (or any MCP client) interacts with your server. Bad tool design = unused server. Use this checklist for every tool you write.

## Naming

- **Format**: `verb_noun` or `verb_noun_qualifier` in `snake_case`
- **Good**: `get_user`, `list_open_orders`, `send_telegram_message`, `query_oi_chain`
- **Bad**: `usersFetch` (camelCase), `data` (no verb), `do_thing` (no noun), `getUserOrdersByDate` (too nested in name)

## Descriptions — write for the model

The model reads the description to decide whether to call your tool. Treat it like a docstring for an LLM, not a human.

### Required elements

1. **What it does** in one sentence
2. **When to use it** (especially if multiple similar tools exist)
3. **What it returns** — shape and key fields
4. **Any caveats** — rate limits, side effects, auth requirements

### Good example

```python
@mcp.tool()
def get_open_interest(symbol: str, expiry: str) -> dict:
    """Fetch live open interest data for an NSE F&O symbol on a given expiry.

    Use this for analyzing OI buildup before suggesting trades. Returns a dict
    with strikes as keys and {ce_oi, pe_oi, ce_change, pe_change} as values.

    Note: OI data before 10:15 AM IST is unreliable due to market open volatility.
    Symbol must be the F&O ticker (e.g., 'HINDPETRO' not 'HPCL').
    """
    ...
```

### Bad example

```python
@mcp.tool()
def get_data(s: str, e: str) -> dict:
    """Get data."""
    ...
```

The model won't know when to pick this. It will be ignored.

## Schemas

Every parameter must be typed. Use Pydantic (Python) or Zod (TypeScript). The framework auto-generates JSON Schema from these.

### Python with Pydantic

```python
from pydantic import Field
from typing import Annotated, Literal

@mcp.tool()
def place_order(
    symbol: Annotated[str, Field(description="F&O symbol, e.g. NIFTY")],
    side: Annotated[Literal["BUY", "SELL"], Field(description="Order direction")],
    quantity: Annotated[int, Field(ge=1, le=100, description="Lots, 1-100")],
    order_type: Annotated[Literal["MARKET", "LIMIT"], Field(default="MARKET")],
    price: Annotated[float | None, Field(default=None, description="Required for LIMIT orders")],
) -> dict:
    """Place an F&O order. Returns order ID and status."""
    ...
```

### TypeScript with Zod

```typescript
server.registerTool(
  'place_order',
  {
    description: 'Place an F&O order. Returns order ID and status.',
    inputSchema: z.object({
      symbol: z.string().describe('F&O symbol, e.g. NIFTY'),
      side: z.enum(['BUY', 'SELL']).describe('Order direction'),
      quantity: z.number().int().min(1).max(100).describe('Lots, 1-100'),
      orderType: z.enum(['MARKET', 'LIMIT']).default('MARKET'),
      price: z.number().optional().describe('Required for LIMIT orders'),
    }),
  },
  async (input) => { /* ... */ }
);
```

## Return values

- Return structured data (dict/object), not formatted strings — let the model format
- Include enough context that the model doesn't need to call another tool
- For lists, paginate if results can exceed ~50 items — return `{items, next_cursor, total}`
- For errors, raise an exception with a clear message; don't return `{"error": "..."}`

## Error messages

The model reads your error messages and decides what to do next. Make them actionable.

| Bad | Good |
|-----|------|
| `"Error"` | `"Symbol 'HPCL' not found. Use F&O ticker 'HINDPETRO' instead."` |
| `"404"` | `"User ID 'abc123' does not exist. IDs are 6-digit integers."` |
| `"Failed"` | `"Order rejected: insufficient margin. Required ₹45,000, available ₹12,000."` |
| `"Invalid input"` | `"Expiry '2025-13-45' invalid. Use YYYY-MM-DD format with a valid date."` |

## Side effects

Any tool that **writes, sends, deletes, charges, or modifies external state** must signal that clearly:

- Put it in the name: `send_*`, `delete_*`, `create_*`, `update_*`, `charge_*`
- Mention it in the description: "Sends an email to the recipient. This cannot be undone."
- For genuinely destructive actions, consider requiring a `confirm: bool` parameter

The model is more conservative with side-effect tools. That's a feature, not a bug.

## Cardinality

- **Sweet spot**: 5–20 tools per server
- **Upper limit**: 30 tools — beyond this, agent performance degrades from token bloat
- **If you need 40+**: split into multiple servers, or use FastMCP's component composition, or implement code mode (FastMCP 3.1+)

GitHub's reference MCP server famously dumps 43 tools and destroys context — don't be that server.

## Final checklist

Before shipping a tool, verify:

- [ ] Name is `verb_noun` snake_case
- [ ] Description explains what, when, and what's returned
- [ ] Every parameter has a type and a description
- [ ] Return value is structured (not a formatted string)
- [ ] Error messages tell the model what to do differently
- [ ] Side effects are obvious from name and description
- [ ] Tested in MCP Inspector with valid + invalid inputs
- [ ] Total tool count on this server is under 30

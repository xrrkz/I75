# robin-trades

Operating rules for letting Claude place equity trades through Robinhood's
Agentic Trading MCP connector. `SKILL.md` is the substance; this file is setup.

## What this is

A rules file, not a trading system. It constrains *how* orders are placed —
limit orders only, hard caps, a mandatory pre-trade checklist, a kill switch —
so that the agent's failure modes are bounded. It does not tell the agent what
to buy, and it makes no claim to an edge.

## Setup

1. **Open a Robinhood agentic account.** Desktop only, and it requires an
   individual investing account in good standing. It is a *separate* account
   from your main portfolio — the agent can only reach money you move into it.
   That separation is the real risk control; everything in `SKILL.md` is the
   second layer.

2. **Connect the MCP server:**

   ```
   claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading
   ```

   Then run `/mcp` in Claude Code to complete the OAuth login.

3. **Leave manual approval on** during setup. You will see each proposed order
   before it goes in. Turn it off only after you have watched enough sessions to
   know what the agent does when unsupervised — and reconsider even then.

4. **Set your caps:**

   ```
   cp trading-limits.example.json trading-limits.json
   ```

   Edit the numbers. They are gitignored. The defaults in the example are small
   on purpose.

5. **Fund it with an amount you would be fine losing entirely.** Not "unlikely
   to lose" — fine losing. That number is the only limit that is actually
   enforced by something other than a document.

## Making it apply everywhere

As-is, this skill only loads when Claude Code runs inside this repo. To have it
apply in any directory:

```
cp -r .claude/skills/robin-trades ~/.claude/skills/
```

Keep `trading-limits.json` next to whichever copy you actually use.

## Beta limits (as of the connector's launch)

Equities only — no options, crypto, futures, or event contracts. No margin
borrowing on agentic accounts. Check Robinhood's docs for current scope.

## Note on this repo

This repo is **public**. `trading-limits.json` and `journal.md` are gitignored
and must stay that way. Never commit balances, account numbers, or position
sizes tied to a real account.

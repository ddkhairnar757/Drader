# Drader Architecture

## Two Division Model

### Research Division (MVP)
- Research
- Backtesting
- Validation
- Paper Trading
- DNA Memory
- Knowledge Graph

### Execution Division (Future — v2.0+)
- Broker Connectivity
- Risk Engine
- Position Monitoring
- Live Deployment

**Do not implement Execution Division functionality unless explicitly requested.**

## Strategy Lifecycle States

```
Draft → Under Review → Backtesting → Validation → Paper Trading → Live Eligible → Deployed → [Suspended | Retired]
```

- Live Eligible is the terminal state of the Research Division.
- Only Live Eligible strategies can cross the membrane to Execution.
- All state transitions are recorded in `strategy_dna`.

## Key Boundaries
- The AI Council is advisory only. The Founder holds ultimate authority.
- Research Division has zero access to broker infrastructure.
- The Membrane between divisions is immutable in code.
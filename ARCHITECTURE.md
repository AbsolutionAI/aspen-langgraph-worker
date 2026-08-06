# Architecture

```
Paperclip/Hermes (aspen-dev) ──issues/skills──► optional invoke
                                                      │
NATS / lab bus ── sense/event ──► LangGraph Worker ──► propose_act
                                                      │
                                         aspen-edge-rrm / swarm (arm gates)
```

See ADR-0005.

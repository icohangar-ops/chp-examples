# Python examples

Each directory is a standalone script that depends on the **published package** —
no vendored copy of the engine anywhere:

```bash
pip install consensus-hardening-protocol
python meshcfo-board-claim/main.py
```

They were derived from the real CHP usage in `meshcfo`, `SEC-earnings-workbench`,
`convergence` and `control-spine`. The only change needed to retarget those repos
is the import namespace:

| Was | Now |
|---|---|
| `from cme.chp.orchestrator import CHPOrchestrator` | `from chp import CHPOrchestrator` |
| `from convergence.chp.registry import DecisionRegistry` | `from chp import DecisionRegistry` |
| `from cme.chp.validators import apply_third_party_validation` | `from chp import apply_third_party_validation` |

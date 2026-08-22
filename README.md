# CHP examples

Reference consumers of the Consensus Hardening Protocol — retargeted off vendored
engine copies onto the **published** packages:

| Package | Install |
|---|---|
| Python | `pip install consensus-hardening-protocol` |
| TypeScript | `npm install @cubiczan/chp` |

## Layout

```
python/
  meshcfo-board-claim/       # board claim · domain floor 100
  convergence-ma/            # M&A adversary pass
  sec-earnings-workbench/    # third-party lock progression
  control-spine-icfr/        # ICFR spine using chp R0 + hash
typescript/
  clearance-gate/            # demo over @cubiczan/chp Profile B
rust/
  cleanmandate-gate/         # Profile B port + conformance adapter
```

## Run (Python)

```bash
pip install consensus-hardening-protocol
python python/meshcfo-board-claim/main.py
python python/convergence-ma/main.py
python python/sec-earnings-workbench/main.py
python python/control-spine-icfr/main.py
```

## Run (TypeScript)

```bash
cd typescript/clearance-gate && npm install && npm run demo
```

## Conformance (Rust / TS adapters)

From a checkout of [`consensus-hardening-protocol`](https://github.com/icohangar-ops/consensus-hardening-protocol)
(or `~/Desktop/chp-package`):

```bash
# TypeScript
(cd ~/Desktop/cubiczan-chp && npm run build)
python3 spec/conformance/run_conformance.py \
  --adapter-cmd "node ~/Desktop/cubiczan-chp/dist/adapter.js" --profile B

# Rust
(cd rust/cleanmandate-gate && cargo build --release)
python3 spec/conformance/run_conformance.py \
  --adapter-cmd "./rust/cleanmandate-gate/target/release/cleanmandate-gate" --profile B
```

Profile A ops are SKIP (unsupported) for the TS/Rust adapters — they implement
Profile B (capital gate), which is what `clearance` and `cleanmandate` were.

## Why not just `npm i` the old clearance CHP?

The original `clearance` / `cleanmandate` gates used local vocabulary
(`REJECTED`, dollar thresholds, quorum locks) that does not match CHP v1.0
§6. These ports implement the normative gate so their `content_hash` values
match the Python reference and the golden vectors.

/**
 * Clearance-shaped demo over `@cubiczan/chp`.
 *
 * The original clearance `runChpGate` mixed R0 vocabulary with spend checks.
 * This demo uses the normative Profile B capital gate from the published package.
 */
import { evaluateGate, approveHuman, type GatePolicy } from "@cubiczan/chp";

const policy: GatePolicy = {
  max_notional: 500,
  daily_cap: 2500,
  hitl_threshold: 250,
  min_confidence: 0.55,
  allowed_actions: ["PAY", "REFUND"],
  per_asset_limits: { USD: 500 },
};

function demo() {
  const auto = evaluateGate(
    { action: "PAY", asset: "USD", notional: 120, confidence: 0.9 },
    policy,
  );
  console.log("auto-approve <$HITL:", auto.state, auto.reason);

  const hitl = evaluateGate(
    { action: "PAY", asset: "USD", notional: 300, confidence: 0.9 },
    policy,
  );
  console.log("needs human:", hitl.state, hitl.reason);

  const locked = approveHuman(
    { action: "PAY", asset: "USD", notional: 300, confidence: 0.9 },
    policy,
    "finance-ops@example.com",
  );
  console.log("after countersign:", locked.state, locked.content_hash.slice(0, 16) + "…");

  const blocked = evaluateGate(
    { action: "PAY", asset: "USD", notional: 900, confidence: 0.9 },
    policy,
  );
  console.log("over max:", blocked.state, blocked.reason);
}

demo();

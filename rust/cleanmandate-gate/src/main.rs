//! CHP Profile B capital gate — Rust port.
//!
//! Retargeted from `cleanmandate`'s `cm-chp` / `cm-policy` crates onto the
//! normative spec (§6) so digests match the Python reference. Whole `f64`
//! values serialise as `100.0` under serde_json, which is what cross-language
//! hashing needs.
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::io::{self, BufRead, Write};

const CHP_VERSION: &str = "1.0";

#[derive(Debug, Clone, Deserialize)]
pub struct GatePolicy {
    pub max_notional: f64,
    pub daily_cap: f64,
    pub hitl_threshold: f64,
    pub min_confidence: f64,
    #[serde(default)]
    pub allowed_actions: Vec<String>,
    #[serde(default)]
    pub per_asset_limits: BTreeMap<String, f64>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ProposedAction {
    pub action: String,
    pub asset: String,
    pub notional: f64,
    #[serde(default)]
    pub confidence: Option<f64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct Claim {
    pub rule: String,
    pub passed: bool,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct GateResult {
    pub state: String,
    pub allowed: bool,
    pub requires_human: bool,
    pub reason: String,
    pub claims: Vec<Claim>,
    pub content_hash: String,
    pub committed_delta: f64,
}

fn py_num(n: f64) -> String {
    // Match Python float rendering for claim details.
    if n.fract() == 0.0 && n.is_finite() {
        format!("{:.1}", n)
    } else {
        // serde/python-ish shortest; trim awkward floats
        let s = format!("{}", n);
        s
    }
}

fn canonical_json(value: &Value) -> String {
    match value {
        Value::Null => "null".into(),
        Value::Bool(b) => if *b { "true" } else { "false" }.into(),
        Value::Number(n) => n.to_string(), // serde_json emits 100.0 for floats
        Value::String(s) => serde_json::to_string(s).unwrap(),
        Value::Array(arr) => {
            let parts: Vec<String> = arr.iter().map(canonical_json).collect();
            format!("[{}]", parts.join(","))
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let parts: Vec<String> = keys
                .into_iter()
                .map(|k| format!("{}:{}", serde_json::to_string(k).unwrap(), canonical_json(&map[k])))
                .collect();
            format!("{{{}}}", parts.join(","))
        }
    }
}

fn content_hash(value: &Value) -> String {
    let body = canonical_json(value);
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())
}

fn chain_hash(prev_sig: &str, entry: &Value) -> String {
    content_hash(&json!({"prev_sig": prev_sig, "entry": entry}))
}

fn gate_result(
    action: &ProposedAction,
    state: &str,
    claims: Vec<Claim>,
    allowed: bool,
    requires_human: bool,
    reason: String,
    committed_delta: f64,
) -> GateResult {
    let mut failed: Vec<String> = claims
        .iter()
        .filter(|c| !c.passed)
        .map(|c| c.rule.clone())
        .collect();
    failed.sort();
    let hashed = json!({
        "chp_version": CHP_VERSION,
        "profile": "B",
        "action": action.action,
        "asset": action.asset,
        "notional": action.notional,
        "confidence": action.confidence,
        "state": state,
        "allowed": allowed,
        "requires_human": requires_human,
        "failed_rules": failed,
    });
    GateResult {
        state: state.into(),
        allowed,
        requires_human,
        reason,
        claims,
        content_hash: content_hash(&hashed),
        committed_delta,
    }
}

pub fn evaluate_gate(action: &ProposedAction, policy: &GatePolicy, committed_today: f64) -> GateResult {
    let mut claims = Vec::new();
    let mut ok = true;
    let mut add = |rule: &str, passed: bool, detail: String| {
        claims.push(Claim {
            rule: rule.into(),
            passed,
            detail,
        });
        ok &= passed;
    };

    let finite_positive = action.notional.is_finite() && action.notional > 0.0;
    add(
        "sane-notional",
        finite_positive,
        format!("notional={}", py_num(action.notional)),
    );

    if !policy.allowed_actions.is_empty() {
        add(
            "allowed-action",
            policy.allowed_actions.iter().any(|a| a == &action.action),
            format!("action {}", action.action),
        );
    }

    let cap = policy
        .per_asset_limits
        .get(&action.asset)
        .copied()
        .unwrap_or(policy.max_notional);
    add(
        "per-asset-cap",
        action.notional <= cap,
        format!(
            "{} notional {} vs cap {}",
            action.asset,
            py_num(action.notional),
            py_num(cap)
        ),
    );
    add(
        "max-notional",
        action.notional <= policy.max_notional,
        format!(
            "{} vs max {}",
            py_num(action.notional),
            py_num(policy.max_notional)
        ),
    );

    let projected = committed_today + if finite_positive { action.notional } else { 0.0 };
    add(
        "daily-cap",
        projected <= policy.daily_cap,
        format!(
            "projected {} vs daily cap {}",
            py_num(projected),
            py_num(policy.daily_cap)
        ),
    );

    if let Some(conf) = action.confidence {
        add(
            "min-confidence",
            conf >= policy.min_confidence,
            format!(
                "confidence {} vs min {}",
                py_num(conf),
                py_num(policy.min_confidence)
            ),
        );
    }

    if !ok {
        let failed: Vec<_> = claims
            .iter()
            .filter(|c| !c.passed)
            .map(|c| c.rule.clone())
            .collect();
        return gate_result(
            action,
            "BLOCKED",
            claims,
            false,
            false,
            format!("blocked: {}", failed.join(", ")),
            0.0,
        );
    }

    if action.notional >= policy.hitl_threshold {
        return gate_result(
            action,
            "HITL_REQUIRED",
            claims,
            false,
            true,
            format!(
                "human approval required: {} >= HITL threshold {}",
                py_num(action.notional),
                py_num(policy.hitl_threshold)
            ),
            0.0,
        );
    }

    gate_result(
        action,
        "LOCKED",
        claims,
        true,
        false,
        "auto-approved under CHP thresholds".into(),
        action.notional,
    )
}

pub fn approve_human(
    action: &ProposedAction,
    policy: &GatePolicy,
    approver: &str,
    committed_today: f64,
) -> GateResult {
    let recheck = evaluate_gate(action, policy, committed_today);
    if recheck.state == "BLOCKED" {
        let mut out = recheck;
        out.reason = format!("approval by {} rejected: {}", approver, out.reason);
        return out;
    }
    gate_result(
        action,
        "LOCKED",
        vec![Claim {
            rule: "human-approval".into(),
            passed: true,
            detail: format!("approved by {}", approver),
        }],
        true,
        false,
        format!("human-approved by {}", approver),
        action.notional,
    )
}

fn handle(op: &str, args: &Value) -> Result<Value, String> {
    match op {
        "canonical_json" => Ok(Value::String(canonical_json(&args["payload"]))),
        "content_hash" => Ok(Value::String(content_hash(&args["payload"]))),
        "chain_hash" => Ok(Value::String(chain_hash(
            args["prev_sig"].as_str().unwrap_or(""),
            &args["entry"],
        ))),
        "evaluate_gate" => {
            let action: ProposedAction = serde_json::from_value(args["action"].clone())
                .map_err(|e| e.to_string())?;
            let policy: GatePolicy =
                serde_json::from_value(args["policy"].clone()).map_err(|e| e.to_string())?;
            let committed = args["committed_today"].as_f64().unwrap_or(0.0);
            Ok(serde_json::to_value(evaluate_gate(&action, &policy, committed)).unwrap())
        }
        "approve_human" => {
            let action: ProposedAction = serde_json::from_value(args["action"].clone())
                .map_err(|e| e.to_string())?;
            let policy: GatePolicy =
                serde_json::from_value(args["policy"].clone()).map_err(|e| e.to_string())?;
            let approver = args["approver"].as_str().unwrap_or("");
            let committed = args["committed_today"].as_f64().unwrap_or(0.0);
            Ok(serde_json::to_value(approve_human(&action, &policy, approver, committed)).unwrap())
        }
        _ => Err("unsupported".into()),
    }
}

fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout();
    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };
        if line.trim().is_empty() {
            continue;
        }
        let req: Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(e) => {
                let _ = writeln!(
                    stdout,
                    "{}",
                    json!({"ok": false, "error": e.to_string()})
                );
                continue;
            }
        };
        let op = req["op"].as_str().unwrap_or("");
        match handle(op, &req["args"]) {
            Ok(result) => {
                let _ = writeln!(stdout, "{}", json!({"ok": true, "result": result}));
            }
            Err(e) => {
                let _ = writeln!(stdout, "{}", json!({"ok": false, "error": e}));
            }
        }
        let _ = stdout.flush();
    }
}

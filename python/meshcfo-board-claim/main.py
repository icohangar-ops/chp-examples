"""meshcfo — a board claim that must trace to an agent, a lock and a document.

Retargeted from meshcfo, which vendored the engine at `cme/chp`. The only change
is the import: `from chp import ...` against the published package.

The point of this example is the finance floor. A board-facing capital decision
sits in a domain that CHP floors at 100, not 70, so a merely-plausible foundation
score does not produce a locked claim.
"""
from chp import (
    CHPOrchestrator,
    DecisionCase,
    DecisionRegistry,
    Dossier,
    Verdict,
    evaluate_r0_gate,
)
from chp.foundation import foundation_floor
from chp.models import FoundationAttack, FoundationDisclosure


def board_case(decision_id: str) -> DecisionCase:
    return DecisionCase(
        decision_id=decision_id,
        title="Increase the enterprise tier headcount",
        domain="board_decision",          # floors at 100
        created_at="2026-08-21T09:00:00Z",
        owner="cfo",
        high_stakes=True,
        dossier=Dossier(
            core_problem="Can we fund six more AEs without a raise?",
            goal_state=["ARR +40% in four quarters"],
            current_state=["18 months runway", "net revenue retention 108%"],
            constraints=["no new equity", "gross margin floor 72%"],
            scope=["FY27 operating plan"],
        ),
    )


def main() -> None:
    print(f"board_decision floor: {foundation_floor('board_decision')}\n")

    # R0 first — the session should not even open on an unscoped question.
    r0 = evaluate_r0_gate(solvable=True, scoped=True, valid=True, worth_it=True)
    print(f"R0 gate: {r0}\n")

    for score, label in ((88, "plausible"), (100, "substantiated")):
        orch = CHPOrchestrator(registry=DecisionRegistry())
        report = orch.run_initial_session(
            case=board_case(f"board-{score}"),
            foundation_disclosure=FoundationDisclosure(
                weakest_assumptions=["NRR holds above 105%"],
                invalidation_conditions=["Two enterprise churns in one quarter"],
                key_vulnerability="Revenue concentrated in four accounts",
            ),
            foundation_attack=FoundationAttack(
                assumption_attacks=["NRR is flattered by one upsell"],
                vulnerability_strike="Top account is 22% of ARR",
                foundation_score=score,
            ),
        )
        emitted = "yes" if report.initial_packet else "no"
        print(f"  score {score:3d} ({label:14s}) -> {report.foundation_verdict.value:8s}  packet emitted: {emitted}")

    print("\nA board claim only becomes quotable at 100. Below that it reframes,")
    print("and there is no packet to hand to anyone.")


if __name__ == "__main__":
    main()

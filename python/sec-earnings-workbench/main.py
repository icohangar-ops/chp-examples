"""SEC-earnings-workbench — shared-context agents under one CHP gate.

Retargeted from SEC-earnings-workbench (`from cme.chp ...`). Demonstrates
third-party validation progressing a provisional lock, against the published
package rather than a vendored engine.
"""
from chp import (
    DecisionCase,
    DecisionRegistry,
    Dossier,
    SessionStatus,
    ThirdPartyValidation,
    ValidationResult,
    apply_third_party_validation,
    evaluate_r0_gate,
)
from chp.models import FoundationAttack, FoundationDisclosure
from chp import CHPOrchestrator


def main() -> None:
    r0 = evaluate_r0_gate(solvable=True, scoped=True, valid=True, worth_it=True)
    print(f"R0: {r0.verdict.value}")

    case = DecisionCase(
        decision_id="earn-q2-guidance",
        title="Publish Q2 guidance revision",
        domain="finance",
        created_at="2026-08-21T14:00:00Z",
        owner="ir-lead",
        high_stakes=True,
        dossier=Dossier(
            core_problem="Do we lower FY ARR guidance after the top-account churn?",
            goal_state=["guidance investors can defend"],
            current_state=["one top account churned", "pipeline coverage 2.1x"],
            constraints=["quiet period starts Friday"],
            scope=["Q2 10-Q narrative"],
        ),
    )
    orch = CHPOrchestrator(registry=DecisionRegistry())
    report = orch.run_initial_session(
        case=case,
        foundation_disclosure=FoundationDisclosure(
            weakest_assumptions=["Replacement pipeline closes this quarter"],
            invalidation_conditions=["Second top-10 churn"],
            key_vulnerability="Guidance rests on one renewal cohort",
        ),
        foundation_attack=FoundationAttack(
            assumption_attacks=["Replacement deals are still in discovery"],
            vulnerability_strike="Cohort concentration is 31% of ARR",
            foundation_score=100,
        ),
    )
    print(f"foundation: {report.foundation_verdict.value}")
    print(f"status after foundation: {report.case.status.value}")

    # Spec §5.10 — third-party validation only applies to a provisional lock.
    report.case.status = SessionStatus.PROVISIONAL_LOCK
    status = apply_third_party_validation(
        report.case,
        ThirdPartyValidation(
            validator="fresh_instance",
            item="Guidance memo v3",
            challenge="stress test against second churn",
            result=ValidationResult.CONFIRM,
            rationale="Memo survives the second-churn scenario",
        ),
    )
    print(f"after third-party confirm: {status.value}")
    print(f"locked decisions: {report.case.locked_decisions}")


if __name__ == "__main__":
    main()

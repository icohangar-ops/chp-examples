"""convergence — high-stakes M&A integration decisions under an adversary pass.

Retargeted from convergence, which vendored the engine at `convergence/chp`.

This example shows the part of CHP that is easy to skip: the adversary is not
advisory. Its findings are what move the session, and a decision that cannot
survive them does not proceed.
"""
from chp import (
    CHPOrchestrator,
    DecisionCase,
    DecisionRegistry,
    Dossier,
    TriangulationRunner,
    evaluate_r0_gate,
)
from chp.foundation import foundation_verdict, validate_foundation_pair
from chp.models import FoundationAttack, FoundationDisclosure


def main() -> None:
    # A question that is not worth answering must be refused, not answered badly.
    unworthy = evaluate_r0_gate(solvable=True, scoped=False, valid=True, worth_it=False)
    print(f"R0 on an unscoped, low-value question: {unworthy.verdict.value}")
    print(f"  failing checks: {[k for k, v in unworthy.results.items() if v != 'PASS']}\n")

    disclosure = FoundationDisclosure(
        weakest_assumptions=["Synergies land inside 18 months"],
        invalidation_conditions=["Key engineering staff leave post-close"],
        key_vulnerability="Integration depends on one platform team",
    )
    attack = FoundationAttack(
        assumption_attacks=["Comparable deals took 30 months to realise synergies"],
        vulnerability_strike="That platform team has 40% annual attrition",
        foundation_score=82,
    )

    errors = validate_foundation_pair(disclosure, attack)
    print(f"foundation pair valid: {not errors}{'' if not errors else ' -> ' + str(errors)}")

    # 'general' floors at 70; the same score in a finance domain would reframe.
    print(f"  verdict as general      : {foundation_verdict(attack, 'general').value}")
    print(f"  verdict as capital_alloc: {foundation_verdict(attack, 'capital_allocation').value}\n")

    case = DecisionCase(
        decision_id="ma-integration-1",
        title="Integrate the acquired platform team",
        domain="general",
        created_at="2026-08-21T09:00:00Z",
        owner="coo",
        high_stakes=True,
        dossier=Dossier(
            core_problem="Merge the platform teams or run them parallel for a year?",
            goal_state=["one deploy pipeline"],
            current_state=["two on-call rotations"],
            constraints=["no forced relocation"],
            scope=["first 4 quarters post-close"],
        ),
    )
    report = CHPOrchestrator(registry=DecisionRegistry()).run_initial_session(
        case=case, foundation_disclosure=disclosure, foundation_attack=attack
    )
    print(f"session status : {report.case.status.value}")
    print(f"verdict        : {report.foundation_verdict.value}")

    adversary = TriangulationRunner.as_adversary(
        "Merging the platform teams will cut deploy time by 40%."
    )
    print(f"\nadversary findings ({len(adversary.adversary_findings)}):")
    for f in adversary.adversary_findings[:4]:
        print(f"  - {f}")


if __name__ == "__main__":
    main()

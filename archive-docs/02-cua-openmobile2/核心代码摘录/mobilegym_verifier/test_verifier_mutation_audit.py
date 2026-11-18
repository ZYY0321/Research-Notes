from bench_env.task.hybrid_tools_0815_explore.verifier_mutation_audit import audit_contracts


def test_single_field_contract_rejects_near_miss() -> None:
    report = audit_contracts(["explore_baicizhan_bcz_001"])
    assert report["summary"]["positive_fixtures_passed"] == 1
    assert report["summary"]["mutations_generated"] == 1
    assert report["summary"]["wrongly_passing_mutations"] == 0


def test_multifield_contract_rejects_partial_completion() -> None:
    report = audit_contracts(["explore_baicizhan_bcz_006"])
    task = report["tasks"][0]
    assert task["positive_fixture_passed"]
    assert len(task["generated_mutations"]) == 2
    assert not task["wrongly_passing_mutations"]
    assert task["semantic_constraint_coverage"]["ratio"] == 1.0


def test_numeric_list_path_is_synthesized_and_mutated() -> None:
    report = audit_contracts(["explore_flomo_flomo_06"])
    task = report["tasks"][0]
    assert task["positive_fixture_passed"]
    assert task["generated_mutations"]
    assert not task["wrongly_passing_mutations"]


def test_terminal_selector_absence_mutant_creates_matching_entity() -> None:
    report = audit_contracts(["explore_daysmatter_dm_007"])
    task = report["tasks"][0]
    assert task["positive_fixture_passed"]
    assert task["generated_mutations"]
    assert not task["wrongly_passing_mutations"]


def test_delivery_specs_wire_contract_paths_as_expected_changes_not_goals() -> None:
    """String state paths must never reach the declarative GoalSpec evaluator."""
    from bench_env.task.hybrid_tools_0815_explore.defs.all_candidates import SPECS

    assert len(SPECS) == 219
    assert all(spec.goals == () for spec in SPECS)
    assert all(spec.expected_changes for spec in SPECS)
    assert all(
        isinstance(path, str)
        for spec in SPECS
        for path in spec.expected_changes
    )

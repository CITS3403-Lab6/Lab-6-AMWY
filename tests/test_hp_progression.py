import pytest
from app.models import Progress
from app.services import (
    apply_daily_hp_result,
    calculate_character_reveal_stage,
    calculate_completion_percentage,
    calculate_level_from_xp,
    get_mindset_target,
)


def test_sage_mindset_target_is_50():
    assert get_mindset_target("Sage") == 50


def test_warrior_mindset_target_is_70():
    assert get_mindset_target("Warrior") == 70


def test_demon_mindset_target_is_90():
    assert get_mindset_target("Demon") == 90


def test_unknown_mindset_falls_back_to_sage():
    assert get_mindset_target("Unknown") == 50


def test_completion_percentage_calculates_correctly():
    assert calculate_completion_percentage(total_tasks=4, completed_tasks=2) == 50


def test_completion_percentage_zero_tasks_returns_zero():
    assert calculate_completion_percentage(total_tasks=0, completed_tasks=0) == 0


def test_level_is_capped_at_100():
    assert calculate_level_from_xp(999999) == 100


def test_character_reveal_stage_every_10_levels():
    assert calculate_character_reveal_stage(1) == 0
    assert calculate_character_reveal_stage(9) == 0
    assert calculate_character_reveal_stage(10) == 1
    assert calculate_character_reveal_stage(20) == 2
    assert calculate_character_reveal_stage(100) == 10


def test_meeting_daily_target_increases_streak_without_hp_loss():
    progress = Progress(hp=100, max_hp=100, streak=2)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=70,
        mindset_type="Warrior",
    )

    assert result["met_target"] is True
    assert result["hp_lost"] == 0
    assert progress.hp == 100
    assert progress.streak == 3


def test_missing_daily_target_reduces_hp_and_resets_streak():
    progress = Progress(hp=100, max_hp=100, streak=4)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=40,
        mindset_type="Sage",
    )

    assert result["met_target"] is False
    assert result["target"] == 50
    assert result["hp_lost"] == 10
    assert progress.hp == 90
    assert progress.streak == 0


def test_hp_never_goes_below_zero():
    progress = Progress(hp=20, max_hp=100, streak=1)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=0,
        mindset_type="Demon",
    )

    assert result["met_target"] is False
    assert result["hp_lost"] == 90
    assert progress.hp == 0
    assert progress.streak == 0


def test_mindset_target_handles_case():
    assert get_mindset_target(" Demon ") == 90
    assert get_mindset_target("sage") == 50
    assert get_mindset_target("") == 50
    assert get_mindset_target(None) == 50


def test_completion_percentage_clamps_completed_above_total():
    assert calculate_completion_percentage(total_tasks=3, completed_tasks=5) == 100


def test_completion_percentage_clamps_negative_completed_count():
    assert calculate_completion_percentage(total_tasks=3, completed_tasks=-2) == 0


def test_completion_percentage_accepts_numeric_strings():
    assert calculate_completion_percentage(total_tasks="4", completed_tasks="3") == 75


def test_completion_percentage_rejects_non_numeric_input():
    with pytest.raises(ValueError):
        calculate_completion_percentage(total_tasks="abc", completed_tasks=1)


def test_level_rejects_negative_xp():
    with pytest.raises(ValueError):
        calculate_level_from_xp(-1)


def test_level_handles_none_xp_as_level_one():
    assert calculate_level_from_xp(None) == 1


def test_character_reveal_stage_clamps_level_above_cap():
    assert calculate_character_reveal_stage(999) == 10


def test_character_reveal_stage_handles_none_as_stage_zero():
    assert calculate_character_reveal_stage(None) == 0


def test_apply_daily_hp_result_rejects_missing_progress():
    with pytest.raises(ValueError):
        apply_daily_hp_result(
            progress=None,
            completion_percentage=50,
            mindset_type="Sage",
        )


def test_apply_daily_hp_result_clamps_completion_above_100():
    progress = Progress(hp=100, max_hp=100, streak=0)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=150,
        mindset_type="Demon",
    )

    assert result["met_target"] is True
    assert result["completion_percentage"] == 100
    assert progress.hp == 100
    assert progress.streak == 1


def test_apply_daily_hp_result_clamps_completion_below_zero():
    progress = Progress(hp=100, max_hp=100, streak=2)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=-50,
        mindset_type="Sage",
    )

    assert result["met_target"] is False
    assert result["completion_percentage"] == 0
    assert result["hp_lost"] == 50
    assert progress.hp == 50
    assert progress.streak == 0


def test_apply_daily_hp_result_repairs_missing_hp_values():
    progress = Progress(hp=None, max_hp=None, streak=None)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=80,
        mindset_type="Demon",
    )

    assert result["met_target"] is False
    assert progress.max_hp == 100
    assert progress.hp == 90
    assert progress.streak == 0


def test_apply_daily_hp_result_clamps_existing_hp_above_max_hp():
    progress = Progress(hp=250, max_hp=100, streak=0)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=100,
        mindset_type="Demon",
    )

    assert result["met_target"] is True
    assert progress.hp == 100
    assert progress.max_hp == 100
    assert progress.streak == 1


def test_apply_daily_hp_result_repairs_invalid_max_hp():
    progress = Progress(hp=50, max_hp=0, streak=1)

    result = apply_daily_hp_result(
        progress=progress,
        completion_percentage=100,
        mindset_type="Sage",
    )

    assert result["met_target"] is True
    assert progress.max_hp == 100
    assert progress.hp == 50
    assert progress.streak == 2

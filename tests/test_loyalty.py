from tea_kitsune.loyalty import next_tier, points_from_visits, tier_for_points


def test_points_from_visits():
    assert points_from_visits(3) == 30
    assert points_from_visits(-2) == 0


def test_tier_progression():
    assert tier_for_points(0).name == "Росток"
    assert tier_for_points(50).name == "Лисёнок"
    assert tier_for_points(500).name == "Кицунэ-мастер"


def test_next_tier():
    assert next_tier(0).name == "Лисёнок"
    assert next_tier(199).name == "Кицунэ-мастер"
    assert next_tier(250) is None

from dataclasses import dataclass

POINTS_PER_VISIT = 10


@dataclass(frozen=True)
class LoyaltyTier:
    name: str
    min_points: int
    reward: str


TIERS = [
    LoyaltyTier("Росток", 0, "Чайная открытка с пожеланием"),
    LoyaltyTier("Лисёнок", 50, "-5% на следующую церемонию"),
    LoyaltyTier("Хранитель чаёв", 120, "Бесплатная дегустация редкого чая"),
    LoyaltyTier("Кицунэ-мастер", 200, "Персональная чайная церемония"),
]


def points_from_visits(visits_count: int) -> int:
    return max(0, visits_count) * POINTS_PER_VISIT


def tier_for_points(points: int) -> LoyaltyTier:
    selected = TIERS[0]
    for tier in TIERS:
        if points >= tier.min_points:
            selected = tier
    return selected


def next_tier(points: int) -> LoyaltyTier | None:
    for tier in TIERS:
        if points < tier.min_points:
            return tier
    return None

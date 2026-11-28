from datetime import UTC, datetime
from uuid import uuid4

import pytest

from aether.contracts import (
    AttributeRating,
    CharacterSheet,
    GenesisProvenance,
    Merit,
    SkillCategoryKind,
    SkillRating,
    Specialization,
    StorytellingCreationProfile,
)
from aether.engines import CharacterGenesisEngine, CharacterGenesisValidationError


def profile() -> StorytellingCreationProfile:
    return StorytellingCreationProfile(
        profile_id=uuid4(),
        world_id=uuid4(),
        ruleset_id="storytelling-test-ruleset",
        attribute_categories=("category-a", "category-b", "category-c"),
        skill_categories=("category-x", "category-y", "category-z"),
        skill_category_kinds={
            "category-x": SkillCategoryKind.MENTAL,
            "category-y": SkillCategoryKind.PHYSICAL,
            "category-z": SkillCategoryKind.SOCIAL,
        },
    )


def sheet(item_profile: StorytellingCreationProfile) -> CharacterSheet:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return CharacterSheet(
        sheet_id=uuid4(),
        world_id=item_profile.world_id,
        character_id=uuid4(),
        ruleset_id=item_profile.ruleset_id,
        attributes=(
            AttributeRating(category="category-a", name="a1", rating=5),
            AttributeRating(category="category-a", name="a2", rating=2),
            AttributeRating(category="category-b", name="b1", rating=5),
            AttributeRating(category="category-c", name="c1", rating=4),
        ),
        skills=(
            SkillRating(category="category-x", name="x1", rating=5),
            SkillRating(category="category-x", name="x2", rating=5),
            SkillRating(category="category-x", name="x3", rating=1),
            SkillRating(category="category-y", name="y1", rating=5),
            SkillRating(category="category-y", name="y2", rating=2),
            SkillRating(category="category-z", name="z1", rating=4),
            SkillRating(category="category-z", name="z2", rating=0),
        ),
        specializations=(
            Specialization(skill="x1", name="s1", level=2),
            Specialization(skill="y1", name="s2", level=1),
        ),
        merits=(Merit(name="merit", points=7),),
        genesis=GenesisProvenance(
            profile_id=item_profile.profile_id,
            ruleset_id=item_profile.ruleset_id,
            source_type="test",
            source_id="genesis",
            created_at=now,
        ),
        version=1,
        updated_at=now,
    )


def test_storytelling_point_distributions_are_validated() -> None:
    item_profile = profile()
    engine = CharacterGenesisEngine()

    engine.validate_sheet(sheet(item_profile), item_profile)

    invalid = sheet(item_profile).model_copy(
        update={
            "attributes": (
                AttributeRating(category="category-a", name="a1", rating=4),
                AttributeRating(category="category-a", name="a2", rating=2),
                AttributeRating(category="category-b", name="b1", rating=5),
                AttributeRating(category="category-c", name="c1", rating=4),
            )
        }
    )
    with pytest.raises(CharacterGenesisValidationError, match="5/4/3"):
        engine.validate_sheet(invalid, item_profile)


def test_skill_zero_penalties_are_determined_by_supplied_categories() -> None:
    item_profile = profile()
    engine = CharacterGenesisEngine()

    assert engine.skill_zero_penalty("category-x", item_profile) == -3
    assert engine.skill_zero_penalty("category-y", item_profile) == -1
    assert engine.skill_zero_penalty("category-z", item_profile) == -1
    with pytest.raises(CharacterGenesisValidationError, match="ruleset"):
        engine.skill_zero_penalty("invented-category", item_profile)


def test_ruleset_mismatch_is_rejected_without_inventing_categories() -> None:
    item_profile = profile()
    mismatched = item_profile.model_copy(update={"profile_id": uuid4()})

    with pytest.raises(CharacterGenesisValidationError, match="ruleset"):
        CharacterGenesisEngine().validate_sheet(sheet(item_profile), mismatched)

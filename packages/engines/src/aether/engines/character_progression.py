from aether.contracts import (
    CharacterProgressionChange,
    CharacterSheet,
    ProgressionChangeKind,
    ProgressionChangeOperation,
    StorytellingCreationProfile,
)


class CharacterGenesisValidationError(ValueError):
    pass


class CharacterProgressionValidationError(ValueError):
    pass


class CharacterGenesisEngine:
    def validate_sheet(
        self,
        sheet: CharacterSheet,
        profile: StorytellingCreationProfile,
    ) -> None:
        if (
            sheet.ruleset_id != profile.ruleset_id
            or sheet.genesis.ruleset_id != profile.ruleset_id
            or sheet.world_id != profile.world_id
            or sheet.genesis.profile_id != profile.profile_id
        ):
            raise CharacterGenesisValidationError("Character sheet does not match creation ruleset")
        self._validate_unique_ratings(sheet)
        self._validate_attribute_distribution(sheet, profile)
        self._validate_skill_distribution(sheet, profile)
        if sum(item.level for item in sheet.specializations) != profile.initial_specialization_levels:
            raise CharacterGenesisValidationError("Specialization points do not match profile")
        if any(item.skill not in {skill.name for skill in sheet.skills} for item in sheet.specializations):
            raise CharacterGenesisValidationError("Specialization references an unknown skill")
        if sum(item.points for item in sheet.merits) != profile.merit_points:
            raise CharacterGenesisValidationError("Merit points do not match profile")

    @staticmethod
    def skill_zero_penalty(
        skill_category: str,
        profile: StorytellingCreationProfile,
    ) -> int:
        from aether.contracts import SkillCategoryKind

        try:
            kind = profile.skill_category_kinds[skill_category]
        except KeyError as error:
            raise CharacterGenesisValidationError(
                "Skill category is not supplied by the world ruleset"
            ) from error
        if kind == SkillCategoryKind.MENTAL:
            return profile.untrained_mental_penalty
        return profile.untrained_physical_social_penalty

    @staticmethod
    def _validate_unique_ratings(sheet: CharacterSheet) -> None:
        for label, ratings in (("attribute", sheet.attributes), ("skill", sheet.skills)):
            keys = [(item.category, item.name) for item in ratings]
            if len(keys) != len(set(keys)):
                raise CharacterGenesisValidationError(f"Duplicate {label} rating")
        if len({item.name for item in sheet.merits}) != len(sheet.merits):
            raise CharacterGenesisValidationError("Duplicate Merit")

    @staticmethod
    def _validate_attribute_distribution(
        sheet: CharacterSheet, profile: StorytellingCreationProfile
    ) -> None:
        if {item.category for item in sheet.attributes} != set(profile.attribute_categories):
            raise CharacterGenesisValidationError("Attribute categories do not match profile")
        totals = sorted(
            sum(
                item.rating - profile.base_attribute_rating
                for item in sheet.attributes
                if item.category == category
            )
            for category in profile.attribute_categories
        )
        if totals != sorted(profile.attribute_priority_budgets):
            raise CharacterGenesisValidationError(
                "Attribute point distribution must use 5/4/3 after base ratings"
            )

    @staticmethod
    def _validate_skill_distribution(
        sheet: CharacterSheet, profile: StorytellingCreationProfile
    ) -> None:
        if {item.category for item in sheet.skills} != set(profile.skill_categories):
            raise CharacterGenesisValidationError("Skill categories do not match profile")
        totals = sorted(
            sum(item.rating for item in sheet.skills if item.category == category)
            for category in profile.skill_categories
        )
        if totals != sorted(profile.skill_priority_budgets):
            raise CharacterGenesisValidationError(
                "Skill point distribution must use 11/7/4"
            )

    def apply_changes(
        self,
        sheet: CharacterSheet,
        changes: tuple[CharacterProgressionChange, ...],
    ) -> CharacterSheet:
        data = sheet.model_dump()
        for change in changes:
            self._apply_change(data, change)
        return CharacterSheet.model_validate(data)

    @staticmethod
    def _apply_change(data: dict, change: CharacterProgressionChange) -> None:
        numeric_fields = {
            ProgressionChangeKind.ATTRIBUTE: ("attributes", "rating"),
            ProgressionChangeKind.SKILL: ("skills", "rating"),
            ProgressionChangeKind.SPECIALIZATION: ("specializations", "level"),
            ProgressionChangeKind.MERIT: ("merits", "points"),
        }
        semantic_fields = {
            ProgressionChangeKind.NARRATIVE_QUALITY: "narrative_qualities",
            ProgressionChangeKind.NARRATIVE_FLAW: "narrative_flaws",
            ProgressionChangeKind.INJURY: "injuries",
            ProgressionChangeKind.TRAIT: "traits",
        }
        if change.kind in numeric_fields:
            field, value_field = numeric_fields[change.kind]
            matches = [
                item
                for item in data[field]
                if item["name"] == change.target
                and (
                    change.category is None
                    or item.get("category") == change.category
                    or field == "specializations"
                    and item.get("skill") == change.category
                )
            ]
            if len(matches) != 1:
                raise CharacterProgressionValidationError(
                    f"Progression target {change.target!r} is missing or ambiguous"
                )
            delta = change.amount if change.operation == ProgressionChangeOperation.INCREASE else -change.amount
            matches[0][value_field] += delta
        elif change.kind in semantic_fields:
            field = semantic_fields[change.kind]
            items = list(data[field])
            if change.operation == ProgressionChangeOperation.ADD:
                if any(item["name"] == change.target for item in items):
                    raise CharacterProgressionValidationError(
                        f"Semantic progression target {change.target!r} already exists"
                    )
                items.append({"name": change.target, "description": change.description})
            else:
                matches = [item for item in items if item["name"] == change.target]
                if len(matches) != 1:
                    raise CharacterProgressionValidationError(
                        f"Semantic progression target {change.target!r} is missing"
                    )
                items.remove(matches[0])
            data[field] = tuple(items)
        else:
            raise CharacterProgressionValidationError("Unsupported progression change")

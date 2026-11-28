from collections import defaultdict
from decimal import Decimal
from datetime import timedelta
from uuid import UUID

from aether.contracts import (
    ResourceCharge,
    TransportRoute,
    TransportRouteSegment,
)


class RouteSelection:
    def __init__(
        self,
        route: TransportRoute,
        segments: tuple[TransportRouteSegment, ...],
    ) -> None:
        self.route = route
        self.segments = segments

    @classmethod
    def select(
        cls,
        route: TransportRoute,
        segments_by_id: tuple[TransportRouteSegment, ...],
        segment_ids: tuple[UUID, ...],
    ) -> "RouteSelection":
        by_id = {segment.segment_id: segment for segment in segments_by_id}
        if len(by_id) != len(segments_by_id):
            raise ValueError("Route contains duplicate segment IDs")
        try:
            selected = tuple(by_id[segment_id] for segment_id in segment_ids)
        except KeyError as error:
            raise ValueError("Journey selects an unknown route segment") from error
        if len(set(segment_ids)) != len(segment_ids):
            raise ValueError("Journey selects a route segment more than once")
        if any(segment.route_id != route.route_id for segment in selected):
            raise ValueError("Journey segments do not belong to the selected route")
        if not selected:
            raise ValueError("Journey requires route segments")
        if selected[0].start_location_id != route.start_location_id:
            raise ValueError("Journey segments do not begin at the route start")
        if selected[-1].end_location_id != route.end_location_id:
            raise ValueError("Journey segments do not end at the route end")
        for previous, following in zip(selected, selected[1:]):
            if previous.end_location_id != following.start_location_id:
                raise ValueError("Selected transport route is disconnected")
        units = {segment.distance_unit for segment in selected}
        if len(units) != 1:
            raise ValueError("Selected segments use inconsistent distance units")
        if any(segment.mode not in route.modes for segment in selected):
            raise ValueError("Selected segments are not compatible with the route mode")
        if not route.modes:
            raise ValueError("Transport route requires at least one mode")
        return cls(route, selected)

    @property
    def total_distance(self) -> Decimal:
        return sum(
            (segment.physical_distance for segment in self.segments),
            start=Decimal(0),
        )

    @property
    def distance_unit(self) -> str:
        return self.segments[0].distance_unit

    @property
    def total_duration(self) -> timedelta:
        return sum(
            (segment.base_duration for segment in self.segments),
            start=timedelta(0),
        )

    @property
    def charges(self) -> tuple[ResourceCharge, ...]:
        return self._sum_charges(
            charge
            for segment in self.segments
            for charge in segment.costs
        )

    @property
    def consumption(self) -> tuple[ResourceCharge, ...]:
        return self._sum_charges(
            charge
            for segment in self.segments
            for charge in segment.resource_consumption
        )

    @staticmethod
    def _sum_charges(charges) -> tuple[ResourceCharge, ...]:
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for charge in charges:
            totals[charge.resource_code] += charge.quantity
        return tuple(
            ResourceCharge(resource_code=code, quantity=quantity)
            for code, quantity in sorted(totals.items())
        )


class GeographyHierarchyEngine:
    @staticmethod
    def validate_new_location(location, all_locations) -> None:
        locations = {item.location_id: item for item in all_locations}
        if location.parent_location_id is None:
            return
        parent = locations.get(location.parent_location_id)
        if parent is None:
            raise ValueError("Parent location does not exist")
        if parent.world_id != location.world_id:
            raise ValueError("Parent location belongs to another world")
        seen = {location.location_id}
        current = parent
        while current is not None:
            if current.location_id in seen:
                raise ValueError("Location hierarchy would contain a cycle")
            seen.add(current.location_id)
            current = (
                locations.get(current.parent_location_id)
                if current.parent_location_id is not None
                else None
            )

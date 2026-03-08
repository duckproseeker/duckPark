from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.scenario.registry import (
    BUILTIN_SCENARIOS,
    DEFAULT_EGO_BLUEPRINT,
    DEFAULT_SPAWN_POINT,
)


@dataclass(frozen=True)
class OfficialScenarioEntry:
    scenario_id: str
    class_name: str
    display_name: str
    source_file: str
    description: str


OFFICIAL_SCENARIO_ENTRIES: tuple[OfficialScenarioEntry, ...] = (
    OfficialScenarioEntry(scenario_id="enter_actor_flow", class_name="EnterActorFlow", display_name="Enter Actor Flow", source_file="actor_flow.py", description="This class holds everything required for a scenario in which another vehicle runs a red light"),
    OfficialScenarioEntry(scenario_id="highway_exit", class_name="HighwayExit", display_name="Highway Exit", source_file="actor_flow.py", description="This scenario is similar to CrossActorFlow"),
    OfficialScenarioEntry(scenario_id="merger_into_slow_traffic", class_name="MergerIntoSlowTraffic", display_name="Merger Into Slow Traffic", source_file="actor_flow.py", description="This scenario is similar to EnterActorFlow"),
    OfficialScenarioEntry(scenario_id="interurban_actor_flow", class_name="InterurbanActorFlow", display_name="Interurban Actor Flow", source_file="actor_flow.py", description="Scenario specifically made for the interurban intersections,"),
    OfficialScenarioEntry(scenario_id="interurban_advanced_actor_flow", class_name="InterurbanAdvancedActorFlow", display_name="Interurban Advanced Actor Flow", source_file="actor_flow.py", description="Scenario specifically made for the interurban intersections,"),
    OfficialScenarioEntry(scenario_id="blocked_intersection", class_name="BlockedIntersection", display_name="Blocked Intersection", source_file="blocked_intersection.py", description="This class holds everything required for a scenario in which,"),
    OfficialScenarioEntry(scenario_id="change_lane", class_name="ChangeLane", display_name="Change Lane", source_file="change_lane.py", description="This class holds everything required for a \"change lane\" scenario involving three vehicles."),
    OfficialScenarioEntry(scenario_id="construction_obstacle", class_name="ConstructionObstacle", display_name="Construction Obstacle", source_file="construction_crash_vehicle.py", description="This class holds everything required for a construction scenario"),
    OfficialScenarioEntry(scenario_id="control_loss", class_name="ControlLoss", display_name="Control Loss", source_file="control_loss.py", description="Implementation of \"Control Loss Vehicle\" (Traffic Scenario 01)"),
    OfficialScenarioEntry(scenario_id="crossing_bicycle_flow", class_name="CrossingBicycleFlow", display_name="Crossing Bicycle Flow", source_file="cross_bicycle_flow.py", description="This class holds everything required for a scenario in which another vehicle runs a red light"),
    OfficialScenarioEntry(scenario_id="cut_in", class_name="CutIn", display_name="Cut In", source_file="cut_in.py", description="The ego vehicle is driving on a highway and another car is cutting in just in front."),
    OfficialScenarioEntry(scenario_id="static_cut_in", class_name="StaticCutIn", display_name="Static Cut In", source_file="cut_in_with_static_vehicle.py", description="Cut in(with static vehicle) scenario synchronizes a vehicle that is parked at a side lane"),
    OfficialScenarioEntry(scenario_id="follow_leading_vehicle", class_name="FollowLeadingVehicle", display_name="Follow Leading Vehicle", source_file="follow_leading_vehicle.py", description="This class holds everything required for a simple \"Follow a leading vehicle\""),
    OfficialScenarioEntry(scenario_id="follow_leading_vehicle_with_obstacle", class_name="FollowLeadingVehicleWithObstacle", display_name="Follow Leading Vehicle With Obstacle", source_file="follow_leading_vehicle.py", description="This class holds a scenario similar to FollowLeadingVehicle"),
    OfficialScenarioEntry(scenario_id="free_ride", class_name="FreeRide", display_name="Free Ride", source_file="freeride.py", description="Implementation of a simple free ride scenario that consits only of the ego vehicle"),
    OfficialScenarioEntry(scenario_id="priority_at_junction", class_name="PriorityAtJunction", display_name="Priority At Junction", source_file="green_traffic_light.py", description="Sets the ego incoming traffic light to green. Support scenario at routes"),
    OfficialScenarioEntry(scenario_id="hard_break_route", class_name="HardBreakRoute", display_name="Hard Break Route", source_file="hard_break.py", description="This class uses the is the Background Activity at routes to create a hard break scenario."),
    OfficialScenarioEntry(scenario_id="highway_cut_in", class_name="HighwayCutIn", display_name="Highway Cut In", source_file="highway_cut_in.py", description="This class holds everything required for a scenario in which another vehicle runs a red light"),
    OfficialScenarioEntry(scenario_id="invading_turn", class_name="InvadingTurn", display_name="Invading Turn", source_file="invading_turn.py", description="This class holds everything required for a scenario in which the ego is about to turn right"),
    OfficialScenarioEntry(scenario_id="maneuver_opposite_direction", class_name="ManeuverOppositeDirection", display_name="Maneuver Opposite Direction", source_file="maneuver_opposite_direction.py", description="\"Vehicle Maneuvering In Opposite Direction\" (Traffic Scenario 06)"),
    OfficialScenarioEntry(scenario_id="no_signal_junction_crossing", class_name="NoSignalJunctionCrossing", display_name="No Signal Junction Crossing", source_file="no_signal_junction_crossing.py", description="Implementation class for"),
    OfficialScenarioEntry(scenario_id="no_signal_junction_crossing_route", class_name="NoSignalJunctionCrossingRoute", display_name="No Signal Junction Crossing Route", source_file="no_signal_junction_crossing.py", description="At routes, these scenarios are simplified, as they can be triggered making"),
    OfficialScenarioEntry(scenario_id="base_vehicle_turning", class_name="BaseVehicleTurning", display_name="Base Vehicle Turning", source_file="object_crash_intersection.py", description="This class holds everything required for a simple object crash"),
    OfficialScenarioEntry(scenario_id="vehicle_turning_route_pedestrian", class_name="VehicleTurningRoutePedestrian", display_name="Vehicle Turning Route Pedestrian", source_file="object_crash_intersection.py", description="This class holds everything required for a simple object crash"),
    OfficialScenarioEntry(scenario_id="stationary_object_crossing", class_name="StationaryObjectCrossing", display_name="Stationary Object Crossing", source_file="object_crash_vehicle.py", description="This class holds everything required for a simple object crash"),
    OfficialScenarioEntry(scenario_id="dynamic_object_crossing", class_name="DynamicObjectCrossing", display_name="Dynamic Object Crossing", source_file="object_crash_vehicle.py", description="This class holds everything required for a simple object crash"),
    OfficialScenarioEntry(scenario_id="parking_crossing_pedestrian", class_name="ParkingCrossingPedestrian", display_name="Parking Crossing Pedestrian", source_file="object_crash_vehicle.py", description="Variation of DynamicObjectCrossing but now the blocker is now a vehicle"),
    OfficialScenarioEntry(scenario_id="opposite_vehicle_junction", class_name="OppositeVehicleJunction", display_name="Opposite Vehicle Junction", source_file="opposite_vehicle_taking_priority.py", description="Scenario in which another vehicle enters the junction a tthe same time as the ego,"),
    OfficialScenarioEntry(scenario_id="other_leading_vehicle", class_name="OtherLeadingVehicle", display_name="Other Leading Vehicle", source_file="other_leading_vehicle.py", description="This class holds everything required for a simple \"Other Leading Vehicle\""),
    OfficialScenarioEntry(scenario_id="parking_cut_in", class_name="ParkingCutIn", display_name="Parking Cut In", source_file="parking_cut_in.py", description="Parking cut in scenario synchronizes a vehicle that is parked at a side lane"),
    OfficialScenarioEntry(scenario_id="parking_exit", class_name="ParkingExit", display_name="Parking Exit", source_file="parking_exit.py", description="This class holds everything required for a scenario in which the ego would be teleported to the parking lane."),
    OfficialScenarioEntry(scenario_id="pedestrian_crossing", class_name="PedestrianCrossing", display_name="Pedestrian Crossing", source_file="pedestrian_crossing.py", description="This class holds everything required for a group of natual pedestrians crossing the road."),
    OfficialScenarioEntry(scenario_id="accident", class_name="Accident", display_name="Accident", source_file="route_obstacles.py", description="This class holds everything required for a scenario in which there is an accident"),
    OfficialScenarioEntry(scenario_id="parked_obstacle", class_name="ParkedObstacle", display_name="Parked Obstacle", source_file="route_obstacles.py", description="Scenarios in which a parked vehicle is incorrectly parked,"),
    OfficialScenarioEntry(scenario_id="hazard_at_side_lane", class_name="HazardAtSideLane", display_name="Hazard At Side Lane", source_file="route_obstacles.py", description="Added the dangerous scene of ego vehicles driving on roads without sidewalks,"),
    OfficialScenarioEntry(scenario_id="junction_left_turn", class_name="JunctionLeftTurn", display_name="Junction Left Turn", source_file="signalized_junction_left_turn.py", description="Vehicle turning left at junction scenario, with actors coming in the opposite direction."),
    OfficialScenarioEntry(scenario_id="junction_right_turn", class_name="JunctionRightTurn", display_name="Junction Right Turn", source_file="signalized_junction_right_turn.py", description="Scenario where the vehicle is turning right at an intersection an has to avoid"),
    OfficialScenarioEntry(scenario_id="vehicle_opens_door_two_ways", class_name="VehicleOpensDoorTwoWays", display_name="Vehicle Opens Door Two Ways", source_file="vehicle_opens_door.py", description="This class holds everything required for a scenario in which another vehicle parked at the side lane"),
    OfficialScenarioEntry(scenario_id="yield_to_emergency_vehicle", class_name="YieldToEmergencyVehicle", display_name="Yield To Emergency Vehicle", source_file="yield_to_emergency_vehicle.py", description="This class holds everything required for a scenario in which the ego has to yield its lane to emergency vehicle."),
)


def _descriptor_template(
    scenario_name: str,
    map_name: str,
    description: str,
    tags: list[str],
) -> dict[str, Any]:
    return {
        "version": 1,
        "scenario_name": scenario_name,
        "map_name": map_name,
        "weather": {"preset": "ClearNoon"},
        "sync": {"enabled": True, "fixed_delta_seconds": 0.05},
        "ego_vehicle": {
            "blueprint": DEFAULT_EGO_BLUEPRINT,
            "spawn_point": DEFAULT_SPAWN_POINT,
        },
        "traffic": {"enabled": False, "num_vehicles": 0, "num_walkers": 0},
        "sensors": {"enabled": False, "sensors": []},
        "termination": {"timeout_seconds": 30, "success_condition": "timeout"},
        "recorder": {"enabled": False},
        "debug": {"viewer_friendly": False},
        "metadata": {
            "author": "scenario-library",
            "tags": tags,
            "description": description,
        },
    }


def list_scenario_catalog() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    for spec in BUILTIN_SCENARIOS.values():
        entries.append(
            {
                "scenario_id": spec.scenario_name,
                "scenario_name": spec.scenario_name,
                "display_name": spec.display_name,
                "description": spec.description,
                "default_map_name": spec.default_map_name,
                "execution_support": "native",
                "source": {
                    "provider": "duckpark",
                    "reference": spec.module.__name__,
                },
                "descriptor_template": _descriptor_template(
                    scenario_name=spec.scenario_name,
                    map_name=spec.default_map_name,
                    description=f"{spec.display_name}（本地可执行场景）",
                    tags=["native", spec.scenario_name],
                ),
            }
        )

    for item in OFFICIAL_SCENARIO_ENTRIES:
        entries.append(
            {
                "scenario_id": item.scenario_id,
                "scenario_name": item.scenario_id,
                "display_name": item.display_name,
                "description": item.description,
                "default_map_name": "Town01",
                "execution_support": "catalog_only",
                "source": {
                    "provider": "scenario_runner",
                    "version": "v0.9.16",
                    "class_name": item.class_name,
                    "source_file": item.source_file,
                },
                "descriptor_template": _descriptor_template(
                    scenario_name=item.scenario_id,
                    map_name="Town01",
                    description=f"{item.display_name}（官方 ScenarioRunner 模板导入）",
                    tags=["catalog-only", item.scenario_id],
                ),
            }
        )

    return entries

from typing import List, Tuple, cast

import unrealsdk
from unrealsdk import *

from .placeable import AbstractPlaceable
from .. import bl2tools
from .. import canvasutils
from .. import settings


class AIPawnBalanceDefinition(AbstractPlaceable):
    def __init__(self, name: str, ai_pawn_balance: unrealsdk.UObject, ai_pawn: unrealsdk.UObject = None):
        super().__init__(name, "AIPawnBalanceDefinition")
        self.ai_pawn_balance: unrealsdk.UObject = ai_pawn_balance
        self.ai_pawn: unrealsdk.UObject = ai_pawn

    def set_scale(self, scale: float) -> None:
        if self.ai_pawn:
            self.ai_pawn.Mesh.Scale = scale

    def get_scale(self) -> float:
        if self.ai_pawn:
            return self.ai_pawn.Mesh.Scale
        return 1

    def add_scale(self, scale: float) -> None:
        if self.ai_pawn:
            self.ai_pawn.Mesh.Scale += scale

    def set_rotation(self, rotator: iter) -> None:
        if self.ai_pawn:
            self.ai_pawn.Mesh.Rotation = tuple(rotator)

    def get_rotation(self) -> iter:
        if not self.ai_pawn:
            return [0, 0, 0]
        return [self.ai_pawn.Mesh.Rotation.Pitch,
                self.ai_pawn.Mesh.Rotation.Yaw,
                self.ai_pawn.Mesh.Rotation.Roll]

    def add_rotation(self, rotator: iter) -> None:
        if self.ai_pawn:
            pitch, yaw, roll = rotator
            self.ai_pawn.Mesh.Rotation.Pitch += pitch
            self.ai_pawn.Mesh.Rotation.Yaw += yaw
            self.ai_pawn.Mesh.Rotation.Roll += roll

    def set_location(self, position: iter) -> None:
        if self.ai_pawn:
            self.ai_pawn.Location = tuple(position)

    def get_location(self) -> iter:
        if not self.ai_pawn:
            return [0, 0, 0]
        return [self.ai_pawn.Location.X,
                self.ai_pawn.Location.Y,
                self.ai_pawn.Location.Z]

    def draw_debug_box(self, player_controller) -> None:
        if self.ai_pawn:
            player_controller.DrawDebugBox((self.ai_pawn.CollisionComponent.Bounds.Origin.X,
                                            self.ai_pawn.CollisionComponent.Bounds.Origin.Y,
                                            self.ai_pawn.CollisionComponent.Bounds.Origin.Z),
                                           (self.ai_pawn.CollisionComponent.Bounds.BoxExtent.X,
                                            self.ai_pawn.CollisionComponent.Bounds.BoxExtent.Y,
                                            self.ai_pawn.CollisionComponent.Bounds.BoxExtent.Z),
                                           *settings.draw_debug_box_color)

    def draw_debug_origin(self, canvas, player_controller) -> None:
        if self.ai_pawn:
            screen_x, screen_y = canvasutils.world_to_screen(canvas, self.get_location(),
                                                             [player_controller.CalcViewRotation.Pitch,
                                                              player_controller.CalcViewRotation.Yaw,
                                                              player_controller.CalcViewRotation.Roll],
                                                             [player_controller.Location.X,
                                                              player_controller.Location.Y,
                                                              player_controller.Location.Z],
                                                             player_controller.ToHFOV(player_controller.GetFOVAngle()))
            canvasutils.draw_box(canvas, 5, 5, screen_x - 5, screen_y - 5, settings.draw_debug_origin_color)

    def instantiate(self) -> Tuple[AbstractPlaceable, List[AbstractPlaceable]]:
        pc = bl2tools.get_player_controller()
        _loc = (pc.Location.X, pc.Location.Y, pc.Location.Z)
        pop_master = unrealsdk.FindAll("WillowPopulationMaster")[-1]
        pawn = pop_master.SpawnPopulationControlledActor(self.ai_pawn_balance.AIPawnArchetype.Class,
                                                         None, "", _loc, (0, 0, 0),
                                                         self.ai_pawn_balance.AIPawnArchetype,
                                                         False, False)
        ret = AIPawnBalanceDefinition(self.name, self.ai_pawn_balance, pawn)

        if pc.GetCurrentPlaythrough() != 2:
            will_pop = unrealsdk.FindAll("WillowPopulationOpportunityPoint")[1:]
            pop = unrealsdk.FindAll("PopulationOpportunityPoint")[1:]
            regions = pop if len(pop) > len(will_pop) else will_pop
            region_game_stage = max(pc.GetGameStageFromRegion(x.GameStageRegion)
                                    for x in regions if x.GameStageRegion)
        else:
            region_game_stage = max(x.GetGameStage() for x in unrealsdk.FindAll("WillowPlayerPawn") if x.Arms)
        # PopulationFactoryBalancedAIPawn 105-120:
        pawn.SetGameStage(region_game_stage)
        pawn.SetExpLevel(region_game_stage)
        pawn.SetGameStageForSpawnedInventory(region_game_stage)
        pawn.SetAwesomeLevel(0)
        pawn.Controller.InitializeCharacterClass()
        pawn.Controller.RecalculateAttributeInitializedState()
        pawn.InitializeBalanceDefinitionState(self.ai_pawn_balance, -1)
        self.ai_pawn_balance.SetupPawnItemPoolList(pawn)
        pawn.AddDefaultInventory()

        ai = pawn.MyWillowMind.GetAIDefinition()
        ai.TargetSearchRadius = 12000

        return ret, [ret, ]

    def get_preview(self) -> AbstractPlaceable:
        ret = cast(AIPawnBalanceDefinition, self.instantiate()[0])
        ret.set_scale(1 / (ret.ai_pawn.Mesh.SkeletalMesh.Bounds.SphereRadius / 60))
        return ret

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: str) -> bool:
        return bl2tools.get_obj_path_name(self.ai_pawn_balance) == uobject \
               or bl2tools.get_obj_path_name(self.ai_pawn) == uobject

    def destroy(self) -> List[AbstractPlaceable]:
        if not self.ai_pawn:
            raise ValueError("Cannot destroy not instantiated Object!")

        self.set_location((-9999999, -9999999, -9999999))  # let's just move the pawn out of our sight
        self.ai_pawn.Destroyed()
        self.set_scale(0)
        self.is_destroyed = True
        return [self, ]

    def store_default_values(self, default_dict: dict) -> None:
        pass

    def restore_default_values(self, default_dict: dict) -> None:
        pass

    def save_to_json(self, saved_json: dict) -> None:
        pawns = saved_json.setdefault("Create", {}).setdefault("AIPawnBalanceDefinition", [])
        pawns.append({bl2tools.get_obj_path_name(self.ai_pawn_balance): {"Location": list(self.get_location()),
                                                                         "Rotation": list(self.get_rotation()),
                                                                         "Scale": self.get_scale()}})

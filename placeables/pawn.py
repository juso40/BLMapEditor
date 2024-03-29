from typing import List, Tuple, Union, cast

import unrealsdk  # type: ignore

from .. import bl2tools
from .placeable import AbstractPlaceable


class AIPawnBalanceDefinition(AbstractPlaceable):
    def __init__(self, name: str, ai_pawn_balance: unrealsdk.UObject, ai_pawn: unrealsdk.UObject = None) -> None:
        super().__init__(name, "AIPawnBalanceDefinition")
        self.ai_pawn_balance: unrealsdk.UObject = ai_pawn_balance
        self.ai_pawn: unrealsdk.UObject = ai_pawn
        self.uobject_path_name: str = bl2tools.get_obj_path_name(self.ai_pawn_balance)

    def get_materials(self) -> List[unrealsdk.UObject]:
        if self.ai_pawn and self.ai_pawn.Mesh:
            return [x for x in self.ai_pawn.Mesh.Materials]  # noqa: C416
        return []

    def set_materials(self, materials: List[unrealsdk.UObject]) -> None:
        if self.ai_pawn and self.ai_pawn.Mesh and materials is not None:
            self.ai_pawn.Mesh.Materials = materials

    def add_material(self, material: unrealsdk.UObject) -> None:
        super().add_material(material)

    def remove_material(self, material: unrealsdk.UObject = None, index: int = -1) -> None:
        super().remove_material(material, index)

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
            self.ai_pawn.Mesh.ForceUpdate(True)

    def get_scale3d(self) -> List[float]:
        if not self.ai_pawn:
            return [1, 1, 1]
        return [self.ai_pawn.Mesh.Scale3D.X, self.ai_pawn.Mesh.Scale3D.Y, self.ai_pawn.Mesh.Scale3D.Z]

    def set_scale3d(self, scale3d: List[float]) -> None:
        self.ai_pawn.Mesh.Scale3D = tuple(scale3d)
        self.ai_pawn.Mesh.ForceUpdate(True)

    def set_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        if self.ai_pawn:
            self.ai_pawn.Mesh.Rotation = tuple(rotator)
            self.ai_pawn.Mesh.ForceUpdate(True)

    def get_rotation(self) -> List[int]:
        if not self.ai_pawn:
            return [0, 0, 0]
        return [self.ai_pawn.Mesh.Rotation.Pitch, self.ai_pawn.Mesh.Rotation.Yaw, self.ai_pawn.Mesh.Rotation.Roll]

    def add_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        if self.ai_pawn:
            pitch, yaw, roll = rotator
            self.ai_pawn.Mesh.Rotation.Pitch += pitch
            self.ai_pawn.Mesh.Rotation.Yaw += yaw
            self.ai_pawn.Mesh.Rotation.Roll += roll
            self.ai_pawn.Mesh.ForceUpdate(True)

    def set_location(self, position: Union[List[float], Tuple[float, float, float]]) -> None:
        if self.ai_pawn:
            self.ai_pawn.Location = tuple(position)

    def get_location(self) -> List[float]:
        if not self.ai_pawn:
            return [0, 0, 0]
        return [self.ai_pawn.Location.X, self.ai_pawn.Location.Y, self.ai_pawn.Location.Z]

    def get_bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        if self.ai_pawn:
            cc = self.ai_pawn.CollisionComponent
            return (
                (cc.Bounds.Origin.X, cc.Bounds.Origin.Y, cc.Bounds.Origin.Z),
                (cc.Bounds.BoxExtent.X, cc.Bounds.BoxExtent.Y, cc.Bounds.BoxExtent.Z),
            )
        return (0, 0, 0), (0, 0, 0)

    def instantiate(self) -> Tuple["AIPawnBalanceDefinition", List["AIPawnBalanceDefinition"]]:
        pc = bl2tools.get_player_controller()
        _loc = (pc.Location.X, pc.Location.Y, pc.Location.Z)
        pop_master = unrealsdk.FindAll("WillowPopulationMaster")[-1]
        pawn = pop_master.SpawnPopulationControlledActor(
            self.ai_pawn_balance.AIPawnArchetype.Class,
            None,
            "",
            _loc,
            (0, 0, 0),
            self.ai_pawn_balance.AIPawnArchetype,
            False,
            False,
        )
        ret = AIPawnBalanceDefinition(self.name, self.ai_pawn_balance, pawn)

        if pc.GetCurrentPlaythrough() != 2:
            will_pop = unrealsdk.FindAll("WillowPopulationOpportunityPoint")[1:]
            pop = unrealsdk.FindAll("PopulationOpportunityPoint")[1:]
            regions = pop if len(pop) > len(will_pop) else will_pop
            region_game_stage = max(pc.GetGameStageFromRegion(x.GameStageRegion) for x in regions if x.GameStageRegion)
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
        self.b_dynamically_created = True

        return ret, [
            ret,
        ]

    def get_preview(self) -> "AIPawnBalanceDefinition":
        ret = cast(AIPawnBalanceDefinition, self.instantiate()[0])
        ret.set_scale(1 / (ret.ai_pawn.Mesh.SkeletalMesh.Bounds.SphereRadius / 60))
        return ret

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unrealsdk.UObject) -> bool:
        return self.ai_pawn_balance is uobject or self.ai_pawn is uobject

    def destroy(self) -> List["AIPawnBalanceDefinition"]:
        if not self.ai_pawn:
            raise ValueError("Cannot destroy not instantiated Object!")

        self.set_location((-9999999, -9999999, -9999999))  # let's just move the pawn out of our sight
        self.ai_pawn.Destroyed()
        self.set_scale(0)
        self.is_destroyed = True
        return [
            self,
        ]

    def store_default_values(self, default_dict: dict) -> None:
        pass

    def restore_default_values(self, default_dict: dict) -> None:
        pass

    def save_to_json(self, saved_json: dict) -> None:
        cleaned_tags: List[str] = [x.strip() for x in self.tags if x.strip()]

        pawns = saved_json.setdefault("Create", {}).setdefault("AIPawnBalanceDefinition", [])
        pawns.append(
            {
                self.uobject_path_name: {
                    "Rename": self.rename,
                    "Tags": cleaned_tags,
                    "Metadata": self.metadata,
                    "Location": self.get_location(),
                    "Rotation": self.get_rotation(),
                    "Scale": self.get_scale(),
                    "Scale3D": self.get_scale3d(),
                    "Materials": [bl2tools.get_obj_path_name(x) for x in self.get_materials()],
                },
            },
        )


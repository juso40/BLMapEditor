from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mods_base import ENGINE, get_pc
from unrealsdk import find_all, make_struct, unreal

from .placeable import AbstractPlaceable

if TYPE_CHECKING:
    from common import AIPawnBalanceDefinition, MaterialInterface, Object, WillowPawn

    make_vector = Object.Vector.make_struct

else:
    make_vector = make_struct


class AIPawnPlaceable(AbstractPlaceable):
    def __init__(self, name: str, ai_pawn_balance: AIPawnBalanceDefinition, ai_pawn: WillowPawn | None = None) -> None:
        super().__init__(name, "AIPawnBalanceDefinition")
        self.ai_pawn_balance: AIPawnBalanceDefinition = ai_pawn_balance
        self.ai_pawn: WillowPawn | None = ai_pawn
        self.uobject_path_name: str = ENGINE.PathName(self.ai_pawn_balance)

    def get_materials(self) -> list[MaterialInterface]:
        if self.ai_pawn and self.ai_pawn.Mesh:
            return [x for x in self.ai_pawn.Mesh.Materials]  # noqa: C416
        return []

    def set_materials(self, materials: list[MaterialInterface]) -> None:
        if self.ai_pawn and self.ai_pawn.Mesh and materials is not None:
            self.ai_pawn.Mesh.Materials = materials

    def add_material(self, material: MaterialInterface) -> None:
        super().add_material(material)

    def remove_material(self, material: MaterialInterface | None = None, index: int = -1) -> None:
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

    def get_scale3d(self) -> list[float]:
        if not self.ai_pawn:
            return [1, 1, 1]
        return [self.ai_pawn.Mesh.Scale3D.X, self.ai_pawn.Mesh.Scale3D.Y, self.ai_pawn.Mesh.Scale3D.Z]

    def set_scale3d(self, scale3d: list[float]) -> None:
        if not self.ai_pawn:
            return
        x, y, z = scale3d
        self.ai_pawn.Mesh.Scale3D.X = x
        self.ai_pawn.Mesh.Scale3D.Y = y
        self.ai_pawn.Mesh.Scale3D.Z = z
        self.ai_pawn.Mesh.ForceUpdate(True)

    def set_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        if not self.ai_pawn:
            return
        pitch, yaw, roll = rotator
        self.ai_pawn.Mesh.Rotation.Pitch = pitch
        self.ai_pawn.Mesh.Rotation.Yaw = yaw
        self.ai_pawn.Mesh.Rotation.Roll = roll
        self.ai_pawn.Mesh.ForceUpdate(True)

    def get_rotation(self) -> list[int]:
        if not self.ai_pawn:
            return [0, 0, 0]
        return [self.ai_pawn.Mesh.Rotation.Pitch, self.ai_pawn.Mesh.Rotation.Yaw, self.ai_pawn.Mesh.Rotation.Roll]

    def add_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        if self.ai_pawn:
            pitch, yaw, roll = rotator
            self.ai_pawn.Mesh.Rotation.Pitch += pitch
            self.ai_pawn.Mesh.Rotation.Yaw += yaw
            self.ai_pawn.Mesh.Rotation.Roll += roll
            self.ai_pawn.Mesh.ForceUpdate(True)

    def set_location(self, position: list[float] | tuple[float, float, float]) -> None:
        if not self.ai_pawn:
            return
        x, y, z = position
        self.ai_pawn.Location.X = x
        self.ai_pawn.Location.Y = y
        self.ai_pawn.Location.Z = z

    def get_location(self) -> list[float]:
        if not self.ai_pawn:
            return [0, 0, 0]
        return [self.ai_pawn.Location.X, self.ai_pawn.Location.Y, self.ai_pawn.Location.Z]

    def get_bounding_box(self) -> tuple[Object.Vector, Object.Vector]:
        if self.ai_pawn:
            cc = self.ai_pawn.CollisionComponent
            return (cc.Bounds.Origin, cc.Bounds.BoxExtent)
        return make_vector("Vector", X=0, Y=0, Z=0), make_vector("Vector", X=0, Y=0, Z=0)

    def instantiate(self) -> tuple[AIPawnPlaceable, list[AIPawnPlaceable]]:
        pc = get_pc()
        _loc = (pc.Location.X, pc.Location.Y, pc.Location.Z)
        pop_master = list(find_all("WillowPopulationMaster"))[-1]
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
        ret = AIPawnPlaceable(self.name, self.ai_pawn_balance, pawn)

        if pc.GetCurrentPlaythrough() != 2:
            will_pop = list(find_all("WillowPopulationOpportunityPoint"))[1:]
            pop = list(find_all("PopulationOpportunityPoint"))[1:]
            regions = pop if len(pop) > len(will_pop) else will_pop
            region_game_stage = max(pc.GetGameStageFromRegion(x.GameStageRegion) for x in regions if x.GameStageRegion)
        else:
            region_game_stage = max(x.GetGameStage() for x in find_all("WillowPlayerPawn") if x.Arms)
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

    def get_preview(self) -> AIPawnPlaceable:
        ret = cast(AIPawnPlaceable, self.instantiate()[0])
        assert ret.ai_pawn is not None, "Instantiate should return a valid WillowPawn!"
        ret.set_scale(1 / (ret.ai_pawn.Mesh.SkeletalMesh.Bounds.SphereRadius / 60))
        return ret

    def set_preview_location(self, location: tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unreal.UObject) -> bool:
        return self.ai_pawn_balance is uobject or self.ai_pawn is uobject

    def destroy(self) -> list[AIPawnPlaceable]:
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
        cleaned_tags: list[str] = [x.strip() for x in self.tags if x.strip()]

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
                    "Materials": [ENGINE.PathName(x) for x in self.get_materials()],
                },
            },
        )

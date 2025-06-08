from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mods_base import ENGINE, get_pc
from unrealsdk import construct_object, find_all, find_class, find_object, make_struct, unreal

from .placeable import AbstractPlaceable

if TYPE_CHECKING:
    from common import (
        BaseBalanceDefinition,
        InteractiveObjectDefinition,
        MaterialInterface,
        Object,
        WillowInteractiveObject,
    )

    make_vector = Object.Vector.make_struct

else:
    make_vector = make_struct


def _initialize_vending_machine(iobject: unreal.UObject) -> None:
    vending_name: str = iobject.InteractiveObjectDefinition._path_name().lower()

    if "health" in vending_name:
        iobject.ShopType = 2
    elif "ammo" in vending_name:
        iobject.ShopType = 1
    else:
        iobject.ShopType = 0

    gamestage = find_object(
        "AttributeInitializationDefinition",
        "GD_Population_Shopping.Balance.Init_FeaturedItem_GameStage",
    )
    if "seraph" in vending_name:
        iobject.FixedItemCost = 120
        iobject.FixedFeaturedItemCost = 50
        iobject.FormOfCurrency = 2
        markup = None
        awesome = None
    elif "torgue" in vending_name:
        iobject.FixedItemCost = -1
        iobject.FixedFeaturedItemCost = 613
        iobject.FormOfCurrency = 4
        markup = find_object(
            "AttributeInitializationDefinition",
            "GD_Iris_TorgueTokenVendor.CommerceMarkup",
        )
        gamestage = find_object(
            "AttributeInitializationDefinition",
            "GD_Iris_TorgueTokenVendor.Balance.Init_FeaturedItem_GameStage",
        )
        awesome = None
    else:
        iobject.FixedItemCost = -1
        iobject.FixedFeaturedItemCost = -1
        iobject.FormOfCurrency = 0
        markup = find_object(
            "AttributeInitializationDefinition",
            "GD_Economy.VendingMachine.Init_MarkupCalc_P1",
        )
        awesome = find_object(
            "AttributeInitializationDefinition",
            "GD_Population_Shopping.Balance.Init_FeaturedItem_AwesomeLevel",
        )

    iobject.bOverrideFormOfCurrency = True

    iobject.CommerceMarkup = (1, None, markup, 1)
    iobject.InventoryConfigurationName = "Inventory"
    iobject.FeaturedItemCommerceMarkup = (int("torgue" in vending_name), None, markup, 1)
    iobject.FeaturedItemConfigurationName = "FeaturedItem"
    iobject.FeaturedItemGameStage = (int(awesome is None), None, gamestage, 1)
    iobject.FeaturedItemAwesomeLevel = (0, None, awesome, 1)

    iobject.ResetInventory()

    if "blackmarket" in vending_name:
        iobject.ShopType = 3
        iobject.DefinitionData = find_object(
            "BlackMarketDefinition",
            "GD_BlackMarket.BlackMarket.MarketDef_BlackMarket",
        )
        iobject.FixedItemCost = 0
        iobject.FixedFeaturedItemCost = 0


def _initialize_fast_travel_station(iobject: unreal.UObject) -> None:
    tp = iobject.TeleportDest
    new_tp = construct_object(cls=tp.Class, template_obj=tp, outer=tp.Outer, flags=0x400004000)
    iobject.TeleportDest = new_tp
    iobject.TeleportDest.UpdateExitPointLocations()
    iobject.TeleportDest.UpdateExitPointHeights()


class InteractiveObjectPlaceable(AbstractPlaceable):
    def __init__(
        self,
        name: str,
        iobject_definition: InteractiveObjectDefinition | BaseBalanceDefinition,
        iobject: WillowInteractiveObject | None = None,
    ) -> None:
        super().__init__(name, "InteractiveObjectDefinition")
        self.io_definition: InteractiveObjectDefinition | BaseBalanceDefinition = iobject_definition
        self.iobject: WillowInteractiveObject | None = iobject
        self.io_name: str = ""
        self.uobject_path_name: str = self.io_definition._path_name()

    def get_materials(self) -> list[MaterialInterface]:
        if self.iobject and self.iobject.ObjectMesh:
            return [x for x in self.iobject.ObjectMesh.Materials]  # noqa: C416
        return []

    def set_materials(self, materials: list[MaterialInterface]) -> None:
        # because chests and some other IO generate Materials on spawning them, its very likely that the exported
        # list of materials wont work, just to be safe, ignore all kind of materials for InteractiveObjects
        # untill i find a better fix
        return
        if self.iobject and self.iobject.ObjectMesh and materials:
            self.iobject.ObjectMesh.Materials = materials

    def add_material(self, material: MaterialInterface) -> None:
        super().add_material(material)

    def remove_material(self, material: MaterialInterface | None = None, index: int = -1) -> None:
        super().remove_material(material, index)

    def set_scale(self, scale: float) -> None:
        if self.iobject:
            self.iobject.DrawScale = scale
            self.b_default_attributes = False

    def get_scale(self) -> float:
        if self.iobject:
            return self.iobject.DrawScale
        return 1

    def add_scale(self, scale: float) -> None:
        if self.iobject:
            self.iobject.DrawScale += scale

    def get_scale3d(self) -> list[float]:
        if not self.iobject:
            return [1, 1, 1]
        return [self.iobject.DrawScale3D.X, self.iobject.DrawScale3D.Y, self.iobject.DrawScale3D.Z]

    def set_scale3d(self, scale3d: list[float]) -> None:
        if not self.iobject:
            return
        x, y, z = scale3d
        self.iobject.DrawScale3D.X = x
        self.iobject.DrawScale3D.Y = y
        self.iobject.DrawScale3D.Z = z
        self.b_default_attributes = False

    def set_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        if not self.iobject:
            return
        pitch, yaw, roll = rotator
        self.iobject.Rotation.Pitch = pitch
        self.iobject.Rotation.Yaw = yaw
        self.iobject.Rotation.Roll = roll
        self.b_default_attributes = False

    def get_rotation(self) -> list[int]:
        if not self.iobject:
            return [0, 0, 0]
        return [self.iobject.Rotation.Pitch, self.iobject.Rotation.Yaw, self.iobject.Rotation.Roll]

    def add_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        if self.iobject:
            pitch, yaw, roll = rotator
            self.iobject.Rotation.Pitch += pitch
            self.iobject.Rotation.Yaw += yaw
            self.iobject.Rotation.Roll += roll
            self.b_default_attributes = False

    def set_location(self, position: list[float] | tuple[float, float, float]) -> None:
        if not self.iobject:
            return
        x, y, z = position
        self.iobject.Location.X = x
        self.iobject.Location.Y = y
        self.iobject.Location.Z = z
        self.b_default_attributes = False

    def get_location(self) -> list[float]:
        if not self.iobject:
            return [0, 0, 0]
        return [self.iobject.Location.X, self.iobject.Location.Y, self.iobject.Location.Z]

    def get_bounding_box(self) -> tuple[Object.Vector, Object.Vector]:
        x, y, z = self.get_location()
        return make_vector("Vector", X=x, Y=y, Z=z), make_vector("Vector", X=250, Y=250, Z=250)

    def instantiate(self) -> tuple[InteractiveObjectPlaceable, list[InteractiveObjectPlaceable]]:
        pc = get_pc()
        _loc = (pc.Location.X, pc.Location.Y, pc.Location.Z)
        pop_master = list(find_all("WillowPopulationMaster"))[-1]

        is_bal_def = self.io_definition.Class.Name == "InteractiveObjectBalanceDefinition"
        if is_bal_def:
            iobject = pop_master.SpawnPopulationControlledActor(
                self.io_definition.DefaultInteractiveObject.InteractiveObjectClass,
                None,
                "",
                _loc,
                (0, 0, 0),
            )
        else:
            iobject = pop_master.SpawnPopulationControlledActor(
                self.io_definition.InteractiveObjectClass,
                None,
                "",
                _loc,
                (0, 0, 0),
            )

        ret = InteractiveObjectPlaceable(self.name, self.io_definition, iobject)

        if pc.GetCurrentPlaythrough() != 2:
            will_pop = list(find_all("WillowPopulationOpportunityPoint"))[1:]
            pop = list(find_all("PopulationOpportunityPoint"))[1:]
            regions = pop if len(pop) > len(will_pop) else will_pop
            region_game_stage = max(pc.GetGameStageFromRegion(x.GameStageRegion) for x in regions if x.GameStageRegion)
        else:
            region_game_stage = max(x.GetGameStage() for x in find_all("WillowPlayerPawn") if x.Arms)

        iobject.SetGameStage(region_game_stage)
        iobject.SetExpLevel(region_game_stage)

        iobject.PostBeginPlay()

        if is_bal_def:
            x = self.io_definition.SelectGradeIndex(region_game_stage, 0)
            iobject.InitializeBalanceDefinitionState(self.io_definition, x)
            self.io_definition.SetupInteractiveObjectLoot(iobject, x)
            iobject.InitializeFromDefinition(self.io_definition.DefaultInteractiveObject, False)

            if iobject.Class.Name in ("WillowVendingMachine", "WillowVendingMachineBlackMarket"):
                _initialize_vending_machine(iobject)
        else:
            iobject.InitializeFromDefinition(self.io_definition, False)
            if "TravelStation" in iobject.InteractiveObjectDefinition.Name:
                iobject.Class = find_class("FastTravelStation")
                print(iobject.PathName(iobject))
                _initialize_fast_travel_station(iobject)
                # This only ever produces WillowInteractiveObject, not TravelStation

        ret.b_dynamically_created = True
        return ret, [
            ret,
        ]

    def get_preview(self) -> InteractiveObjectPlaceable:
        ret = cast(InteractiveObjectPlaceable, self.instantiate()[0])
        ret.set_scale(0.2)
        return ret

    def set_preview_location(self, location: tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unreal.UObject) -> bool:
        return self.io_definition is uobject or self.iobject is uobject

    def destroy(self) -> list[InteractiveObjectPlaceable]:
        if not self.iobject:
            raise ValueError("Cannot destroy not instantiated Object!")

        if not self.b_dynamically_created:
            self.io_name = ENGINE.PathName(self.iobject)
        self.iobject.Destroyed()
        self.set_location((-9999999, -9999999, -9999999))
        self.set_scale(0)
        self.is_destroyed = True
        return [self]

    def store_default_values(self, default_dict: dict) -> None:
        if self.iobject and ENGINE.PathName(self.iobject) not in default_dict:
            default_dict[ENGINE.PathName(self.iobject)] = {
                "Location": list(self.get_location()),
                "Rotation": list(self.get_rotation()),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [ENGINE.PathName(x) for x in self.get_materials()],
            }

    def restore_default_values(self, default_dict: dict) -> None:
        if self.iobject and ENGINE.PathName(self.iobject) in default_dict:
            defaults = default_dict[ENGINE.PathName(self.iobject)]
            self.set_scale(defaults["Scale"])
            self.set_location(defaults["Location"])
            self.set_rotation(defaults["Rotation"])
            self.set_scale3d(defaults["Scale3D"])
            self.set_materials(defaults["Materials"])
            self.b_default_attributes = True

    def save_to_json(self, saved_json: dict) -> None:
        if not self.b_dynamically_created and self.b_default_attributes and not self.is_destroyed:
            return

        cleaned_tags: list[str] = [x.strip() for x in self.tags if x.strip()]

        if not self.b_dynamically_created and not self.b_default_attributes and not self.is_destroyed:
            smc_list = saved_json.setdefault("Edit", {}).setdefault("InteractiveObjectDefinition", {})
            smc_list[ENGINE.PathName(self.iobject)] = {
                "Rename": self.rename,
                "Tags": cleaned_tags,
                "Metadata": self.metadata,
                "Location": self.get_location(),
                "Rotation": self.get_rotation(),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [ENGINE.PathName(x) for x in self.get_materials()],
            }
        elif not self.b_dynamically_created and self.is_destroyed:
            smc_list = saved_json.setdefault("Destroy", {}).setdefault("InteractiveObjectDefinition", [])
            smc_list.append(self.io_name)

        elif self.b_dynamically_created:
            create_me = saved_json.setdefault("Create", {}).setdefault("InteractiveObjectDefinition", [])
            create_me.append(
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

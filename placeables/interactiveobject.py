from typing import List, Tuple, Union, cast

import unrealsdk  # type: ignore

from .. import bl2tools
from .placeable import AbstractPlaceable


def _initialize_vending_machine(iobject: unrealsdk.UObject) -> None:
    vending_name: str = bl2tools.get_obj_path_name(iobject.InteractiveObjectDefinition).lower()

    if "health" in vending_name:
        iobject.ShopType = 2
    elif "ammo" in vending_name:
        iobject.ShopType = 1
    else:
        iobject.ShopType = 0

    gamestage = unrealsdk.FindObject(
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
        markup = unrealsdk.FindObject(
            "AttributeInitializationDefinition",
            "GD_Iris_TorgueTokenVendor.CommerceMarkup",
        )
        gamestage = unrealsdk.FindObject(
            "AttributeInitializationDefinition",
            "GD_Iris_TorgueTokenVendor.Balance.Init_FeaturedItem_GameStage",
        )
        awesome = None
    else:
        iobject.FixedItemCost = -1
        iobject.FixedFeaturedItemCost = -1
        iobject.FormOfCurrency = 0
        markup = unrealsdk.FindObject(
            "AttributeInitializationDefinition",
            "GD_Economy.VendingMachine.Init_MarkupCalc_P1",
        )
        awesome = unrealsdk.FindObject(
            "AttributeInitializationDefinition",
            "GD_Population_Shopping.Balance.Init_FeaturedItem_AwesomeLevel",
        )

    iobject.bOverrideFormOfCurrency = True

    iobject.CommerceMarkup = (1, None, markup, 1)
    iobject.InventoryConfigurationName = "Inventory"
    iobject.FeaturedItemCommerceMarkup = (int("togue" in vending_name), None, markup, 1)
    iobject.FeaturedItemConfigurationName = "FeaturedItem"
    iobject.FeaturedItemGameStage = (int(awesome is None), None, gamestage, 1)
    iobject.FeaturedItemAwesomeLevel = (0, None, awesome, 1)

    iobject.ResetInventory()

    if "blackmarket" in vending_name:
        iobject.ShopType = 3
        iobject.DefinitionData = unrealsdk.FindObject(
            "BlackMarketDefinition",
            "GD_BlackMarket.BlackMarket.MarketDef_BlackMarket",
        )
        iobject.FixedItemCost = 0
        iobject.FixedFeaturedItemCost = 0


def _initialize_fast_travel_station(iobject: unrealsdk.UObject) -> None:
    tp = iobject.TeleportDest
    new_tp = unrealsdk.ConstructObject(Class=tp.Class, Template=tp, Outer=tp.Outer)
    new_tp.ObjectFlags.B |= 4
    iobject.TeleportDest = new_tp
    iobject.TeleportDest.UpdateExitPointLocations()
    iobject.TeleportDest.UpdateExitPointHeights()


class InteractiveObjectBalanceDefinition(AbstractPlaceable):
    def __init__(self, name: str, iobject_definition: unrealsdk.UObject, iobject: unrealsdk.UObject = None) -> None:
        super().__init__(name, "InteractiveObjectDefinition")
        self.io_definition: unrealsdk.UObject = iobject_definition
        self.iobject: unrealsdk.UObject = iobject
        self.io_name: str = ""
        self.uobject_path_name: str = bl2tools.get_obj_path_name(self.io_definition)

    def get_materials(self) -> List[unrealsdk.UObject]:
        if self.iobject and self.iobject.ObjectMesh:
            return [x for x in self.iobject.ObjectMesh.Materials]  # noqa: C416
        return []

    def set_materials(self, materials: List[unrealsdk.UObject]) -> None:
        # because chests and some other IO generate Materials on spawning them, its very likely that the exported
        # list of materials wont work, just to be safe, ignore all kind of materials for InteractiveObjects
        # untill i find a better fix
        return
        if self.iobject and self.iobject.ObjectMesh and materials:
            self.iobject.ObjectMesh.Materials = materials

    def add_material(self, material: unrealsdk.UObject) -> None:
        super().add_material(material)

    def remove_material(self, material: unrealsdk.UObject = None, index: int = -1) -> None:
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

    def get_scale3d(self) -> List[float]:
        if not self.iobject:
            return [1, 1, 1]
        return [self.iobject.DrawScale3D.X, self.iobject.DrawScale3D.Y, self.iobject.DrawScale3D.Z]

    def set_scale3d(self, scale3d: List[float]) -> None:
        self.iobject.DrawScale3D = tuple(scale3d)

    def set_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        if self.iobject:
            self.iobject.Rotation = tuple(rotator)
            self.b_default_attributes = False

    def get_rotation(self) -> List[int]:
        if not self.iobject:
            return [0, 0, 0]
        return [self.iobject.Rotation.Pitch, self.iobject.Rotation.Yaw, self.iobject.Rotation.Roll]

    def add_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        if self.iobject:
            pitch, yaw, roll = rotator
            self.iobject.Rotation.Pitch += pitch
            self.iobject.Rotation.Yaw += yaw
            self.iobject.Rotation.Roll += roll
            self.b_default_attributes = False

    def set_location(self, position: Union[List[float], Tuple[float, float, float]]) -> None:
        if self.iobject:
            self.iobject.Location = tuple(position)
            self.b_default_attributes = False

    def get_location(self) -> List[float]:
        if not self.iobject:
            return [0, 0, 0]
        return [self.iobject.Location.X, self.iobject.Location.Y, self.iobject.Location.Z]

    def get_bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        x, y, z = self.get_location()
        return (x, y, z), (250, 250, 250)

    def instantiate(self) -> Tuple["InteractiveObjectBalanceDefinition", List["InteractiveObjectBalanceDefinition"]]:
        pc = bl2tools.get_player_controller()
        _loc = (pc.Location.X, pc.Location.Y, pc.Location.Z)
        pop_master = unrealsdk.FindAll("WillowPopulationMaster")[-1]

        is_bal_def = bl2tools.obj_is_in_class(self.io_definition, "InteractiveObjectBalanceDefinition")
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

        ret = InteractiveObjectBalanceDefinition(self.name, self.io_definition, iobject)

        if pc.GetCurrentPlaythrough() != 2:
            will_pop = unrealsdk.FindAll("WillowPopulationOpportunityPoint")[1:]
            pop = unrealsdk.FindAll("PopulationOpportunityPoint")[1:]
            regions = pop if len(pop) > len(will_pop) else will_pop
            region_game_stage = max(pc.GetGameStageFromRegion(x.GameStageRegion) for x in regions if x.GameStageRegion)
        else:
            region_game_stage = max(x.GetGameStage() for x in unrealsdk.FindAll("WillowPlayerPawn") if x.Arms)

        iobject.SetGameStage(region_game_stage)
        iobject.SetExpLevel(region_game_stage)

        iobject.PostBeginPlay()

        if is_bal_def:
            x = self.io_definition.SelectGradeIndex(region_game_stage, 0)
            iobject.InitializeBalanceDefinitionState(self.io_definition, x)
            self.io_definition.SetupInteractiveObjectLoot(iobject, x)
            iobject.InitializeFromDefinition(self.io_definition.DefaultInteractiveObject, False)

            if bl2tools.obj_is_in_class(iobject, "WillowVendingMachine") or bl2tools.obj_is_in_class(
                iobject,
                "WillowVendingMachineBlackMarket",
            ):
                _initialize_vending_machine(iobject)
        else:
            iobject.InitializeFromDefinition(self.io_definition, False)
            if "TravelStation" in iobject.InteractiveObjectDefinition.Name:
                iobject.Class = unrealsdk.FindClass("FastTravelStation")
                unrealsdk.Log(iobject.PathName(iobject))
                _initialize_fast_travel_station(iobject)
                # This only ever produces WillowInteractiveObject, not TravelStation

        ret.b_dynamically_created = True
        return ret, [
            ret,
        ]

    def get_preview(self) -> "InteractiveObjectBalanceDefinition":
        ret = cast(InteractiveObjectBalanceDefinition, self.instantiate()[0])
        ret.set_scale(0.2)
        return ret

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unrealsdk.UObject) -> bool:
        return self.io_definition is uobject or self.iobject is uobject

    def destroy(self) -> List["InteractiveObjectBalanceDefinition"]:
        if not self.iobject:
            raise ValueError("Cannot destroy not instantiated Object!")

        if not self.b_dynamically_created:
            self.io_name = bl2tools.get_obj_path_name(self.iobject)
        self.iobject.Destroyed()
        self.set_location((-9999999, -9999999, -9999999))  # let's just move the pawn out of our sight
        self.set_scale(0)
        self.is_destroyed = True
        return [self]

    def store_default_values(self, default_dict: dict) -> None:
        if self.iobject and bl2tools.get_obj_path_name(self.iobject) not in default_dict:
            default_dict[bl2tools.get_obj_path_name(self.iobject)] = {
                "Location": list(self.get_location()),
                "Rotation": list(self.get_rotation()),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [bl2tools.get_obj_path_name(x) for x in self.get_materials()],
            }

    def restore_default_values(self, default_dict: dict) -> None:
        if self.iobject and bl2tools.get_obj_path_name(self.iobject) in default_dict:
            defaults = default_dict[bl2tools.get_obj_path_name(self.iobject)]
            self.set_scale(defaults["Scale"])
            self.set_location(defaults["Location"])
            self.set_rotation(defaults["Rotation"])
            self.set_scale3d(defaults["Scale3D"])
            self.set_materials(defaults["Materials"])
            self.b_default_attributes = True

    def save_to_json(self, saved_json: dict) -> None:
        if not self.b_dynamically_created and self.b_default_attributes and not self.is_destroyed:
            return

        cleaned_tags: List[str] = [x.strip() for x in self.tags if x.strip()]

        if not self.b_dynamically_created and not self.b_default_attributes and not self.is_destroyed:
            smc_list = saved_json.setdefault("Edit", {}).setdefault("InteractiveObjectDefinition", {})
            smc_list[bl2tools.get_obj_path_name(self.iobject)] = {
                "Rename": self.rename,
                "Tags": cleaned_tags,
                "Metadata": self.metadata,
                "Location": self.get_location(),
                "Rotation": self.get_rotation(),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [bl2tools.get_obj_path_name(x) for x in self.get_materials()],
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
                        "Materials": [bl2tools.get_obj_path_name(x) for x in self.get_materials()],
                    },
                },
            )

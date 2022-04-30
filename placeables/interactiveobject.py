from typing import Tuple, List, Union, cast

import unrealsdk
from unrealsdk import *

from .placeable import AbstractPlaceable

from .. import canvasutils
from .. import bl2tools
from .. import settings



class InteractiveObjectBalanceDefinition(AbstractPlaceable):
    def __init__(self, name: str, iobject_definition: unrealsdk.UObject, iobject: unrealsdk.UObject = None):
        super().__init__(name, "InteractiveObjectDefinition")
        self.io_definition: unrealsdk.UObject = iobject_definition
        self.iobject: unrealsdk.UObject = iobject
        self.io_name: str = ""

    def get_materials(self) -> List[unrealsdk.UObject]:
        if self.iobject and self.iobject.ObjectMesh:
            return [x for x in self.iobject.ObjectMesh.Materials]
        else:
            return []

    def set_materials(self, materials: List[unrealsdk.UObject]) -> None:
        # because chests and some other IO generate Materials on spawning them, its very likely that the exported
        # list of materials wont work, just to be safe, ignore all kind of materials for InteractiveObjects
        # untill i find a better fix
        return
        if self.iobject and self.iobject.ObjectMesh and materials is not None:
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
        return [self.iobject.Rotation.Pitch,
                self.iobject.Rotation.Yaw,
                self.iobject.Rotation.Roll]

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
        return [self.iobject.Location.X,
                self.iobject.Location.Y,
                self.iobject.Location.Z]

    def draw_debug_box(self, player_controller: unrealsdk.UObject) -> None:
        if self.iobject:
            player_controller.DrawDebugSphere(tuple(self.get_location()),
                                              120, 1,
                                              *settings.draw_debug_box_color, True, 0.01)

    def draw_debug_origin(self, canvas: unrealsdk.UObject, player_controller: unrealsdk.UObject) -> None:
        if self.iobject:
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

        is_bal_def = bl2tools.obj_is_in_class(self.io_definition, "InteractiveObjectBalanceDefinition")
        if is_bal_def:
            iobject = pop_master.SpawnPopulationControlledActor(
                self.io_definition.DefaultInteractiveObject.InteractiveObjectClass, None, "", _loc, (0, 0, 0)
            )
        else:
            iobject = pop_master.SpawnPopulationControlledActor(
                self.io_definition.InteractiveObjectClass, None, "", _loc, (0, 0, 0)
            )

        ret = InteractiveObjectBalanceDefinition(self.name, self.io_definition, iobject)

        if pc.GetCurrentPlaythrough() != 2:
            will_pop = unrealsdk.FindAll("WillowPopulationOpportunityPoint")[1:]
            pop = unrealsdk.FindAll("PopulationOpportunityPoint")[1:]
            regions = pop if len(pop) > len(will_pop) else will_pop
            region_game_stage = max(pc.GetGameStageFromRegion(x.GameStageRegion)
                                    for x in regions if x.GameStageRegion)
        else:
            region_game_stage = max(x.GetGameStage() for x in unrealsdk.FindAll("WillowPlayerPawn") if x.Arms)

        iobject.SetGameStage(region_game_stage)
        iobject.SetExpLevel(region_game_stage)

        if is_bal_def:
            x = self.io_definition.SelectGradeIndex(region_game_stage, 0)
            iobject.InitializeBalanceDefinitionState(self.io_definition, x)
            self.io_definition.SetupInteractiveObjectLoot(iobject, x)
            iobject.InitializeFromDefinition(self.io_definition.DefaultInteractiveObject, False)

            if bl2tools.obj_is_in_class(iobject, "WillowVendingMachine"):
                vending_name = bl2tools.get_obj_path_name(iobject.InteractiveObjectDefinition).lower()
                markup = unrealsdk.FindObject("AttributeInitializationDefinition",
                                              "GD_Economy.VendingMachine.Init_MarkupCalc_P1")
                iobject.CommerceMarkup.InitializationDefinition = markup
                iobject.FeaturedItemCommerceMarkup.InitializationDefinition = markup
                iobject.InventoryConfigurationName = "Inventory"
                iobject.FeaturedItemConfigurationName = "FeaturedItem"
                item_stage = unrealsdk.FindObject("AttributeInitializationDefinition",
                                                  "GD_Population_Shopping.Balance.Init_FeaturedItem_GameStage")
                item_awesome = unrealsdk.FindObject("AttributeInitializationDefinition",
                                                    "GD_Population_Shopping.Balance.Init_FeaturedItem_AwesomeLevel")
                iobject.FeaturedItemGameStage.InitializationDefinition = item_stage
                iobject.FeaturedItemAwesomeLevel.InitializationDefinition = item_awesome
                if "health" in vending_name:
                    iobject.ShopType = 2
                elif "ammo" in vending_name:
                    iobject.ShopType = 1
                elif "weapon" in vending_name:
                    iobject.ShopType = 0

                iobject.ResetInventory()
        else:
            iobject.InitializeFromDefinition(self.io_definition, False)

        ret.b_dynamically_created = True
        return ret, [ret, ]

    def get_preview(self) -> AbstractPlaceable:
        ret = cast(InteractiveObjectBalanceDefinition, self.instantiate()[0])
        ret.set_scale(0.2)
        return ret

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unrealsdk.UObject) -> bool:
        return self.io_definition is uobject or self.iobject is uobject

    def destroy(self) -> List[AbstractPlaceable]:
        if not self.iobject:
            raise ValueError("Cannot destroy not instantiated Object!")

        if not self.b_dynamically_created:
            self.io_name = bl2tools.get_obj_path_name(self.iobject)
        self.iobject.Destroyed()
        self.set_location((-9999999, -9999999, -9999999))  # let's just move the pawn out of our sight
        self.set_scale(0)
        self.is_destroyed = True
        return [self, ]

    def store_default_values(self, default_dict: dict) -> None:
        if self.iobject and bl2tools.get_obj_path_name(self.iobject) not in default_dict:
            default_dict[bl2tools.get_obj_path_name(self.iobject)] = {
                "Location": list(self.get_location()),
                "Rotation": list(self.get_rotation()),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [bl2tools.get_obj_path_name(x) for x in self.get_materials()]
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
        elif not self.b_dynamically_created and not self.b_default_attributes and not self.is_destroyed:
            smc_list = saved_json.setdefault("Edit", {}).setdefault("InteractiveObjectDefinition", {})
            smc_list[bl2tools.get_obj_path_name(self.iobject)] = {"Location": self.get_location(),
                                                                  "Rotation": self.get_rotation(),
                                                                  "Scale": self.get_scale(),
                                                                  "Scale3D": self.get_scale3d(),
                                                                  "Materials":
                                                                      [bl2tools.get_obj_path_name(x)
                                                                       for x in self.get_materials()]
                                                                  }
        elif not self.b_dynamically_created and self.is_destroyed:
            smc_list = saved_json.setdefault("Destroy", {}).setdefault("InteractiveObjectDefinition", [])
            smc_list.append(self.io_name)

        elif self.b_dynamically_created:
            create_me = saved_json.setdefault("Create", {}).setdefault("InteractiveObjectDefinition", [])
            create_me.append({bl2tools.get_obj_path_name(self.io_definition): {"Location": self.get_location(),
                                                                               "Rotation": self.get_rotation(),
                                                                               "Scale": self.get_scale(),
                                                                               "Scale3D": self.get_scale3d(),
                                                                               "Materials":
                                                                                   [bl2tools.get_obj_path_name(x)
                                                                                    for x in self.get_materials()]
                                                                               }})

    def draw(self) -> None:
        super().draw()

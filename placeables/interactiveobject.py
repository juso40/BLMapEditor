from typing import Tuple, List, cast

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

    def set_rotation(self, rotator: iter) -> None:
        if self.iobject:
            self.iobject.Rotation = tuple(rotator)
            self.b_default_attributes = False

    def get_rotation(self) -> iter:
        if not self.iobject:
            return [0, 0, 0]
        return [self.iobject.Rotation.Pitch,
                self.iobject.Rotation.Yaw,
                self.iobject.Rotation.Roll]

    def add_rotation(self, rotator: iter) -> None:
        if self.iobject:
            pitch, yaw, roll = rotator
            self.iobject.Rotation.Pitch += pitch
            self.iobject.Rotation.Yaw += yaw
            self.iobject.Rotation.Roll += roll
            self.b_default_attributes = False

    def set_location(self, position: iter) -> None:
        if self.iobject:
            self.iobject.Location = tuple(position)
            self.b_default_attributes = False

    def get_location(self) -> iter:
        if not self.iobject:
            return [0, 0, 0]
        return [self.iobject.Location.X,
                self.iobject.Location.Y,
                self.iobject.Location.Z]

    def draw_debug_box(self, player_controller) -> None:
        if self.iobject:
            player_controller.DrawDebugSphere(tuple(self.get_location()),
                                              120, 1,
                                              *settings.draw_debug_box_color)

    def draw_debug_origin(self, canvas, player_controller) -> None:
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

    def holds_object(self, uobject: str) -> bool:
        return bl2tools.get_obj_path_name(self.io_definition) == uobject \
               or bl2tools.get_obj_path_name(self.iobject) == uobject

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
                "Scale": self.get_scale()
            }

    def restore_default_values(self, default_dict: dict) -> None:
        if self.iobject and bl2tools.get_obj_path_name(self.iobject) in default_dict:
            defaults = default_dict[bl2tools.get_obj_path_name(self.iobject)]
            self.set_scale(defaults["Scale"])
            self.set_location(defaults["Location"])
            self.set_rotation(defaults["Rotation"])
            self.b_default_attributes = True

    def save_to_json(self, saved_json: dict) -> None:
        if not self.b_dynamically_created and self.b_default_attributes and not self.is_destroyed:
            return
        elif not self.b_dynamically_created and not self.b_default_attributes and not self.is_destroyed:
            smc_list = saved_json.setdefault("Edit", {}).setdefault("InteractiveObjectDefinition", {})
            smc_list[bl2tools.get_obj_path_name(self.iobject)] = {"Location": list(self.get_location()),
                                                                  "Rotation": list(self.get_rotation()),
                                                                  "Scale": self.get_scale()}
        elif not self.b_dynamically_created and self.is_destroyed:
            smc_list = saved_json.setdefault("Destroy", {}).setdefault("InteractiveObjectDefinition", [])
            smc_list.append(self.io_name)

        elif self.b_dynamically_created:
            create_me = saved_json.setdefault("Create", {}).setdefault("InteractiveObjectDefinition", [])
            create_me.append({bl2tools.get_obj_path_name(self.io_definition): {"Location": list(self.get_location()),
                                                                               "Rotation": list(self.get_rotation()),
                                                                               "Scale": self.get_scale()}})

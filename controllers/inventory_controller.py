import pygame
import sys

from Unrealistic_Engine.controllers.controller import Controller
from Unrealistic_Engine.utils import utils
from Unrealistic_Engine.views.inventory_view import InventoryView
from Unrealistic_Engine.views.view import View
from Unrealistic_Engine.utils.position import Position
from Unrealistic_Engine.models.leaf_node import LeafNode
from Unrealistic_Engine.models.menu import Menu
from Unrealistic_Engine.models.map import Map
from Unrealistic_Engine.controllers.controller_factory import ControllerFactory
from Unrealistic_Engine.models.item import Item


class InventoryController(Controller):

    def __init__(self, model, view, *args, **kwargs):
        self.model = model
        self.view = view

        # Add Background layer to visible models
        self.view.add_model(
            None, InventoryView.render_background,
            Position(0, 0), View.BACKGROUND)

        # Add Character to visible models
        self.view.add_model(
            self.model.character, InventoryView.render_character_data,
            Position(Map.MAP_SIZE/4, 0), View.FOREGROUND)

        # Add item description - using blank item for initialization
        self.description_item = Item(0, 0, "", 0)
        self.view.add_model(
            self.description_item, InventoryView.render_description,
            Position(0, 0), View.FOREGROUND)
        # Build item list from model into a menu
        self.inventory_menu = Menu(
            self.view, InventoryView.render_inventory_menu, Position(0, 0))

        for item in self.model.character.inventory.item_list:
            self.inventory_menu.nodes.append(
                LeafNode(item.name, self.select_item, item))

    def handle_key_press(self, pressed_key):
        if pressed_key == pygame.K_LEFT:
            if len(Menu.breadcrumbs) > 0:
                self.inventory_menu = self.inventory_menu.go_to_previous_menu()

        if pressed_key == pygame.K_RIGHT or pressed_key == pygame.K_RETURN:
            self.inventory_menu = self.inventory_menu.activate_node()

        if pressed_key == pygame.K_UP:
            self.inventory_menu.dec_active_node()

        if pressed_key == pygame.K_DOWN:
            self.inventory_menu.inc_active_node()

        if pressed_key == pygame.K_i:
            # For now goes back to only game controller, but we need a
            # way to detect previous controller
            self.close_inventory()

    def select_item(self, item):
        self.description_item.description = item.description
        if item.slot == Item.Bag:
            # Show an error that item can't be equipped
            return
        current_loadout = self.model.character.loadout
        if item.slot in current_loadout:
            if item is current_loadout[item.slot]:
                item.unequip(self.model.character)
            else:
                item.equip(self.model.character)
        else:
            item.equip(self.model.character)

    def close_inventory(self):
        Controller.build_and_swap_controller(self.model,"game_controller",
                                             "game_view", self, self.view)

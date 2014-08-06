import pygame
import copy
import sys
import os

from Unrealistic_Engine import event_types
from Unrealistic_Engine.utils import utils
from Unrealistic_Engine.utils.position import Position
from Unrealistic_Engine.models.dialog import Dialog
from Unrealistic_Engine.models.map import Map
from Unrealistic_Engine.models.trigger import Trigger
from Unrealistic_Engine.views.game_view import GameView
from Unrealistic_Engine.controllers.controller import Controller
from Unrealistic_Engine.models.character import Character
from Unrealistic_Engine.views.view import View
from Unrealistic_Engine.controllers.controller_factory import ControllerFactory


class GameController(Controller):

    def __init__(self, model, view, *args, **kwargs):
        self.model = model
        self.view = view
        self.triggers = {}
        self.previous_position = None
        self.changed_map = False
        self.unmoved = True

        pygame.mixer.music.load(os.path.join('Music',
                                             self.model.current_map.music))
        pygame.mixer.music.play()

        self._build_triggers()

        # Add Map model
        view.add_model(model.current_map, GameView.render_map, Position(0, 0), View.BACKGROUND)

        # Add Character model
        view.add_model(
            model.character,
            GameView.render_character,
            model.character.position,
            GameView.FOREGROUND)

        self.unmoved = True

    def handle_key_press(self, pressed_key):
        position = self.view.get_visible_model_position(
            self.model.character)
        destination_tile = None

        if pressed_key == pygame.K_LEFT or pressed_key == pygame.K_a:
            self.model.character.direction = Character.LEFT
            self.unmoved = False
            destination_tile = self.model.current_map.get_map_tile(
                position.x_coord - 1, position.y_coord, 0)
            if (position.x_coord - 1) >= 0 and destination_tile.walkable == 1:
                position.set_x_coord(position.x_coord - 1)
        if pressed_key == pygame.K_RIGHT or pressed_key == pygame.K_d:
            self.model.character.direction = Character.RIGHT
            self.unmoved = False
            destination_tile = self.model.current_map.get_map_tile(
                position.x_coord + 1, position.y_coord, 0)
            if(position.x_coord + 1) < Map.GRID_SIZE and destination_tile.walkable == 1:
                position.set_x_coord(position.x_coord + 1)
        if pressed_key == pygame.K_UP or pressed_key == pygame.K_w:
            self.model.character.direction = Character.UP
            self.unmoved = False
            destination_tile = self.model.current_map.get_map_tile(
                position.x_coord, position.y_coord - 1, 0)
            if(position.y_coord - 1) >= 0 and destination_tile.walkable == 1:
                position.set_y_coord(position.y_coord - 1)
        if pressed_key == pygame.K_DOWN or pressed_key == pygame.K_s:
            self.model.character.direction = Character.DOWN
            self.unmoved = False
            destination_tile = self.model.current_map.get_map_tile(
                position.x_coord, position.y_coord + 1, 0)
            if(position.y_coord + 1) < Map.GRID_SIZE and destination_tile.walkable == 1:
                position.set_y_coord(position.y_coord + 1)
        if pressed_key == pygame.K_ESCAPE:
            ControllerFactory.build_and_swap_controller(self.model,
                                                        "menu_controller",
                                                        "main_menu", self,
                                                        self.view)
        if pressed_key == pygame.K_i:
            ControllerFactory.build_and_swap_controller(self.model,
                                                        "inventory_controller",
                                                        "inventory_view", self,
                                                        self.view)

        self.view.set_visible_model_position(self.model.character, position)
        self.model.character.position = position

        # Check if any triggers have been activated.
        if position in self.triggers and self.triggers[position].is_active:
            # TODO Handle chance here.
            self._handle_trigger(self.triggers[position], position, False,
                                 pressed_key)
        if self.previous_position in self.triggers and self.triggers[
            self.previous_position].is_active:
            # TODO Handle chance here.
            self._handle_trigger(self.triggers[self.previous_position],
                                 self.previous_position, True, pressed_key)

        self.previous_position = copy.copy(position)
        if self.changed_map:
            # If we changed maps we need to reset our previous position such that we don't fire the
            # trigger twice.
            self.previous_position = None
            self.changed_map = False

    def _change_map(self, map_name):
        self.changed_map = True
        self.view.remove_model(self.model.current_map)

        prev_music = self.model.current_map.music
        self.model.current_map = self.model.maps[map_name]

        # Change the music if necessary
        curr_music = self.model.current_map.music
        if prev_music != curr_music:
            pygame.mixer.music.load(os.path.join('Music',
                                                self.model.current_map.music))
            pygame.mixer.music.play()

        self.view.add_model(self.model.current_map, GameView.render_map,
                            Position(0, 0), View.BACKGROUND)
        self.triggers = {}
        self.previous_position = None
        self._build_triggers()

    def _build_triggers(self):
        for row in self.model.current_map.layers[1]:
            for tile in row:
                if tile != 0 and tile.trigger is not None:
                    self.triggers[tile.position] = tile.trigger

    def _handle_trigger(self, trigger, position, is_previous, pressed_key):
        # We support triggers being fired when entering or leaving a tile.
        valid_previous_trigger = trigger.triggered_on == Trigger.EXIT and is_previous
        valid_current_trigger = trigger.triggered_on == Trigger.ENTER and not is_previous

        valid_action_trigger = trigger.triggered_on == Trigger.KEY_ACTION and \
                               pressed_key == pygame.K_SPACE

        if not (valid_previous_trigger or valid_current_trigger or valid_action_trigger):
            return

        # Make sure the character is facing the appropriate direction
        if not (self.model.character.direction == trigger.direction_facing or \
                trigger.direction_facing == Trigger.DIRECTION_ANY):
            return

        if trigger.is_one_time:
            trigger.is_active = False

        if trigger.action_type == Trigger.CHANGE_MAP:
            self._change_map(trigger.action_data['map_name'])
            position = Position(
                trigger.action_data['character_x'],
                trigger.action_data['character_y'])

            self.view.set_visible_model_position(self.model.character, position)

        if trigger.action_type == Trigger.START_BATTLE:
            ControllerFactory.build_and_swap_controller(self.model,
                                                        "battle_controller",
                                                        "battle_view", self,
                                                        self.view,
                                                        trigger.action_data[
                                                            "enemy"])

        if trigger.action_type == Trigger.GET_ITEM:
            self.model.character.inventory.\
                    add_item(self.model.items[trigger.action_data['item']])
                # Use a dialog here to show that an item is acquired

        if trigger.action_type == Trigger.SHOW_DIALOG:
            if not self.unmoved:
                self.unmoved = True
                new_dialog = Dialog(
                    Position(trigger.action_data['dialog_x'], trigger.action_data['dialog_y']),
                    trigger.action_data['dialog_text'],
                    trigger.action_data['timed'],
                    trigger.action_data['timeout'],
                    self)
                self.view.add_model(
                    new_dialog, GameView.render_dialog, new_dialog.location, GameView.OVERLAY)
                
                if not new_dialog.timed:
                    ControllerFactory.build_and_swap_controller(new_dialog,
                                                        "dialog_controller",
                                                        "game_view", self,
                                                        self.view)

        print("Action occurred with data: " + str(trigger.action_data))

    def handle_game_event(self, event):
        if event.type == event_types.KILL_DIALOG:
            self.view.remove_model(event.Dialog)

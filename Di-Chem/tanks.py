import ctypes
import sys
import time

import keyboard
from kivy.base import runTouchApp
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty, ColorProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.app import App
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.graphics import Color, Line
from kivymd.uix.button import MDIconButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.icon_definitions import md_icons
from kivymd.uix.tooltip import MDTooltip

from database import *


tank=OutputLayout()
tank_wash=TankWashDetails()


class NButton(Button, FocusBehavior):
    focused = BooleanProperty(False)
    focus_color = ColorProperty((0, 0.5, 1, 1))  # Change this to your desired focus color
    row = NumericProperty()
    col = NumericProperty()

    def __init__(self, **kwargs):
        super(NButton, self).__init__(**kwargs)
        self.default_color = self.background_color
        self.bind(pos=self.update_outline, size=self.update_outline)
        with self.canvas.before:
            Color(0.0, 0.478, 1, 1)  # Blue color
            self.outline = Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

    def update_outline(self, *args):
        self.outline.rectangle = (self.x, self.y, self.width, self.height)

    def on_focused(self, instance, value):
        if value:
            self.background_color = self.focus_color
        else:
            self.background_color = self.default_color

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if self.focused:
            if keycode[1] == 'down':
                self.navigate(0, -10)
                return True
            elif keycode[1] == 'up':
                self.navigate(0, 10)
                return True
            elif keycode[1] == 'left':
                self.navigate(0, 1)
                return True
            elif keycode[1] == 'right':
                self.navigate(0, -1)
                return True
            elif keycode[1] == 'enter':
                self.dispatch('on_press')
                return True
    def navigate(self, row_change, col_change):
        chemical_grid = self.parent.parent
        row = chemical_grid.children.index(self.parent)
        col = self.parent.children.index(self)
        # print(row, col)

        if row < len(chemical_grid.children) - 1:
            next_row_columns = len(chemical_grid.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(chemical_grid.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(chemical_grid.children[row].children) - 1))

        new_widget = chemical_grid.children[new_row].children[new_col]

        if isinstance(new_widget, NTextInput) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True

class TankTextInput(TextInput, FocusBehavior):
    def insert_text(self, substring, from_undo=False):
        # Get the current text in the TextInput
        current_text = self.text

        # Check if the input character is allowed
        if substring in '0123456789.':
            # Check if there's already a decimal point in the input
            if '.' in current_text:
                # If there is, split the input at the decimal point
                integer_part, fractional_part = current_text.split('.')

                # If a '.' is typed again, do not allow it
                if substring == '.':
                    return

                # Allow only one digit in the fractional part
                if len(fractional_part) < 1:
                    super().insert_text(substring, from_undo=from_undo)
            else:
                # If there is no decimal point, allow any length before the decimal point
                super().insert_text(substring, from_undo=from_undo)
        else:
            # If the input is not a valid character, ignore it
            return
    row = NumericProperty()
    col = NumericProperty()

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super(TankTextInput, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        alt_pressed = 'alt' in modifiers
        if alt_pressed and keycode[1] == 'left':
            self.cursor_previous_letter()
            return True
        elif alt_pressed and keycode[1] == 'right':
            self.cursor_next_letter()
            return True

        if keycode[1] == 'down':
            self.navigate(0, -4)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 4)
            return True
        elif keycode[1] == 'left':
            self.navigate(0, 1)
            return True
        elif keycode[1] == 'right':
            self.navigate(0, -1)
            return True

    def cursor_previous_letter(self):
        if self.cursor:
            cursor_x, cursor_y = self.cursor
            print("1.1: ", cursor_x, cursor_y)
            # if cursor_x < len(self.text):
            self.cursor = (cursor_x, cursor_y)
            print("1.2: ", self.cursor)

    def cursor_next_letter(self):
        if self.cursor:
            cursor_x, cursor_y = self.cursor
            print("2.1: ", cursor_x, cursor_y)
            # if cursor_x > 0:
            self.cursor = (cursor_x, cursor_y)
            print("2.2: ", self.cursor)

    def navigate(self, row_change, col_change):
        print(self.parent.parent)
        chemical_grid = self.parent.parent
        print(chemical_grid.children.index(self.parent))
        print(self.parent.children.index(self))
        row = chemical_grid.children.index(self.parent)
        col = self.parent.children.index(self)
        # print(row, col)

        if row > len(chemical_grid.children) - 1:
            next_row_columns = len(chemical_grid.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(chemical_grid.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(chemical_grid.children[row].children) - 1))

        new_widget = chemical_grid.children[new_row].children[new_col]

        if isinstance(new_widget, TankTextInput) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True

class AddTextInput(TextInput, FocusBehavior):
    def insert_text(self, substring, from_undo=False):
        # Get the current text in the TextInput
        current_text = self.text

        # Check if the input character is allowed
        if substring in '0123456789.':
            # Check if there's already a decimal point in the input
            if '.' in current_text:
                # If there is, split the input at the decimal point
                integer_part, fractional_part = current_text.split('.')

                # If a '.' is typed again, do not allow it
                if substring == '.':
                    return

                # Allow only one digit in the fractional part
                if len(fractional_part) < 1:
                    super().insert_text(substring, from_undo=from_undo)
            else:
                # If there is no decimal point, allow any length before the decimal point
                super().insert_text(substring, from_undo=from_undo)
        else:
            # If the input is not a valid character, ignore it
            return
    row = NumericProperty()
    col = NumericProperty()

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super(AddTextInput, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        alt_pressed = 'alt' in modifiers
        if alt_pressed and keycode[1] == 'left':
            self.cursor_previous_letter()
            return True
        elif alt_pressed and keycode[1] == 'right':
            self.cursor_next_letter()
            return True

        if keycode[1] == 'down':
            self.navigate(0, -5)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 5)
            return True
        elif keycode[1] == 'left':
            self.navigate(0, 1)
            return True
        elif keycode[1] == 'right':
            self.navigate(0, -1)
            return True

    def cursor_previous_letter(self):
        if self.cursor:
            cursor_x, cursor_y = self.cursor
            print("1.1: ", cursor_x, cursor_y)
            # if cursor_x < len(self.text):
            self.cursor = (cursor_x, cursor_y)
            print("1.2: ", self.cursor)

    def cursor_next_letter(self):
        if self.cursor:
            cursor_x, cursor_y = self.cursor
            print("2.1: ", cursor_x, cursor_y)
            # if cursor_x > 0:
            self.cursor = (cursor_x, cursor_y)
            print("2.2: ", self.cursor)

    def navigate(self, row_change, col_change):
        print(self.parent.parent)
        chemical_grid = self.parent.parent
        print(chemical_grid.children.index(self.parent))
        print(self.parent.children.index(self))
        row = chemical_grid.children.index(self.parent)
        col = self.parent.children.index(self)
        # print(row, col)

        if row > len(chemical_grid.children) - 1:
            next_row_columns = len(chemical_grid.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(chemical_grid.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(chemical_grid.children[row].children) - 1))

        new_widget = chemical_grid.children[new_row].children[new_col]

        if isinstance(new_widget, AddTextInput) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True
class NTextInput(TextInput, FocusBehavior):
    row = NumericProperty()
    col = NumericProperty()

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super(NTextInput, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        alt_pressed = 'alt' in modifiers
        if alt_pressed and keycode[1] == 'left':
            self.cursor_previous_letter()
            return True
        elif alt_pressed and keycode[1] == 'right':
            self.cursor_next_letter()
            return True

        if keycode[1] == 'down':
            self.navigate(0, -10)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 10)
            return True
        elif keycode[1] == 'left':
            self.navigate(0, 1)
            return True
        elif keycode[1] == 'right':
            self.navigate(0, -1)
            return True

    def cursor_previous_letter(self):
        if self.cursor:
            cursor_x, cursor_y = self.cursor
            print("1.1: ", cursor_x, cursor_y)
            # if cursor_x < len(self.text):
            self.cursor = (cursor_x, cursor_y)
            print("1.2: ", self.cursor)

    def cursor_next_letter(self):
        if self.cursor:
            cursor_x, cursor_y = self.cursor
            print("2.1: ", cursor_x, cursor_y)
            # if cursor_x > 0:
            self.cursor = (cursor_x, cursor_y)
            print("2.2: ", self.cursor)

    def navigate(self, row_change, col_change):
        chemical_grid = self.parent.parent
        row = chemical_grid.children.index(self.parent)
        col = self.parent.children.index(self)
        # print(row, col)

        if row < len(chemical_grid.children) - 1:
            next_row_columns = len(chemical_grid.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(chemical_grid.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(chemical_grid.children[row].children) - 1))

        new_widget = chemical_grid.children[new_row].children[new_col]

        if isinstance(new_widget, NTextInput) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True


class NewTank(BoxLayout):
    def __init__(self, **kwargs):
        super(NewTank, self).__init__(**kwargs)

    def save_tank_data(self, instance):
        try:
            Machin_Name = self.ids.machine_name.text
            Machin_Path = self.ids.machine_path.text
            Drain_Path = self.ids.drain_path.text
            Slave_ID = self.ids.slave_id.text
            Tank_1 = self.ids.tank_1.text
            Tank_2 = self.ids.tank_2.text
            Tank_3 = self.ids.tank_3.text
            Tank_4 = self.ids.tank_4.text
            Tank_5 = self.ids.tank_5.text
            Tank1_stock = self.ids.tank1_stock.text
            Tank2_stock = self.ids.tank2_stock.text
            Tank3_stock = self.ids.tank3_stock.text
            Tank4_stock = self.ids.tank4_stock.text
            Tank5_stock = self.ids.tank5_stock.text

            tank_paths = [Tank_1, Tank_2, Tank_3, Tank_4, Tank_5]
            # Validate if any required field is empty
            if not all([Machin_Name, Machin_Path, Slave_ID]):
                toast("Error: Check All fields.", duration=0.6)
                return

            slave_id_int = int(Slave_ID)

            # Check if Slave ID already exists
            if Slave_ID in tank.fetch_all_machine_slaveid():
                toast(f"Error: This {Slave_ID} Slave ID is Already Exist", duration=0.6)
                return

            # Check if any Tank Path already exists
            existing_paths = tank.fetch_tank_path_valid()
            existing_tank_paths = [path for path in [Tank_1, Tank_2, Tank_3, Tank_4, Tank_5] if path in existing_paths]
            if existing_tank_paths:
                toast(f"Error: The Tank Paths already exist: {', '.join(existing_tank_paths)}", duration=0.6)
                return

            valid_tank_paths = [path for path in tank_paths if path]

            # Check for duplicate tank paths in the provided paths
            if len(valid_tank_paths) != len(set(valid_tank_paths)):
                duplicate_paths = set([path for path in valid_tank_paths if valid_tank_paths.count(path) > 1])
                toast(f"Error: Duplicate Tank Paths found: {', '.join(map(str, duplicate_paths))}", duration=0.6)
                return
            for path in valid_tank_paths:
                try:
                    path_int = int(path)
                    if not (1 <= path_int <= 254):
                        toast(f"Error: Tank Path {path} is not in the acceptable range (1-254).", duration=0.6)
                        return
                except ValueError:
                    return

            # Check if Slave ID is within the acceptable range
            if not (1 <= slave_id_int <= 254):
                toast(f"Error: Slave ID {Slave_ID} is not in the acceptable range (1-254).", duration=0.6)
                return

            # Insert tank data if all validations pass
            tank.insert_tank_data(Machin_Name, Machin_Path, Drain_Path, Slave_ID, Tank_1, Tank_2, Tank_3, Tank_4,
                                  Tank_5, Tank1_stock, Tank2_stock, Tank3_stock, Tank4_stock, Tank5_stock)

            app_instance = App.get_running_app()
            if app_instance:
                app_instance.root.settank()

            parent_popup = self.parent.parent.parent  # Adjust the number of ".parent" based on your hierarchy
            parent_popup.dismiss()

        except Exception as e:
            print(f"Error:{e}")

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(400, 100))
        error_popup.open()

class ShowTank(MDBoxLayout):
    def __init__(self, **kwargs):
        super(ShowTank, self).__init__(**kwargs)

    def display_selected_machin_data(self,selected_machin_info, machin_name):

        self.ids.machin_id.text =str(selected_machin_info[0])
        self.ids.machin_names.text =str(selected_machin_info[1])
        self.ids.tank_1.text = str(selected_machin_info[2])
        self.ids.tank_1_prewash.text = str(selected_machin_info[3])
        self.ids.tank_1_after1.text = str(selected_machin_info[4])
        self.ids.tank_1_after2.text = str(selected_machin_info[5])
        self.ids.tank_2.text = str(selected_machin_info[6])
        self.ids.tank_2_prewash.text = str(selected_machin_info[7])
        self.ids.tank_2_after1.text = str(selected_machin_info[8])
        self.ids.tank_2_after2.text = str(selected_machin_info[9])
        self.ids.tank_3.text = str(selected_machin_info[10])
        self.ids.tank_3_prewash.text = str(selected_machin_info[11])
        self.ids.tank_3_after1.text = str(selected_machin_info[12])
        self.ids.tank_3_after2.text = str(selected_machin_info[13])
        self.ids.tank_4.text = str(selected_machin_info[14])
        self.ids.tank_4_prewash.text = str(selected_machin_info[15])
        self.ids.tank_4_after1.text = str(selected_machin_info[16])
        self.ids.tank_4_after2.text = str(selected_machin_info[17])
        self.ids.tank_5.text = str(selected_machin_info[18])
        self.ids.tank_5_prewash.text = str(selected_machin_info[19])
        self.ids.tank_5_after1.text = str(selected_machin_info[20])
        self.ids.tank_5_after2.text = str(selected_machin_info[21])

    def update_tank_wash_data(self):
        # Retrieve values from form fields
        id=self.ids.machin_id.text
        Machin_Name = self.ids.machin_names.text
        Tank1 = self.ids.tank_1.text
        tank_1_prewash = self.ids.tank_1_prewash.text
        tank_1_after1 = self.ids.tank_1_after1.text
        tank_1_after2 = self.ids.tank_1_after2.text
        Tank2 = self.ids.tank_2.text
        tank_2_prewash = self.ids.tank_2_prewash.text
        tank_2_after1 = self.ids.tank_2_after1.text
        tank_2_after2 = self.ids.tank_2_after2.text
        Tank3 = self.ids.tank_3.text
        tank_3_prewash = self.ids.tank_3_prewash.text
        tank_3_after1 = self.ids.tank_3_after1.text
        tank_3_after2 = self.ids.tank_3_after2.text
        Tank4 = self.ids.tank_4.text
        tank_4_prewash = self.ids.tank_4_prewash.text
        tank_4_after1 = self.ids.tank_4_after1.text
        tank_4_after2 = self.ids.tank_4_after2.text
        Tank5 = self.ids.tank_5.text
        tank_5_prewash = self.ids.tank_5_prewash.text
        tank_5_after1 = self.ids.tank_5_after1.text
        tank_5_after2 = self.ids.tank_5_after2.text


        # Update the data using the database function
        try:
            tank_wash.update_tank_details_data(
                connection,
                id,
                Machin_Name, Tank1, tank_1_prewash, tank_1_after1, tank_1_after2,
                Tank2, tank_2_prewash, tank_2_after1, tank_2_after2,
                Tank3, tank_3_prewash, tank_3_after1, tank_3_after2,
                Tank4, tank_4_prewash, tank_4_after1, tank_4_after2,
                Tank5, tank_5_prewash, tank_5_after1, tank_5_after2
            )

            print("Data updated successfully.")
            machin_name = self.ids.machin_names.text
            wash_id=self.ids.machin_id.text
            selected_machin_info = tank_wash.fetch_tank_details_data_byid(wash_id)

            self.display_selected_machin_data(selected_machin_info, wash_id)
            print("yes")

        except Exception as e:
            toast(f"Error updating data: {str(e)}", duration=0.6)
            return

    def show_error_popup(self, message):
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(400, 100))
        error_popup.open()

    def go_tank_pop(self):
        app = App.get_running_app()
        app.root.tankpop()

        # Close the parent popup
        parent_popup = self.parent.parent.parent  # Adjust the hierarchy if necessary
        if parent_popup:
            parent_popup.dismiss()


class TankDetails(MDBoxLayout):
    def __init__(self, **kwargs):
        super(TankDetails, self).__init__(**kwargs)

    def display_selected_machin(self, selected_machin_info, machin_id):

        self.ids.machin_id.text = machin_id
        self.ids.machin_name.text = str(selected_machin_info[0])
        self.ids.tank_1_path.text = str(selected_machin_info[1])
        self.ids.tank_2_path.text = str(selected_machin_info[2])
        self.ids.tank_3_path.text = str(selected_machin_info[3])
        self.ids.tank_4_path.text = str(selected_machin_info[4])
        self.ids.tank_5_path.text = str(selected_machin_info[5])

    def save_tank_details(self, instance):

        machin_id=self.ids.machin_id.text
        Machin_Name = self.ids.machin_name.text
        Tank1 = self.ids.tank_1.text
        tank_1_prewash = self.ids.tank_1_prewash.text
        tank_1_after1 = self.ids.tank_1_after1.text
        tank_1_after2 = self.ids.tank_1_after2.text
        Tank2 = self.ids.tank_2.text
        tank_2_prewash = self.ids.tank_2_prewash.text
        tank_2_after1 = self.ids.tank_2_after1.text
        tank_2_after2 = self.ids.tank_2_after2.text
        Tank3 = self.ids.tank_3.text
        tank_3_prewash = self.ids.tank_3_prewash.text
        tank_3_after1 = self.ids.tank_3_after1.text
        tank_3_after2 = self.ids.tank_3_after2.text
        Tank4 = self.ids.tank_4.text
        tank_4_prewash = self.ids.tank_4_prewash.text
        tank_4_after1 = self.ids.tank_4_after1.text
        tank_4_after2 = self.ids.tank_4_after2.text
        Tank5 = self.ids.tank_5.text
        tank_5_prewash = self.ids.tank_5_prewash.text
        tank_5_after1 = self.ids.tank_5_after1.text
        tank_5_after2 = self.ids.tank_5_after2.text

        # Save the data using the database function
        try:
            tank_wash.insert_tank_details_data(
                connection,
                machin_id,Machin_Name, Tank1, tank_1_prewash, tank_1_after1, tank_1_after2,
                Tank2, tank_2_prewash, tank_2_after1, tank_2_after2,
                Tank3, tank_3_prewash, tank_3_after1, tank_3_after2,
                Tank4, tank_4_prewash, tank_4_after1, tank_4_after2,
                Tank5, tank_5_prewash, tank_5_after1, tank_5_after2
            )


            print("Data saved successfully.")

        except Exception as e:
            toast(f"Error saving data: {str(e)}", duration=0.6)
            error_message = f"Error saving data: {str(e)}"
            print(error_message)
            return

        # Update the application state if the app instance is available

        app = App.get_running_app()
        app.root.tankpop()

        # Close the parent popup
        parent_popup = self.parent.parent.parent  # Adjust the hierarchy if necessary
        if parent_popup:
            parent_popup.dismiss()

    def show_error_popup(self, message):
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()

    def go_to_tank_pop(self):
        app = App.get_running_app()
        app.root.tankpop()

        # Close the parent popup
        parent_popup = self.parent.parent.parent  # Adjust the hierarchy if necessary
        if parent_popup:
            parent_popup.dismiss()
class TankWash(MDBoxLayout):
    def __init__(self, **kwargs):
        super(TankWash, self).__init__(**kwargs)
        self.selected_machin_name = None
        self.fetch_and_display_machin_names()

    def on_open_button_press(self, instance):
        selected_machin_label = self.ids.selected_Machin

        if selected_machin_label.text:
            machin_id = selected_machin_label.text

            selected_machin_info = tank_wash.fetch_tank_details_data(machin_id)
            if selected_machin_info:

                tank_details = App.get_running_app().root.show_tank()
            else:
                toast(f"Error: No Data Added for {machin_id}.", duration=0.6)
                return

            if tank_details:
                # Retrieve the content from the popup
                tank_details_view = tank_details.content

                # Check if the view has the display method
                if hasattr(tank_details_view, 'display_selected_machin_data'):
                    # Display the selected machine data
                    tank_details_view.display_selected_machin_data(selected_machin_info, machin_id)

                # Close the parent popup
                parent_popup = self.parent.parent.parent
                if parent_popup:
                    parent_popup.dismiss()
            else:
                toast("Error: TankDetails popup not found.", duration=0.6)
        else:
            toast("Error: No machine selected.", duration=0.6)

    def fetch_and_display_machin_names(self):
        machine_names = self.get_machin_names()

        machin_layout = self.ids.total_machin
        machin_layout.clear_widgets()  # Clear existing buttons

        for name in machine_names:
            if name:
                button = Button(text=name, size_hint_y=None, height=30, background_color=(3, 3, 3, 1),
                                color=(0, 0, 0, 3))
                button.bind(on_release=self.on_tank_button_click)
                machin_layout.add_widget(button)

    def get_machin_names(self):
        machin_names = tank.fetch_all_machine_names()

        machin_names = [name for name in machin_names if name]
        # print("BatchNames:", batch_names)

        return machin_names

    def on_tank_button_click(self, instance):
        try:
            button_text = instance.text
            id_index = button_text.find("ID:")
            if id_index != -1:

                id_start = id_index + len("ID:")


                machin_name_index = button_text.find("MachineName:", id_start)


                if machin_name_index != -1:
                    id_value = button_text[id_start:machin_name_index].strip()
                else:

                    id_value = button_text[id_start:].strip()
                selected_machin_label = self.ids.selected_Machin
                selected_machin_label.text = id_value
                self.selected_machin_name = id_value
        except KeyError:
            print("ID 'selected_machin' not found in self.ids. Please check your layout.")

    def on_add_button_press(self, instance):
        # Retrieve the selected machine ID from the UI
        selected_machine_label = self.ids.selected_Machin

        # Check if a machine ID is provided
        if selected_machine_label.text:
            machine_id = selected_machine_label.text
            print(f"Machine ID selected: {machine_id}")

            # Check if data exists for the machine ID
            data_exists = tank_wash.fetch_machin_name(machine_id)

            if data_exists is not None:
                try:
                    # Convert machine ID to an integer for comparison
                    machine_id_int = int(machine_id)

                    # Check if the machine ID is already in the existing data
                    if machine_id_int in data_exists:
                        toast(f"Error: {machine_id} already has data.", duration=0.6)
                except ValueError:
                    toast(f"Invalid machine ID: {machine_id}", duration=0.6)
            else:
                # Fetch tank information for the machine ID
                selected_machine_info = tank.fetch_tank_for_wash(machine_id)
                tank_details_popup = App.get_running_app().root.tank_details()

                # Check if the tank details popup exists
                if tank_details_popup:
                    tank_details_view = tank_details_popup.content
                    # Check if the view has the method to display the machine info
                    if hasattr(tank_details_view, 'display_selected_machin'):
                        tank_details_view.display_selected_machin(selected_machine_info, machine_id)

                    # Dismiss the parent popup if it exists
                    parent_popup = self.parent.parent.parent
                    if parent_popup:
                        parent_popup.dismiss()
                else:
                    print("Error: TankDetails popup not found.")
        else:
            toast("Error: No machine selected.", duration=0.6)

    def on_search_input_change(self, text):

        if self.ids.search_input.text=='':
            self.fetch_and_display_machin_names()
        else:
            filtered_batch_names = self.get_filtered_machin_names(text)
            self.update_machin_layout(filtered_batch_names)


    def get_filtered_machin_names(self, search_text):
        all_machin_names = self.get_machin_names()
        filtered_machin_names = [name for name in all_machin_names if search_text.lower() in name.lower()]
        return filtered_machin_names

    def update_machin_layout(self, machin_names):
        batch_layout = self.ids.total_machin
        batch_layout.clear_widgets()  # Clear existing buttons

        for name in machin_names:
            if name:
                button = Button(text=name, size_hint_y=None, height=30, background_color=(3, 3, 3, 1),
                                color=(0, 0, 0, 3))
                button.bind(on_release=self.on_tank_button_click)
                batch_layout.add_widget(button)
    def show_error_popup(self, message):
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()


class MyApp(BoxLayout):
    def __init__(self, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.total_widgets = []
        self.output_layout_json_filename = 'OutputLayoutData.json'
        self.settank()
        self.selected_tank_data = {}
        self.connection = create_connection("ChemDB.db")
        self.current_popup = None

    def settank(self):  # modify version2
        print("Calling set tank method")

        # Fetch data from the OutputTank table in the database
        data = tank.fetch_OutputTank_data()

        # Clear the existing content of the GridLayout
        set_tank = self.ids.set_tank
        set_tank.clear_widgets()

        # Add the headers to the GridLayout
        headers = ['ID', 'MachineName', 'MachinePath', 'DrainPath', 'SlaveID', 'Tank1Path', 'Tank2Path', 'Tank3Path',
                   'Tank4Path', 'Tank5Path', 'Tank1Stock', 'Tank2Stock', 'Tank3Stock', 'Tank4Stock', 'Tank5Stock']

        for i, header in enumerate(headers):
            if header in ['ID']:
                size = (90, 30) if header == 'ID' else (90, 30)
            elif header in ['MachineName']:
                size = (139, 30) if header == 'MachineName' else (139, 30)
            else:
                size = (130, 30)  # Default size for other columns

            set_tank.add_widget(
                NTextInput(text=header, halign='center', size_hint=(None, None), size=size, readonly=True,
                           font_size=17, font_name="Aileron-Bold.otf")
            )

        # Add the data to the GridLayout
        for row in data:
            tank_id = str(row[0])
            button = NButton(text=tank_id, size_hint=(None, None), size=(90, 30))
            button.bind(on_press=lambda instance, tankid=tank_id, selected_row=row: self.on_tank_button_press(instance,
                                                                                                              tankid,
                                                                                                              selected_row))
            set_tank.add_widget(button)
            self.total_widgets.append(button)
            for value in row[1:2]:
                machin_text_input = NTextInput(text=str(value), halign='center', size_hint=(None, None), size=(139, 30),
                                               readonly=False, multiline=False, input_filter=lambda text,
                                                                                                    from_undo: text if text.isalnum() or text == " " or text == "_" else '')

                set_tank.add_widget(machin_text_input)
                self.total_widgets.append(machin_text_input)

            for value in row[2:4]:
                text_input = NTextInput(text=str(value), halign='center', size_hint=(None, None), size=(130, 30),
                                        readonly=False, multiline=False)

                set_tank.add_widget(text_input)
                self.total_widgets.append(text_input)
            for value in row[4:5]:
                text_input = NTextInput(text=str(value), halign='center', size_hint=(None, None), size=(130, 30),
                                        readonly=False, multiline=False, input_filter='int')

                set_tank.add_widget(text_input)
                self.total_widgets.append(text_input)
            for value in row[5:]:
                text_input = NTextInput(text=str(value), halign='center', size_hint=(None, None), size=(130, 30),
                                        readonly=False, multiline=False, input_filter='int')

                set_tank.add_widget(text_input)
                self.total_widgets.append(text_input)
        print("Total number of widgets:", len(self.total_widgets))
        set_tank.children[len(set_tank.children) - 1].focus = True

    def save_tank_changes(self):  # modify version2
        try:
            if not self.total_widgets:
                toast("Error: No data detected to update.", duration=0.6)
                return None

            tank.fetch_and_store_output_layout_data(self.connection, self.output_layout_json_filename)

            with open(self.output_layout_json_filename, 'r') as json_file:
                data_list = json.load(json_file)

            for i in range(0, len(self.total_widgets), 15):  # Assuming 10 widgets per tank data row
                tank_id = self.total_widgets[i].text  # TankID widget
                print(f"Processing tank ID: {tank_id}")

                # Find the index of the tank in data_list
                index = next((index for index, data in enumerate(data_list) if str(data['ID']) == tank_id), None)
                if index is not None:
                    print("Tank ID found in data_list.")
                    # Prepare the updated data for the tank
                    updated_data = {
                        'MachineName': self.total_widgets[i + 1].text,
                        'MachinePath': self.total_widgets[i + 2].text,
                        'DrainPath': self.total_widgets[i + 3].text,
                        'SlaveID': self.total_widgets[i + 4].text,
                        'Tank1Path': self.total_widgets[i + 5].text,
                        'Tank2Path': self.total_widgets[i + 6].text,
                        'Tank3Path': self.total_widgets[i + 7].text,
                        'Tank4Path': self.total_widgets[i + 8].text,
                        'Tank5Path': self.total_widgets[i + 9].text,
                        'Tank1Stock': self.total_widgets[i + 10].text,
                        'Tank2Stock': self.total_widgets[i + 11].text,
                        'Tank3Stock': self.total_widgets[i + 12].text,
                        'Tank4Stock': self.total_widgets[i + 13].text,
                        'Tank5Stock': self.total_widgets[i + 14].text,
                    }
                    data_list[index].update(updated_data)
                else:
                    print("Tank ID not found in data_list.")

            # Validate SlaveIDs
            slave_id_counts = {}
            for data in data_list:
                slave_id = data['SlaveID']
                if slave_id in slave_id_counts:
                    slave_id_counts[slave_id] += 1
                else:
                    slave_id_counts[slave_id] = 1

            duplicate_slave_ids = [slave_id for slave_id, count in slave_id_counts.items() if count > 1]
            if duplicate_slave_ids:
                duplicate_slave_id_str = ', '.join(duplicate_slave_ids)
                toast(f"Error: Duplicate Slave IDs detected: {duplicate_slave_id_str}.", duration=0.6)
                return None

            # Validate tank paths
            validation_result = self.validate_tank_paths(data_list)
            if validation_result != "Validation complete. No errors found.":
                toast(validation_result, duration=0.6)
                return None

            with open(self.output_layout_json_filename, 'w') as json_file:
                json.dump(data_list, json_file, indent=2)

            tank.update_from_output_layout(self.connection, self.output_layout_json_filename)

            self.settank()
        except Exception as e:
            print(f"Error saving changes: {e}")

    def validate_tank_paths(self, data_list):
        try:
            all_tank_paths = set()
            for tank_details in data_list:
                tank_id = tank_details['ID']
                for tank_path_key in ['Tank1Path', 'Tank2Path', 'Tank3Path', 'Tank4Path', 'Tank5Path']:
                    tank_path_value = tank_details[tank_path_key]
                    if tank_path_value:
                        try:
                            tank_path_value_int = int(tank_path_value)
                        except ValueError:
                            return f"Validation Error: TankPath '{tank_path_value}' for tank ID '{tank_id}' is not a valid integer."

                        # Check if the tank path value is within the range 1 to 254
                        if not (1 <= tank_path_value_int <= 254):
                            return f"Validation Error: TankPath '{tank_path_value}' for tank ID '{tank_id}' is out of range (1-254)."

                        # Check for repeated tank path values
                        if tank_path_value_int in all_tank_paths:
                            return f"Validation Error: TankPath '{tank_path_value_int}' for tank ID '{tank_id}' is repeated."
                        else:
                            all_tank_paths.add(tank_path_value_int)

            return "Validation complete. No errors found."
        except Exception as e:
            print(f"Error validating TankPaths: {e}")

    def on_tank_button_press(self, instance, tankid, selected_row):
        print(f"Button with ID {tankid} is pressed")
        self.ids.machine_name.text = str(selected_row[1])
        self.ids.machine_path.text = str(selected_row[2])
        self.ids.drain_path.text = str(selected_row[3])
        self.ids.slave_id.text=str(selected_row[4])
        self.ids.tank_1.text = str(selected_row[5])
        self.ids.tank_2.text = str(selected_row[6])
        self.ids.tank_3.text = str(selected_row[7])
        self.ids.tank_4.text = str(selected_row[8])
        self.ids.tank_5.text = str(selected_row[9])

        self.selected_tank_data = {
            'tank_id': str(selected_row[0]),
            'machine_name': str(selected_row[1]),
            'machine_path': str(selected_row[2]),
            'drain_path': str(selected_row[3]),
            'slave_id':str(selected_row[4]),
            'tank_1': str(selected_row[5]),
            'tank_2': str(selected_row[6]),
            'tank_3': str(selected_row[7]),
            'tank_4': str(selected_row[8]),
            'tank_5': str(selected_row[9])

        }

    def save_tank_data(self, instance):
        Machin_Name = self.ids.machine_name.text
        Machin_Path = self.ids.machine_path.text
        Drain_Path = self.ids.drain_path.text
        Slave_ID = self.ids.slave_id.text
        Tank_1 = self.ids.tank_1.text
        Tank_2 = self.ids.tank_2.text
        Tank_3 = self.ids.tank_3.text
        Tank_4 = self.ids.tank_4.text
        Tank_5 = self.ids.tank_5.text
        Tank1_stock = self.ids.tank1_stock.text
        Tank2_stock = self.ids.tank2_stock.text
        Tank3_stock = self.ids.tank3_stock.text
        Tank4_stock = self.ids.tank4_stock.text
        Tank5_stock = self.ids.tank5_stock.text

        tank.insert_tank_data(Machin_Name, Machin_Path, Drain_Path, Slave_ID, Tank_1, Tank_2, Tank_3, Tank_4, Tank_5,
                              Tank1_stock, Tank2_stock, Tank3_stock, Tank4_stock, Tank5_stock)
        self.settank()

    def newtank(self):
        tank = NewTank()
        newtankWindow = Popup(title='NewTanks', content=tank, size_hint=(None, None), size=(1000, 600), padding=10,
                              title_size=20, title_font="Aileron-Bold.otf")
        newtankWindow.open()

    def confirm_delete_popup(self):
        if not self.selected_tank_data:
            toast("Error: No tank selected.", duration=0.6)
            return
        tank_id = self.selected_tank_data['tank_id']

        @mainthread
        def delete_and_reset():
            # Create a new SQLite connection object within this function
            connection = sqlite3.connect("ChemDB.db")
            try:
                if tank.delete_tank(connection, tank_id):
                    self.settank()
                    print("Tank deleted successfully")
                    self.ids.machine_name.text = ''
                    self.ids.machine_path.text = ''
                    self.ids.drain_path.text = ''
                    self.ids.tank_1.text = ''
                    self.ids.tank_2.text = ''
                    self.ids.tank_3.text = ''
                    self.ids.tank_4.text = ''
                    self.ids.tank_5.text = ''
                    self.confirmation_popup.dismiss()
                else:
                    print("Error deleting tank")
            except Exception as e:
                print(f"Error deleting batch: {e}")

        def callback_yes(instance=None):
            delete_and_reset()

        def callback_no(instance=None):
            self.confirmation_popup.dismiss()

        message = (f'Confirm to delete TankId {tank_id} ?\n\n'
                   f'Press y/n')


        self.confirmation_popup = ConfirmationPopup(message=message,
                                                    callback_yes=callback_yes,
                                                    callback_no=callback_no)
        self.confirmation_popup.open()

        def callback_yes():
            delete_and_reset()

        def callback_no():
            self.confirmation_popup.dismiss()

        # Registering hotkeys
        keyboard.add_hotkey("y", callback_yes)
        keyboard.add_hotkey("n", callback_no)

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(400, 100))
        error_popup.open()
        self.current_popup = error_popup

    def close_error_popup(self):
        # Check if there is a current popup and dismiss it if there is
        if self.current_popup:
            self.current_popup.dismiss()
            self.current_popup = None

    def start_keyboard_listener(self):
        # Start listening for keyboard events in a separate thread
        keyboard.add_hotkey("ctrl+s", self.on_enter_pressed)
        keyboard.add_hotkey("delete", self.on_delete_button)
        # keyboard.add_hotkey("ctrl+g", self.on_general)
        # keyboard.add_hotkey("ctrl+u", self.on_user)
        keyboard.add_hotkey("ctrl+n", self.on_new_pressed)
        keyboard.add_hotkey("end", self.on_end)

    def on_end(self, event=None):
        Clock.schedule_once(self.go_to_end)

    def go_to_end(self, dt):
        self.close_error_popup()

    def on_new_pressed(self, event=None):
        Clock.schedule_once(self.go_to_new)

    def go_to_new(self, dt):
        self.newtank()

    def on_general(self, event=None):
        Clock.schedule_once(self.go_to_general)

    def go_to_general(self, dt):
        app = App.get_running_app()
        app.switch_to_general()

    def on_user(self, event=None):
        Clock.schedule_once(self.go_to_user)

    def go_to_user(self, dt):
        app = App.get_running_app()
        app.switch_to_user()

    def on_enter_pressed(self, event=None):
        # Method to be called when Enter key is pressed
        Clock.schedule_once(self.enter_save_changes)

    def enter_save_changes(self, dt):
        self.save_tank_changes()

    def on_delete_button(self):
        Clock.schedule_once(self.delete_from_key)

    def delete_from_key(self, dt):
        if self.ids.machine_name.text != '':
            self.confirm_delete_popup()

    def handle_delete_button_press(self):
        if self.ids.machine_name.text != '':
            self.confirm_delete_popup()

    def tankpop(self):
        data = TankWash()
        tankWindow = Popup(title='Tank Wash', content=data, size_hint=(None, None), size=(500, 400), padding=10,title_size=20, title_font = "Aileron-Bold.otf")
        tankWindow.open()

    def tank_details(self):
        tank = TankDetails()
        detailsWindow = Popup(title='Tank Wash Details', content=tank, size_hint=(None, None), size=(900, 500), padding=10,title_size=20, title_font = "Aileron-Bold.otf")
        detailsWindow.open()
        return detailsWindow

    def show_tank(self):
        tank_data = ShowTank()
        Window = Popup(title='Wash Details', content=tank_data, size_hint=(None, None), size=(800, 400), padding=10,title_size=20, title_font = "Aileron-Bold.otf")
        Window.open()
        return Window


class ConfirmationPopup(Popup):
    def __init__(self, message, callback_yes, callback_no, **kwargs):
        super(ConfirmationPopup, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (250, 250)
        self.title = "Confirmation"

        box_layout = BoxLayout(orientation='vertical')
        box_layout.add_widget(Label(text=message))

        button_layout = BoxLayout(spacing=10)

        yes_button = Button(text='Yes', on_release=callback_yes, size_hint=(None, None), size=(50, 40))
        no_button = Button(text='No', on_release=callback_no, size_hint=(None, None), size=(50, 40))

        button_layout.add_widget(yes_button)
        button_layout.add_widget(no_button)

        box_layout.add_widget(button_layout)

        self.content = box_layout

class TanksApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home_hotkey_id = None

    def build(self):
        self.icon = 'logindi.png'
        Window.maximize()
        Builder.load_file('tankspage.kv')
        app = MyApp()
        app.start_keyboard_listener()
        sys.setrecursionlimit(10 ** 9)
        return app

    def delay_fn(self, fn_name):
        self.root.ids.general_button.disabled = True
        self.root.ids.user_button.disabled = True
        self.root.ids.tanks_button.disabled = True
        self.root.ids.tank_wash_button.disabled = True
        self.root.ids.new_button.disabled = True
        self.root.ids.save_button.disabled = True
        self.root.ids.delete_button.disabled = True
        self.root.ids.home.disabled = True
        Clock.schedule_once(lambda dt: getattr(self, fn_name)(), 0.6)

    def change_button_color(self, button):
        button.md_bg_color = (77/255, 199/255, 226/255, 1)
        Clock.schedule_once(lambda dt: self.reset_button_color(button), .1)

    def reset_button_color(self, button):

        button.md_bg_color = (0.3, 0.3, 0.3, 1)

    def switch_to_main(self):
        Builder.unload_file('tankspage.kv')
        print("Unloaded report")
        from main import MainApp
        self.stop()
        MainApp().run()

    def switch_to_general(self):
        Builder.unload_file('tankspage.kv')
        print("Unloaded setting")
        from settings import generalApp
        self.stop()
        generalApp().run()

    def switch_to_user(self):
        Builder.unload_file('tankspage.kv')
        print("Unloaded setting")
        from user import UserApp
        self.stop()
        UserApp().run()

    def switch_to_tanks(self):
        Builder.unload_file('tankspage.kv')
        print("Unloaded setting")
        self.stop()
        TanksApp().run()

    def on_start(self):
        # Register the hotkey
        # self.home_hotkey_id = keyboard.add_hotkey("home", self.on_home_pressed)
        pass

    def on_home_pressed(self, event=None):
        Clock.schedule_once(self.go_to_home)

    def home_hotkey_unhook(self):
        # Unhook the hotkey if it was registered
        if self.home_hotkey_id is not None:
            try:
                keyboard.remove_hotkey(self.home_hotkey_id)
            except ValueError:
                pass
            self.home_hotkey_id = None

    def on_stop(self):
        keyboard.unhook_all_hotkeys()
        self.home_hotkey_unhook()


    def go_to_home(self, dt):
        self.switch_to_main()




if __name__ == '__main__':
    TanksApp().run()

import ctypes
import sys
import time

import keyboard
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ColorProperty, ObjectProperty, NumericProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.toast import toast
from kivy.graphics import Color, Line
import threading
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.icon_definitions import md_icons
from database import *

batch=BatchChemicalData()
batch_metadata=BatchMetaData()
user=User()
tank=OutputLayout()
chemical=Chemical()

class BatchInteger(TextInput):
    def insert_text(self, substring, from_undo=False):

        current_text = self.text

        if substring in '0123456789.':

            if '.' in current_text:

                integer_part, fractional_part = current_text.split('.')

                if substring == '.':
                    return

                if len(fractional_part) < 3:
                    super().insert_text(substring, from_undo=from_undo)
            else:
                super().insert_text(substring, from_undo=from_undo)
        else:
            return

    row = NumericProperty()
    col = NumericProperty()

class CustomSpinner(Spinner):
    def __init__(self, **kwargs):
        super(CustomSpinner, self).__init__(**kwargs)
        self.dropdown_cls.max_height = 190
class MaxLengthTextInput(TextInput):
    row = NumericProperty()
    col = NumericProperty()
    def __init__(self, **kwargs):
        self.maxlength = kwargs.pop('maxlength', None)
        super(MaxLengthTextInput, self).__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        if self.maxlength is not None:
            if len(self.text) + len(substring) > self.maxlength:
                substring = substring[:self.maxlength - len(self.text)]
        return super(MaxLengthTextInput, self).insert_text(substring, from_undo=from_undo)

class FocusTextInput(TextInput, FocusBehavior):
    row = NumericProperty()
    col = NumericProperty()



    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'tab':
            self.dispatch('on_triple_tap')
            return True
        if super(FocusTextInput, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        alt_pressed = 'alt' in modifiers
        if alt_pressed and keycode[1] == 'left':
            self.cursor_previous_letter()
            return True
        elif alt_pressed and keycode[1] == 'right':
            self.cursor_next_letter()
            return True

        if keycode[1] == 'down':
            self.navigate(0, -14)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 14)
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

        if isinstance(new_widget, FocusTextInput) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True

class FocusSpinner(Spinner, FocusBehavior):
    focused = BooleanProperty(False)
    focus_color = ColorProperty((0, 0.5, 1, 1))  # Change this to your desired color
    dropdown_open = BooleanProperty(False)
    selected_dropdown_item = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(FocusSpinner, self).__init__(**kwargs)
        self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
        self.bind(on_text=self.on_spinner_text)
        Clock.schedule_once(self.set_initial_selected_item)

    def set_initial_selected_item(self, dt):
        # Set the initial selected dropdown item when the spinner is first displayed
        for child in self._dropdown.container.children:
            if child.text == self.text:
                self.selected_dropdown_item = child
                self.selected_dropdown_item.state = 'down'
            else:
                child.state = 'normal'

    def on_text(self, spinner, text):
        # Ensure that the dropdown exists
        if spinner._dropdown is not None:
            # Find the selected dropdown item
            for child in spinner._dropdown.container.children:
                if child.text == text:
                    self.selected_dropdown_item = child
                    # Change the state of the selected item to 'down'
                    self.selected_dropdown_item.state = 'down'
                else:
                    # Reset the state of other items to 'normal'
                    child.state = 'normal'

    def on_spinner_text(self, spinner, text):
        # Find the selected dropdown item
        for child in spinner._dropdown.container.children:
            if child.text == text:
                self.selected_dropdown_item = child
                # Change the state of the selected item to 'down'
                self.selected_dropdown_item.state = 'down'
            else:
                # Reset the state of other items to 'normal'
                child.state = 'normal'

    def on_focused(self, instance, value):
        self.background_color = self.focus_color if value else (1, 1, 1, 1)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.focused = True
        return super(FocusSpinner, self).on_touch_down(touch)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super(FocusSpinner, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        if self.focused:
            if not self.dropdown_open:
                if keycode[1] == 'enter':
                    # Simulate behavior of Down key press
                    self._select_next_dropdown_item()
                    self.background_color = (1, 0, 0, 1)
                    return True

            elif self.dropdown_open:
                self.background_color =  (1, 0, 0, 1)
                if keycode[1] == 'down':
                    self._select_next_dropdown_item()
                    return True
                elif keycode[1] == 'up':
                    self._select_previous_dropdown_item()
                    return True
                elif self.dropdown_open:
                    if keycode[1] == 'enter':
                        print("Selecting dropdown item...")
                        item_selected = False
                        for child in self._dropdown.container.children:
                            print("Dropdown item state:", child.state)
                            if hasattr(child, 'state') and child.state == 'down':
                                self.text = child.text
                                print("Selected item text:", child.text)
                                self.dropdown_open = False  # Close the dropdown
                                self.focused = True  # Unfocus the spinner
                                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
                                item_selected = True
                                return True

                        if not item_selected:
                            print("No dropdown item selected")
                            # If no item was selected, retain focus on the spinner
                            self.focused = True
                            return False

        # Handle focusing on spinner values without the dropdown open
        if self.focused and not self.dropdown_open:
            if keycode[1] == 'enter':
                # Do something when Enter is pressed without the dropdown open
                print("Focusing on spinner values without dropdown open")
                return True

        elif self.dropdown_open:
            if keycode[1] == 'enter':
                # Keep the dropdown open if it's already open
                return True

        # Handle default navigation behavior
        if self.focused:
            if keycode[1] == 'down':
                self.navigate(0, -14)
                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
                return True
            elif keycode[1] == 'up':
                self.navigate(0, 14)
                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
                return True
            elif keycode[1] == 'left':
                self.navigate(0, 1)
                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
                return True
            elif keycode[1] == 'right':
                self.navigate(0, -1)
                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
                return True
            elif keycode[1] == 'enter':
                self.dispatch('on_press')
                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
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

        if isinstance(new_widget,Spinner) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True

    def _select_next_dropdown_item(self):
        self.dropdown_open = True
        if not self.text:  # If the spinner's text is empty
            self.text = self.values[0]  # Set it to the first value
            return
        try:
            idx = self.values.index(self.text)
            next_idx = (idx + 1) % len(self.values)
            self._dropdown.select(self.values[next_idx])
        except ValueError:
            toast("Error: The data is not in database.", duration=0.6)
            return

    def _select_previous_dropdown_item(self):
        if not self.text:  # If the spinner's text is empty
            if self.values:
                self.text = self.values[-1]  # Set it to the last value
            else:
                return  # No values available, can't select
        try:
            idx = self.values.index(self.text)
            previous_idx = (idx - 1) % len(self.values)
            self._dropdown.select(self.values[previous_idx])
        except ValueError:
            toast("Error: The data is not in database.", duration=0.6)
            return
    def show_error_popup(self, message):
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()


class FocusButton(Button, FocusBehavior):
    focused = BooleanProperty(False)
    focus_color = ColorProperty((0, 0.5, 1, 1))  # Change this to your desired focus color
    row = NumericProperty()
    col = NumericProperty()

    def __init__(self, **kwargs):
        super(FocusButton, self).__init__(**kwargs)
        self.default_color = self.background_color
        self.bind(pos=self.update_outline, size=self.update_outline)
        with self.canvas.before:
            Color(18/255,145/255,206/255, 1)  # Blue color
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
                self.navigate(0, -14)
                return True
            elif keycode[1] == 'up':
                self.navigate(0, 14)
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
        if row < len(chemical_grid.children) - 1:
            next_row_columns = len(chemical_grid.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(chemical_grid.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(chemical_grid.children[row].children) - 1))

        new_widget = chemical_grid.children[new_row].children[new_col]

        if isinstance(new_widget, FocusButton) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True


class NewBatch(BoxLayout):
    def __init__(self, **kwargs):
        super(NewBatch, self).__init__(**kwargs)

    def save_button_pressed(self, instance):
        batch_name = self.ids.batch_name.text
        fabric_weight = self.ids.fabric_weight.text
        mlr = self.ids.mlr.text
        machin_name = self.ids.machin_name.text

        if not batch_name or not fabric_weight or not mlr or not machin_name:
            # Display an error message or alert the user that all fields must be filled
            toast("Error: Check All fields.", duration=0.6)
            return

        conn = create_connection("ChemDB.db")
        if batch_metadata.data_exist_bachmeta(conn, batch_name, fabric_weight, mlr, machin_name):
            toast("Error: The data already exists.", duration=0.6)
        else:
            # Call the function with all the required arguments
            batch_metadata.insert_into_BatchMetaData(conn, batch_name, fabric_weight, mlr, machin_name)
            App.get_running_app().root.display_selected_batch(batch_metadata.fetch_selected_batch_details())
            batch_id = batch_metadata.fetch_selected_batch_id()
            if batch_id:
                # Show the data for the selected batch name
                App.get_running_app().root.display_selected_batch_data_by_name(batch_id)

            self.ids.batch_name.text = ''
            self.ids.fabric_weight.text = ''
            self.ids.mlr.text = ''
            self.ids.machin_name.text = ''

            parent_popup = self.parent.parent.parent  # Adjust the number of ".parent" based on your hierarchy
            parent_popup.dismiss()

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()


    def spinner_clicked(self, spinner_instance, value):
        print(f"Spinner clicked with text: {value}")

    def switch_to_refresh(self):
        time.sleep(1)
        Builder.unload_file('batchpage.kv')
        print("Unloaded Batch")
        BatchApp.stop(self)
        BatchApp().run()
class OpenBatch(BoxLayout):
    def __init__(self, **kwargs):
        super(OpenBatch, self).__init__(**kwargs)
        self.selected_batch_name = None
        self.batch_names_cache = []
        self.fetch_and_display_batch_names()
        self.search_debounce_event = None

    def fetch_and_display_batch_names(self):
        if not self.batch_names_cache:
            threading.Thread(target=self.fetch_batch_names_async).start()
        else:
            self.display_batch_names(self.batch_names_cache[-100:])

    def fetch_batch_names_async(self):
        batch_names = self.get_batch_names()
        self.batch_names_cache = batch_names
        Clock.schedule_once(lambda dt: self.display_batch_names(batch_names[-100:]))

    def display_batch_names(self, batch_names):
        batch_layout = self.ids.total_batch
        batch_layout.clear_widgets()

        for name in batch_names:
            if name:
                button = Button(
                    text=name, size_hint_y=None, height=30,
                    background_color=(3, 3, 3, 1), color=(0, 0, 0, 3)
                )
                button.bind(on_release=self.on_batch_button_click)
                batch_layout.add_widget(button)

    def get_batch_names(self):
        batch_names = batch_metadata.fetch_batch_name()
        return [name for name in batch_names if name]

    def on_batch_button_click(self, instance):
        button_text = instance.text
        id_index = button_text.find("ID:")

        if id_index != -1:
            id_start = id_index + len("ID:")
            batchname_index = button_text.find("BatchName:", id_start)
            if batchname_index != -1:
                id_value = button_text[id_start:batchname_index].strip()
            else:
                id_value = button_text[id_start:].strip()

            selected_batch_label = self.ids.selected_batch
            selected_batch_label.text = id_value
            self.selected_batch_name = id_value

    def on_open_button_press(self, instance):
        selected_batch_label = self.ids.selected_batch
        if selected_batch_label.text:
            # Fetch batch information asynchronously
            threading.Thread(target=self.fetch_batch_info_async, args=(selected_batch_label.text,)).start()
        else:
            toast("Error: No batch selected.", duration=0.6)

    def fetch_batch_info_async(self, batch_id):
        try:
            selected_batch_info = batch_metadata.fetch_selected_batch_info(batch_id)
            Clock.schedule_once(lambda dt: self.display_selected_batch_info(selected_batch_info), 0)
        except Exception as e:
            pass

    def display_selected_batch_info(self, selected_batch_info):
        print(selected_batch_info)

        app = App.get_running_app()
        root = app.root

        root.display_selected_batch(selected_batch_info)
        if self.selected_batch_name:
            root.display_selected_batch_data_by_name(self.selected_batch_name)
            self.fetch_and_display_batch_names()

        # Schedule the popup dismissal on the main thread
        Clock.schedule_once(self.dismiss_popup, 0)

    def dismiss_popup(self, dt):
        parent_popup = self.parent.parent.parent
        parent_popup.dismiss()

    def on_search_input_change(self, text):
        if self.search_debounce_event:
            self.search_debounce_event.cancel()

        self.search_debounce_event = Clock.schedule_once(lambda dt: self.perform_search(text), 0.2)

    def perform_search(self, text):
        if not text:
            self.fetch_and_display_batch_names()
        else:
            filtered_batch_names = self.get_filtered_batch_names(text)
            self.update_batch_layout(filtered_batch_names)

    def get_filtered_batch_names(self, search_text):
        return [name for name in self.batch_names_cache if search_text.lower() in name.lower()]

    def update_batch_layout(self, batch_names):
        batch_layout = self.ids.total_batch
        batch_layout.clear_widgets()

        for name in batch_names:
            if name:
                button = Button(
                    text=name, size_hint_y=None, height=30,
                    background_color=(3, 3, 3, 1), color=(0, 0, 0, 3)
                )
                button.bind(on_release=self.on_batch_button_click)
                batch_layout.add_widget(button)

class MyApp(BoxLayout):
    def __init__(self, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.total_widgets = []
        self.json_filename = 'BatchChemicalData.json'
        self.BatchmetaData(selected_batch_data={})
        self.selected_batch_data = {}
        self.selected_batch_name = None
        self.data = None
        self.connection = create_connection("ChemDB.db")
        self.chemical_names = self.get_chemical_names()
        self.text_input = self.ids.chemspin
        self.dropdown = DropDown()
        self.populate_dropdown()
        self.current_popup = None

    def on_textinput_focus(self, instance, focused):
        if focused:
            self.show_dropdown()
        else:
            self.dropdown.dismiss()

    def close_dropdown(self):
        self.dropdown.dismiss()

    def show_dropdown(self):
        self.dropdown.clear_widgets()
        for name in self.chemical_names:
            btn = Button(text=name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_chemical(btn.text))
            self.dropdown.add_widget(btn)
        self.dropdown.max_height = 190  # Set the max_height directly on the dropdown object
        self.dropdown.open(self.text_input if self.text_input.focus else None)

    def populate_dropdown(self):
        self.dropdown.clear_widgets()
        for name in self.chemical_names:
            btn = Button(text=name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_chemical(btn.text))
            self.dropdown.add_widget(btn)

    def filter_chemicals(self, value):
        filtered_names = [name for name in self.chemical_names if value.lower() in name.lower()]
        self.dropdown.clear_widgets()
        for name in filtered_names:
            btn = Button(text=name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_chemical(btn.text))
            self.dropdown.add_widget(btn)
        if filtered_names:
            if not self.dropdown.parent:  # Check if the dropdown is already open
                self.dropdown.open(self.text_input)
        else:
            self.dropdown.dismiss()

    def select_chemical(self, name):
        self.text_input.text = name
        self.dropdown.dismiss()

    def display_selected_batch_data_by_name(self, selected_batch_name):
        # Fetch batch chemical data for the opened batch using the batch name
        data = Clock.schedule_once(lambda dt:batch.fetch_BatchChemicalData_data_by_batch_name(selected_batch_name),0.5)
        print("selected batch name:",{selected_batch_name})

        # Update the UI with the fetched data
        self.BatchmetaData({'batch_name': selected_batch_name, 'data': data})
        self.ids.userauthen.text = "All User"
        self.ids.status.text = "Pending"
        self.ids.dispense_when.text="Request"
        batchmeta_grid = self.ids.batchmeta_grid
        batchmeta_grid.children[len(batchmeta_grid.children) - 1].focus = True



    def display_selected_batch(self, selected_batch_info):
        try:

            self.ids.batch_id.text = str(selected_batch_info[0])
            self.ids.batch_name.text = str(selected_batch_info[1])
            self.ids.fabric_weight.text = str(selected_batch_info[2])
            self.ids.mlr.text = str(selected_batch_info[3])
            self.ids.machin_no.text = str(selected_batch_info[4])
            self.ids.created_by.text = str(selected_batch_info[5])
            self.ids.created_date.text = str(selected_batch_info[6])
            self.ids.userauthen.text = "All User"
            self.ids.status.text = "Pending"
            batchmeta_grid = self.ids.batchmeta_grid
            batchmeta_grid.children[len(batchmeta_grid.children) - 1].focus = True

        except KeyError as e:
            print(f"Error: ID not found - {e}")

    def save_button(self):  # modify version2
        try:
            # Get values from TextInput fields
            batch_id = self.ids.batch_id.text
            batch_name = self.ids.batch_name.text
            seq_no = int(self.ids.seq_no.text)
            chemical = self.ids.chemspin.text
            target_weight = float(self.ids.target_weight.text)
            user_name = self.ids.userauthen.text
            status = self.ids.status.text
            tank_spinner = self.ids.tank_spinner.text
            dispense_when = self.ids.dispense_when.text
            machine_name = self.ids.machin_no.text
            target_wt_validate = tank.validate_target_wt_based_tank(tank_spinner, machine_name)
            print('valuse', target_wt_validate)
            # Check if any required field is empty
            if float(target_weight) > int(target_wt_validate):
                toast(f"Error: Correct your Target weight for {tank_spinner} capacity {target_wt_validate} .",
                      duration=0.6)
                return
            if not all([batch_name, chemical, user_name, status, tank_spinner, seq_no, target_weight, dispense_when]):
                toast("Error: Please fill in all required fields.", duration=0.6)
                return

            conn = create_connection("ChemDB.db")

            # Check if the data already exists
            if batch.data_exists_batch(conn, batch_id, batch_name, seq_no, tank_spinner, chemical, target_weight,
                                       user_name, status, dispense_when):
                toast("Error: The data already exists.", duration=0.6)
                return

            # Check if the entered chemical exists
            chemical_names = self.get_chemical_names()
            if chemical not in chemical_names:
                toast(f"Error: '{chemical}' is not a valid chemical name.", duration=0.6)
                return

            # Insert data into BatchChemicalData table
            batch.insert_into_BatchChemicalData(conn, batch_id, batch_name, seq_no, tank_spinner, chemical,
                                                target_weight, user_name,
                                                status, dispense_when)

            close_connection(conn)

            print("Save button clicked successfully.")

            # Clear the input fields after successful save
            self.ids.seq_no.text = ""
            self.ids.chemspin.text = ""
            self.ids.chemspin.focus = False
            self.close_dropdown()
            self.ids.target_weight.text = ""
            self.ids.userauthen.text = "All User"
            self.ids.status.text = "Pending"
            self.ids.tank_spinner.text = ""
            print(batch_id)
            self.display_selected_batch_data_by_name(batch_id)

        except Exception as e:
            toast("Error: Please fill in all required fields.", duration=0.6)
            return

    def confirm_update_batch(self):
        batch_name = self.ids.batch_name.text
        batch_id = self.ids.batch_id.text

        if not batch_id:
            toast("Error: No batch opened.", duration=0.6)
            return

        def callback_yes(instance):
            try:
                # Call the correct function to delete the batch
                batch_metadata.delete_Batchmedata(create_connection("ChemDB.db"), batch_id)
                print("Batch deleted successfully")

                # Schedule GUI updates in the main thread
                Clock.schedule_once(lambda dt: self.update_batch_gui_elements(), 0)
            except Exception as e:
                print(f"Error deleting batch: {e}")

            self.confirmation_popup.dismiss()

        def callback_no(instance):
            self.confirmation_popup.dismiss()

        message = (f'Confirm to delete Batch {batch_name} ?\n\n'
                   f'Press y/n')

        self.confirmation_popup = ConfirmationPopup(message=message,
                                                    callback_yes=callback_yes,
                                                    callback_no=callback_no)
        self.confirmation_popup.open()

    # Add a method to display error popups
    def show_error_popup(self, message):
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()
        self.current_popup = error_popup

    def dismiss_error_popup(self):
        # Check if there is a current popup and dismiss it if there is
        if self.current_popup:
            self.current_popup.dismiss()
            self.current_popup = None

    def save_changes(self):
        batch_id = self.ids.batch_id.text
        batch_name = self.ids.batch_name.text
        connection = create_connection("ChemDB.db")
        machine_name = self.ids.machin_no.text
        batch.fetch_and_store_data(connection, self.json_filename, batch_id)

        try:
            if not self.total_widgets:
                toast("Error: No data detected to update.", duration=0.6)
                return None

            # Load the existing data from the JSON file
            with open(self.json_filename, 'r') as json_file:
                data_list = json.load(json_file)

            # Iterate through the widgets and update the corresponding data
            for i in range(0, len(self.total_widgets), 14):  # Assuming 14 widgets per row
                record_id = int(self.total_widgets[i].text)  # ID widget

                for data in data_list:
                    if data['ID'] == record_id:
                        # Update the data dictionary with new values from the UI
                        data.update({
                            'SeqNo': self.total_widgets[i + 1].text,
                            'TargetTank': self.total_widgets[i + 2].text,
                            'Chemical No': self.total_widgets[i + 3].text,
                            'Chemical': self.total_widgets[i + 4].text,
                            'TargetWeight': float(self.total_widgets[i + 5].text),
                            'DispensedWeight': self.total_widgets[i + 6].text,
                            'UserName': self.total_widgets[i + 7].text,
                            'Status': self.total_widgets[i + 8].text,
                            'Date': self.total_widgets[i + 9].text,
                            'DispDate': self.total_widgets[i + 10].text,
                            'DispTime': self.total_widgets[i + 11].text,
                            'WaterAddition': self.total_widgets[i + 12].text,
                            'DispenseWhen': self.total_widgets[i + 13].text
                        })

                        # Validate the target weight based on the tank
                        target_tank = data.get('TargetTank')
                        target_wt_validate = tank.validate_target_wt_based_tank(target_tank, machine_name)
                        print('validated weight:', target_wt_validate)

                        # Check if the target weight exceeds the tank capacity
                        if float(data.get('TargetWeight')) > float(target_wt_validate):
                            toast(
                                f"Error: Correct your target weight for {target_tank}, max capacity is {target_wt_validate}.",
                                duration=0.6)
                            return None  # Exit if validation fails
                        break  # Move on to the next record

            # Save the modified data back to the JSON file
            with open(self.json_filename, 'w') as json_file:
                json.dump(data_list, json_file, indent=2)

            print("Changes saved to JSON file successfully.")

            # Update the SQLite database
            try:
                database_file = 'ChemDB.db'
                connection = sqlite3.connect(database_file)
                batch.update_from_json(connection, self.json_filename)  # Assuming this method handles the update logic
                print("Changes saved to the database successfully.")

            except sqlite3.Error as e:
                print(f"SQLite error: {e}")

            # Refresh the displayed data
            self.display_selected_batch_data_by_name(batch_id)

        except Exception as e:
            print(f"Error saving changes: {str(e)}")



    def get_user_names(self):
        # Fetch user names from the database
        user_names = user.fetch_user_names()
        user_names.insert(0, 'All User')
        return user_names

    def get_tank_details(self):
        database_file = "ChemDB.db"
        connection = sqlite3.connect(database_file)
        machine_name = self.ids.machin_no.text
        tank_details = tank.fetch_tank_paths(connection, machine_name)


        # Check if tank_details is not None before inserting
        if tank_details is not None and any(tank_details):
            self.ids.tank_spinner.values = tank_details
            return tank_details
        else:
            self.ids.tank_spinner.values = ["No Tank"]
            return ["No Tank"]  # Default values in case of an error or empty values

    def get_chemical_names(self):
        # Fetch chemical names from the database
        chemical_names = chemical.fetch_chemical_names()

        # Remove empty strings from the list
        chemical_names = [name for name in chemical_names if name]

        return chemical_names

    def BatchmetaData(self, selected_batch_data):

        self.total_widgets.clear()
        self.ids.batchmeta_grid.clear_widgets()
        batchmeta_grid = self.ids.batchmeta_grid
        # Clear existing widgets in batchmeta_grid
        batchmeta_grid.clear_widgets()

        headers = ['ID', 'SeqNo','TargetTank', 'Chemical No', 'Chemical', 'TargetWeight', 'DispensedWt', 'UserName',
                   'Status', 'Date', 'DispDate', 'DispTime', 'WaterAddition','DispenseWhen']

        # Add headers to the grid
        for header in headers:
            batchmeta_grid.add_widget(
                FocusTextInput(text=header, halign='center',font_size=17, size_hint=(None, None), size=(137.6, 35), readonly=True,multiline=False,font_name="Aileron-Bold.otf"))

        batch_id = selected_batch_data.get('batch_name')
        print(batch_id)
        batchmeta_grid.children[len(batchmeta_grid.children) - 1].focus = True
        if batch_id:
            # Fetch batch chemical data for the opened batch using the batch name
            data = batch.fetch_BatchChemicalData_data_by_batch_name(batch_id)

            for row in data:
                batch_id = str(row[0])
                button = FocusButton(text=batch_id, size_hint=(None, None), size=(137.6, 30))
                button.bind(
                    on_press=lambda instance, batchid=batch_id, selected_row=row: self.on_batch_button_press(
                        instance, batchid, selected_row))
                batchmeta_grid.add_widget(button)
                self.total_widgets.append(button)

                for value in row[1:2]:
                    text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None), size=(137.6, 30),
                                           readonly=True, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_input)
                    self.total_widgets.append(text_input)


                for index, value in enumerate(row[2:3]):
                    tank_spinner = FocusSpinner(text=str(value), values=self.get_tank_details(), halign='center',
                                           size_hint=(None, None), size=(137.6, 30), color=(0, 0, 0, 1),
                                           background_color=(3, 3, 3, 1))
                    tank_spinner.bind(on_text=self.spinner_clicked)
                    tank_spinner.dropdown_cls.max_height = 190
                    batchmeta_grid.add_widget(tank_spinner)
                    self.total_widgets.append(tank_spinner)

                for value in row[3:4]:
                    text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None), size=(137.6, 30),
                                           readonly=True, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_input)
                    self.total_widgets.append(text_input)

                for index, value in enumerate(row[4:5]):
                    text_spinner = FocusSpinner(text=str(value), values=self.get_chemical_names(), halign='center',
                                           size_hint=(None, None), size=(137.6, 30), color=(0, 0, 0, 1),
                                           background_color=(3, 3, 3, 1))
                    text_spinner.bind(on_text=self.spinner_clicked)
                    text_spinner.dropdown_cls.max_height = 190
                    batchmeta_grid.add_widget(text_spinner)
                    self.total_widgets.append(text_spinner)

                for value in row[5:6]:
                    text_write_widget = CustomTextInput(text=str(value), halign='center', size_hint=(None, None),
                                                  size=(137.6, 30),
                                                  readonly=False, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_write_widget)
                    self.total_widgets.append(text_write_widget)

                for value in row[6:7]:
                    text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None), size=(137.6, 30),
                                           readonly=True, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_input)
                    self.total_widgets.append(text_input)

                for value in row[7:8]:
                    user_spinner = FocusTextInput(text=str(value),halign='center',
                                           size_hint=(None, None), size=(137.6, 30), color=(0, 0, 0, 1),
                                           background_color=(3, 3, 3, 1),readonly=True)
                    batchmeta_grid.add_widget(user_spinner)
                    self.total_widgets.append(user_spinner)

                for value in row[8:9]:
                    status_spinner = FocusTextInput(text=str(value),halign='center',
                                             size_hint=(None, None), size=(137.6, 30), color=(0, 0, 0, 1),
                                             background_color=(3, 3, 3, 1),readonly=True)
                    batchmeta_grid.add_widget(status_spinner)
                    self.total_widgets.append(status_spinner)

                for value in row[9:11]:
                    text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None), size=(137.6, 30),
                                           readonly=True, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_input)
                    self.total_widgets.append(text_input)

                for value in row[11:12]:
                    text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None), size=(137.6, 30),
                                           readonly=True, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_input)
                    self.total_widgets.append(text_input)

                for value in row[12:13]:
                    text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None), size=(137.6, 30),
                                           readonly=True, background_color=(3, 3, 3, 1),multiline=False)
                    batchmeta_grid.add_widget(text_input)
                    self.total_widgets.append(text_input)
                for index, value in enumerate(row[13:]):
                    dispense_values = ['Request', 'Sequence']
                    dispense_spinner = FocusSpinner(text=str(value), values=dispense_values, halign='center',
                                             size_hint=(None, None), size=(137.6, 30), color=(0, 0, 0, 1),
                                             background_color=(3, 3, 3, 1))
                    dispense_spinner.bind(on_text=self.spinner_clicked)
                    batchmeta_grid.add_widget(dispense_spinner)
                    self.total_widgets.append(dispense_spinner)
            print("Total number of widgets:", len(self.total_widgets))

    def on_batch_button_press(self, instance, batchid, selected_row):
        print(f"Button with ID:{batchid}is pressed")
        self.selected_batch_data = {'batchid': batchid, 'selected_row': selected_row}
        self.ids.seq_no.text = str(selected_row[1])
        self.ids.chemspin.text = str(selected_row[4])
        self.ids.chemspin.focus = False
        self.close_dropdown()
        self.ids.target_weight.text = str(selected_row[5])
        self.ids.userauthen.text = str(selected_row[7])
        self.ids.status.text = str(selected_row[8])
        self.ids.dispense_date.text = str(selected_row[10])
        self.ids.dispense_time.text = (str(selected_row[11]))
        self.ids.tank_spinner.text = str(selected_row[2])
        self.ids.dispense_when.text = str(selected_row[13])

        self.selected_batch_data = {
            'batch_id': str(selected_row[0]),
            'seq_no': str(selected_row[1]),
            'chemical': str(selected_row[4]),
            'target_weight': str(selected_row[5]),
            'user_name': str(selected_row[7]),
            'status': str(selected_row[8]),
            'tank_spinner': str(selected_row[2]),
            'dispense_when': str(selected_row[13])
        }

    def spinner_clicked(self, spinner_instance, value):
        print(f"Spinner clicked with text: {value}")

    def confirm_delete_batch(self):
        batch_name = self.ids.batch_name.text
        batch_id = self.ids.batch_id.text

        if not batch_id:
            toast("Error: No batch opened.", duration=0.6)
            return

        def callback_yes(instance):
            try:
                # Call the correct function to delete the batch
                batch_metadata.delete_Batchmedata(create_connection("ChemDB.db"), batch_id)
                print("Batch deleted successfully")

                # Schedule GUI updates in the main thread
                Clock.schedule_once(lambda dt: self.update_batch_gui_elements(), 0)
            except Exception as e:
                print(f"Error deleting batch: {e}")

            self.confirmation_popup.dismiss()

        def callback_no(instance):
            self.confirmation_popup.dismiss()

        message = (f'Confirm to delete Batch {batch_name} ?\n\n'
                   f'Press y/n')

        self.confirmation_popup = ConfirmationPopup(message=message,
                                                    callback_yes=callback_yes,
                                                    callback_no=callback_no)
        self.confirmation_popup.open()

        def callback_yes():
            try:
                # Call the correct function to delete the batch
                batch_metadata.delete_Batchmedata(create_connection("ChemDB.db"), batch_id)
                print("Batch deleted successfully")

                # Schedule GUI updates in the main thread
                Clock.schedule_once(lambda dt: self.update_batch_gui_elements(), 0)
            except Exception as e:
                print(f"Error deleting batch: {e}")

            self.confirmation_popup.dismiss()

        def callback_no():
            self.confirmation_popup.dismiss()

        keyboard.add_hotkey("y", callback_yes)
        keyboard.add_hotkey("n", callback_no)

    def update_batch_gui_elements(self):
        # Update GUI elements in the main thread
        batch_id = self.ids.batch_id.text
        batch_name = self.ids.batch_name.text
        self.ids.batch_id.text = ""
        self.ids.batch_name.text = ""
        self.ids.fabric_weight.text = ""
        self.ids.mlr.text = ""
        self.ids.machin_no.text = ""
        self.ids.created_by.text = ""
        self.ids.created_date.text = ""
        self.ids.batchmeta_grid.clear_widgets()  # Clearing grid widgets
        self.ids.seq_no.text = ""
        self.ids.chemspin.text = ""
        self.ids.target_weight.text = ""
        self.ids.userauthen.text = "All User"
        self.ids.status.text = "Pending"
        self.ids.dispense_date.text = ""
        self.ids.dispense_time.text = ""
        self.ids.tank_spinner.text = ""
        self.ids.chemspin.focus = False
        self.close_dropdown()
        self.display_selected_batch_data_by_name(batch_id)

    def update_gui_elements(self):
        # Update GUI elements in the main thread
        batch_id = self.ids.batch_id.text
        batch_name = self.ids.batch_name.text
        self.ids.seq_no.text = ""
        self.ids.chemspin.text = ""
        self.ids.target_weight.text = ""
        self.ids.userauthen.text = "All User"
        self.ids.status.text = "Pending"
        self.ids.dispense_date.text = ""
        self.ids.dispense_time.text = ""
        self.ids.tank_spinner.text = ""
        self.ids.chemspin.focus = False
        self.close_dropdown()
        self.display_selected_batch_data_by_name(batch_id)

    def confirm_delete_popup(self):
        if not self.selected_batch_data:
            toast("Error: No batch selected.", duration=0.6)
            return

        batch_id = self.selected_batch_data['batch_id']
        batch_name = self.ids.batch_name.text

        def callback_yes(instance):
            try:
                # Call the correct function to delete the batch
                batch.delete_Batchchemical(create_connection("ChemDB.db"), batch_id)

                print("Batch deleted successfully")

                # Schedule GUI updates in the main thread
                Clock.schedule_once(lambda dt: self.update_gui_elements(), 0)
            except Exception as e:
                print(f"Error deleting batch: {e}")

            self.confirmation_popup.dismiss()
            self.ids.chemspin.focus = False
            self.close_dropdown()

        def callback_no(instance):

            self.confirmation_popup.dismiss()

        message = (f'Confirm to delete Batch_ID {batch_id} in {batch_name}?\n\n'
                   f'Press y/n')

        self.confirmation_popup = ConfirmationPopup(message=message,
                                                    callback_yes=callback_yes,
                                                    callback_no=callback_no)
        self.confirmation_popup.open()

        def callback_data_yes():
            try:
                # Call the correct function to delete the batch
                batch.delete_Batchchemical(create_connection("ChemDB.db"), batch_id)

                print("Batch deleted successfully")

                # Schedule GUI updates in the main thread
                Clock.schedule_once(lambda dt: self.update_gui_elements(), 0)

            except Exception as e:
                print(f"Error deleting batch: {e}")

            self.confirmation_popup.dismiss()
            self.ids.chemspin.focus = False
            self.close_dropdown()

        def callback_no():
            self.confirmation_popup.dismiss()

        # Bind keyboard events
        keyboard.add_hotkey("y", callback_data_yes)
        keyboard.add_hotkey("n", callback_no)

    def show_error_pop(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()
        self.current_popup = error_popup

    def dismiss_popup(self):
        # Check if there is a current popup and dismiss it if there is
        if self.current_popup:
            self.current_popup.dismiss()
            self.current_popup = None


    def newpop(self):
        data = NewBatch()
        newbatchWindow = Popup(title='New Batch', content=data, size_hint=(None, None), size=(500, 400), padding=10,title_size=20, title_font ="Aileron-Bold.otf")
        newbatchWindow.open()

    def openpop(self):
        self.ids.seq_no.text = ""
        self.ids.chemspin.text = ""
        self.ids.target_weight.text = ""
        self.ids.userauthen.text = "All User"
        self.ids.status.text = "Pending"
        self.ids.tank_spinner.text = ""
        self.ids.dispense_date.text = ""
        self.ids.dispense_time.text = ""
        self.ids.chemspin.focus = False
        self.close_dropdown()
        opendata = OpenBatch()
        openbatchWindow = Popup(title='Open Batch', content=opendata, size_hint=(None, None), size=(500, 400),
                                padding=10,title_size=20, title_font ="Aileron-Bold.otf")
        openbatchWindow.open()

    def delete_button(self):
        keyboard.add_hotkey("delete", self.on_delete_pressed)
        keyboard.add_hotkey("ctrl+delete", self.batch_delete)

    def batch_delete(self):
        Clock.schedule_once(self.batch_delete_key)

    def batch_delete_key(self, dt):
        self.confirm_delete_batch()

    def on_delete_pressed(self):
        Clock.schedule_once(self.delete_key)

    def delete_key(self, dt):
        if 'batch_id' in self.selected_batch_data:
            batch_id = self.selected_batch_data['batch_id']
            if batch.check_batch_exists(batch_id):
                self.confirm_delete_popup()

    def start_keyboard_listener(self):
        # Start listening for keyboard events in a separate thread
        keyboard.add_hotkey("enter", self.on_enter_pressed)
        keyboard.add_hotkey("ctrl+s", self.on_saved_all)
        keyboard.add_hotkey("ctrl+n", self.on_new_pressed)
        keyboard.add_hotkey("ctrl+o", self.on_open_pressed)
        keyboard.add_hotkey("end", self.on_end)

    def on_end(self, event=None):
        Clock.schedule_once(self.go_to_end)

    def go_to_end(self, dt):
        self.dismiss_error_popup()
        self.dismiss_popup()

    def on_open_pressed(self, event=None):
        Clock.schedule_once(self.go_to_open)

    def go_to_open(self, dt):
        self.openpop()

    def on_new_pressed(self, event=None):
        Clock.schedule_once(self.go_to_new)

    def go_to_new(self, dt):
        self.newpop()

    def on_saved_all(self, event=None):
        Clock.schedule_once(self.enter_save_all)

    def enter_save_all(self, dt):
        self.save_changes()

    def on_enter_pressed(self, event=None):
        # Method to be called when Enter key is pressed
        Clock.schedule_once(self.enter_save_changes)

    def enter_save_changes(self, dt):
        if self.ids.seq_no.text != '' and self.ids.dispense_date == "":
            self.save_button()

class CustomTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):

        current_text = self.text

        if substring in '0123456789.':

            if '.' in current_text:

                integer_part, fractional_part = current_text.split('.')

                if substring == '.':
                    return

                if len(fractional_part) < 3:
                    super().insert_text(substring, from_undo=from_undo)
            else:
                super().insert_text(substring, from_undo=from_undo)
        else:
            return

    row = NumericProperty()
    col = NumericProperty()

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'tab':
            self.dispatch('on_triple_tap')
            return True
        if super(CustomTextInput, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        alt_pressed = 'alt' in modifiers
        if alt_pressed and keycode[1] == 'left':
            self.cursor_previous_letter()
            return True
        elif alt_pressed and keycode[1] == 'right':
            self.cursor_next_letter()
            return True

        if keycode[1] == 'down':
            self.navigate(0, -14)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 14)
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

        if isinstance(new_widget, CustomTextInput) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True


class ConfirmationPopup(Popup):
    def __init__(self, message, callback_yes, callback_no, **kwargs):
        super(ConfirmationPopup, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (300, 200)
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

class BatchApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home_hotkey_id = None

    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.icon = 'logindi.png'
        Window.maximize()
        Builder.load_file('batchpage.kv')
        app = MyApp()
        app.start_keyboard_listener()  # Start listening for keyboard events
        app.delete_button()
        sys.setrecursionlimit(10 ** 9)
        return app

    def delay_fn(self, fn_name):
        self.root.ids.del_button.disabled = True
        self.root.ids.add_button.disabled = True
        self.root.ids.new_button.disabled = True
        self.root.ids.open_button.disabled = True
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
        Builder.unload_file('batchpage.kv')
        print("Unloaded Batch")
        from main import MainApp
        BatchApp.stop(self)
        MainApp().run()

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



    def go_to_home(self,dt):
        self.switch_to_main()

    def get_user_names(self):
        # Fetch user names from the database
        user_names = user.fetch_user_names()
        user_names.insert(0, 'All User')


        return user_names

    def machin_name(self):
        machin_name=tank.get_machin_name()
        machin_names=[name for name in machin_name if name]
        print("Machin Names:",machin_name)
        return machin_name


    def get_chemical_names(self):
        # Fetch chemical names from the database
        chemical_names = chemical.fetch_chemical_names()

        # Remove empty strings from the list
        chemical_names = [name for name in chemical_names if name]

        # Log the chemical names for debugging
        print("Chemical names:", chemical_names)

        return chemical_names


    def __del__(self):
        pass


if __name__ == '__main__':
    BatchApp().run()

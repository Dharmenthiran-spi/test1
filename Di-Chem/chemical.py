import ctypes
import json
import sys
import time

import keyboard
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import NumericProperty, Clock, ObjectProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.icon_definitions import md_icons
from database import *
from main import ConnectionManager
from kivy.graphics import Color, Line
chemical=Chemical()

print('hellow')
class CustomTextInput(TextInput):
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
            self.navigate(0, -11)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 11)
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
        table_text_fields = self.parent.parent
        row = table_text_fields.children.index(self.parent)
        col = self.parent.children.index(self)

        if row < len(table_text_fields.children) - 1:
            next_row_columns = len(table_text_fields.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(table_text_fields.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(table_text_fields.children[row].children) - 1))

        new_widget = table_text_fields.children[new_row].children[new_col]
        print(col)
        if col <= 449 and col >= 11 and col_change == -11:
            print(col)
            table_text_fields.scroll_y -= 0.025
        elif col >= 11 and col <= 449 and col_change == 11:
            print(col)
            table_text_fields.scroll_y += 0.025
        elif col < 11:

            pass

        if isinstance(new_widget, TextInput) and not new_widget.disabled:
            new_widget.focus = True
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


    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super(MaxLengthTextInput, self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        alt_pressed = 'alt' in modifiers
        if alt_pressed and keycode[1] == 'left':
            self.cursor_previous_letter()
            return True
        elif alt_pressed and keycode[1] == 'right':
            self.cursor_next_letter()
            return True

        if keycode[1] == 'down':
            self.navigate(0, -11)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 11)
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
        table_text_fields = self.parent.parent
        row = table_text_fields.children.index(self.parent)
        col = self.parent.children.index(self)

        if row < len(table_text_fields.children) - 1:
            next_row_columns = len(table_text_fields.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(table_text_fields.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(table_text_fields.children[row].children) - 1))

        new_widget = table_text_fields.children[new_row].children[new_col]
        print(col)
        if col <= 449 and col >= 11 and col_change == -11:
            print(col)
            table_text_fields.scroll_y -= 0.025
        elif col >= 11 and col <= 449 and col_change == 11:
            print(col)
            table_text_fields.scroll_y += 0.025
        elif col < 11:

            pass

        if isinstance(new_widget, TextInput) and not new_widget.disabled:
            new_widget.focus = True
class MyApp(BoxLayout):
    def __init__(self, connection_manager=None,**kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.connection_manager = connection_manager
        self.selected_valve_data = {}
        self.text_inputs = []
        self.total_widgets = []
        self.json_filename = 'ChemicalData.json'
        self.current_popup = None
        self.start_keyboard_listener()
        self.check_max_stock()
        self.chemical()

    def check_max_stock(self):
        max_tank = chemical.fetch_max_stock_value()
        if all(value == ('',) or value == (0,) for value in max_tank):
            chemical.insert_the_max_stock()
        else:
            print("Values are not empty. Proceeding as normal.")

    def start_keyboard_listener(self):

        keyboard.add_hotkey("enter", self.on_enter_pressed)

    def on_enter_pressed(self, event=None):
        # Method to be called when Enter key is pressed
        Clock.schedule_once(self.enter_save_changes)

    def enter_save_changes(self, dt):
        self.save_changes()

    def chemical(self):
        print("Calling chemical method")
        self.total_widgets.clear()
        # Fetch data from the Chemical table in the database
        data = chemical.fetch_chemical_data()

        # Clear the existing content of the GridLayout
        chemical_grid = self.ids.chemical_grid
        chemical_grid.background_color = [1, 1, 1, 1]
        chemical_grid.clear_widgets()

        # Define header sizes
        header_sizes = {
            'Valve No': 160,
            'Chemical Name': 268,
            'Stock': 180,
            'Min Stock': 180,
            'Max Stock':180,
            'Input Path': 250,
            'Last Updated': 300,
            'Station 1': 100,
            'Station 2': 100,
            'Station 3': 100,
            'Station 4': 100
        }

        # Add the headers to the GridLayout with individual sizes
        for header in header_sizes:
            chemical_grid.add_widget(
                NTextInput(text=header, halign='center', size_hint=(None, None),
                           size=(header_sizes[header], 35), readonly=True, background_color=(1, 1, 1, 1),font_size = 17,font_name="Aileron-Bold.otf"))

        for row in data:
            valve_number = str(row[0])
            button = BlueOutlinedButton(text=valve_number, size_hint=(None, None), size=(160, 30))
            button.bind(
                on_press=lambda instance, valve=valve_number, selected_row=row: self.on_valve_button_press(valve,
                                                                                                           selected_row))
            chemical_grid.add_widget(button)
            self.total_widgets.append(button)

            for value in row[1:2]:
                text_input = MaxLengthTextInput(text=str(value), halign='center', size_hint=(None, None), size=(268, 30),
                                       readonly=False, focus=False, background_color=(1, 1, 1, 1),multiline=False,maxlength=16,input_filter=lambda text, from_undo:text if text.isalnum() or text == " " or text == "_" else '')
                text_input.bind(on_touch_down=lambda instance, touch, text_value=str(value), selected_row=row,
                                                     column_index=row.index(value): self.on_text_input_press(text_value,
                                                                                                             selected_row,
                                                                                                             column_index))
                chemical_grid.add_widget(text_input)
                self.total_widgets.append(text_input)
            for value in row[2:4]:
                stock_input = CustomTextInput(text=str(value), halign='center', size_hint=(None, None), size=(180, 30),
                                        readonly=False, focus=False, background_color=(1, 1, 1, 1), input_filter='float',multiline=False)
                stock_input.bind(on_touch_down=lambda instance, touch, text_value=str(value), selected_row=row,
                                                      column_index=row.index(value): self.on_text_input_press(
                    text_value,
                    selected_row,
                    column_index))

                chemical_grid.add_widget(stock_input)
                self.total_widgets.append(stock_input)
            for value in row[4:5]:
                max_input = CustomTextInput(text=str(value), halign='center', size_hint=(None, None), size=(180, 30),
                                        readonly=False, focus=False, background_color=(1, 1, 1, 1), input_filter='float',multiline=False)
                max_input.bind(on_touch_down=lambda instance, touch, text_value=str(value), selected_row=row,
                                                      column_index=row.index(value): self.on_text_input_press(
                    text_value,
                    selected_row,
                    column_index))

                chemical_grid.add_widget(max_input)
                self.total_widgets.append(max_input)

            for value in row[6:7]:
                layout_input = NTextInput(text=str(value), halign='center', size_hint=(None, None), size=(250, 30),
                                         readonly=False, focus=False, background_color=(1, 1, 1, 1),multiline=False)
                layout_input.bind(on_touch_down=lambda instance, touch, text_value=str(value), selected_row=row,
                                                       column_index=row.index(value): self.on_text_input_press(
                    text_value,
                    selected_row,
                    column_index))

                chemical_grid.add_widget(layout_input)
                self.total_widgets.append(layout_input)

            for value in row[5:6]:
                Date_input = NTextInput(text=str(value), halign='center', size_hint=(None, None), size=(300, 30),
                                       readonly=True, focus=False, background_color=(1, 1, 1, 1),multiline=False)
                Date_input.bind(on_touch_down=lambda instance, touch, text_value=str(value), selected_row=row,
                                                     column_index=row.index(value): self.on_text_input_press(
                    text_value,
                    selected_row,
                    column_index))

                chemical_grid.add_widget(Date_input)
                self.total_widgets.append(Date_input)

            for value in row[7:]:
                station_input = NTextInput(text=str(value), halign='center',input_filter='int', size_hint=(None, None), size=(100, 30),
                                       readonly=False, focus=False, background_color=(1, 1, 1, 1),multiline=False)
                station_input.bind(on_touch_down=lambda instance, touch, text_value=str(value), selected_row=row,
                                                     column_index=row.index(value): self.on_text_input_press(
                    text_value,
                    selected_row,
                    column_index))

                chemical_grid.add_widget(station_input)
                self.total_widgets.append(station_input)

        print("Total number of widgets:", len(self.total_widgets))
        chemical_grid.children[len(chemical_grid.children) - 2].focus = True


    def on_text_input_press(self, text_value, selected_row, column_index):

        self.ids.valve_no.text = str(selected_row[0])
        self.ids.chemical_name.text = str(selected_row[1])
        self.ids.stockchem.text = str(selected_row[2])
        self.ids.min_stock.text = str(selected_row[3])
        self.ids.input_path.text = str(selected_row[5])

        self.selected_valve_data = {
            'valve_number': str(selected_row[0]),
            'chemical_name': str(selected_row[1]),
            'stockchem': str(selected_row[2]),
            'min_stock': str(selected_row[3]),
            'input_path': str(selected_row[5]),
        }


    def on_valve_button_press(self, valve_number, selected_row):
        print(f"Button with Valve No {valve_number} is pressed")
        self.ids.valve_no.text = str(selected_row[0])
        self.ids.chemical_name.text = str(selected_row[1])
        self.ids.stockchem.text = str(selected_row[2])
        self.ids.min_stock.text = str(selected_row[3])
        self.ids.input_path.text = str(selected_row[5])

        # Update the selected_valve_data dictionary with the current values
        self.selected_valve_data = {
            'valve_number': str(selected_row[0]),
            'chemical_name': str(selected_row[1]),
            'stockchem': str(selected_row[2]),
            'min_stock': str(selected_row[3]),
            'input_path': str(selected_row[5]),
        }

    def validate_tank_capacity(self, valve_number, column_name, differences):
        try:
            # Load form_data.json file
            with open('form_data.json', 'r') as file:
                form_data = json.load(file)

            # Get max tank capacity from form_data
            max_tank_capacity_str = form_data.get('max_tank_capacity', '0')  # Default to '0' if key is not present

            try:
                max_tank_capacity = float(max_tank_capacity_str)

                # Validate only for 'Stock' and 'MinStock' columns
                if column_name in ('Stock', 'MinStock'):
                    updated_stock = float(differences['new_value'])  # Convert the updated value to float

                    # Validate values
                    if updated_stock > max_tank_capacity or updated_stock < 0:
                        toast(f"Error for ValveNo {valve_number}: Correct the {column_name}.", duration=0.6)
                        return False

            except ValueError:
                # Handle the case where the max_tank_capacity_str or updated_value is not a valid float
                toast(f"Error for ValveNo {valve_number}: {column_name} must be a valid numeric value.", duration=0.6)
                return False

            return True

        except (FileNotFoundError, json.JSONDecodeError) as e:
            toast(f"Error for ValveNo {valve_number}: Unable to read form_data.json - {str(e)}", duration=0.6)
            return False

    def save_changes(self):
        database_file = "ChemDB.db"
        chemical_data_file = 'ChemicalData.json'

        try:
            # Check if there are changes to save
            if not self.total_widgets:
                toast("Error: No data detected to update.", duration=0.6)
                return

            # Create or get connection to the database
            with sqlite3.connect(database_file) as connection:
                try:
                    # Fetch and store chemical data
                    chemical.fetch_and_store_chemical_data(connection, chemical_data_file)

                    # Load existing data from JSON file
                    with open(self.json_filename, 'r') as json_file:
                        data = json.load(json_file)

                    # Update data based on changes
                    for i in range(0, len(self.total_widgets), 11):
                        valve_no = int(self.total_widgets[i].text)  # Ensure this is a valid integer
                        for d in data:
                            if d.get('ValveNo') == valve_no:
                                name = self.total_widgets[i + 1].text.strip()
                                if name:  # Check if 'Name' is not empty
                                    try:
                                        # Extract and validate station values
                                        station_values = [
                                            int(self.total_widgets[i + j].text.strip() or 0)
                                            # Use 0 if the value is empty
                                            for j in range(7, 11)
                                        ]
                                        for station_value in station_values:
                                            if not (0 <= station_value <= 254):
                                                toast(f"Station value must be between 0 and 254 for valve {valve_no}.",
                                                      duration=0.6)
                                                return
                                    except ValueError as e:
                                        toast(f"Invalid station value detected at index {i}. Error message: {e}",
                                              duration=0.6)
                                        return

                                # Update data if all station values are valid
                                d.update({
                                    'Name': name,
                                    'Stock': float(self.total_widgets[i + 2].text.strip() or 0),
                                    'MinStock': float(self.total_widgets[i + 3].text.strip() or 0),
                                    'MaxStock': int(self.total_widgets[i + 4].text.strip() or 0),
                                    'LastUpdated': self.total_widgets[i + 6].text,
                                    'InputLayoutPath': self.total_widgets[i + 5].text.strip(),
                                    'Station1': station_values[0] if name else d.get('Station1', 0),
                                    'Station2': station_values[1] if name else d.get('Station2', 0),
                                    'Station3': station_values[2] if name else d.get('Station3', 0),
                                    'Station4': station_values[3] if name else d.get('Station4', 0)
                                })
                                break

                    # Validate before saving changes to the JSON file
                    validation_result = self.validate_and_save_changes(data)
                    if validation_result:
                        with open(self.json_filename, 'w') as json_file:
                            json.dump(data, json_file, indent=2)

                        # Update SQLite database
                        chemical.update_from_chemical(connection, self.json_filename)
                        self.chemical()

                except sqlite3.Error as e:
                    print(f"SQLite error: {e}")
                except Exception as e:
                    print(f"error: {e}")

                    return False
        except Exception as e:
            print(f"Failed to connect to database: {e}")

    def validate_and_save_changes(self, data):
        try:
            # Additional validation before saving changes to the JSON file
            for d in data:
                valve_no = d.get('ValveNo')
                stock_value = float(d.get('Stock', 0))
                min_stock_value = float(d.get('MinStock', 0))
                max_stock_value=int(d.get('MaxStock',''))
                name_value = d.get('Name', '')
                input_layout=d.get('InputLayoutPath','')
                try:
                    max_tank_capacity = float(max_stock_value)

                    # Validate Stock and MinStock against max_tank_capacity
                    if stock_value > max_tank_capacity or min_stock_value > max_tank_capacity:
                        toast(f"Error for ValveNo {valve_no}: Correct your Stock and MinStock.", duration=0.6)
                        return False

                    # Validate 'Name' column
                    if name_value or min_stock_value or stock_value or input_layout:
                        # Check if Stock, MinStock, and InputLayoutPath are empty
                        if not d.get('Name'):
                            toast(f"Error for ValveNo {valve_no}: Enter a value for 'Name'.", duration=0.6)
                            return False
                        if not d.get('Stock'):
                            toast(f"Error for ValveNo {valve_no}: Enter a value for 'Stock'.", duration=0.6)
                            return False

                        if not d.get('MinStock'):
                            toast(f"Error for ValveNo {valve_no}: Enter a value for 'MinStock'.", duration=0.6)
                            return False

                        if not d.get('InputLayoutPath'):
                            toast(f"Error for ValveNo {valve_no}: Enter a value for 'InputLayoutPath'.", duration=0.6)
                            return False

                except ValueError:
                    # Handle the case where max_tank_capacity_str is not a valid float
                    toast("Error: max_tank_capacity must be a valid numeric value.", duration=0.6)
                    return False
        except Exception as ex:
            print(f'error in validate:{ex}')

        # Save the changes back to the JSON file
        with open(self.json_filename, 'w') as json_file:
            json.dump(data, json_file, indent=2)

        print("Changes saved successfully.")
        return True

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(500, 100))
        error_popup.open()
class BlueOutlinedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_outline, size=self.update_outline)
        with self.canvas.before:
            Color(77/255, 199/255, 226/255, 1)  # Blue color

            self.outline = Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

    def update_outline(self, *args):
        self.outline.rectangle = (self.x, self.y, self.width, self.height)
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
            self.navigate(0, -11)
            return True
        elif keycode[1] == 'up':
            self.navigate(0, 11)
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
        table_text_fields = self.parent.parent
        row = table_text_fields.children.index(self.parent)
        col = self.parent.children.index(self)

        if row < len(table_text_fields.children) - 1:
            next_row_columns = len(table_text_fields.children[row + 1].children)
            new_row = max(1, min(row + row_change, len(table_text_fields.children) - 1))
            new_col = max(0, min(col + col_change, next_row_columns - 1))
        else:
            new_row = row
            new_col = max(0, min(col + col_change, len(table_text_fields.children[row].children) - 1))

        new_widget = table_text_fields.children[new_row].children[new_col]
        print(col)
        if col <= 449 and col >= 11 and col_change == -11:
            print(col)
            table_text_fields.scroll_y -= 0.025
        elif col >= 11 and col <= 449 and col_change == 11:
            print(col)
            table_text_fields.scroll_y += 0.025
        elif col < 11:

            pass

        if isinstance(new_widget, TextInput) and not new_widget.disabled:
            new_widget.focus = True


class ChemicalApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home_hotkey_id = None

    def build(self):
        self.icon = 'logindi.png'
        Window.maximize()
        Builder.load_file('chempage.kv')
        sys.setrecursionlimit(10 ** 9)
        app = MyApp()

        return app

    def on_start(self):
        # Register the hotkey
        # self.home_hotkey_id = keyboard.add_hotkey("home", self.on_home_pressed)
        pass

    def change_button_color(self, button):
        button.md_bg_color = (77/255, 199/255, 226/255, 1)
        Clock.schedule_once(lambda dt: self.reset_button_color(button), .1)

    def reset_button_color(self, button):

        button.md_bg_color = (0.3, 0.3, 0.3, 1)

    def on_home_pressed(self,event=None):
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

    def chem_delay_fn(self, fn_name):
        self.root.ids.save_button.disabled = True
        self.root.ids.home.disabled = True
        # self.root.ids.chemical.clear_widgets()
        Clock.schedule_once(lambda dt: getattr(self, fn_name)(), 0.6)

    def switch_to_main(self):
        Builder.unload_file('chempage.kv')
        print("Unloaded Chemical")
        from main import MainApp
        ChemicalApp.stop(self)
        main_app = MainApp()  # Pass connection_manager to MainApp
        main_app.run()

    def save_changes(self):
        # Call the save_changes method in MyApp
        self.root.save_changes()

    def go_to_home(self,dt):
        self.switch_to_main()

    def __del__(self):
        pass



if __name__ == '__main__':
    ChemicalApp().run()

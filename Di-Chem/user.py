import ctypes
import sys
import time

import keyboard
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty, ColorProperty, ObjectProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.toast import toast
from kivy.graphics import Color, Line
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.icon_definitions import md_icons
from database import *

from kivy.app import App

user=User()
class NewUser(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def save_user_data(self, instance):
        # Get the values from the TextInput fields
        name = self.ids.name.text
        user_name = self.ids.user_name.text
        password = self.ids.password.text
        privilege = self.ids.pre_vilage.text

        if not name or not user_name or not password or not privilege:
            toast("Error: Check All fields.", duration=0.6)
            return

        conn = create_connection("ChemDB.db")  # Replace "YourDatabase.db" with your actual database name

        # Check if user data already exists
        if user.data_exists(conn, user_name,password):
            toast("Error: User with the same username already exists.", duration=0.6)
            close_connection(conn)
            return

        user.insert_user_data(name, user_name, password, privilege)

        app_instance = App.get_running_app()
        if app_instance:
            app_instance.root.setuser()

        parent_popup = self.parent.parent.parent  # Adjust the number of ".parent" based on your hierarchy
        parent_popup.dismiss()



    def spinner_clicked(self, spinner_instance, value):
        print(f"Spinner clicked with text: {value}")

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()



class FocusTextInput(TextInput, FocusBehavior):
    row = NumericProperty()
    col = NumericProperty()
    def __init__(self, **kwargs):
        self.maxlength = kwargs.pop('maxlength', None)
        super(FocusTextInput, self).__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        if self.maxlength is not None:
            if len(self.text) + len(substring) > self.maxlength:
                substring = substring[:self.maxlength - len(self.text)]
        return super(FocusTextInput, self).insert_text(substring, from_undo=from_undo)




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
                self.navigate(0, -5)
                self.background_color = self.focus_color if self.focused else (3, 3, 3, 1)
                return True
            elif keycode[1] == 'up':
                self.navigate(0, 5)
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

        if isinstance(new_widget, FocusSpinner) and new_widget.disabled:
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

        if isinstance(new_widget, FocusButton) and new_widget.disabled:
            new_col += col_change
            if new_col < 0:
                new_col = max(0, len(chemical_grid.children[new_row].children) - 1)
            elif new_col >= len(chemical_grid.children[new_row].children):
                new_col = 0

            new_widget = chemical_grid.children[new_row].children[new_col]

        new_widget.focus = True



class MyApp(BoxLayout):


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_text_input = None
        self.selected_user_data = {}  # Added as a class attribute
        self.total_widgets = []
        self.setuser()
        self.connection = create_connection("ChemDB.db")
        self.dropdown = DropDown()
        self.current_popup = None

    def setuser(self):
        print("Calling User method")  # Add this line to check if the method is called
        self.total_widgets.clear()
        # Fetch data from the Chemical table in the database
        data = user.fetch_UserTable_data()

        # Clear the existing content of the GridLayout
        setting_user = self.ids.setting_user


        setting_user.clear_widgets()
        self.total_widgets.clear()

        # Add the headers to the GridLayout
        headers = ['ID', 'Name', 'UserName', 'Password', 'Privilage']
        for header in headers:
            setting_user.add_widget(
                FocusTextInput(text=header, halign='center', size_hint=(None, None), size=(390, 35), readonly=True,scroll_y = 0,
                               background_color=(3, 3, 3, 1),font_size=17,font_name="Aileron-Bold.otf"))

        # Add the data to the GridLayout
        for row in data:
            user_id = str(row[0])
            button = FocusButton(text=user_id, size_hint=(None, None), size=(390, 30), color=(0, 0, 0, 1))
            button.bind(
                on_press=lambda instance, userid=user_id, selected_row=row: self.on_user_button_press(instance, userid,
                                                                                                      selected_row))
            setting_user.add_widget(button)
            self.total_widgets.append(button)
            for value in row[1:4]:
                text_input = FocusTextInput(text=str(value), halign='center', size_hint=(None, None),
                                            size=(390, 30), multiline=False,
                                            readonly=False,maxlength=15, background_color=(3, 3, 3, 1),input_filter=lambda text, from_undo:text if text.isalnum() or text == " " or text == "_" else '')
                text_input.bind(on_triple_tap=self.dropdown_nav_active)
                setting_user.add_widget(text_input)
                self.total_widgets.append(text_input)

            for values in row[4:]:
                # Assuming values is a dictionary
                spinner_values = ['Admin', 'User']  # Adjust as needed
                spinner = FocusSpinner(text=str(values), values=spinner_values, halign='center',
                                       size_hint=(None, None),
                                       size=(390, 30), color=(0, 0, 0, 1), background_color=(3, 3, 3, 1))
                spinner.bind(on_text=self.spinner_clicked)

                setting_user.add_widget(spinner)
                self.total_widgets.append(spinner)
        print("Total number of widgets:", len(self.total_widgets))
        setting_user.children[len(setting_user.children) - 1].focus = True
        # Set focus to the first widget after adding new widgets




    def dropdown_nav_active(self, instance):
        if len(self.dropdown.children[0].children) <= 0:
            # toast("No Matches", duration=0.6)
            pass
        else:
            self.dropdown.children[0].children[-1].focus = True

    def on_text_input_press(self, text_value, selected_row, column_index):
        self.ids.name.text = str(selected_row[1])
        self.ids.user_name.text = str(selected_row[2])
        self.ids.password.text = str(selected_row[3])
        self.ids.pre_vilage.text = str(selected_row[4])

        self.selected_user_data = {
            'user_id': str(selected_row[0]),
            'name': str(selected_row[1]),
            'user_name': str(selected_row[2]),
            'password': str(selected_row[3]),
            'pre_vilage': str(selected_row[4])
        }
    def on_user_button_press(self, instance, userid, selected_row):
        print(f"Button with ID {userid} is pressed")


        self.ids.name.text = str(selected_row[1])
        self.ids.user_name.text = str(selected_row[2])
        self.ids.password.text = str(selected_row[3])
        self.ids.pre_vilage.text = str(selected_row[4])

        self.selected_user_data = {
            'user_id': str(selected_row[0]),
            'name': str(selected_row[1]),
            'user_name': str(selected_row[2]),
            'password': str(selected_row[3]),
            'pre_vilage': str(selected_row[4])
            }

    def save_changes(self):
        if not self.total_widgets:
            toast("Error: No data detected to update.", duration=0.6)
            return None
        self.ids.name.text = ''
        self.ids.user_name.text = ''
        self.ids.password.text = ''
        self.ids.pre_vilage.text = ''
        connection = sqlite3.connect("ChemDB.db")
        data = user.fetch_UserTable_data()
        expected_length = len(data) * len(data[0])

        if len(self.total_widgets) != expected_length:
            print(
                f"Error: Length of text_inputs ({len(self.total_widgets)}) doesn't match the expected length ({expected_length})")
            return

        differences = []

        for row_index, row in enumerate(data):
            for col_index, col in enumerate(row):
                text_input_index = (row_index * len(row)) + col_index

                if text_input_index < len(self.total_widgets):
                    print(f"Processing index {text_input_index}...")
                    updated_value = self.total_widgets[text_input_index].text
                    user_id = row[0]
                    column_name = ""

                    if col_index == 1:
                        column_name = "Name"
                    elif col_index == 2:
                        column_name = "UserName"
                    elif col_index == 3:
                        column_name = "Password"
                    elif col_index == 4:
                        column_name = "Privilage"

                    original_data =user.fetch_user_data_for_id(connection, user_id)

                    if original_data[col_index] != updated_value:
                        differences.append({
                            "user_id": user_id,
                            "column_name": column_name,
                            "old_value": original_data[col_index],
                            "new_value": updated_value
                        })
                        updated_row = user.update_row_user(user_id, column_name, updated_value)

                        if updated_row is not None:
                            # Update the existing widget with the new value
                            self.total_widgets[text_input_index].text = str(updated_row[col_index])  # Convert to string

                            # Print the changes
                            print(f"Updated value in column {column_name} for id {user_id}: "
                                  f"{original_data[col_index]} -> {updated_value}")

                            # You can now use the 'differences' list for further processing if needed
                    else:
                        print(f"Error: Index {text_input_index} is out of range for text_inputs")

        # Print the differences at the end
        print("Differences:", differences)
        self.setuser()

    def show_delete_popup(self, instance, userid):
        if self.selected_user_data:
            # Create and open the DeletePopup
            delete_popup = DeletePopup(self.delete_data, userid=userid)
            delete_popup.open()
        else:
            toast("Error: No user selected.", duration=0.6)
            return

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()
        self.current_popup = error_popup

    def close_popup(self):
        # Check if there is a current popup and dismiss it if there is
        if self.current_popup:
            self.current_popup.dismiss()
            self.current_popup = None

    @mainthread
    def delete_data(self, userid):
        # Delete from the database
        user.delete_user(self.connection, userid)

        # Refresh the page by loading data again
        self.setuser()

        print(f"Deleted data for user ID: {userid}")
        self.ids.name.text = ''
        self.ids.user_name.text = ''
        self.ids.password.text = ''
        self.ids.pre_vilage.text = ''

    def spinner_clicked(self, spinner_instance, value):
        print(f"Spinner clicked with text: {value}")


    def newpop(self):
        data = NewUser()
        popupWindow=Popup(title="User",content=data,size_hint=(None,None),size=(500,400),padding=10,title_size=20, title_font = "Aileron-Bold.otf")
        popupWindow.open()

    def start_keyboard_listener(self):
        # Start listening for keyboard events in a separate thread
        keyboard.add_hotkey("ctrl+s", self.on_enter_pressed)
        # keyboard.add_hotkey("ctrl+g", self.on_general)
        # keyboard.add_hotkey("ctrl+t", self.on_tank)
        keyboard.add_hotkey("ctrl+n", self.on_new_pressed)
        keyboard.add_hotkey("end", self.on_end)

    def on_end(self,event=None):
        Clock.schedule_once(self.go_to_end)

    def go_to_end(self,dt):
        self.close_popup()

    def on_new_pressed(self, event=None):
        Clock.schedule_once(self.go_to_new)

    def go_to_new(self, dt):
        self.newpop()
    def on_general(self, event=None):
        Clock.schedule_once(self.go_to_general)

    def go_to_general(self, dt):
        app = App.get_running_app()
        app.switch_to_general()

    def on_tank(self, event=None):
        Clock.schedule_once(self.go_to_tank)

    def go_to_tank(self, dt):
        app = App.get_running_app()
        app.switch_to_tanks()
    def on_enter_pressed(self, event=None):
        # Method to be called when Enter key is pressed
        Clock.schedule_once(self.enter_save_changes)

    def enter_save_changes(self,dt):

        self.save_changes()
    def delete_button(self):
        keyboard.add_hotkey("delete", self.on_delete_pressed)

    def on_delete_pressed(self):
        Clock.schedule_once(self.delete_key)

    def delete_key(self, dt):
        if 'user_id' in self.selected_user_data:
            user_id = self.selected_user_data.get('user_id', None)
            if user.check_user_exists(user_id):
                self.show_delete_popup(self.selected_user_data, user_id)
            else:
                toast("Error: No user selected.", duration=0.6)
                return
        else:
            toast("Error: No user selected.", duration=0.6)
            return
class DeletePopup(Popup):
    def __init__(self, delete_callback, userid, **kwargs):
        super(DeletePopup, self).__init__(**kwargs)
        self.title = "Confirmation"
        self.size_hint = (None, None)
        self.size = (250, 250)
        self.delete_callback = delete_callback
        self.userid = userid

        # Create a layout for the popup
        delete_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Add a confirmation label
        delete_layout.add_widget(Label(text=f'Confirm to delete UserId {userid} ?\n\n'
                                            f'press y/n'))

        # Add "Yes" and "No" buttons
        yes_button = Button(text="Yes", size_hint=(None, None), size=(50, 40), on_press=self.perform_delete)
        no_button = Button(text="No", size_hint=(None, None), size=(50, 40), on_press=self.dismiss)

        delete_layout.add_widget(yes_button)
        delete_layout.add_widget(no_button)

        # Set the layout as the content of the popup
        self.content = delete_layout
        keyboard.add_hotkey("y", self.delete_user)
        keyboard.add_hotkey("n", self.dismiss)

    def delete_user(self):
        print(f"Performing delete for user ID: {self.userid}")
        self.delete_callback(self.userid)
        self.dismiss()
    def perform_delete(self, instance):
        print(f"Performing delete for user ID: {self.userid}")
        self.delete_callback(self.userid)
        self.dismiss()



class UserApp(MDApp):
    selected_user_data = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home_hotkey_id = None

    def build(self):
        self.icon = 'logindi.png'
        Window.maximize()
        Builder.load_file('userpage.kv')
        app = MyApp()
        app.start_keyboard_listener()
        sys.setrecursionlimit(10 ** 9)
        app.delete_button()
        return app

    def newpop(self):
        data = NewUser()
        popupWindow=Popup(title="User",content=data,size_hint=(None,None),size=(500,400),padding=10)
        popupWindow.open()

    def delay_fn(self, fn_name):
        self.root.ids.general_button.disabled = True
        self.root.ids.user_button.disabled = True
        self.root.ids.tanks_button.disabled = True
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
        Builder.unload_file('userpage.kv')
        print("Unloaded user")
        from main import MainApp
        UserApp.stop(self)
        MainApp().run()

    def switch_to_general(self):
        Builder.unload_file('userpage.kv')
        print("Unloaded setting")
        from settings import generalApp
        UserApp.stop(self)
        generalApp().run()

    def switch_to_user(self):
        Builder.unload_file('userpage.kv')
        print("Unloaded setting")
        # from user import UserApp
        UserApp.stop(self)
        UserApp().run()


    def switch_to_tanks(self):
        Builder.unload_file('userpage.kv')
        print("Unloaded setting")
        from tanks import TanksApp
        UserApp.stop(self)
        TanksApp().run()

    def save_changes(self):
        # Call the save_changes method in MyApp
        self.root.save_changes()
    def on_home_pressed(self,event=None):
        Clock.schedule_once(self.go_to_home)
    def go_to_home(self,dt):
        self.switch_to_main()

    def on_start(self):
        # Register the hotkey
        # self.home_hotkey_id = keyboard.add_hotkey("home", self.on_home_pressed)
        pass


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

    def __del__(self):
        pass
if __name__ == '__main__':
    UserApp().run()
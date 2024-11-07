import ctypes
import sys
import time

import keyboard
import serial
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import BooleanProperty, StringProperty, Clock
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.icon_definitions import md_icons

import serial.tools.list_ports
import json
from database import *

chemical=Chemical()

class WashTextInput(TextInput, FocusBehavior):
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
class MyApp(BoxLayout):
    connected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.connection = create_connection("ChemDB.db")
        self.load_data_from_json()
        self.update_available_ports()
        self.current_popup = None

    def update_available_ports(self):
        self.ids.com_port.values = [

        ]

        try:
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            self.ids.com_port.values = available_ports

        except Exception as e:
            print(f"Error getting available ports: {e}")
        self.ids.machin_com_port.values = [

        ]
        try:
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            self.ids.machin_com_port.values = available_ports

        except Exception as e:
            print(f"Error getting available ports: {e}")



    def load_data_from_json(self):
        try:
            with open('form_data.json', 'r') as json_file:
                connection_info = json.load(json_file)
                com_port_value = connection_info.get('com_port', '')  # Correct key name
                baud_rate_value = connection_info.get('baud_rate', '')  # Correct key name
                no_of_chemical_value = connection_info.get('no_of_chemical', '')  # Correct key name
                max_tank_capacity_value = connection_info.get('max_tank_capacity', '')  # Correct key name
                no_of_station = connection_info.get('no_of_station', '')
                type_of_machin = connection_info.get('type_of_machin','')
                machin_slaveid = connection_info.get('machin_slaveid','')
                machine_com_port=connection_info.get('machine_comport','')
                machine_baud_rate=connection_info.get('machin_baud_rate','')
                default_water_wash1=connection_info.get('default_water1','')
                default_water_wash2=connection_info.get('default_water2','')
                self.ids.com_port.text = com_port_value
                self.ids.baud_rate.text = baud_rate_value
                self.ids.no_of_chemical.text = no_of_chemical_value
                self.ids.max_tank_capacity.text = max_tank_capacity_value
                self.ids.no_of_station.text=no_of_station
                self.ids.type_of_machin.text=type_of_machin
                self.ids.machin_slaveid.text=machin_slaveid
                self.ids.machin_com_port.text=machine_com_port
                self.ids.machin_baud_rate.text=machine_baud_rate
                self.ids.default_water1.text=default_water_wash1
                self.ids.default_water2.text=default_water_wash2

        except FileNotFoundError:
            print("No form_data.json file found.")

    def save_data_to_json(self):
        # Read the input values from the form
        try:
            com_port_value = self.ids.com_port.text
            baud_rate_value = self.ids.baud_rate.text
            no_of_chemical_value = self.ids.no_of_chemical.text
            max_tank_capacity_value = self.ids.max_tank_capacity.text
            no_of_station = self.ids.no_of_station.text
            type_of_machin = self.ids.type_of_machin.text
            machin_slaveid = self.ids.machin_slaveid.text
            machine_com_port=self.ids.machin_com_port.text
            machin_baud_rate = self.ids.machin_baud_rate.text
            default_after_wash1=self.ids.default_water1.text
            default_after_wash2=self.ids.default_water2.text

            # Validate the number of chemicals
            if not self.validate_no_of_chemical():
                return

            # Validate the number of stations
            if no_of_station !='':

                if not (no_of_station.isdigit() and 1 <= int(no_of_station) <= 4):
                    toast("Error: Number of stations should be between 1 and 4.", duration=0.6)
                    return

            # Validate the machine slave ID
            if machin_slaveid !="":

                if not (machin_slaveid.isdigit() and 1 <= int(machin_slaveid) <= 254):
                    toast("Error: Machine slave ID should be between 1 and 254.", duration=0.6)
                    return

            # Create a dictionary with the form data
            data = {
                'com_port': com_port_value,
                'baud_rate': baud_rate_value,
                'no_of_chemical': no_of_chemical_value,
                'max_tank_capacity': max_tank_capacity_value,
                'no_of_station': no_of_station,
                'type_of_machin': type_of_machin,
                'machin_slaveid': machin_slaveid,
                'machine_comport': machine_com_port,
                'machin_baud_rate': machin_baud_rate,
                'default_water1':default_after_wash1,
                'default_water2':default_after_wash2
            }

            # Save the data to the JSON file
            with open('form_data.json', 'w') as json_file:
                json.dump(data, json_file)
        except Exception as e:
            print("exception error:",e)


    def validate_no_of_chemical(self):
        try:
            if self.ids.no_of_chemical.text != '':
                total_valve_count = chemical.get_total_valve_count(self.connection)
                entered_value = int(self.ids.no_of_chemical.text)

                if entered_value > total_valve_count:
                    # Show the current value from the JSON file in the text field
                    self.ids.no_of_chemical.text = str(self.load_no_of_chemical_from_json())
                    toast(f"Error:chemicals cannot exceed the total number of valves ({total_valve_count}).", duration=0.6)
                    return False
        except ValueError:
            toast("Error: Please enter a valid numeric value for the number of chemicals.", duration=0.6)
            self.ids.no_of_chemical.text = ""
            return False

        return True

    def load_no_of_chemical_from_json(self):
        try:
            with open('form_data.json', 'r') as json_file:
                connection_info = json.load(json_file)
                return connection_info.get('no_of_chemical', '')
        except FileNotFoundError:
            print("No form_data.json file found.")
            return ""


    def spinner_clicked(self, text):
        print(f"Spinner clicked with value: {text}")

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(450, 100))
        error_popup.open()
        self.current_popup = error_popup

    def dismiss_error_popup(self):
        # Check if there is a current popup and dismiss it if there is
        if self.current_popup:
            self.current_popup.dismiss()
            self.current_popup = None

    def start_keyboard_listener(self):
        # Start listening for keyboard events in a separate thread
        # keyboard.add_hotkey("ctrl+u", self.on_user)
        # keyboard.add_hotkey("ctrl+t", self.on_tank)
        # keyboard.add_hotkey("end", self.on_end)
        pass
    def on_end(self,event=None):
        Clock.schedule_once(self.go_to_end)

    def go_to_end(self,dt):
        self.dismiss_error_popup()
    def on_user(self,event=None):
         Clock.schedule_once(self.go_to_user)
    def go_to_user(self,dt):
        app = App.get_running_app()
        app.switch_to_user()
    def on_tank(self,event=None):
        Clock.schedule_once(self.go_to_tank)
    def go_to_tank(self,dt):
        app = App.get_running_app()
        app.switch_to_tanks()



class generalApp(MDApp):
    my_app_instance = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home_hotkey_id = None

    def build(self):
        self.icon = 'logindi.png'
        Window.maximize()
        Builder.load_file('generalpage.kv')
        my_app_instance = MyApp()
        my_app_instance.start_keyboard_listener()
        sys.setrecursionlimit(10 ** 9)
        return my_app_instance

    def delay_fn(self, fn_name):
        self.root.ids.general_button.disabled = True
        self.root.ids.user_button.disabled = True
        self.root.ids.tanks_button.disabled = True
        self.root.ids.save_button.disabled = True
        self.root.ids.home.disabled = True
        Clock.schedule_once(lambda dt: getattr(self, fn_name)(), 0.6)

    def change_button_color(self, button):
        button.md_bg_color = (77/255, 199/255, 226/255, 1)
        Clock.schedule_once(lambda dt: self.reset_button_color(button), .1)

    def reset_button_color(self, button):

        button.md_bg_color = (0.3, 0.3, 0.3, 1)

    def switch_to_main(self):
        Builder.unload_file('generalpage.kv')
        print("Unloaded general")
        from main import MainApp
        generalApp.stop(self)
        MainApp().run()

    def switch_to_general(self):
        Builder.unload_file('generalpage.kv')
        print("Unloaded setting")
        generalApp.stop(self)
        generalApp().run()

    def switch_to_user(self):
        Builder.unload_file('generalpage.kv')
        print("Unloaded setting")
        from user import UserApp
        generalApp.stop(self)
        UserApp().run()

    def switch_to_tanks(self):
        Builder.unload_file('generalpage.kv')
        print("Unloaded setting")
        from tanks import TanksApp
        generalApp.stop(self)
        TanksApp().run()

    def go_to_home(self, dt):
        self.switch_to_main()

    def on_start(self):
        # Register the hotkey
        # self.home_hotkey_id = keyboard.add_hotkey("home", self.on_home_pressed)
        pass

    def on_home_pressed(self, event=None):
        Clock.schedule_once(self.go_to_home)

    def __del__(self):
        pass


if __name__ == '__main__':
    generalApp().run()
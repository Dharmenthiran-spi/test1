import time
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
import keyboard
from kivy.app import App
from kivy.base import EventLoop
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import ObjectProperty, Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.resources import resource_add_path
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.card import MDCard
from kivy.properties import NumericProperty, BooleanProperty, ColorProperty, ObjectProperty
from kivy.uix.behaviors import FocusBehavior
from kivymd.uix.textfield import MDTextField
from database import *
import os
import sys
import json
import traceback
print('hi')
user = User()

class MyApp(BoxLayout):
    pass

class LoginTextInput(MDTextField, FocusBehavior):
    row = NumericProperty()
    col = NumericProperty()
    def __init__(self, **kwargs):
        self.maxlength = kwargs.pop('maxlength', None)
        super(LoginTextInput, self).__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        if self.maxlength is not None:
            if len(self.text) + len(substring) > self.maxlength:
                substring = substring[:self.maxlength - len(self.text)]
        return super(LoginTextInput, self).insert_text(substring, from_undo=from_undo)

class LoginApp(MDApp):
    def build(self):
        self.icon = 'logindi.png'
        self.title='Login'
        Window.size_hint = (None, None)
        Window.size = (700, 400)
        Window.minimum_width = 700
        Window.minimum_height = 350
        create_table()
        self.start_keyboard_listener()
        sys.setrecursionlimit(10 ** 9)
        return Builder.load_file('login.kv')

    def start_keyboard_listener(self):
        keyboard.add_hotkey("enter", self.on_enter_pressed)
        keyboard.add_hotkey("ctrl", self.on_clear_pressed)

    def on_enter_pressed(self, *args):
        Clock.schedule_once(self.enter_button)

    def enter_button(self, dt):
        self.switch_to_main()

    def on_clear_pressed(self, event=None):
        Clock.schedule_once(self.clear_button)

    def clear_button(self, dt):
        self.dismiss_screen()

    def switch_to_main(self):
        entered_username = self.root.ids.user_name.text
        entered_password = self.root.ids.password.text

        def handle_successful_login(username, password):
            print("Login successful. Switching to the main page.")
            login_info = {'username': username, 'password': password}
            # Save the login information to a JSON file
            self.save_login_info_to_json(login_info)
            Builder.unload_file('login.kv')
            LoginApp.stop(self)
            from main import MainApp
            MainApp().run()

        if user.check_admin_users():
            if user.validate_login(entered_username, entered_password):
                handle_successful_login(entered_username, entered_password)
            else:
                toast("Error: Invalid username or password.", duration=0.6)
        else:
            if user.validate_login(entered_username, entered_password):
                handle_successful_login(entered_username, entered_password)
            elif entered_username == "spi" and entered_password == "12345":
                print("Default login credentials used. Switching to the main page.")
                handle_successful_login(entered_username, entered_password)
            else:
                toast("Error: Invalid username or password.", duration=0.6)

    def show_error_popup(self, message):
        # Create a popup with an error message
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 100))
        error_popup.open()

    def dismiss_screen(self):
        print("Cancel button clicked. Dismissing the screen.")
        App.get_running_app().stop()

    def save_login_info_to_json(self, login_info):
        json_file_path = 'login_info.json'

        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(login_info, json_file)
            print(f"Login information saved to {json_file_path}.")
        except Exception as e:
            print(f"Error saving login information: {e}")

    def on_stop(self):
        keyboard.unhook_all_hotkeys()

    def __del__(self):
        pass

if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    LoginApp().run()

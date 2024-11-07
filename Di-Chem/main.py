import csv
import ctypes
import threading
import time
from functools import partial
import os
import sys
import traceback
import keyboard
from kivy.clock import mainthread
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDIcon
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.icon_definitions import md_icons
import serial.tools.list_ports
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ObjectProperty, Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import StencilPush, StencilUse, StencilUnUse, StencilPop, Color, Rectangle
from database import *
from DirectDosing_HMI_Network_v1_1 import*
from DirectDosing_WeigingSystem_V1_1 import *
import concurrent.futures
from kivy.properties import ColorProperty
from kivymd.uix.behaviors import RectangularRippleBehavior
from USBvcpSerializer_V1 import USBvcpSerializer_V1

chemical=Chemical()
batch=BatchChemicalData()
batch_metadata=BatchMetaData()
user=User()
tank=OutputLayout()
db_communication=DatabaseInterfaceForHMI()
mydata=DatabaseInterfaceForWeigingSytsem()
scheduled_events = {}

class WaterFill(Widget,ButtonBehavior):

    level = NumericProperty(0)  # Use Kivy's NumericProperty to ensure level is a numeric type
    max_level = None
    color = (0.7, 0.7, 0.7, 1)
    background_color = (1, 1, 1)

    def __init__(self, valve_no, app=None, max_level=0, **kwargs):
        super(WaterFill, self).__init__(**kwargs)
        self.valve_no = valve_no
        self.app = app
        self.max_level = max_level
        self.bind(pos=self.update_graphics, size=self.update_graphics, level=self.update_graphics)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.app.update_valve_details(self.valve_no)

    def update_graphics(self, instance, value):
        self.canvas.clear()  # Clear previous drawings

        with self.canvas:
            StencilPush()
            Rectangle(pos=self.pos, size=self.size)
            StencilUse()
            Color(*self.background_color)
            Rectangle(pos=self.pos, size=self.size)
            Color(*self.color)

            try:
                level_value = float(self.level)
            except ValueError:
                level_value = 0

            try:
                max_value = float(self.max_level)
            except ValueError:
                max_value = 1
            if max_value > 0:
                filled_height = (level_value / max_value) * self.height
            else:
                filled_height = 0

            Rectangle(pos=self.pos, size=(self.width, filled_height))

            StencilUnUse()
            StencilPop()


class HmiPolling(BoxLayout):



    def __init__(self, **kwargs):
        super(HmiPolling, self).__init__(**kwargs)
        self.continuous_update()
        self.populate_slave_ids()
        self.selected_slave_id=None
        self.displayed_RX_Batch = set()
        self.slave_fetch_interval = None
        self.selected_station_name = None
        self.last_file_size = 0


    def continuous_update(self):
        scheduled_events['update_icon']=Clock.schedule_interval(self.update_icon, 0.25)

    def update_icon(self,dt):
        self.update_slave_id_status()

    def populate_slave_ids(self):
        response = ResponseHmi.response_hmi
        unresponse = Unresponse_Hmi.unresponse_hmi

        slave_id_list = tank.fetch_slave_id_hmi()

        for slave_id in slave_id_list:
            # Create a vertical BoxLayout for the icon and button
            item_layout = BoxLayout(orientation='vertical', spacing=5)

            # Determine icon color based on response status
            if slave_id in response:
                icon_color = (0, 1, 0, 1)  # Green
                # print('response_hmi',slave_id)
                # print("response_dir",ResponseHmi.response_hmi)

            elif slave_id in unresponse:
                icon_color = (1, 0, 0, 1)  # Red
                # print('unresponse_hmi', slave_id)
                # print('unresponsive_dir',Unresponse_Hmi.unresponse_hmi)
            else:
                icon_color = (0.5, 0.5, 0.5, 1)  # Gray (default color if not found in any list)

            icon = MDIcon(
                icon='lan-connect',
                size_hint=(None, None),
                size=(dp(50), dp(50)),
                theme_text_color='Custom',
                text_color=icon_color
            )

            slave_button = MDRaisedButton(
                text=str(slave_id),
                size_hint=(None, None),
                size=(dp(150), dp(30))
            )
            slave_button.bind(on_release=self.slave_button_pressed)

            item_layout.add_widget(icon)
            item_layout.add_widget(slave_button)

            self.ids.hmi_slaveid.add_widget(item_layout)

    def slave_button_pressed(self,button):
        self.selected_slave_id =button.text
        self.ids.slave_id.text=button.text


    def update_slave_id_status(self):
        response = ResponseHmi.response_hmi
        unresponse = Unresponse_Hmi.unresponse_hmi

        for item_layout in self.ids.hmi_slaveid.children:
            slave_button = item_layout.children[0]  # The slave button
            icon = item_layout.children[1]  # The icon

            try:
                slave_id = int(slave_button.text)  # Convert the button text to int for comparison
            except ValueError:
                continue

            if slave_id in response:
                icon.text_color = (0, 1, 0, 1)  # Green
                # print('response_slave', slave_id)
                # print("response_dir", ResponseHmi.response_hmi)
            elif slave_id in unresponse:
                icon.text_color = (1, 0, 0, 1)  # Red
                # print('unresponse_slave', slave_id)
                # print('unresponsive_dir', Unresponse_Hmi.unresponse_hmi)
            else:
                icon.text_color = (0.5, 0.5, 0.5, 1)  # Gray

    def on_batch_Request_button_press(self):

        rx_batch_data = self.ids.tx_data_batch
        rx_batch_data.clear_widgets()
        rx_batch_data.cols = 1
        rx_batch_data.spacing = 10

        if self.selected_slave_id:

            # Reset state for new station selection
            self.displayed_RX_Batch = set()
            self.last_file_size = 0

            slave_id = f"HMI:{self.selected_slave_id}"


            # Fetch once immediately
            self.fetch_response_details(rx_batch_data, slave_id, initial_fetch=True)

            # Schedule fetching and displaying of additional messages every 1 second
            if self.slave_fetch_interval:
                self.slave_fetch_interval.cancel()
            self.slave_fetch_interval = Clock.schedule_interval(
                lambda dt: self.fetch_response_details(rx_batch_data, slave_id), 1)
            scheduled_events['fetch_response_details'] = self.slave_fetch_interval

        else:
            toast("Error: No slave_id selected.", duration=0.6)
    def fetch_response_details(self, grid, slave_id, initial_fetch=False):
        file_path = 'Request-Batch-Info.log'

        try:
            if not os.path.exists(file_path):
                print("Tx_Data_Machine.log file not found.")
                return

            file_size = os.path.getsize(file_path)
            new_data_available = file_size > self.last_file_size
            self.last_file_size = file_size

            with open(file_path, 'r', buffering=8192) as file:
                lines = file.readlines()

            # Reverse lines for processing recent messages first
            lines.reverse()

            # Filter messages based on the station
            filtered_lines = [line.strip() for line in lines if slave_id in line]

            if initial_fetch or new_data_available:
                # Fetch the latest 10 messages that have not been displayed
                new_messages = []
                for line in filtered_lines:
                    if line not in self.displayed_RX_Batch:
                        new_messages.append(line)
                        if len(new_messages) == 10:
                            break
                self.displayed_RX_Batch.update(new_messages)

                # Update the UI with the latest messages
                self.update_station_ui(grid, new_messages, prepend=True)
            else:
                # No new data, fetch the next batch of messages in reverse order
                remaining_messages = [line for line in filtered_lines if line not in self.displayed_RX_Batch]
                next_details = remaining_messages[:10]
                self.displayed_RX_Batch.update(next_details)
                self.update_station_ui(grid, next_details)

        except FileNotFoundError:
            print("Tx_Data_Machine.log file not found.")

    def on_batch_button_press(self):

        rx_batch_data = self.ids.tx_data_batch
        rx_batch_data.clear_widgets()
        rx_batch_data.cols = 1
        rx_batch_data.spacing = 10

        if self.selected_slave_id:
            # Reset state for new station selection
            self.displayed_RX_Batch = set()
            self.last_file_size = 0

            slave_id = f"HMI: {self.selected_slave_id}"

            # Fetch once immediately
            self.fetch_slave_details(rx_batch_data, slave_id, initial_fetch=True)

            # Schedule fetching and displaying of additional messages every 1 second
            if self.slave_fetch_interval:
                self.slave_fetch_interval.cancel()
            self.slave_fetch_interval = Clock.schedule_interval(lambda dt: self.fetch_slave_details(rx_batch_data, slave_id), 1)
            scheduled_events['fetch_slave_details'] =self.slave_fetch_interval
        else:
            toast("Error: No slave_id selected.", duration=0.6)

    def fetch_slave_details(self, grid, slave_id, initial_fetch=False):
        file_path = 'Batch_Request.log'

        try:
            if not os.path.exists(file_path):
                print("Tx_Data_Machine.log file not found.")
                return

            file_size = os.path.getsize(file_path)
            new_data_available = file_size > self.last_file_size
            self.last_file_size = file_size

            with open(file_path, 'r', buffering=8192) as file:
                lines = file.readlines()

            # Reverse lines for processing recent messages first
            lines.reverse()

            # Filter messages based on the station
            filtered_lines = [line.strip() for line in lines if slave_id in line]

            if initial_fetch or new_data_available:
                # Fetch the latest 10 messages that have not been displayed
                new_messages = []
                for line in filtered_lines:
                    if line not in self.displayed_RX_Batch:
                        new_messages.append(line)
                        if len(new_messages) == 10:
                            break
                self.displayed_RX_Batch.update(new_messages)

                # Update the UI with the latest messages
                self.update_station_ui(grid, new_messages, prepend=True)
            else:
                # No new data, fetch the next batch of messages in reverse order
                remaining_messages = [line for line in filtered_lines if line not in self.displayed_RX_Batch]
                next_details = remaining_messages[:10]
                self.displayed_RX_Batch.update(next_details)
                self.update_station_ui(grid, next_details)

        except FileNotFoundError:
            print("Tx_Data_Machine.log file not found.")

    def update_station_ui(self, grid, batch,prepend=False):
        # Add the batch of messages to the UI
        for line in batch:
            error_label = TextInput(text=line, size_hint=(None,None),size=(2000,30),
                                    background_color=(3, 3, 3, 1), readonly=True, halign='left',multiline=True)
            if prepend:
                grid.add_widget(error_label, index=0)  # Prepend messages
            else:
                grid.add_widget(error_label)




class Main(BoxLayout):
    connection = create_connection("ChemDB.db")
    connected = BooleanProperty(False)
    current_instance = None
    com_port = []
    available_baud_rates = [9600, 14400, 19200, 38400, 57600, 115200, 128000]
    logged_in_user = None

    def __init__(self,connection_manager=None, **kwargs):
        super(Main, self).__init__(**kwargs)
        self.hwnd = ctypes.windll.user32.GetForegroundWindow()
        style = ctypes.windll.user32.GetWindowLongW(self.hwnd, -16)
        style &= ~0x00080000
        ctypes.windll.user32.SetWindowLongW(self.hwnd, -16, style)
        self.create_valve_progress_bars()
        scheduled_events['create_valve_progress_bars']=Clock.schedule_interval(self.create_valve_progress_bars, 1)
        self.logged_in_user=None
        self.current_popup = None
        self.file_paths = []
        self.selected_file = None
        self.json_file = 'processed_files.json'
        self.connection_manager = connection_manager
        self.show_hmi_request_list()
        self.csv_file_identify()

    def Hmi_popup(self):

        hmi_polling = HmiPolling()
        hmi_window = Popup(title='HMI-Status', content=hmi_polling, size_hint=(None, None), size=(1500, 650),
                                padding=10, title_size=25, title_font="Aileron-Bold.otf",background='white',title_color=(0,0,0,1))
        no_slave=tank.fetch_slave_id_hmi()
        if len(no_slave)>20:
            hmi_window.size_hint_x=.95
        elif len(no_slave)<20:
            hmi_window.size_hint_x =.75
        hmi_window.open()

    def change_button_color(self, button):
        button.md_bg_color = (77/255, 199/255, 226/255, 1)
        Clock.schedule_once(lambda dt: self.reset_button_color(button), .1)

    def reset_button_color(self, button):
        button.md_bg_color = (0.3, 0.3, 0.3, 1)

    def continuous_checking(self,dt):
        self.load_csv_files()

    def csv_file_identify(self):
        scheduled_events['continuous_checking']=Clock.schedule_interval(self.continuous_checking, 0.25)
    def load_csv_files(self):
        desktop_directory = os.path.join(os.path.expanduser("~"), "Desktop")
        self.file_paths = [f for f in os.listdir(desktop_directory) if f.endswith('.csv')]

        processed_files = self.load_processed_files()

        unprocessed_files = [f for f in self.file_paths if f not in processed_files]

        self.ids.file_list.clear_widgets()
        for file_name in unprocessed_files:
            btn = Button(text=file_name, size_hint_y=None, height=30,color=(0, 0, 0, 3), background_color=(3, 3, 3, 1),valign='middle', halign='left')
            btn.bind(on_release=self.on_file_select)
            self.ids.file_list.add_widget(btn)

    def load_processed_files(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                return json.load(f)
        return []

    def save_processed_file(self, file_name):
        processed_files = self.load_processed_files()
        processed_files.append(file_name)
        with open(self.json_file, 'w') as f:
            json.dump(processed_files, f)

    def on_file_select(self, button):
        self.selected_file = button.text
        print(f"Selected file: {self.selected_file}")

    def upload_csv(self):
        if self.selected_file:
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", self.selected_file)
            self.insert_data_from_csv(file_path)
            self.load_csv_files()
        else:
            toast("No file selected",duration=0.6)

    def open_csv(self):
        if self.selected_file:
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", self.selected_file)
            self.show_file_content(file_path)
        else:
            toast("No file selected",duration=0.6)

    def insert_data_from_csv(self, file_path):
        try:
            connection = sqlite3.connect("ChemDB.db")

            with open(file_path, newline='') as csvfile:
                csvreader = csv.reader(csvfile)
                headers = next(csvreader)

                for row in csvreader:
                    if len(row) == 4:
                        batch_name, fabric_wt, mlr, machin_name = row
                        print("batch_name",batch_name)
                        message=batch_metadata.insert_into_BatchMetaData_csv(connection, batch_name, fabric_wt, mlr, machin_name)
                        toast(message,duration=0.6)

                    try:
                        if len(row) == 7:
                            seq_no, target_tank, chemical, target_weight, user_name, status, dispense_when = row
                            msg=batch.insert_into_BatchChemicalData_csv(connection, batch_name, seq_no, target_tank,
                                                               chemical, target_weight, user_name, status,
                                                               dispense_when)
                            Clock.schedule_once(lambda dt: self.display_toast(msg), 1)
                            self.save_processed_file(self.selected_file)
                        else:
                            print(f"Batch '{batch_name}' not found in the 'BatchMetaData' table.")
                    except Exception as ex:
                        print(ex)
        except Exception as e:
            print(f"Error: {e}")

    def display_toast(self, message):
        # Assuming you have a Toast or similar implementation
        toast(message, duration=0.6)

    def show_file_content(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()

        content_popup = Popup(
            title='File Content',
            title_size=25,
            title_font="Aileron-Bold.otf",
            content=Label(
                text=content,
                text_size=(None, None),
                size_hint=(1, 1),
                halign='left',
                valign='top',font_size=15,
            ),
            size_hint=(0.35, 0.45),
            auto_dismiss=True
        )
        content_popup.open()

    def show_hmi_request_list(self):
        hmi_request_list = self.ids.request_list
        hmi_request_list.clear_widgets()
        for item in SharedData.dispense_chem:
            print('item',item)
            item_label = Label(text=str(item),color=(0, 0, 0, 3),size_hint=(None,None),size=(30,30),valign='center')
            hmi_request_list.add_widget(item_label)

    def BatchmetaData(self, batch_data):
        self.ids.tank_grid.clear_widgets()
        batchmeta_grid = self.ids.tank_grid
        self.ids.scroll_view.do_scroll_y = True
        batchmeta_grid.cols = 1
        batchmeta_grid.spacing = 180
        batchmeta_grid.padding = 10
        batch_name = batch_data.get('BatchName')

        chem_layout = GridLayout(cols=1, padding=30)
        empty_widget = Label(size_hint=(None, None), size=(40, 20))
        label = Label(text=f'Pending {batch_name} Chemical Data', size_hint=(None, None), size=(750, 40), font_size=17,
                      bold=True)
        chem_layout.add_widget(empty_widget)
        chem_layout.add_widget(label)
        chem_layout.padding = 100

        batchmeta_grid.add_widget(chem_layout)

        scroll_view = ScrollView(size_hint=(None, None), do_scroll_y=True, size=(940, 450))

        full_chem_layout = GridLayout(cols=10, spacing=0, padding=0, size_hint_y=None, size_hint_x=None)
        full_chem_layout.bind(minimum_height=full_chem_layout.setter('height'))

        header_sizes = {
            'ID': 55,
            'SeqNo': 65,
            'TargetTank': 110,
            'ChemicalNo': 113,
            'Chemical': 100,
            'TargetWt': 105,
            'DispWeight': 113,
            'Status': 85,
            'WaterAdd': 90,
            'Disp when': 105
        }

        # Add header widgets
        for header, size in header_sizes.items():
            full_chem_layout.add_widget(
                TextInput(text=header, halign='center', size_hint=(None, None), size=(size, 30), readonly=True,
                          multiline=False, font_name="Aileron-Bold.otf")
            )

        batch_id = batch_data.get('BatchID')
        if batch_id:
            data = batch.fetch_details_by_batch_chemical(batch_id)
            # Add data rows to the grid
            for row in data:
                for index, value in enumerate(row):
                    size = header_sizes[list(header_sizes.keys())[index]]  # Get the size for the corresponding column
                    text_input = TextInput(text=str(value), halign='center', size_hint=(None, None), size=(size, 30),
                                           readonly=True, background_color=(1, 1, 1, 1), multiline=False)
                    full_chem_layout.add_widget(text_input)

        scroll_view.add_widget(full_chem_layout)

        batchmeta_grid.add_widget(scroll_view)

    def update_settings_button(self, logged_in_user):
        with open('login_info.json') as f:
            login_info = json.load(f)

        username = login_info.get('username', '')
        if username  == 'spi':
            self.ids.settings_button.disabled = False
            self.active_setting_button()
        else:
            print(f"Logged-in user: {logged_in_user}")
            if logged_in_user == 'Admin':
                self.ids.settings_button.disabled = False
                self.active_setting_button()
            else:
                self.ids.settings_button.disabled = True
            print(f"Settings button disabled: {self.ids.settings_button.disabled}")

    def active_setting_button(self):
        # keyboard.add_hotkey("s", self.setting_pressed)
        pass

    def setting_pressed(self,event=None):
        Clock.schedule_once(self.setting_button)

    def setting_button(self,dt):
       pass

    def create_valve_progress_bars(self,dt=None):
        if not self.ids.scroll_view.do_scroll_y:
            tank_grid = self.ids.tank_grid
            tank_grid.clear_widgets()
            total_valve_count = chemical.get_total_valve_count(self.connection)
            no_of_chemical = self.get_no_of_chemical()
            if no_of_chemical !='':
                no_of_chemical = int(self.get_no_of_chemical())
                if no_of_chemical == 0:
                    return

                columns_per_chemical = 6 if no_of_chemical > 6 else no_of_chemical
                total_columns = (no_of_chemical + columns_per_chemical - 1) // columns_per_chemical

                tank_grid = self.ids.tank_grid
                tank_grid.cols = total_columns
                tank_grid.spacing = [20, 10]
                tank_grid.padding = [20, 20]
                tank_grid.size_hint_x = None

                valve_no_counter = 1

                for column in range(total_columns):
                    valve_layout = BoxLayout(orientation='vertical', size_hint=(None, None), size=(50, 700))

                    valves_in_column = min(columns_per_chemical, no_of_chemical - column * columns_per_chemical)

                    for _ in range(valves_in_column):
                        max_level = chemical.get_max_stock_for_valve(self.connection, valve_no_counter)
                        label = Button(
                            text=f' {valve_no_counter}',
                            size_hint=(None, None),
                            size=(40, 30),
                            on_press=lambda instance, v=valve_no_counter: self.update_valve_details(v)
                        )

                        water_fill = WaterFill(
                            valve_no_counter,
                            max_level=max_level,
                            app=self,
                            size_hint=(None, None),
                            size=(40, 60),
                            pos_hint={'center_y': 0.5, 'x': 0}
                        )

                        valve_layout.add_widget(label)
                        valve_layout.add_widget(water_fill)
                        self.set_water_level(valve_no_counter, water_fill)

                        valve_no_counter += 1

                        spacer = BoxLayout(size_hint_y=None, height=10)
                        valve_layout.add_widget(spacer)

                    empty_space_height = 300 - (
                            valves_in_column * 90)

                    empty_layout = Widget(top=0)
                    valve_layout.add_widget(empty_layout)

                    tank_grid.add_widget(valve_layout)
        else:
            pass


    def update_valve_details(self, valve_no):
        details = chemical.fetch_valve_details_from_database(valve_no)

        if details is not None:
            # Update the labels and TextInput
            self.ids.valve_no.text = str(valve_no)
            self.ids.stock_no.text = str(details['Stock'])
            self.ids.Chemical_no.text = details['Name']
            self.ids.minstock_no.text = str(details['MinStock'])
        else:
            print(f"Details not found for Valve {valve_no}")

    def set_water_level(self, valve_no, water_fill):
        try:

            stock_value = chemical.fetch_stock_for_valve(self.connection, valve_no)

            if stock_value is not None:

                if isinstance(stock_value, (int, float, str)) and stock_value != '':

                    water_fill.level = float(stock_value)

                    min_stock = chemical.fetch_min_stock_for_valve(self.connection, valve_no)

                    if isinstance(min_stock, (int, float, str)) and min_stock != '':
                        min_stock = float(min_stock)
                        if stock_value > min_stock:
                            water_fill.color = (0.5, 1, 0.5, 1)  # Green color
                        elif stock_value == min_stock:
                            water_fill.color = (1, 0, 0, 1)  # White color
                        else:
                            water_fill.color = (1, 0, 0, 1)  # Red color
                else:

                    water_fill.level = 0
            else:

                water_fill.level = 0

        except Exception as e:
            print(f"Error setting water level from database: {e}")
            water_fill.level = 0


    def save_changes(self):

        valve_number = self.ids.valve_no.text
        chemical_name = self.ids.Chemical_no.text
        stockchem = self.ids.stock_no.text
        min_stock = self.ids.minstock_no.text
        valve_no = self.ids.valve_no.text

        # Validate stock_no against max_tank_capacity
        max_tank_capacity = float(chemical.get_max_tank_valve(valve_no))  # Convert max_tank_capacity to float

        try:
            stock_no = float(stockchem)  # Convert stockchem to float
            if stock_no > max_tank_capacity:
                toast(f"Error: Stock exceeds the maximum tank capacity ({max_tank_capacity}).", duration=0.6)
                return
        except ValueError:
            toast("Error: Stock must be a numeric value.", duration=0.6)
            return

        conn = create_connection("ChemDB.db")
        chemical.update_chemical_data(conn, valve_number, chemical_name, stockchem, min_stock)

        container = self.ids.tank_grid
        container.clear_widgets()

        # Recreate the valve progress bars
        self.create_valve_progress_bars()

    def get_max_tank_capacity(self):
        try:
            with open('form_data.json', 'r') as file:
                data = json.load(file)
                return data.get('max_tank_capacity', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def get_no_of_chemical(self):
        try:
            with open('form_data.json', 'r') as file:
                data = json.load(file)
                return data.get('no_of_chemical', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def minus_stock(self):
        try:
            chemical_name=self.ids.Chemical_no.text
            stock_addiction = self.ids.stock_addition.text
            stock_value = self.ids.stock_no.text
            valve_no = self.ids.valve_no.text

            if chemical_name=='':
                toast("Error: Chemical name is required for stock addition.", duration=0.6)
                return

            current_value = float(stock_addiction)

            existing_value = float(stock_value) if stock_value else 0.0

            new_value = existing_value - current_value
            max_tank_capacity = float(chemical.get_max_tank_valve(valve_no))

            try:
                stock_no = float(new_value)
                if stock_no > max_tank_capacity:
                    toast(f"Error: Stock exceeds the maximum tank capacity ({max_tank_capacity}).", duration=0.6)
                    return
            except ValueError:
                toast("Error: Stock must be a numeric value.", duration=0.6)
                return

            self.ids.stock_no.text = str(new_value)
            self.save_changes()
            self.ids.stock_addition.text = ''


        except ValueError:
            toast("Invalid input. Please enter a numeric value.", duration=0.6)

    def Add_stock(self):
        try:
            self.ids.add.md_bg_color = (0.3, 0.3, 0.3, 1)
            chemical_add=self.ids.Chemical_no.text
            stock_addiction_add = self.ids.stock_addition.text
            stock_value_add = self.ids.stock_no.text
            valve_value = self.ids.valve_no.text

            if chemical_add == '':
                toast(f"Error: Chemical name is required for stock addition.", duration=0.6)
                return

            current_value = float(stock_addiction_add)

            existing_value = float(stock_value_add) if stock_value_add else 0.0

            new_value = existing_value + current_value
            max_tank_capacity = float(chemical.get_max_tank_valve(valve_value))


            try:
                stock_no = float(new_value)
                print("max_tank", max_tank_capacity)
                print("stock",stock_no)
                if stock_no > max_tank_capacity:
                    toast(f"Error: Stock exceeds the maximum tank capacity ({max_tank_capacity}).", duration=0.6)
                    return
            except ValueError:
                toast("Error: Stock must be a numeric value.", duration=0.6)
                return

            self.ids.stock_no.text = str(new_value)
            self.save_changes()
            self.ids.stock_addition.text = ''

        except ValueError:
            toast("Invalid input. Please enter a numeric value.", duration=0.6)

    def show_error_popup(self, message):
        error_popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(400, 100))
        error_popup.open()
        self.current_popup = error_popup

    def dismiss_error_popup(self):
        # Check if there is a current popup and dismiss it if there is
        if self.current_popup:
            self.current_popup.dismiss()
            self.current_popup = None

    def open_pop(self):
        self.ids.station_button.md_bg_color = (0.3, 0.3, 0.3, 1)
        return OpenStation()


class StationDetails(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.displayed_station_messages = set()
        self.station_fetch_interval = None
        self.selected_station_name = None
        self.last_file_size = 0

    def on_station_button_click(self, instance):
        button_text = instance.text
        selected_station_label = self.ids.selected_station
        selected_station_label.text = button_text
        self.selected_station_name = button_text

    def on_open_button_press(self, instance):
        app = App.get_running_app()
        tx_machin_data = app.root.ids.tank_grid
        tx_machin_data.clear_widgets()
        tx_machin_data.cols = 1
        tx_machin_data.spacing = 10

        if self.selected_station_name:
            # Reset state for new station selection
            self.displayed_station_messages = set()
            self.last_file_size = 0

            station = f"Station:{self.selected_station_name}"

            # Fetch once immediately
            self.fetch_station_details(tx_machin_data, station, initial_fetch=True)

            # Schedule fetching and displaying of additional messages every 1 second
            if self.station_fetch_interval:
                self.station_fetch_interval.cancel()
            self.station_fetch_interval = Clock.schedule_interval(lambda dt: self.fetch_station_details(tx_machin_data, station), 1)
            scheduled_events['fetch_station_details'] =self.station_fetch_interval
        else:
            toast("Error: No station selected.", duration=0.6)

    def fetch_station_details(self, grid, station, initial_fetch=False):
        file_path = 'Tx_Data_Machine.log'

        try:
            if not os.path.exists(file_path):
                print("Tx_Data_Machine.log file not found.")
                return

            file_size = os.path.getsize(file_path)
            new_data_available = file_size > self.last_file_size
            self.last_file_size = file_size

            with open(file_path, 'r', buffering=8192) as file:
                lines = file.readlines()
            lines.reverse()
            filtered_lines = [line.strip() for line in lines if station in line]

            if initial_fetch or new_data_available:
                # Fetch the latest 10 messages that have not been displayed
                new_messages = []
                for line in filtered_lines:
                    if line not in self.displayed_station_messages:
                        new_messages.append(line)
                        if len(new_messages) == 10:
                            break
                self.displayed_station_messages.update(new_messages)

                # Update the UI with the latest messages
                self.update_station_ui(grid, new_messages, prepend=True)
            else:
                # No new data, fetch the next batch of messages in reverse order
                remaining_messages = [line for line in filtered_lines if line not in self.displayed_station_messages]
                next_batch = remaining_messages[:10]
                self.displayed_station_messages.update(next_batch)
                self.update_station_ui(grid, next_batch)

        except FileNotFoundError:
            print("Tx_Data_Machine.log file not found.")

    def update_station_ui(self, grid, batch,prepend=False):
        # Add the batch of messages to the UI
        for line in batch:
            error_label = TextInput(text=line, size_hint=(None, None), size=(2000, 30),
                                    background_color=(3, 3, 3, 1), readonly=True, halign='left')
            if prepend:
                grid.add_widget(error_label, index=0)
            else:
                grid.add_widget(error_label)
class OpenStation(BoxLayout):
    def __init__(self, **kwargs):
        super(OpenStation, self).__init__(**kwargs)
        self.show_station_layout()

    def show_station_layout(self):
        app=App.get_running_app()
        app.root.ids.tank_pending_grid.clear_widgets()
        app.root.ids.scroll_view.do_scroll_y = True
        station_details=app.root.ids.tank_pending_grid
        station_details.padding=20
        station_layout= StationDetails()
        station_details.add_widget(station_layout)



class Batch(BoxLayout):
    pass


class MachinConnectionManager:
    _instance = None

    def __new__(cls,executor):
        if cls._instance is None:
            cls._instance = super(MachinConnectionManager, cls).__new__(cls)
            cls._instance._initialize(executor)
        return cls._instance

    def _initialize(self,executor):
        self.executor = executor
        self.machinDev = None
        self.is_connected = False
        self.device_thread = None
        self.shutdown_event = threading.Event()

    def connect(self):
        if self.is_connected:
            print("Device is already connected. Skipping connection attempt.")
            return

        try:
            with open('form_data.json', 'r') as file:
                data = json.load(file)

            com_port_value = data.get("machine_comport")
            baud_rate = data.get("machin_baud_rate")
            slaveID = int(data.get("machin_slaveid"))
            noOfStations = int(data.get("no_of_station"))
            self.machinDev = DirectDosing_WeigingSystem_V1(slaveID, noOfStations)
            connected = self.machinDev.Connect(com_port_value, baud_rate, rx_buffer_size=4096, tx_buffer_size=4096)

            if connected:
                self.is_connected = True
                self.machine_status()
                print("Device connected successfully.")
                self.executor.submit(self.run_machin_device)
                # self.device_thread = threading.Thread(target=self.run_machin_device, name="DeviceThread", daemon=True)
                # self.device_thread.start()
            else:
                self.update_ui((1, 0, 0, 1), 'Disconnected')
                print(f"Failed to connect to the device on {com_port_value} at {baud_rate} baud.")
        except Exception as e:
            self.update_ui((1, 0, 0, 1), 'Disconnected')
            print(f"Error while connecting: {e}")

    def machine_status(self):
        if self.is_connected:
            try:
                app = App.get_running_app()
                if app and app.title == 'Main':
                    response_machine=Responsemachine.response_machine
                    if isinstance(response_machine, list) and response_machine:
                        self.update_ui((0, 1, 0, 1), 'Connected')
                    else:
                        self.update_ui((1, 0, 0, 1), 'Disconnected')
            except Exception as e:
                print(f"Error in machine status: {e}")

        Clock.schedule_once(lambda dt: threading.Timer(1, self.machine_status).start(), 0)

    def update_ui(self, color, text):
        def _update_ui(dt):
            app = App.get_running_app()
            try:
                if app and app.title == 'Main':
                    app.root.ids.machin_connection_button.background_color = color
                    app.root.ids.machin_connection_button.text = text
            except AttributeError as e:
                print(f"Error machine UI: {e}. Ensure 'machine_button' exists in the layout.")

        Clock.schedule_once(_update_ui)

    def run_machin_device(self):
        while self.is_connected and not self.shutdown_event.is_set():
            try:
                if self.machinDev.is_connected():
                    self.machinDev.Run()
                else:
                    raise Exception("Device disconnected during operation.")
            except Exception as e:
                print(f"Error during MachinRun: {e}")
                self.handle_disconnection()
                break
            time.sleep(0.25)  # Loop Time

    def handle_disconnection(self):
        if self.is_connected:
            self.is_connected = False
            if self.machinDev:
                self.machinDev.Disconnect()
            self.update_ui((1, 0, 0, 1), 'Disconnected')
            print("Device disconnected.")

    def machin_disconnect(self):
        if self.is_connected:
            self.is_connected = False
            if self.device_thread and self.device_thread.is_alive():
                self.device_thread.join(timeout=5)
            if self.machinDev:
                self.machinDev.Disconnect()
            self.update_ui((1, 0, 0, 1), 'Disconnected')
            print("Device disconnected.")

    def get_machin_status(self):
        print("identify-machine-status:", self.is_connected)
        return self.is_connected

class ConnectionManager:
    _instance = None
    _initialized = False

    def __new__(cls,executor):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance._initialize(executor)
        return cls._instance

    def _initialize(self,executor):
        self.executor = executor
        self.myDev = None
        self.is_connected = False
        self.monitor_thread = None

    def __init__(self,executor):
        self.executor = executor
        if not self._initialized:
            self.start_continuous_check()
            ConnectionManager._initialized = True
            self.shutdown_event = threading.Event()

    def connect(self):
        if self.is_connected:
            print("Device is already connected. Skipping connection attempt.")
            app = App.get_running_app()
            # app.root.ids.hmi_switch.active = True
            return

        try:
            with open('form_data.json', 'r') as file:
                data = json.load(file)

            com_port_value = data.get("com_port")
            baud_rate = data.get("baud_rate")
            SlaveIDList = tank.fetch_slave_id_hmi()
            print("Slave list:", SlaveIDList)

            self.myDev = DirectDosing_HMI_Network_V1(SlaveIDList)
            self.is_connected = self.myDev.Connect(com_port_value, baud_rate, rx_buffer_size=4096, tx_buffer_size=4096)

            if self.is_connected:
                self.connection_status()
                self.executor.submit(self.monitor_device_connection)
                # self.monitor_thread = threading.Thread(target=self.monitor_device_connection, name="MonitorThread", daemon=True)
                # self.monitor_thread.start()
                self.executor.submit(self.run_device)
                # self.device_thread = threading.Thread(target=self.run_device, name="DeviceThread", daemon=True)
                # self.device_thread.start()
            else:
                print(f"Failed to connect to the device on {com_port_value} at {baud_rate} baud.")
                self.update_ui((1, 0, 0, 1), 'Disconnected')
                app = App.get_running_app()
                # app.root.ids.hmi_switch.active = False
        except Exception as e:
            print(f"Error while connecting: {e}")
            self.update_ui((1, 0, 0, 1), 'Disconnected')
            response_list = ResponseHmi().response_hmi
            response_list.clear()


    def connection_status(self):
        app = App.get_running_app()
        if app and app.title == 'Main':
            response_list = ResponseHmi.response_hmi
            # print('response_hmi',response_list)
            if isinstance(response_list, list) and response_list:
                self.update_ui((0, 1, 0, 1), 'Connected')
            else:
                self.update_ui((1, 0, 0, 1), 'Disconnected')
        else:
            pass
        Clock.schedule_once(lambda dt: threading.Timer(1, self.connection_status).start(), 0)


    def update_ui(self, color, text):
        def _update_ui(dt):
            app = App.get_running_app()
            try:
                if app and app.title == 'Main':
                    connection_button = app.root.ids.connection_button
                    connection_button.background_color = color
                    connection_button.text = text
            except AttributeError as e:
                print(f"Error updating UI: {e}. Ensure 'connection_button' exists in the layout.")

        Clock.schedule_once(_update_ui)

    def run_device(self):
        while self.is_connected and not self.shutdown_event.is_set():
            try:
                self.myDev.Run()
            except Exception as e:
                print(f"Error during Run: {e}")
                self.handle_disconnection()
                break
            time.sleep(0.25)

    def check_chemical_dispense(self):
        if ChemicalDispense.chem_dispense:
            print("ChemicalDispense.chem_dispense: ", ChemicalDispense.chem_dispense)
            for item in ChemicalDispense.chem_dispense:
                self.myDev.Add_Report_Dispensing(item)
                for sublist in self.myDev.ChemicalsRequestedFromHMI:
                    if item == sublist[2]:
                        ChemicalDispense.chem_dispense.remove(item)
                        break
            print("chem_dispense:", ChemicalDispense.chem_dispense)

    def check_chemical_complete(self):
        if ChemicalCompleted.chem_complete:
            for item in ChemicalCompleted.chem_complete:
                self.myDev.Add_Report_Completed(item)
                for sublist in self.myDev.ChemicalsRequestedFromHMI:
                    if item == sublist[2]:
                        ChemicalCompleted.chem_complete.remove(item)
                        break
            print("complete_chem:", ChemicalCompleted.chem_complete)

    def check_dispense_error(self):
        error_remove = []
        if ErrorCode.dispense_error:
            for item in ErrorCode.dispense_error:
                if self.myDev.Add_Report_Error(item):
                    error_remove.append(item)
            for item in error_remove:
                ErrorCode.dispense_error.remove(item)

    def continuous_check_list(self):
        while True:
            self.check_chemical_complete()
            self.check_chemical_dispense()
            self.check_dispense_error()
            time.sleep(0.25)

    def start_continuous_check(self):
        self.executor.submit(self.continuous_check_list)
        # thread = threading.Thread(target=self.continuous_check_list)
        # thread.daemon = True
        # thread.start()

    def monitor_device_connection(self):
        while self.is_connected and not self.shutdown_event.is_set():
            try:
                if not self.myDev.is_connected():
                    raise Exception("Device disconnected during operation.")
            except Exception as e:
                print(f"Error during monitoring: {e}")
                self.handle_disconnection()
                break
            time.sleep(1)

    def handle_disconnection(self):
        if self.is_connected:
            self.is_connected = False
            if self.myDev:
                self.myDev.Disconnect()
            self.update_ui((1, 0, 0, 1), 'Disconnected')
            response_list = ResponseHmi().response_hmi
            response_list.clear()
            print("Device disconnected.")

    def disconnect(self):
        if self.is_connected:
            self.is_connected = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            if self.myDev and self.myDev.is_connected():
                self.myDev.Disconnect()
            self.update_ui((1, 0, 0, 1), 'Disconnected')

    def get_connection_status(self):
        return self.is_connected

    def stop_device(self):
        self.stop_thread = True
        print("Device thread stopped.")

WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
GWL_STYLE = -16

class MainApp(MDApp):
    connection = create_connection("ChemDB.db")
    my_app_instance = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MainApp, cls).__new__(cls)
            cls._instance.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        return cls._instance

    def __init__(self, connection_manager=None,**kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.connection_port = ConnectionManager(self.executor)
        self.machine_connection= MachinConnectionManager(self.executor)
        self.connection_manager = connection_manager
        self.global_queue = []
        self.messages = []
        self.display_index = 0
        self.fetch_interval = None
        self.displayed_messages = []
        self.last_fetched_index = 0
        self.last_file_size = 0
        self.error_fetch_interval = None
        self.displayed_error_messages = []
        self.error_display_index = 0
        self.last_file_size = 0




    def build(self):
        self.icon = 'logindi.png'
        self.title='Main'
        Window.clearcolor = (0, 0, 0, 1)
        Window.maximize()
        Builder.load_file('mainpage.kv')
        my_app = Main()
        self.is_connected = False
        self.start_keyboard_listener()
        sys.excepthook = self.global_exception_handler
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.start_fetching_batches()
        sys.setrecursionlimit(10 ** 9)
        if sys.platform == 'win32':
            Clock.schedule_once(self.modify_window_style, 1)
        return my_app

    def modify_window_style(self, *args):
        hwnd = ctypes.windll.user32.GetActiveWindow()
        if hwnd:
            # Get the current window style
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)

            # Remove the close, minimize, and maximize buttons
            style &= ~WS_SYSMENU
            style &= ~WS_MINIMIZEBOX
            style &= ~WS_MAXIMIZEBOX

            # Apply the new style
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

            # Redraw the window with the new style
            ctypes.windll.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0027)


    def start_keyboard_listener(self):
        # Start listening for keyboard events in a separate thread
        # keyboard.add_hotkey("c", self.chemical_pressed)
        # keyboard.add_hotkey("b", self.batch_pressed)
        # keyboard.add_hotkey("r", self.report_pressed)
        keyboard.add_hotkey("+" ,self.add_pressed)
        keyboard.add_hotkey("-",self.minus_pressed)
        # keyboard.add_hotkey("end", self.on_end)

    def on_end(self, event=None):
        Clock.schedule_once(self.go_to_end)

    def go_to_end(self, dt):
        self.root.dismiss_error_popup()
    def minus_pressed(self,event=None):
        Clock.schedule_once(self.minus_button)

    def minus_button(self,dt):
        self.Minus_stock()
    def add_pressed(self,event=None):
        Clock.schedule_once(self.add_button)
    def add_button(self,dt):
        self.add_stock()
    def chemical_pressed(self, event=None):
        # Method to be called when Enter key is pressed
        Clock.schedule_once(self.chemical_button)

    def chemical_button(self,dt):

        self.switch_to_second()

    def batch_pressed(self, event=None):
        Clock.schedule_once(self.batch_button)

    def batch_button(self,dt):
        self.switch_to_third()

    def report_pressed(self,event=None):
        Clock.schedule_once(self.report_button)

    def report_button(self,dt):
        self.switch_to_fifth()

    def start_fetching_batches(self):
        scheduled_events['fetch_and_update_batches']=Clock.schedule_interval(
            self.fetch_and_update_batches, 1)
    def fetch_and_update_batches(self,dt=None):
        # Fetch pending batches
        pending_batches = self.fetch_pending_batches()
        self.update_batches(pending_batches)
        self.root.show_hmi_request_list()


    def on_start(self):
        self.connection_port.get_connection_status()
        self.machine_connection.get_machin_status()
        print("when i enter ")
        try:
            if self.machine_connection.get_machin_status():  # Condition based on identify-machine-status
                if Responsemachine.response_machine and any(isinstance(item, str) and item.strip() for item in Responsemachine.response_machine):
                    self.root.ids.machin_connection_button.background_color = (0, 1, 0, 1)  # Green
                    self.root.ids.machin_connection_button.text = 'Connected'
            else:
                self.root.ids.machin_connection_button.background_color = (1, 0, 0, 1)  # Red
                self.root.ids.machin_connection_button.text = 'Disconnected'
        except Exception as e:
            print('error',e)

        try:
            if self.connection_port.get_connection_status():
                if ResponseHmi.response_hmi and any(isinstance(item, str) and item.strip() for item in ResponseHmi.response_hmi):
                    self.root.ids.connection_button.background_color = (0, 1, 0, 1)  # Green
                    self.root.ids.connection_button.text = 'Connected'
            else:
                self.root.ids.connection_button.background_color = (1, 0, 0, 1)  # Red
                self.root.ids.connection_button.text = 'Disconnected'


        except Exception as e:
            self.root.ids.connection_button.background_color = (1, 0, 0, 1)  # Red
            self.root.ids.connection_button.text = 'Disconnected'

        pending_batches = self.fetch_pending_batches()
        total_valve_count = chemical.get_total_valve_count(self.connection)

        valve_no_label = self.root.ids.valve_no
        valve_no_label.text = f'{total_valve_count}'

        self.update_batches(pending_batches)

        self.connection_port.connect()
        self.machine_connection.connect()

        try:

            with open('login_info.json', 'r') as json_file:
                login_info = json.load(json_file)

            self.logged_in_user = user.authenticate_user(login_info)

            print(f"Logged-in user: {self.logged_in_user}")

            self.root.update_settings_button(self.logged_in_user)
        except Exception as ex:
            print("no login_info.json file found")



    def fetch_pending_batches(self):

        pending_batches = batch.fetch_BatchChemicalData_status(status_filter='Pending')
        return pending_batches

    def show_error_message(self, hmi_active, machin_active):
        error_message_grid = self.root.ids.error_msg_grid
        error_message_grid.clear_widgets()
        self.displayed_error_messages = []
        self.error_display_index = 0
        self.last_file_size = 0

        # Determine the prefix based on the active checkboxes
        if hmi_active and machin_active:
            prefix = None
        elif hmi_active:
            prefix = "SlaveID"
        elif machin_active:
            prefix = "StationID"
        else:
            prefix = None

        # Check if at least one checkbox is active
        if hmi_active or machin_active:
            # Fetch and display initial messages
            self.fetch_and_display_error_messages(error_message_grid, prefix, initial_fetch=True)

            # Cancel the previous scheduled fetching interval, if any
            if self.error_fetch_interval:
                self.error_fetch_interval.cancel()

            # Schedule fetching and displaying of additional messages every 2 seconds
            self.error_fetch_interval = Clock.schedule_interval(
                lambda dt: self.fetch_and_display_error_messages(error_message_grid, prefix), 2)
            scheduled_events['fetch_and_display_error_messages'] = self.error_fetch_interval

        else:
            print("No checkbox active. Stopping fetch and display.")
            # Cancel the scheduled fetching interval if both checkboxes are inactive
            if self.error_fetch_interval:
                self.error_fetch_interval.cancel()

    def fetch_and_display_error_messages(self, grid, prefix, initial_fetch=False):
        try:
            file_path = 'Error_Message.log'
            if not os.path.exists(file_path):
                print("Error_Message.log file not found.")
                return

            file_size = os.path.getsize(file_path)
            new_data_available = file_size > self.last_file_size
            self.last_file_size = file_size

            with open(file_path, 'r', buffering=8192) as file:
                # Read all lines from the file
                lines = file.readlines()

                # Filter messages based on the prefix
                if prefix is None:
                    filtered_lines = [line.strip() for line in lines]
                else:
                    filtered_lines = [line.strip() for line in lines if prefix in line]

                if new_data_available or initial_fetch:

                    new_messages = filtered_lines[-10:]  # Get the latest 10 messages
                    self.displayed_error_messages = new_messages + self.displayed_error_messages
                    self.displayed_error_messages = self.displayed_error_messages[:50]
                    self.error_display_index = len(new_messages)

                    # Update the UI with the latest messages
                    self.update_error_ui(grid, new_messages, prepend=True)
                else:
                    # When no new data, fetch the next batch of messages in reverse order
                    if self.error_display_index < len(filtered_lines):
                        next_batch = filtered_lines[self.error_display_index:self.error_display_index + 10]
                        self.error_display_index += 10
                        self.update_error_ui(grid, next_batch)

        except FileNotFoundError:
            print("Error_Message.log file not found.")

    def update_error_ui(self, grid, messages, prepend=False):
        # Add the messages to the UI
        for line in messages:
            error_label = TextInput(text=line, size_hint=(None, None), size=(2000, 30),
                                    background_color=(3, 3, 3, 1), readonly=True, halign='left')
            if prepend:
                grid.add_widget(error_label, index=len(grid.children))
            else:
                grid.add_widget(error_label)


    def show_tx_rx_command(self, hmi_active, machin_active):
        error_message_grid = self.root.ids.error_msg_grid
        error_message_grid.clear_widgets()
        self.displayed_messages = []
        self.last_fetched_index = 0
        self.last_file_size = 0

        if hmi_active and machin_active:
            prefix = None
        elif hmi_active:
            prefix = "HMI"
        elif machin_active:
            prefix = "Machine"
        else:
            prefix = None

        if hmi_active or machin_active:

            self.fetch_and_display_data(error_message_grid, prefix)

            if self.fetch_interval:
                self.fetch_interval.cancel()

            self.fetch_interval = Clock.schedule_interval(lambda dt: self.fetch_and_display_data(error_message_grid, prefix), 2)
            scheduled_events['fetch_and_display_data'] =self.fetch_interval
        else:
            print("No checkbox active. Stopping fetch and display.")

            if self.fetch_interval:
                self.fetch_interval.cancel()

    def fetch_and_display_data(self, grid, prefix):
        try:
            file_path = 'Tx_RX_Command.log'
            if not os.path.exists(file_path):
                print("Tx_RX_Command.log file not found.")
                return

            file_size = os.path.getsize(file_path)
            new_data_available = file_size > self.last_file_size
            self.last_file_size = file_size

            with open(file_path, 'r') as file:

                lines = file.readlines()

                if prefix is None:
                    filtered_lines = [line.strip() for line in lines]
                else:
                    filtered_lines = [line.strip() for line in lines if prefix in line]

                if new_data_available:

                    new_messages = filtered_lines[-10:]
                    self.displayed_messages = new_messages + self.displayed_messages
                    self.displayed_messages = self.displayed_messages[:50]

                    self.last_fetched_index = len(filtered_lines) - 10

                    self.update_ui(grid, new_messages, prepend=True)
                else:

                    if self.last_fetched_index > 0:
                        start_index = max(0, self.last_fetched_index - 10)
                        next_batch = filtered_lines[start_index:self.last_fetched_index]
                        self.last_fetched_index = start_index
                        self.update_ui(grid, next_batch)

        except FileNotFoundError:
            print("Tx_RX_Command.log file not found.")

    def update_ui(self, grid, messages, prepend=False):
        # Add the messages to the UI
        app= App.get_running_app()
        if app.title =='Main':
            for line in messages:
                error_label = TextInput(text=line, size_hint=(None, None), size=(2000, 30),
                                        background_color=(3, 3, 3, 1), readonly=True, halign='left')
                if prepend:
                    grid.add_widget(error_label, index=len(grid.children))
                else:
                    grid.add_widget(error_label)
            # print("Length of message:",len(messages))

    def update_batches(self, pending_batches):
        pending_batches_grid = self.root.ids.pending_batches_grid
        pending_batches_grid.clear_widgets()
        try:

            for batch in pending_batches:
                label_text = f"Record ID: {batch['ID']} - Batch ID:{batch['BatchID']} - Chemical: {batch['Chemical']}"
                button = Button(text=label_text, size_hint=(None, None), size=(400, 30),
                                color=(0, 0, 0, 3), background_color=(3, 3, 3, 1),valign='middle', halign='left',padding=10)
                button.bind(on_release=lambda _, current_batch=batch: (
                    self.root.BatchmetaData(current_batch),
                    self.on_chem_button_click(current_batch),
                    self.add_to_queue(current_batch['ID'])
                ))
                button.text_size =(400, 30)
                pending_batches_grid.add_widget(button)
        except Exception as e:
            print(f"unhandled exception:",e)

    def add_to_queue(self, record_id):
        self.global_queue=record_id

    def run_button_click(self):
        self.root.ids.run_button.md_bg_color = (0.3, 0.3, 0.3, 1)
        valve_no=batch.fetch_valveno_record_id(self.global_queue)
        valve_record_id=(self.global_queue,valve_no)
        if valve_no is not None:
            db_communication.dispense_chemical_list(valve_record_id)
            self.root.show_hmi_request_list()


    def on_chem_button_click(self, batch_data):
        self.root.ids.tank_pending_grid.clear_widgets()
        pending_batch_grid = self.root.ids.tank_pending_grid
        pending_batch_grid.cols = 1
        pending_batch_grid.spacing = 50
        pending_batch_grid.padding = 0
        batch_id= batch_data.get('BatchID')
        batch_name = batch_data.get('BatchName')
        chemical = batch_data.get('Chemical')

        batch_layout = GridLayout(cols=1, pos_hint={'center_x': 0.5, 'center_y': 1}, size_hint=(1, .1))
        label = Label(text=f'{batch_name} Data', size_hint=(None,None), size=(800,30),
                      pos_hint={'center_x': -.1, 'center_y': 0.5},font_size =17,bold=True)
        batch_layout.add_widget(label)
        batch_layout.padding=20

        pending_batch_grid.add_widget(batch_layout)

        full_batch_layout = self.batch()
        self.batch().pos_hint = {'center_x': 1, 'center_y': 0.5}

        pending_batch_grid.add_widget(full_batch_layout)

        if batch_id and chemical:

            data = batch_metadata.fetch_selected_batch_main(batch_id)

            full_batch_instance = full_batch_layout

            full_batch_instance.ids.batch_name.text = str(data[1])
            full_batch_instance.ids.fabric_weight.text = str(data[2])
            full_batch_instance.ids.mlr.text = str(data[3])
            full_batch_instance.ids.machin_no.text = str(data[4])
            full_batch_instance.ids.created_by.text = str(data[5])
            full_batch_instance.ids.created_date.text = str(data[6])

    def batch(self):
        return Batch()

    def add_stock(self):
        self.root.Add_stock()

    def Minus_stock(self):
        self.root.minus_stock()

    def delay_fn(self, fn_name):
        # Disable various buttons
        self.root.ids.chemical_button.disabled = True
        self.root.ids.batch_button.disabled = True
        self.root.ids.settings_button.disabled = True
        self.root.ids.report_button.disabled = True
        self.root.ids.tank_button.disabled = True
        self.root.ids.station_button.disabled = True
        self.root.ids.run_button.disabled = True
        self.root.ids.upload_button.disabled = True
        self.root.ids.open_button.disabled = True
        self.root.ids.hmi_button.disabled = True
        self.root.ids.chemical_Grid.clear_widgets()
        # self.root.ids.main_page.clear_widgets()
        Clock.schedule_once(lambda dt: getattr(self, fn_name)(), 0.6)

    def change_button_color(self, button):
        button.md_bg_color = (77/255, 199/255, 226/255, 1)

    def switch_to_main(self):
        Builder.unload_file('mainpage.kv')
        print("Unloaded main")
        # from main import MainApp
        MainApp.stop(self)
        MainApp().run()


    def switch_to_second(self):
        Builder.unload_file('mainpage.kv')
        print("Unloaded Main")
        MainApp.stop(self)
        from chemical import ChemicalApp
        ChemicalApp().run()


    def switch_to_third(self):

        Builder.unload_file('mainpage.kv')
        MainApp.stop(self)
        from Batch import BatchApp
        BatchApp().run()


    def switch_to_fourth(self):

        Builder.unload_file('mainpage.kv')
        MainApp.stop(self)
        from settings import generalApp
        generalApp().run()



    def switch_to_fifth(self):

        Builder.unload_file('mainpage.kv')
        MainApp.stop(self)
        from report import ReportApp
        ReportApp().run()




    def close_window(self):
        try:
            self.connection_port.disconnect()
            self.machine_connection.machin_disconnect()
            App.get_running_app().stop()
            Window.close()
        except Exception as e:
            print(f"Error during closing the window: {e}")

    def on_stop(self):
        self.connection_port.get_connection_status()
        self.machine_connection.get_machin_status()
        print("when leave the main")
        keyboard.unhook_all_hotkeys()
        self.unschedule_all()
        # self.cleanup()
    def on_leave(self):
        print(self.is_connected)

    def global_exception_handler(self, exctype, value, tb):
        if exctype == RecursionError:
            current_limit = sys.getrecursionlimit()
            new_limit = current_limit * 2
            sys.setrecursionlimit(new_limit)

        else:

            traceback.print_exception(exctype, value, tb)

    def unschedule_all(self):
        # Unschedule only the functions that were scheduled in schedule_functions
        for key, event in scheduled_events.items():
            Clock.unschedule(event)
        scheduled_events.clear()
        print("All scheduled functions unscheduled")

    def __del__(self):
        self.executor.shutdown()

if __name__ == '__main__':
    MainApp().run()
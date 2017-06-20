from os.path import expanduser, sep
import os
import ctypes
import shutil
import fnmatch
import thread
import time
import win32api
import win32con

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.config import Config

import wifiservice
import sharescripter
from wifiservice import WiFiService
from savingformwidget import SavingFormWidget
from xmlcreator import create_empty_xml_profile, edit_xml_profile, parse_xml_profile
from keycodes import get_key_normal_name, is_int, scan_key_name_pressed, all_keys_up
from bluetoothservice import BluetoothService
from keydb_simulator import set_mode

Builder.load_file("profiletab.kv")
Builder.load_file("savingform.kv")
PROFILE_PATH = ""
SELECTED_PROFILE = "Nothing Selected"
HOTSPOT_ENABLED = os.path.isfile("data/hotspot")


class RacePadServerWidget(BoxLayout):
    selected_profile = None
    wifi_service = None
    btn_ids = ['btn_1', 'btn_2', 'btn_3', 'btn_4', 'btn_5', 'btn_6', 'btn_7', 'btn_8', 'btn_l', 'btn_r', 'btn_u', 'btn_d', 'btn_x', 'game_name', 'game_path']

    def __init__(self, **kwargs):
        super(RacePadServerWidget, self).__init__(**kwargs)
        try:
            self.bluetooth_service = BluetoothService(PROFILE_PATH)
            thread.start_new(self.bluetooth_service.start_bluetooth_service, ())
        except IOError:
            connection_status_text = self.ids.connection_status
            connection_status_text.text = "Bluetooth Adapter is switched OFF or Not present"
        self.init_wifi_service()
        thread.start_new_thread(self.connection_monitor, ())
        os.system("netsh wlan stop hosted network")

    def init_wifi_service(self):
        self.wifi_service = WiFiService(PROFILE_PATH, self.ids.port_text_input.text)
        if wifiservice.check_wifi_availability():
            self.ids.wifi_adapter_status.text = "Wireless Adapter Status : WIFI Adapter Enabled"
            self.ids.listening_ip_addresses.text = "Listening IP Addresses : " + sharescripter.get_listening_ips()
            self.ids.listening_ip_addresses.disabled = False
            if ctypes.windll.shell32.IsUserAnAdmin() != 0:
                self.ids.hotspot_label.text = "Create Race Pad HotSpot"
                self.ids.hotspot_label.disabled = False
                self.ids.hotspot_switch.disabled = False
                self.ids.hotspot_repair.disabled = False
                if os.path.isfile("data/hotspot"):
                    self.ids.hotspot_switch.active = True
                    self.hotspot_switch_thread(self.ids.hotspot_switch, True)
                try:
                    key = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE, "Software\\Bits Blender\\Race Pad", 0, win32con.KEY_ALL_ACCESS)
                    data, typeId = win32api.RegQueryValueEx(key, "NetworkSetup")
                    if data[0] == '0':
                        self.repair_callback(None, "setting up network this will happen only once")
                        win32api.RegSetValueEx(key, "NetworkSetup", 0, win32con.REG_SZ, "1")
                    win32api.RegCloseKey(key)
                except:
                    self.repair_callback(None, "setting up network this will happen only once")
                thread.start_new(self.wifi_service.start_wifi_service, ())
            if not self.wifi_service.connected:
                self.ids.port_label.disabled = False
                self.ids.port_text_input.disabled = False
                self.ids.refresh_port.disabled = False

    def hotspot_switch_thread(self, switch_instance, value):
        thread.start_new(self.hotspot_switch_callback, (value, switch_instance))

    def hotspot_switch_callback(self, value, switch):
        if value:
            switch.disabled = True
            sharable_connections = sharescripter.sharable_connections_list()
            self.ids.connections_spinner.values = sharable_connections
            self.ids.connections_spinner.text = sharescripter.shared_connection(sharable_connections, self.ids.progress_bar, switch)
            self.ids.hotspot_share_label.disabled = False
            self.ids.connections_spinner.disabled = False
            os.system("netsh wlan start hosted network")
        else:
            os.system("netsh wlan stop hosted network")
            self.ids.hotspot_share_label.disabled = True
            self.ids.connections_spinner.disabled = True
            self.ids.connections_spinner.text = "select the connection to share"
        self.ids.listening_ip_addresses.text = "Listening IP Addresses : " + sharescripter.get_listening_ips()

    def connections_spinner_callback(self, instance, value):
        if value != "select the connection to share":
            thread.start_new(sharescripter.enable_sharing, (value,))

    def refresh_port_callback(self, instance):
        temp_obj = self.ids.port_text_input
        error_popup = Popup(title="Error", size_hint=[None, None], size=[400, 400])
        content = BoxLayout(orientation = "vertical")
        content.add_widget(Label(text="Port number should be in between 10000-60000\n\nchanging Port to default port number 55555",size_hint_y=0.9))
        btn = Button(text="Ok",size_hint_y=0.1)
        btn.bind(on_press=error_popup.dismiss)
        content.add_widget(btn)
        error_popup.content=content
        if len(temp_obj.text) == 5:
            try:
                int(temp_obj.text)
                self.wifi_service = None
                self.init_wifi_service()
            except ValueError:
                error_popup.open()
                temp_obj.text = "55555"
        else:
            error_popup.open()
            temp_obj.text = "55555"

    def profile_select_method(self, profile):
        global SELECTED_PROFILE, PROFILE_PATH
        SELECTED_PROFILE = profile.text
        self.selected_profile = SELECTED_PROFILE
        id_keys = self.ids.keys()
        for i in range(len(id_keys)):
            if id_keys[i] in self.btn_ids:
                btn_text = parse_xml_profile(PROFILE_PATH + sep + SELECTED_PROFILE + ".xml", id_keys[i])
                if btn_text is not None:
                    if is_int(btn_text):
                        btn_text = int(btn_text)
                        self.ids[id_keys[i]].text = get_key_normal_name(btn_text)
                    else:
                        self.ids[id_keys[i]].text = btn_text
                else:
                    self.ids[id_keys[i]].text = id_keys[i]

    def repair_callback(self, instance, title="Repairing HotSpot"):
        self.ids.hotspot_switch.active = False
        self.hotspot_switch_callback(None, False)
        repair_progress = Popup(title=title,  size_hint=[None, None], size=[500, 500], auto_dismiss=False)
        content = BoxLayout(orientation="vertical")
        content.add_widget(Label(text="Please don't add any network device while repairing"))
        prog_bar = ProgressBar()
        content.add_widget(prog_bar)
        action_label = Label(text="Please Wait....")
        content.add_widget(action_label)
        repair_progress.content = content
        repair_progress.open()
        thread.start_new(sharescripter.repair_hotspot, (repair_progress, prog_bar, action_label))

    def connection_monitor(self):
        connection_status_text = self.ids.connection_status
        device_name = self.ids.device_name
        device_address = self.ids.device_address
        adapter_status = self.ids.adapter_status
        service_status = self.ids.service_status
        mode = self.ids.press_mode
        while True:
            if not self.bluetooth_service.bluetooth_available:
                print("Bluetooth is Not Enabled")
                adapter_status.text = "Adapter Status: Bluetooth is Not Enabled or Not Available"
                device_name.disabled = True
                device_name.text = "Client Name: Unknown"
                device_address.disabled = True
                device_address.text = "Client Address: None"
                service_status.text = "Service Status: Dead Network Found. please enable the Bluetooth and restart"
                break
            else:
                adapter_status.text = "Adapter Status: Bluetooth Adapter Enabled"
                if self.bluetooth_service.discovered:
                    service_status.text = "Service Status: Ready"
                    if self.bluetooth_service.connected:
                        device_address.disabled = False
                        device_address.text = "Client Address: "+self.bluetooth_service.get_client_address()
                        device_name.disabled = False
                        device_name.text = "Client Name: "+self.bluetooth_service.get_client_name()
                        set_mode(mode.active)
                    else:
                        connection_status_text.text = "No Connection"
                        device_address.disabled = True
                        device_address.text = "Client Address: None"
                        device_name.disabled = True
                        device_name.text = "Client Name: Unknown"
            if self.bluetooth_service.connected or self.wifi_service.connected:
                connection_status_text.text = "Connected"
                if self.wifi_service.connected:
                    self.ids.port_text_input.disabled = True
                    self.ids.refresh_port.disabled = True
                    if Config.getboolean("kivy", "update_profiles"):
                        thread.start_new(self.wifi_service.update_profiles, ())
                if self.bluetooth_service.connected:
                    if Config.getboolean("kivy", "update_profiles"):
                        thread.start_new(self.bluetooth_service.update_profiles, ())
            else:
                connection_status_text.text = "No Connection"
                self.ids.port_text_input.disabled = False
                self.ids.refresh_port.disabled = False
            global HOTSPOT_ENABLED
            HOTSPOT_ENABLED = self.ids.hotspot_switch.active
            self.ids.listening_ip_addresses.text = "Listening IP Addresses : " + sharescripter.get_listening_ips()
            time.sleep(1)


class ProfileTabWidget(BoxLayout):
    profiles_list = ListProperty([])
    action_text = StringProperty("")
    saving_widget = None
    save_form = None
    selected_profile = None
    conform_message = None
    overwrite_warning = None

    def __init__(self, **kwargs):
        super(ProfileTabWidget, self).__init__(**kwargs)
        self.scan_profiles_method()

    def scan_profiles_method(self):
        global PROFILE_PATH
        self.action_text = "Scanning Profiles"
        self.profiles_list = []
        for profile in os.listdir(PROFILE_PATH):
            if fnmatch.fnmatch(profile, "*.xml"):
                profile = profile[0:len(profile) - 4]
                self.profiles_list.append(profile)
        self.action_text = "Scanning Profiles Completed"
        return self.profiles_list

    def add_profile(self):
        self.action_text = "Adding Profile"
        self.saving_widget = SavingFormWidget()
        create_empty_xml_profile("RacePadProfile", self.saving_widget.id_keys)
        save_profile_btn = self.saving_widget.ids.save_btn
        save_profile_btn.bind(on_press=self.on_press_save_profile_btn)
        self.save_form = Popup(content=self.saving_widget, title="Save Profile")
        self.save_form.bind(on_dismiss=prevent_close_on_esc)
        cancel_profile_btn = self.saving_widget.ids.cancel_btn
        cancel_profile_btn.bind(on_press=self.on_press_cancel_profile_btn)
        self.save_form.open()

    def on_press_save_profile_btn(self, *args):
        game_name = self.saving_widget.ids.game_name
        game_name_text = game_name.text
        if game_name_text == "":
            layout = BoxLayout(orientation="vertical")
            label = Label(text="Game Name shouldn't be empty")
            layout.add_widget(label)
            ok_btn = Button(text="OK", size_hint_y=None, size_y="25dp")
            layout.add_widget(ok_btn)
            error_dialogue = Popup(content=layout, size_hint=[None, None], size=[300, 300], title="Error")
            ok_btn.bind(on_press=error_dialogue.dismiss)
            error_dialogue.open()
        else:
            same_name_found = False
            for i in range(len(self.profiles_list)):
                if self.profiles_list[i] == game_name_text:
                    same_name_found = True
                    break
            if same_name_found:
                layout = BoxLayout(orientation="vertical")
                label1 = Label(text="Profile Name " + game_name_text + " already exists")
                label2 = Label(text="Do you want to overwrite it?")
                layout.add_widget(label1)
                layout.add_widget(label2)
                btn_layout = BoxLayout()
                ok_btn = Button(text="Yes", size_hint_y=None, size_y="25dp")
                btn_layout.add_widget(ok_btn)
                cancel_btn = Button(text="No", size_hint_y=None, size_y="25dp")
                btn_layout.add_widget(cancel_btn)
                layout.add_widget(btn_layout)
                self.overwrite_warning = Popup(content=layout, size_hint=[None, None], size=[300, 300],
                                               title="Warning!")
                cancel_btn.bind(on_press=self.overwrite_warning.dismiss)
                ok_btn.bind(on_press=self.on_press_overwrite)
                self.overwrite_warning.open()
            else:
                global PROFILE_PATH
                edit_xml_profile("game_name", game_name_text)
                edit_xml_profile("game_path", self.saving_widget.ids.game_path.text)
                os.rename("data/temp_profile.xml", "data/" + game_name_text + ".xml")
                shutil.copy("data/" + game_name_text + ".xml", PROFILE_PATH)
                os.remove("data/" + game_name_text + ".xml")
                self.save_form.dismiss()
                self.scan_profiles_method()
                self.action_text = game_name_text + " Profile added"
                Config.set("kivy", "update_profiles", 1)
                Config.write()

    def on_press_overwrite(self, instance):
        game_name_text = self.saving_widget.ids.game_name.text
        global PROFILE_PATH
        edit_xml_profile("game_name", game_name_text)
        edit_xml_profile("game_path", self.saving_widget.ids.game_path.text)
        os.rename("data/temp_profile.xml", "data/" + game_name_text + ".xml")
        shutil.copy("data/" + game_name_text + ".xml", PROFILE_PATH)
        os.remove("data/" + game_name_text + ".xml")
        self.save_form.dismiss()
        self.overwrite_warning.dismiss()
        self.scan_profiles_method()
        self.action_text = game_name_text + " Profile overwritten"
        Config.set("kivy", "update_profiles", 1)
        Config.write()

    def on_press_cancel_profile_btn(self, *args):
        self.action_text = "Saving Profile cancelled"
        self.save_form.dismiss()

    def edit_profile(self):
        global SELECTED_PROFILE, PROFILE_PATH
        if SELECTED_PROFILE == "Nothing Selected":
            self.action_text = SELECTED_PROFILE + " to Edit"
        else:
            self.action_text = SELECTED_PROFILE + " is Editing"
            shutil.copy(PROFILE_PATH + sep + SELECTED_PROFILE + ".xml", "data/temp_profile.xml")
            self.saving_widget = SavingFormWidget()
            for i in range(len(self.saving_widget.id_keys)):
                btn_text = parse_xml_profile("data/temp_profile.xml", self.saving_widget.id_keys[i])
                if btn_text is not None:
                    if is_int(btn_text):
                        btn_text = int(btn_text)
                        self.saving_widget.ids[self.saving_widget.id_keys[i]].text = get_key_normal_name(btn_text)
                    else:
                        self.saving_widget.ids[self.saving_widget.id_keys[i]].text = btn_text
            self.save_form = Popup(content=self.saving_widget, title="Save Profile")
            self.save_form.bind(on_dismiss=prevent_close_on_esc)
            cancel_profile_btn = self.saving_widget.ids.cancel_btn
            cancel_profile_btn.bind(on_press=self.on_press_cancel_profile_btn)
            edit_save_btn = self.saving_widget.ids.save_btn
            edit_save_btn.bind(on_press=self.on_press_edit_save_btn)
            self.save_form.open()
            self.action_text = SELECTED_PROFILE + " is Edited"

    def on_press_edit_save_btn(self, args):
        global SELECTED_PROFILE, PROFILE_PATH
        game_name = self.saving_widget.ids.game_name
        game_name_text = game_name.text
        if game_name_text == "":
            layout = BoxLayout(orientation="vertical")
            label = Label(text="Game Name shouldn't be empty")
            layout.add_widget(label)
            ok_btn = Button(text="OK", size_hint_y=None, size_y="25dp")
            layout.add_widget(ok_btn)
            error_dialogue = Popup(content=layout, size_hint=[None, None], size=[300, 300], title="Error")
            ok_btn.bind(on_press=error_dialogue.dismiss)
            error_dialogue.open()
        else:
            os.remove(PROFILE_PATH + sep + SELECTED_PROFILE + ".xml")
            edit_xml_profile("game_name", game_name_text)
            edit_xml_profile("game_path", self.saving_widget.ids.game_path.text)
            os.rename("data/temp_profile.xml", "data/" + game_name_text + ".xml")
            shutil.copy("data/" + game_name_text + ".xml", PROFILE_PATH)
            os.remove("data/" + game_name_text + ".xml")
            self.save_form.dismiss()
            self.scan_profiles_method()
            self.action_text = game_name_text + " Profile updated"
            SELECTED_PROFILE = "Nothing Selected"
            Config.set("kivy", "update_profiles", 1)
            Config.write()

    def delete_profile(self):
        global SELECTED_PROFILE
        self.selected_profile = SELECTED_PROFILE
        if not (self.selected_profile == "Nothing Selected"):
            self.action_text = "Waiting for Conformation to delete " + self.selected_profile
            ok_btn = Button(text="Yes", size_hint_y=None, size_y="25dp")
            cancel_btn = Button(text="No", size_hint_y=None, size_y="25dp")
            message = Label(text="Are you sure to Delete Profile " + self.selected_profile + "?")
            message.text_size = message.size
            main_layout = BoxLayout(orientation="vertical")
            main_layout.add_widget(message)
            btn_layout = BoxLayout()
            btn_layout.add_widget(ok_btn)
            btn_layout.add_widget(cancel_btn)
            main_layout.add_widget(btn_layout)
            self.conform_message = Popup(auto_dismiss=False, content=main_layout, title="Conform Deletion",
                                         size_hint=[None, None], size=[400, 400])
            ok_btn.bind(on_press=self.delete_profile_after_conformation)
            cancel_btn.bind(on_press=self.delete_conform_message_dismiss)
            self.conform_message.open()
        else:
            self.action_text = self.selected_profile + " to Delete"

    def delete_conform_message_dismiss(self, *args):
        self.conform_message.dismiss()
        self.action_text = self.selected_profile + " deletion cancelled"

    def delete_profile_after_conformation(self, *args):
        global PROFILE_PATH, SELECTED_PROFILE
        file_path = PROFILE_PATH + sep + self.selected_profile + ".xml"
        os.remove(file_path)
        self.scan_profiles_method()
        self.conform_message.dismiss()
        self.action_text = self.selected_profile + " Deleted"
        Config.set("kivy", "update_profiles", 1)
        Config.write()
        self.selected_profile = "Nothing Selected"
        SELECTED_PROFILE = self.selected_profile


class RacePadServerApp(App):
    def build(self):
        self.icon = "data/race_pad.ico"
        return RacePadServerWidget()

    def on_stop(self):
        print "Closing"
        os.system("netsh wlan stop hosted network")
        global HOTSPOT_ENABLED
        if HOTSPOT_ENABLED:
            open("data/hotspot","w").close()
        else:
            if os.path.isfile("data/hotspot"):
                os.remove("data/hotspot")


def prevent_close_on_esc(instance):
    if scan_key_name_pressed() == "VK_ESCAPE":
        return True
    return False


def make_profiles_directory():
    global PROFILE_PATH
    user_path = expanduser("~") + sep + "Documents"
    PROFILE_PATH = user_path + sep + "RacePadServer" + sep + "Profiles"
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)


def make_config_directory():
    user_path = expanduser("~")
    config_path = user_path + sep + ".kivy"
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    shutil.copy("config.ini", config_path)

if __name__ == "__main__":
    count = 0
    os.system("taskkill /im RacePadServer.exe")
    task_list = os.popen("tasklist").read()
    count = task_list.count("RacePadServer2.1")
    if count < 2:
        all_keys_up()
        make_config_directory()
        make_profiles_directory()
        Config.set("kivy", "update_profiles", 0)
        Config.write()
        RacePadServerApp().run()

import win32api
import time
import thread

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.filebrowser import FileBrowser
from kivy.uix.label import Label

from keycodes import scan_key_code_pressed, get_key_normal_name
from xmlcreator import edit_xml_profile


class SavingFormWidget(BoxLayout):
    pop_filebrowser = None
    popup_inf = None
    game_path_text = StringProperty("")
    id_values = None
    id_keys = None
    key_detected = StringProperty("")
    message_text = StringProperty("Press on the button and then click on the key which you like to Assign")

    def __init__(self, **kwargs):
        super(SavingFormWidget, self).__init__(**kwargs)
        self.id_values = self.ids.values()
        self.id_keys = self.ids.keys()
        self.popup_inf = Popup(content=Label(text="Waiting for Key!!!"), title="Information", size_hint=[None, None],
                               size=[300, 300])

    def file_browser(self):
        filebrowser = FileBrowser(select_string='Select')
        filebrowser.bind(on_success=self._fbrowser_sucess, on_canceled=self._fbrowser_cancel)
        self.pop_filebrowser = Popup(content=filebrowser, title="pick a file")
        self.pop_filebrowser.open()

    def _fbrowser_sucess(self, instance):
        txt = str(instance.selection)
        txt = txt[3:len(txt) - 2]
        self.game_path_text = txt
        self.pop_filebrowser.dismiss()

    def _fbrowser_cancel(self, instance):
        self.pop_filebrowser.dismiss()

    def scan_key_board(self, instance):
        print("Waiting for key press.........")
        self.message_text = "Waiting....... \npress the key now \nTo Assign"
        self.popup_inf.open()
        thread.start_new(self.assign_keycode, (instance,))

    def assign_keycode(self, instance):
        instance = str(instance)
        i = None
        for i in range(len(self.ids)):
            if instance == str(self.id_values[i]):
                break
        btn = self.ids[self.id_keys[i]]
        temp = btn.background_normal
        btn.background_normal = btn.background_down
        while win32api.GetAsyncKeyState(1) != 0:
            time.sleep(0.1)
        key_code = scan_key_code_pressed()
        edit_xml_profile(self.id_keys[i], str(key_code))
        key_code = get_key_normal_name(key_code)
        btn.text = key_code
        btn.background_normal = temp
        self.message_text = "Press on the button and then click on the key which you like to Assign"
        self.popup_inf.dismiss()

from bluetooth import *
from os.path import sep
from keydb_simulator import key_code_parser
from kivy.config import Config
import thread
import fnmatch
import os
import time


class BluetoothService:
    server_sock = None
    client_sock = None
    client_info = None
    uuid = None
    connected = None
    profile_path = None
    devices = None
    discovered = None
    bluetooth_available = None

    def __init__(self, profile_path):
        self.discovered = False
        thread.start_new_thread(self.get_devices, ())
        self.uuid = "44361e26-3245-415a-8085-5f8944ef9b78"
        self.connected = False
        self.profile_path = profile_path
        self.bluetooth_available = True

    def get_devices(self):
        try:
            self.devices = discover_devices(duration=1, lookup_names=True, lookup_class=False)
            self.discovered = True
        except IOError:
            self.bluetooth_available = False
            print "Bluetooth Adapter is switched OFF or Not present"

    def start_bluetooth_service(self):
        while True:
            self.server_sock = BluetoothSocket(RFCOMM)
            self.server_sock.bind(("", PORT_ANY))
            self.bluetooth_available = True
            self.server_sock.listen(1)
            self.server_sock.getsockname()[1]
            advertise_service(self.server_sock,
                              "RacePadServer",
                              service_id=self.uuid,
                              service_classes=[self.uuid, SERIAL_PORT_CLASS],
                              profiles=[SERIAL_PORT_PROFILE])
            print "Started Service"
            self.client_sock, self.client_info = self.server_sock.accept()
            self.connected = True
            profile_count = 0
            for profile in os.listdir(self.profile_path):
                if fnmatch.fnmatch(profile, "*.xml"):
                    profile_count += 1
            self.client_sock.send(str(profile_count))
            time.sleep(0.5)
            for profile in os.listdir(self.profile_path):
                if fnmatch.fnmatch(profile, "*.xml"):
                    self.client_sock.send(profile)
                    xml_file = open(self.profile_path + sep + profile, "rb")
                    file_bytes = xml_file.read()
                    xml_file.close()
                    self.client_sock.send(file_bytes)
                    time.sleep(0.5)
            try:
                while True:
                    data = self.client_sock.recv(1024)
                    if len(data) == 0:
                        break
                    codes = data.split('~')
                    for code in codes:
                        key_code_parser(code)
            except IOError:
                pass

            self.connected = False
            print("disconnected")
            self.client_sock.close()
            self.server_sock.close()

    def update_profiles(self):
        Config.set("kivy", "update_profiles", 0)
        Config.write()
        profile_count = 0
        for profile in os.listdir(self.profile_path):
            if fnmatch.fnmatch(profile, "*.xml"):
                profile_count += 1
        self.client_sock.send(str(profile_count))
        print "updating"
        time.sleep(0.5)
        for profile in os.listdir(self.profile_path):
            if fnmatch.fnmatch(profile, "*.xml"):
                self.client_sock.send(profile)
                xml_file = open(self.profile_path + sep + profile, "rb")
                file_bytes = xml_file.read()
                xml_file.close()
                self.client_sock.send(file_bytes)
                time.sleep(0.5)


    def connection_status(self):
        return self.connected

    def get_client_name(self):
        if self.connected and self.discovered:
            for address, name in self.devices:
                if address == self.client_info[0]:
                    return name
            return "UnKnown"
        return None

    def get_client_address(self):
        if self.connected and self.discovered:
            return self.client_info[0]
        return None

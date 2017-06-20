import socket
from os.path import sep
from keydb_simulator import key_code_parser
import fnmatch
import os
import time
import subprocess
from kivy.config import Config

class WiFiService:
    server_sock = None
    client_sock = None
    client_addr = None
    connected = None
    profile_path = None
    wifi_available = None

    def __init__(self, profile_path, port):
        self.connected = False
        self.profile_path = profile_path
        self.wifi_available = check_wifi_availability()
        self.port = port
        self.client_addr = None

    def start_wifi_service(self):
        while True:
            if self.wifi_available:
                self.server_sock = socket.socket()
                self.server_sock.bind(("", int(self.port)))
                self.server_sock.listen(1)
                print "WIFI Started Service"
                self.client_sock, self.client_addr = self.server_sock.accept()
                self.connected = True
                print self.client_addr
                self.client_sock.send("Successfully Connected to RacePadServer".center(1024, '\''))
                profile_count = 0
                for profile in os.listdir(self.profile_path):
                    if fnmatch.fnmatch(profile, "*.xml"):
                        profile_count += 1
                self.client_sock.send(str(profile_count).center(1024, '\''))
                time.sleep(0.2)
                for profile in os.listdir(self.profile_path):
                    if fnmatch.fnmatch(profile, "*.xml"):
                        try:
                            send = self.client_sock.send(profile.center(1024, '\''))
                        except:
                            break
                        xml_file = open(self.profile_path + sep + profile, "rb")
                        file_bytes = xml_file.read()
                        xml_file.close()
                        self.client_sock.send(file_bytes.center(1024, '\''))
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
            
    def connection_status(self):
        return self.connected

    def get_client_address(self):
        if self.connected:
            return self.client_addr
        return None

    def update_profiles(self):
        Config.set("kivy", "update_profiles", 0)
        Config.write()
        profile_count = 0
        for profile in os.listdir(self.profile_path):
            if fnmatch.fnmatch(profile, "*.xml"):
                profile_count += 1
        self.client_sock.send(str(profile_count).center(1024, '\''))
        print "updating"
        time.sleep(0.2)
        print(profile_count)
        for profile in os.listdir(self.profile_path):
            if fnmatch.fnmatch(profile, "*.xml"):
                try:
                    self.client_sock.send(profile.center(1024, '\''))
                except:
                    break
                xml_file = open(self.profile_path + sep + profile, "rb")
                file_bytes = xml_file.read()
                xml_file.close()
                self.client_sock.send(file_bytes.center(1024, '\''))
                print profile+" Sending Successs"
                time.sleep(0.5)
        print "updated"


def check_wifi_availability():
        output = subprocess.check_output("netsh wlan show drivers", shell=True)
        if len(output) > 50:
            return True
        else:
            return False


import subprocess
import os
import time


def get_listening_ips():
    ips = []
    output = subprocess.check_output("ipconfig", shell=True)
    beg = 0
    end = len(output)
    ip_text = "IPv4 Address. . . . . . . . . . . :"
    while True:
        pos = output.find(ip_text, beg, end)
        ip = ""
        if pos == -1:
            break
        beg = pos+len(ip_text)+1
        while output[beg] != "\n":
            ip += output[beg]
            beg += 1
        ips.append(ip)
    ip = ""
    if len(ips) == 0:
        return "No Active Connections Found"
    for i in ips:
        ip += i.strip()+" / "
    ip = ip[0:len(ip)-2]
    return ip


def sharable_connections_list():
    sharable_connections = []
    subprocess.check_output("powershell set-executionpolicy remotesigned")
    script = open("data/script.ps1", "w")
    script.write("$m = New-Object -ComObject HNetCfg.HNetShare\n")
    script.write("$m.EnumEveryConnection |% { $m.NetConnectionProps.Invoke($_) }\n")
    script.close()
    output = subprocess.check_output(["powershell", "-file", "data/script.ps1"], shell=True)
    name_txt = "Name            :"
    beg = 0
    end = len(output)
    while True:
        ip = ""
        pos = output.find(name_txt, beg, end)
        if pos == -1:
            break
        beg = pos+len(name_txt)+1
        while output[beg] != "\n":
            ip += output[beg]
            beg += 1
        ip = ip[0:len(ip)-1]
        sharable_connections.append(ip)
    return sharable_connections


def shared_connection(sharable_connections, prog_bar, switch):
    prog_bar.disabled = False
    prog_bar.max = len(sharable_connections)
    i = 0
    for connection in sharable_connections:
        i += 1
        prog_bar.value = i
        script = open("data/script.ps1", "w")
        script.write("$m = New-Object -ComObject HNetCfg.HNetShare\n")
        script.write("$m.EnumEveryConnection |% { $m.NetConnectionProps.Invoke($_) }\n")
        script.write("$c = $m.EnumEveryConnection |? { $m.NetConnectionProps.Invoke($_).Name -eq \""+connection+"\" }\n")
        script.write("$config = $m.INetSharingConfigurationForINetConnection.Invoke($c)\n")
        script.write("Write-Output $config.SharingEnabled\n")
        script.close()
        subprocess.check_output("powershell set-executionpolicy remotesigned")
        output = subprocess.check_output(["powershell", "-file", "data/script.ps1"], shell=True)
        output = output.strip()
        output= output[len(output)-8:len(output)]
        output = output.strip()
        if output == "True":
            prog_bar.value = 0
            prog_bar.disabled = True
            switch.disabled = False
            return connection
    prog_bar.value = 0
    prog_bar.disabled = True
    switch.disabled = False
    return "select the connection to share"


def enable_sharing(connection_name, disable_all=False):
    subprocess.check_output("powershell set-executionpolicy remotesigned")
    for connection in sharable_connections_list():
        script = open("data/script.ps1", "w")
        script.write("$m = New-Object -ComObject HNetCfg.HNetShare\n")
        script.write("$m.EnumEveryConnection |% { $m.NetConnectionProps.Invoke($_) }\n")
        script.write("$c = $m.EnumEveryConnection |? { $m.NetConnectionProps.Invoke($_).Name -eq \""+connection+"\" }\n")
        script.write("$config = $m.INetSharingConfigurationForINetConnection.Invoke($c)\n")
        script.write("$config.DisableSharing()\n")
        script.close()
        subprocess.check_output(["powershell", "-file", "data/script.ps1"], shell=True)
    if disable_all:
        print "Resetted sucessfully"
        return
    script = open("data/script.ps1", "w")
    script.write("$m = New-Object -ComObject HNetCfg.HNetShare\n")
    script.write("$m.EnumEveryConnection |% { $m.NetConnectionProps.Invoke($_) }\n")
    script.write("$c = $m.EnumEveryConnection |? { $m.NetConnectionProps.Invoke($_).Name -eq \""+connection_name+"\" }\n")
    script.write("$config = $m.INetSharingConfigurationForINetConnection.Invoke($c)\n")
    script.write("$config.EnableSharing(0)\n")
    script.close()
    subprocess.check_output(["powershell", "-file", "data/script.ps1"], shell=True)
    script = open("data/script.ps1", "w")
    script.write("$m = New-Object -ComObject HNetCfg.HNetShare\n")
    script.write("$m.EnumEveryConnection |% { $m.NetConnectionProps.Invoke($_) }\n")
    script.write("$c = $m.EnumEveryConnection |? { $m.NetConnectionProps.Invoke($_).Name -eq \"Race Pad Network\" }\n")
    script.write("$config = $m.INetSharingConfigurationForINetConnection.Invoke($c)\n")
    script.write("$config.EnableSharing(1)\n")
    script.close()
    subprocess.check_output(["powershell", "-file", "data/script.ps1"], shell=True)


def repair_hotspot(popup_dialog, prog_bar, action_label):
    prog_bar.max = 8
    prog_bar.value = 0
    action_label.text = "Stopping Race Pad HotSpot service"
    os.system("netsh wlan stop hosted network")
    prog_bar.value = 1
    action_label.text = "Resetting Race Pad HotSpot network configuration"
    os.system("netsh wlan set hostednetwork mode=allow ssid=RacePadHotSpot key=h1a2r3d4")
    prog_bar.value = 2
    action_label.text = "scanning sharable connections"
    adp_list1 = sharable_connections_list()
    prog_bar.value = 3
    action_label.text = "Starting Race Pad HotSpot"
    os.system("netsh wlan start hosted network")
    time.sleep(0.5)
    prog_bar.value = 4
    action_label.text = "Scanning current sharable connections"
    adp_list2 = sharable_connections_list()
    prog_bar.value = 5
    action_label.text = "Searching corrupted data"
    for item in adp_list2:
        if item not in adp_list1:
            break
    prog_bar.value = 6
    action_label.text = "making corrections"
    os.system("netsh interface set interface name = \""+item+"\" newname=\"Race Pad Network\"")
    prog_bar.value = 7
    action_label.text = "resetting sharing options"
    enable_sharing(None, True)
    prog_bar.value = 8
    os.system("netsh wlan stop hosted network")
    popup_dialog.dismiss()

if __name__ == "__main__":
    print(get_listening_ips())
    list1 = sharable_connections_list()
    for str1 in list1:
        print(str1)
    print shared_connection()


$m = New-Object -ComObject HNetCfg.HNetShare
$m.EnumEveryConnection |% { $m.NetConnectionProps.Invoke($_) }
$c = $m.EnumEveryConnection |? { $m.NetConnectionProps.Invoke($_).Name -eq "Race Pad Network" }
$config = $m.INetSharingConfigurationForINetConnection.Invoke($c)
$config.EnableSharing(1)

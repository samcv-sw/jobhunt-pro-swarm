Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c py -3.12 """ & WshShell.CurrentDirectory & "\scratch\start_server.py""", 0, False

param([int]$Mypid)
$bots = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { 
    $_.ProcessId -ne $Mypid -and $_.CommandLine -match "run_tg_local|telegram_bot"
}
foreach ($b in $bots) {
    taskkill /PID $b.ProcessId /F 2>$null
    Write-Output "Killed stale bot PID $($b.ProcessId)"
}

$TOKEN = '7e7ad272cc2d4470e8078fca29dfacf301fb01fe'

Add-Type -AssemblyName System.Net.Http

# Test username variations
foreach ($username in @('jhfguf', 'JHFGUF', 'Jhfguf')) {
    $c = New-Object System.Net.Http.HttpClient
    $c.DefaultRequestHeaders.Add('Authorization', "Token $TOKEN")
    $r = $c.GetAsync("https://www.pythonanywhere.com/api/v0/user/$username/").Result
    Write-Host "User '$username' HTTP: $([int]$r.StatusCode) => $($r.Content.ReadAsStringAsync().Result.Substring(0,100))"
    $c.Dispose()
}

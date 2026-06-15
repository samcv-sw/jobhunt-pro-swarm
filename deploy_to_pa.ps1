$TOKEN = '7e7ad272cc2d4470e8078fca29dfacf301fb01fe'
$USERNAME = 'JHFGUF'
$LOCAL_ROOT = 'c:\Users\samde\Desktop\cv sam new ma3 kimi'

Add-Type -AssemblyName System.Net.Http

function Upload-File($localPath, $paAbsPath) {
    # URL: /api/v0/user/JHFGUF/files/path/home/JHFGUF/jobhunt/...
    $url = "https://www.pythonanywhere.com/api/v0/user/$USERNAME/files/path$paAbsPath"
    
    $handler = New-Object System.Net.Http.HttpClientHandler
    $client = New-Object System.Net.Http.HttpClient($handler)
    $client.DefaultRequestHeaders.Add('Authorization', "Token $TOKEN")
    $client.Timeout = [System.TimeSpan]::FromMinutes(5)
    
    $fileBytes = [System.IO.File]::ReadAllBytes($localPath)
    $fileName = [System.IO.Path]::GetFileName($localPath)
    $fileSize = $fileBytes.Length
    Write-Host "  Uploading $fileName ($fileSize bytes) => $paAbsPath"
    
    $form = New-Object System.Net.Http.MultipartFormDataContent
    $byteContent = New-Object System.Net.Http.ByteArrayContent -ArgumentList (,$fileBytes)
    $byteContent.Headers.Add('Content-Type', 'application/octet-stream')
    $form.Add($byteContent, 'content', $fileName)
    
    try {
        $response = $client.PostAsync($url, $form).GetAwaiter().GetResult()
        $statusCode = [int]$response.StatusCode
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if ($statusCode -ge 200 -and $statusCode -lt 300) {
            Write-Host "  OK  HTTP $statusCode"
            return $true
        } else {
            Write-Host "  ERR HTTP $statusCode : $($body.Substring(0, [Math]::Min(200, $body.Length)))"
            return $false
        }
    } catch {
        Write-Host "  EXC: $_"
        return $false
    } finally {
        $form.Dispose()
        $client.Dispose()
        $handler.Dispose()
    }
}

Write-Host ""
Write-Host "===================================================="
Write-Host "  JobHunt Pro -> PythonAnywhere Deploy (JHFGUF)"
Write-Host "===================================================="
Write-Host ""

$remoteBase = "/home/$USERNAME/jobhunt"
$files = @(
    @{ local = "$LOCAL_ROOT\web\templates\blog.html";     remote = "$remoteBase/web/templates/blog.html" },
    @{ local = "$LOCAL_ROOT\web\templates\faq.html";      remote = "$remoteBase/web/templates/faq.html" },
    @{ local = "$LOCAL_ROOT\web\templates\login.html";    remote = "$remoteBase/web/templates/login.html" },
    @{ local = "$LOCAL_ROOT\web\templates\register.html"; remote = "$remoteBase/web/templates/register.html" },
    @{ local = "$LOCAL_ROOT\web\app_v2.py";               remote = "$remoteBase/web/app_v2.py" }
)

$ok = 0
$fail = 0
foreach ($f in $files) {
    if (Test-Path $f.local) {
        $result = Upload-File $f.local $f.remote
        if ($result) { $ok++ } else { $fail++ }
    } else {
        Write-Host "  NOT FOUND: $($f.local)"
        $fail++
    }
    Write-Host ""
}

Write-Host "Upload results: $ok OK, $fail failed"
Write-Host ""
Write-Host "Reloading webapp..."
$reloadHandler = New-Object System.Net.Http.HttpClientHandler
$reloadClient = New-Object System.Net.Http.HttpClient($reloadHandler)
$reloadClient.DefaultRequestHeaders.Add('Authorization', "Token $TOKEN")
$reloadUrl = "https://www.pythonanywhere.com/api/v0/user/$USERNAME/webapps/jhfguf.pythonanywhere.com/reload/"
$reloadResp = $reloadClient.PostAsync($reloadUrl, (New-Object System.Net.Http.StringContent(''))).GetAwaiter().GetResult()
$reloadCode = [int]$reloadResp.StatusCode
$reloadBody = $reloadResp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
$reloadClient.Dispose()
$reloadHandler.Dispose()
Write-Host "Reload HTTP $reloadCode : $reloadBody"

Write-Host ""
Write-Host "===================================================="
Write-Host "  Done! https://jhfguf.pythonanywhere.com"
Write-Host "===================================================="

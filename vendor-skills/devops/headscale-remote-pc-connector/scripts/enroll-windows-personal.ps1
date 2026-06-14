param(
  [Parameter(Mandatory=$true)] [string]$TargetKey,
  [Parameter(Mandatory=$true)] [string]$AgentPubKey,
  [string]$Hostname = $env:COMPUTERNAME,
  [string]$LoginServer = 'https://vpn.andigital.ru'
)

$ErrorActionPreference = 'Stop'

function New-RandomPassword {
  -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 28 | ForEach-Object {[char]$_})
}

function Ensure-LocalUser {
  param(
    [Parameter(Mandatory=$true)] [string]$Name,
    [bool]$Admin = $false
  )
  $user = Get-LocalUser -Name $Name -ErrorAction SilentlyContinue
  if (-not $user) {
    $pw = New-RandomPassword
    New-LocalUser -Name $Name -Password (ConvertTo-SecureString $pw -AsPlainText -Force) `
      -PasswordNeverExpires -AccountNeverExpires | Out-Null
  }
  Enable-LocalUser -Name $Name
  if ($Admin) {
    Add-LocalGroupMember -Group 'Администраторы' -Member $Name -ErrorAction SilentlyContinue
    Add-LocalGroupMember -Group 'Administrators' -Member $Name -ErrorAction SilentlyContinue
  }
}

function Ensure-UserAuthorizedKey {
  param(
    [Parameter(Mandatory=$true)] [string]$UserName,
    [Parameter(Mandatory=$true)] [string]$PubKey
  )
  $profile = Join-Path 'C:\Users' $UserName
  $sshDir = Join-Path $profile '.ssh'
  $auth = Join-Path $sshDir 'authorized_keys'
  New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
  Set-Content -Path $auth -Value $PubKey -Encoding ascii
  icacls $sshDir /inheritance:r | Out-Null
  icacls $sshDir /grant "$($UserName):(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
  icacls $auth /inheritance:r | Out-Null
  icacls $auth /grant "$($UserName):F" 'SYSTEM:F' | Out-Null
}

function Ensure-AdministratorsAuthorizedKey {
  param([Parameter(Mandatory=$true)] [string]$PubKey)
  $ak = 'C:\ProgramData\ssh\administrators_authorized_keys'
  New-Item -ItemType Directory -Path 'C:\ProgramData\ssh' -Force | Out-Null
  Set-Content -Path $ak -Value $PubKey -Encoding ascii
  icacls $ak /inheritance:r | Out-Null
  icacls $ak /grant 'SYSTEM:F' '*S-1-5-32-544:F' | Out-Null
}

# Install Tailscale if missing
$tailscaleExe = 'C:\Program Files\Tailscale\tailscale.exe'
if (-not (Test-Path $tailscaleExe)) {
  winget install --id Tailscale.Tailscale --accept-source-agreements --accept-package-agreements --silent
}

# Join personal Headscale mesh
& $tailscaleExe up `
  --login-server $LoginServer `
  --authkey $TargetKey `
  --advertise-tags=tag:personal-target `
  --accept-dns=true `
  --unattended `
  --hostname=$Hostname `
  --shields-up=false

# Install/OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

if (-not (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' `
    -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
}
Set-NetFirewallRule -Name OpenSSH-Server-In-TCP -Profile Any -Enabled True -Action Allow

# Two SSH roles
Ensure-LocalUser -Name 'codex' -Admin:$false
Ensure-LocalUser -Name 'codexadmin' -Admin:$true
Ensure-UserAuthorizedKey -UserName 'codex' -PubKey $AgentPubKey
Ensure-AdministratorsAuthorizedKey -PubKey $AgentPubKey

# Connector watchdog
$base = 'C:\ProgramData\CodexConnector'
New-Item -ItemType Directory -Path $base -Force | Out-Null
$watchdog = Join-Path $base 'Ensure-ConnectorRouting.ps1'
$watchdogContent = @'
$ErrorActionPreference = 'SilentlyContinue'
$log = 'C:\ProgramData\CodexConnector\connector-watchdog.log'
while ($true) {
  Start-Service Tailscale 2>$null
  Start-Service sshd 2>$null
  Enable-NetFirewallRule -Name OpenSSH-Server-In-TCP 2>$null
  Set-NetFirewallRule -Name OpenSSH-Server-In-TCP -Profile Any -Enabled True -Action Allow 2>$null
  Set-NetIPInterface -InterfaceAlias 'Tailscale' -AddressFamily IPv4 -InterfaceMetric 1 2>$null
  $am = Get-NetIPInterface -InterfaceAlias 'AmneziaVPN' -ErrorAction SilentlyContinue
  if ($am) {
    Set-NetIPInterface -InterfaceAlias 'AmneziaVPN' -AddressFamily IPv4 -InterfaceMetric 5 -IgnoreDefaultRoutes Disabled 2>$null
    Set-NetIPInterface -InterfaceAlias 'AmneziaVPN' -AddressFamily IPv6 -InterfaceMetric 5 -IgnoreDefaultRoutes Disabled 2>$null
    Set-NetIPInterface -InterfaceAlias 'Broadband Connection' -AddressFamily IPv4 -InterfaceMetric 35 2>$null
  }
  "$(Get-Date -Format s) ok tailscale=1 sshd=1 amnezia=$([bool]$am)" | Add-Content $log
  Start-Sleep -Seconds 5
}
'@
Set-Content -Path $watchdog -Value $watchdogContent -Encoding UTF8

$taskCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$watchdog`""
schtasks /Create /TN CodexConnectorWatchdog /SC ONSTART /RU SYSTEM /RL HIGHEST /TR $taskCmd /F | Out-Null
schtasks /Run /TN CodexConnectorWatchdog | Out-Null

# Optional Amnezia GUI autostart if installed
$amneziaExe = 'C:\Program Files\AmneziaVPN\AmneziaVPN.exe'
if (Test-Path $amneziaExe) {
  schtasks /Create /TN CodexStartAmneziaAtUserLogon /SC ONLOGON /RL HIGHEST /TR "`"$amneziaExe`"" /F | Out-Null
}

Write-Host 'OK: personal connector installed. Roles: codex (regular), codexadmin (admin).'
Write-Host 'Check from agent server: ssh codex@' $Hostname 'hostname'
Write-Host 'Admin check from agent server: ssh codexadmin@' $Hostname 'hostname'

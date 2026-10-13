$ErrorActionPreference = "SilentlyContinue"
$log = "E:\LLM\try\minidrama\保洁\_recycle_result.txt"
$out = @()
# ① 先记录清空前空间
$u = Get-PSDrive D
$out += "清空前可用: " + [math]::Round($u.Free/1GB, 2) + " GB"
# ② 用 Shell.Application 清空D 盘回收站（正规 API，会走系统流程）
$shell = New-Object -ComObject Shell.Application
$rb = $shell.Namespace(0xA)
$count = $rb.Items().Count
$out += "回收站条目数: $count"
$rb.Items() | ForEach-Object { Remove-Item $_.Path -Force -Recurse -ErrorAction SilentlyContinue }
#③ 传统 API 清空（D 盘）
Clear-RecycleBin -DriveLetter D -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
$u2 = Get-PSDrive D
$out += "清空后可用: " + [math]::Round($u2.Free/1GB, 2) + " GB"
$out | Out-File -FilePath $log -Encoding UTF8

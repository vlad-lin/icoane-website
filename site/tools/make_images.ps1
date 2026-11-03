# Creates the photos listed in images.txt (written by build_data.py) in site/public/img:
# img/full at most 1600 px (the icon pages), img/thumb at most 560 px (the gallery).
# Photos no longer used are deleted. Uses only built-in Windows .NET.
#   powershell -ExecutionPolicy Bypass -File site\tools\make_images.ps1
param([int]$FullSize = 1600, [int]$ThumbSize = 560)

Add-Type -AssemblyName System.Drawing
$site = Split-Path -Parent $PSScriptRoot
$full = Join-Path $site 'public\img\full'
$thumb = Join-Path $site 'public\img\thumb'
New-Item -ItemType Directory -Force $full, $thumb | Out-Null

$jpeg = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$params = New-Object System.Drawing.Imaging.EncoderParameters 1
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), 82L

function Save-Resized($src, $dst, $size) {
  $img = [System.Drawing.Image]::FromFile($src)
  $scale = [math]::Min(1.0, $size / [math]::Max($img.Width, $img.Height))
  $w = [int][math]::Round($img.Width * $scale); $h = [int][math]::Round($img.Height * $scale)
  $bmp = New-Object System.Drawing.Bitmap $w, $h
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = 'HighQualityBicubic'
  $g.PixelOffsetMode = 'HighQuality'
  $g.DrawImage($img, 0, 0, $w, $h)
  $g.Dispose(); $img.Dispose()
  $bmp.Save($dst, $jpeg, $params)
  $bmp.Dispose()
}

function Get-LongSide($path) {
  $img = [System.Drawing.Image]::FromFile($path)
  $n = [math]::Max($img.Width, $img.Height)
  $img.Dispose()
  return $n
}

$lines = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'images.txt') -Encoding UTF8
$wanted = @{}
foreach ($line in $lines) {
  if (-not $line.Trim()) { continue }
  $src, $name, $used = $line -split "`t"
  if ($used -eq '0') { continue }
  $wanted[$name] = $true
  $dstFull = Join-Path $full $name
  $dstThumb = Join-Path $thumb $name
  if (-not (Test-Path -LiteralPath $dstFull) -or (Get-LongSide $dstFull) -gt $FullSize) {
    Save-Resized $src $dstFull $FullSize
  }
  if (-not (Test-Path -LiteralPath $dstThumb)) { Save-Resized $src $dstThumb $ThumbSize }
}

$removed = 0
foreach ($dir in @($full, $thumb)) {
  foreach ($f in Get-ChildItem $dir -Filter *.jpg) {
    if (-not $wanted.ContainsKey($f.Name)) { Remove-Item -LiteralPath $f.FullName; $removed++ }
  }
}
Write-Output "$($wanted.Count) images ready in $site\img ($removed unused files removed)"

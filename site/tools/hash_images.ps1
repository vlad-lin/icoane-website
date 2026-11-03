# Writes tools/hashes.txt: "<photo name><TAB><256-bit difference hash, hex>" for every
# photo in images.txt, computed from the original in the export. Photos of the same
# physical icon (re-posted in later years) get nearly identical hashes, which lets
# build_data.py merge those reposts into one entry.
#   powershell -ExecutionPolicy Bypass -File site\tools\hash_images.ps1
Add-Type -AssemblyName System.Drawing
$lines = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'images.txt') -Encoding UTF8
$out = foreach ($line in $lines) {
  if (-not $line.Trim()) { continue }
  $src, $name, $null = $line -split "`t"
  $img = [System.Drawing.Image]::FromFile($src)
  # Two steps (560 px, then 17x16) so the result matches hashing a gallery thumbnail.
  $scale = [math]::Min(1.0, 560 / [math]::Max($img.Width, $img.Height))
  $mid = New-Object System.Drawing.Bitmap ([int]($img.Width * $scale)), ([int]($img.Height * $scale))
  $g = [System.Drawing.Graphics]::FromImage($mid)
  $g.InterpolationMode = 'HighQualityBicubic'
  $g.DrawImage($img, 0, 0, $mid.Width, $mid.Height)
  $g.Dispose(); $img.Dispose()
  $bmp = New-Object System.Drawing.Bitmap 17, 16
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = 'HighQualityBicubic'
  $g.DrawImage($mid, 0, 0, 17, 16)
  $bits = New-Object System.Text.StringBuilder
  for ($y = 0; $y -lt 16; $y++) {
    for ($x = 0; $x -lt 16; $x++) {
      $a = $bmp.GetPixel($x, $y); $b = $bmp.GetPixel($x + 1, $y)
      $la = $a.R * 299 + $a.G * 587 + $a.B * 114; $lb = $b.R * 299 + $b.G * 587 + $b.B * 114
      [void]$bits.Append($(if ($la -gt $lb) { '1' } else { '0' }))
    }
  }
  $hex = -join (0..63 | ForEach-Object { '{0:x}' -f [Convert]::ToInt32($bits.ToString().Substring($_ * 4, 4), 2) })
  $g.Dispose(); $bmp.Dispose(); $mid.Dispose()
  "{0}`t{1}" -f $name, $hex
}
$out | Set-Content -Path (Join-Path $PSScriptRoot 'hashes.txt') -Encoding utf8
Write-Output "$($out.Count) photos hashed"

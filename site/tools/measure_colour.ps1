# Writes tools/colour.txt: "<photo name><TAB><mean saturation 0-1>" for every photo in
# images.txt, measured on the original in the export (so it also covers photos that
# are not published). Ink drawings on glass are nearly colourless, which lets
# build_data.py tell them apart from painted icons even when the caption doesn't say so.
Add-Type -AssemblyName System.Drawing
$lines = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'images.txt') -Encoding UTF8
$out = foreach ($line in $lines) {
  if (-not $line.Trim()) { continue }
  $src, $name, $null = $line -split "`t"
  $orig = [System.Drawing.Image]::FromFile($src)
  $scale = [math]::Min(1.0, 560 / [math]::Max($orig.Width, $orig.Height))
  $img = New-Object System.Drawing.Bitmap $orig, ([int]($orig.Width * $scale)), ([int]($orig.Height * $scale))
  $orig.Dispose()
  $sum = 0.0; $n = 0
  $step = [math]::Max(1, [int]($img.Width / 60))
  # Sample the central 70% so frames and backgrounds count less.
  for ($x = [int]($img.Width * .15); $x -lt $img.Width * .85; $x += $step) {
    for ($y = [int]($img.Height * .15); $y -lt $img.Height * .85; $y += $step) {
      $c = $img.GetPixel($x, $y)
      $max = [math]::Max($c.R, [math]::Max($c.G, $c.B)); $min = [math]::Min($c.R, [math]::Min($c.G, $c.B))
      if ($max -gt 0) { $sum += ($max - $min) / $max }
      $n++
    }
  }
  $img.Dispose()
  "{0}`t{1:N3}" -f $name, ($sum / $n)
}
$out | Set-Content -Path (Join-Path $PSScriptRoot 'colour.txt') -Encoding utf8
Write-Output "$($out.Count) photos measured"

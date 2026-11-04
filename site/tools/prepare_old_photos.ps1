# Prepares the photos from the 2019-2020 archive ("poze vechi", kept on this PC only) that
# site/old-works/works.json puts on the site: turns them upright (camera rotation), crops
# them to the icon, and saves them at most 2000 px into "poze vechi\_pentru-site".
# build_data.py then lists them for the usual image scripts.
#   powershell -ExecutionPolicy Bypass -File site\tools\prepare_old_photos.ps1
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression.FileSystem
$site = Split-Path -Parent $PSScriptRoot
$archive = Join-Path (Split-Path -Parent $site) 'poze vechi'
$outDir = Join-Path $archive '_pentru-site'
New-Item -ItemType Directory -Force $outDir | Out-Null
$json = [IO.File]::ReadAllText((Join-Path $site 'old-works\works.json'), [Text.Encoding]::UTF8)
$data = $json | ConvertFrom-Json

$jpeg = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$params = New-Object System.Drawing.Imaging.EncoderParameters 1
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), 90L

function Open-Photo($rel) {
  # "Some document.docx#word/media/image4.jpeg" = a photo inside a Word document.
  if ($rel -match '^(.+?\.docx)#(.+)$') {
    $zip = [IO.Compression.ZipFile]::OpenRead((Join-Path $archive $Matches[1]))
    try {
      $ms = New-Object IO.MemoryStream
      $s = $zip.GetEntry($Matches[2]).Open(); $s.CopyTo($ms); $s.Dispose()
      return [System.Drawing.Image]::FromStream($ms)
    } finally { $zip.Dispose() }
  }
  return [System.Drawing.Image]::FromFile((Join-Path $archive $rel))
}

function Save-Prepared($rel, $crop, $name) {
  $img = Open-Photo $rel
  foreach ($p in $img.PropertyItems) {
    if ($p.Id -eq 0x0112) {
      switch ([BitConverter]::ToUInt16($p.Value, 0)) {
        3 { $img.RotateFlip('Rotate180FlipNone') }
        6 { $img.RotateFlip('Rotate90FlipNone') }
        8 { $img.RotateFlip('Rotate270FlipNone') }
      }
    }
  }
  if ($crop) {
    $rect = New-Object System.Drawing.Rectangle ([int]($img.Width * $crop[0])), ([int]($img.Height * $crop[1])),
      ([int]($img.Width * $crop[2])), ([int]($img.Height * $crop[3]))
  } else {
    $rect = New-Object System.Drawing.Rectangle 0, 0, $img.Width, $img.Height
  }
  $scale = [math]::Min(1.0, 2000 / [math]::Max($rect.Width, $rect.Height))
  $w = [int][math]::Round($rect.Width * $scale); $h = [int][math]::Round($rect.Height * $scale)
  $bmp = New-Object System.Drawing.Bitmap $w, $h
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = 'HighQualityBicubic'
  $g.PixelOffsetMode = 'HighQuality'
  $g.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $w, $h), $rect, 'Pixel')
  $g.Dispose(); $img.Dispose()
  $bmp.Save((Join-Path $outDir $name), $jpeg, $params)
  $bmp.Dispose()
}

$n = 0
foreach ($wk in $data.works) { Save-Prepared $wk.photo $wk.crop "$($wk.id).jpg"; $n++ }
foreach ($a in $data.add_photos) { Save-Prepared $a.photo $a.crop "add-$($a.to).jpg"; $n++ }
foreach ($c in $data.church_photos) { Save-Prepared $c.photo $c.crop $c.name; $n++ }
Write-Output "$n photos prepared in $outDir"

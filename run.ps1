$originalDir = $(pwd).path
$oldPath = $(Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment\' -Name PATH).path
$oldPathArray = $oldPath -split ";"
$newPath = "$originalDir\Tools\ImageMagick-i686-pc-cygwin\ImageMagick-6.8.8\bin;$originalDir\Tools\poppler-0.51_x86\poppler-0.51\bin;$originalDir\Tools\Tesseract-OCR"
$newPathArray = $newPath -split ";"

$toBeAdded = ""
foreach($item in $newPathArray){
	if(!($oldPathArray -contains $item)){
		$toBeAdded += "$item;"
	}
}
$toBeAdded = $toBeAdded.trimEnd(";")
$finalPath = "$oldPath;$toBeAdded"
if($finalPath){
	Set-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment\' -Name PATH -Value $finalPath
}	
.\Scripts\venv\Scripts\activate
python .\Scripts\PDF_OCR.py
deactivate
Add-Type -Path "$env:TEMP\adomd\extracted\lib\net45\Microsoft.AnalysisServices.AdomdClient.dll"

$port = 54689
$connStr = "Data Source=localhost:$port"
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($connStr)
$conn.Open()
Write-Host "Connected."

$cmd = $conn.CreateCommand()
$cmd.CommandText = "SELECT * FROM `$SYSTEM.DBSCHEMA_CATALOGS"
$reader = $cmd.ExecuteReader()
Write-Host "FieldCount: $($reader.FieldCount)"
for ($i = 0; $i -lt $reader.FieldCount; $i++) {
    Write-Host "  Field $i : $($reader.GetName($i)) (Type: $($reader.GetFieldType($i).Name))"
}
$rowNum = 0
while ($reader.Read()) {
    $rowNum++
    $vals = New-Object object[] $reader.FieldCount
    $reader.GetValues($vals) | Out-Null
    Write-Host "Row $rowNum : $($vals -join ' | ')"
}
$reader.Close()
$conn.Close()

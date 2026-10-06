Add-Type -Path "$env:TEMP\adomd\extracted\lib\net45\Microsoft.AnalysisServices.AdomdClient.dll"
$port = 54689
$connStr = "Data Source=localhost:$port;Initial Catalog=57f4a915-fdfb-4d12-a7f1-b7db891f86b2"
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($connStr)
$conn.Open()

function ShowRows($dax) {
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $dax
    $reader = $cmd.ExecuteReader()
    $names = @()
    for ($i = 0; $i -lt $reader.FieldCount; $i++) { $names += $reader.GetName($i) }
    Write-Host ($names -join " | ")
    while ($reader.Read()) {
        $vals = @()
        for ($i = 0; $i -lt $reader.FieldCount; $i++) {
            $v = $reader.GetValue($i)
            if ($v -eq $null) { $vals += "<null>" } else { $vals += $v.ToString() }
        }
        Write-Host ($vals -join " | ")
    }
    $reader.Close()
}

Write-Host "--- TMSCHEMA_TABLES ---"
ShowRows "SELECT [Name], [ObjectTypeName] FROM `$SYSTEM.TMSCHEMA_TABLES"

Write-Host "`n--- TMSCHEMA_PARTITIONS (Name, State, RefreshedTime, Rows via Records) ---"
ShowRows "SELECT [Name], [State], [RefreshedTime], [ModifiedTime] FROM `$SYSTEM.TMSCHEMA_PARTITIONS"

$conn.Close()

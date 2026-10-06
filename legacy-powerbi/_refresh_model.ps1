$libDir = "$env:TEMP\amo\extracted\lib\net45"
Add-Type -Path (Join-Path $libDir "Microsoft.AnalysisServices.Core.dll")
Add-Type -Path (Join-Path $libDir "Microsoft.AnalysisServices.dll")
Add-Type -Path (Join-Path $libDir "Microsoft.AnalysisServices.Tabular.dll")

$port = 54689
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("Data Source=localhost:$port")
Write-Host "Connected to server. Version: $($server.Version)"

$db = $server.Databases[0]
Write-Host "Database: $($db.Name), Compatibility level: $($db.CompatibilityLevel)"

Write-Host "`nTriggering full refresh of the model..."
$db.Model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$db.Model.SaveChanges()
Write-Host "Refresh + SaveChanges completed."

Write-Host "`n--- Partition states after refresh ---"
foreach ($table in $db.Model.Tables) {
    foreach ($partition in $table.Partitions) {
        Write-Host "$($table.Name) / $($partition.Name): State=$($partition.State) RefreshedTime=$($partition.RefreshedTime)"
    }
}

$server.Disconnect()

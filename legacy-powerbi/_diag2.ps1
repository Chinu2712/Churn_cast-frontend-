Add-Type -Path "$env:TEMP\adomd\extracted\lib\net45\Microsoft.AnalysisServices.AdomdClient.dll"
$port = 54689
$connStr = "Data Source=localhost:$port;Initial Catalog=57f4a915-fdfb-4d12-a7f1-b7db891f86b2"
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($connStr)
$conn.Open()

$dax = 'EVALUATE ROW("n", COUNTROWS(Customers))'
Write-Host "DAX: $dax"
$cmd = $conn.CreateCommand()
$cmd.CommandText = $dax
try {
    $reader = $cmd.ExecuteReader()
    Write-Host "FieldCount: $($reader.FieldCount)"
    for ($i = 0; $i -lt $reader.FieldCount; $i++) {
        Write-Host "  Field $i : $($reader.GetName($i))"
    }
    $n = 0
    while ($reader.Read()) {
        $n++
        Write-Host "Row $n raw value: [$($reader.GetValue(0))] Type: $($reader.GetValue(0).GetType().FullName)"
    }
    Write-Host "Total rows read: $n"
    $reader.Close()
} catch {
    Write-Host "EXCEPTION: $($_.Exception.ToString())"
}
$conn.Close()

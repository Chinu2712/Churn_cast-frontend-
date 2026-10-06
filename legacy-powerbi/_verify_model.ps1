Add-Type -Path "$env:TEMP\adomd\extracted\lib\net45\Microsoft.AnalysisServices.AdomdClient.dll"

$port = 54689
$connStr = "Data Source=localhost:$port;Initial Catalog=57f4a915-fdfb-4d12-a7f1-b7db891f86b2"
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($connStr)
$conn.Open()
Write-Host "Connected. Server: $($conn.ServerVersion). Database: $($conn.Database)"

function Run-Dax($dax) {
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $dax
    $reader = $cmd.ExecuteReader()
    $rows = New-Object System.Collections.Generic.List[object]
    while ($reader.Read()) {
        $vals = New-Object object[] $reader.FieldCount
        $reader.GetValues($vals) | Out-Null
        $rows.Add($vals)
    }
    $reader.Close()
    # -NoEnumerate is the correct idiom to return a single List object without
    # PowerShell flattening it (or its single-element rows) into bare scalars.
    Write-Output -NoEnumerate $rows
}

function Get-Cell($rows, [int]$rowIndex, [int]$colIndex) {
    $row = $rows.Item($rowIndex)
    return $row.GetValue($colIndex)
}

Write-Host "`n--- Catalogs (DMV) ---"
$catalogRows = Run-Dax "SELECT [CATALOG_NAME] FROM `$SYSTEM.DBSCHEMA_CATALOGS"
Write-Host "Row count: $($catalogRows.Count)"

Write-Host "`n--- Row counts per table ---"
$tables = @("Customers", "FeatureContributions", "RevenueHistory", "MonthlyRevenue", "CohortRetention",
            "BacktestMetrics", "Calibration", "DriftMetrics", "DriftDistributions", "LeakageChecklist", "ModelMeta")
foreach ($t in $tables) {
    $dax = "EVALUATE ROW(""n"", COUNTROWS('$t'))"
    try {
        $result = Run-Dax $dax
        Write-Host "$t : $(Get-Cell $result 0 0) rows"
    } catch {
        Write-Host "$t : ERROR - $($_.Exception.Message)"
    }
}

Write-Host "`n--- Key measures ---"
$measures = @(
    "Next Month Revenue", "Forecast Low", "Forecast High", "Actual Revenue MTD",
    "Forecast MAPE %", "Total Customers", "High Risk Customers", "% High Risk Customers",
    "Revenue at Risk", "Holdout AUC", "Accuracy Note"
)
foreach ($m in $measures) {
    $dax = "EVALUATE ROW(""v"", [$m])"
    try {
        $result = Run-Dax $dax
        Write-Host "[$m] = $(Get-Cell $result 0 0)"
    } catch {
        Write-Host "[$m] : ERROR - $($_.Exception.Message)"
    }
}

Write-Host "`n--- Sample: top 3 customers by churn probability ---"
$dax = @"
EVALUATE
TOPN(3, Customers, Customers[churn_probability], 0)
ORDER BY Customers[churn_probability] DESC
"@
try {
    $result = Run-Dax $dax
    Write-Host "Rows returned: $($result.Count)"
    for ($i = 0; $i -lt $result.Count; $i++) {
        $row = $result.Item($i)
        Write-Host " - row $($i): $($row.Length) columns, first value = $($row.GetValue(0))"
    }
} catch {
    Write-Host "ERROR - $($_.Exception.Message)"
}

Write-Host "`n--- What-if measures (usage drop simulation) ---"
$dax = @"
EVALUATE
ROW(
    "SimProb", CALCULATE([Simulated Churn Probability], Customers[customer_id] = "CUST-0001", UsageDropPercent[Usage Drop %] = 50),
    "SimImpact", CALCULATE([Simulated Revenue Impact], Customers[customer_id] = "CUST-0001", UsageDropPercent[Usage Drop %] = 50)
)
"@
try {
    $result = Run-Dax $dax
    Write-Host "SimProb=$(Get-Cell $result 0 0) SimImpact=$(Get-Cell $result 0 1)"
} catch {
    Write-Host "ERROR - $($_.Exception.Message)"
}

$conn.Close()
Write-Host "`nDone."

param(
    $rootDirectory = (Get-Location).Path
)

function RecurseiveList($path) {
    Get-ChildItem -ErrorAction SilentlyContinue -Force -Path $path | 
        Where-Object { !($_.Attributes -match "ReparsePoint") } |
        ForEach-Object {
        $_
        if ($_.PSIsContainer) {
            RecurseiveList($_.FullName)
        }
    }
}

Measure-Command {
    RecurseiveList($rootDirectory) |
        Select-Object -Property FullName, LastWriteTime, Length, @{Name = "Parent"; Expression = {$_.Parent.FullName}}, @{Name = "Directory"; Expression = {$_.Directory.FullName}}, PSIsContainer | Export-Csv -NoTypeInformation -Delimiter '|' -Path ((Get-Date -Format "yyyy-MM-dd HH-mm-ss") + ".csv")
}

# Windows Disk Usage Comparator

A couple scripts to help with tracking where Windows is consuming disk space.

## `file_sizes.ps1`

A PowerShell script that recursively trawls a filesystem and records every file and directory it can read, saving the resulting objects to a CSV.

This script is best run as an administrator to ensure it captures system files, but will run just fine as a mortal non-admin user.

## `space_compare.py`

A python script that will take in one or two CSVs produced by `file_sizes.ps1` and produce JSON files that describe the decreases in consumption (files that were removed between the two snapshots, as well as files that decreased in size between the two snapshots) and increases in consumption (new files, and files that have increased in size). It will also produce a file describing the current disk consumption information.

If run with a single input file, it only produces the description of the current disk consumption.

The output files are JSON files suitable for loading with [`ncdu`](https://dev.yorhel.nl/ncdu) for viewing and exploring the consumption hierarchy.

## Using the tools

Step 1: Run the powershell script on the folder root you care about:

```powershell
PS D:\Working\WindowsDiskConsumption> whoami
prometheus\prima
PS D:\Working\WindowsDiskConsumption> .\file_sizes.ps1 C:\


Days              : 0
Hours             : 0
Minutes           : 2
Seconds           : 22
Milliseconds      : 986
Ticks             : 1429863322
TotalDays         : 0.00165493440046296
TotalHours        : 0.0397184256111111
TotalMinutes      : 2.38310553666667
TotalSeconds      : 142.9863322
TotalMilliseconds : 142986.3322
```

Step 2: Run the Python script on the resulting CSV

```bash
Mortal@Prometheus /mnt/d/Working/WindowsDiskConsumption
$ time python space_compare.py "`ls *csv | tail -n1`"

real    0m16.968s
user    0m13.406s
sys     0m3.250s

Mortal@Prometheus /mnt/d/Working/WindowsDiskConsumption
$ ls -l *csv *json
-rwxrwxrwx 1 Michael Michael 110772913 Jun 29 15:16 '2018-06-29 15-13-49.csv'
-rwxrwxrwx 1 Michael Michael 120290965 Jun 29 15:17 '2018-06-29T15-16-51 Current.json'
```

Step 3: Load the output JSON files into `ncdu`

```text
ncdu 1.12 ~ Use the arrow keys to navigate, press ? for help           [imported]
--- C:\/C:\Windows --------------------------------------------------------------
                         /..
    7.9 GiB [##########] /WinSxS
    5.4 GiB [######    ] /System32
    1.6 GiB [#         ] /SysWOW64
    1.3 GiB [#         ] /InfusedApps
  920.2 MiB [#         ] /SoftwareDistribution
  742.2 MiB [          ] /assembly
  582.4 MiB [          ] /Microsoft.NET
  360.4 MiB [          ] /Fonts
  245.0 MiB [          ] /SystemApps
  126.1 MiB [          ] /Installer
  117.7 MiB [          ] /Speech_OneCore
  102.9 MiB [          ] /Speech
   79.9 MiB [          ] /ServiceProfiles
   69.7 MiB [          ] /INF
   68.6 MiB [          ] /Help
   67.6 MiB [          ] /servicing
   52.3 MiB [          ] /Globalization
   51.2 MiB [          ] /ShellExperiences
   43.9 MiB [          ] /Containers
   41.8 MiB [          ] /Logs
   37.2 MiB [          ] /Boot
   36.4 MiB [          ] /InputMethod
   27.6 MiB [          ] /IME
   25.5 MiB [          ] /SystemResources
   19.7 MiB [          ] /media
   15.1 MiB [          ] /Web
   13.5 MiB [          ] /Temp
   13.0 MiB [          ] /TextInput
   11.5 MiB [          ] /Cursors
    8.5 MiB [          ] /ImmersiveControlPanel
    7.9 MiB [          ] /apppatch
    7.0 MiB [          ] /PolicyDefinitions
    6.9 MiB [          ] /Prefetch
    6.2 MiB [          ] /ShellComponents
 Total disk usage:  20.0 GiB  Apparent size:  19.7 GiB  Items: 138124
```

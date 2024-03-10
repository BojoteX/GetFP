# GetFP (Simbrief + MSFS custom GATE start) 

## Description
GetFP is a simple utility tool designed to streamline the process of downloading your Simbrief most recent MSFS flight plan directly into Microsoft Flight Simulator. It simplifies the workflow for sim pilots who would like to start from a custom GATE or RAMP. Just include the GATE number in the Simbrief Flight Plan remarks and the utility will automatically create a .FLT file with the custom start location. for GATES simply use GATE D42 or GATE D 42 in a single line. For RAMP you'll use RAMP 32 or RAMP A23. 

## Features
- Download MSFS flight plan from SimBrief with custom start location.
- Supports both MS Store and Steam versions of MSFS.
- Option to include or exclude SID/STARs in the downloaded flight plan.

You can download the source and run the Python script or simply download the release version (.exe)

> [!WARNING]
> Its possible you get a virus warning when downloading the .exe file, in that case I suggest you download the sources or execute the Python (.py) script directly.

## Configuration
When running for the first time the application will request your Simbrief Alias (Username) so it can fetch the latest Flight Plan. You can find your Alias in the Account Settings menu option of your Simbrief page. Once the initial fetch is succesful, a configuration .ini file will be created using the following format:

```
[Settings]
simbriefuser = YOUR_USERNAME  # Your Simbrief username. (Located in Simbrief Account settings menu option 
filename = LAST.PLN           # This is the name of the .PLN file that will be created.
include_sid_star = 1          # Flight Plan downloaded from Simbrief can include SID/STAR or simply waypoints. 
delete_customflight = 0       # Removes the MISSIONS/Custom folder when you run the utility and set this to 1.
```


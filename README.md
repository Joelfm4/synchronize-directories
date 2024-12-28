# Folder Synchronization 

A simple script for synchronizing the contents of a **source folder** with a **destination folder**.

## Features
- **Folder Synchronization**: Reflects all changes made in the source folder to the replica.
- **Change Detection**: Detects new, moved, modified, or deleted files in the source folder and automatically updates the destination folder accordingly.
- **Performance**: Uses **multithreading** for efficient I/O operations and **parallelism** to watch for changes
- **Logs**: Keeps a record of all logs.

## Installation

#### 1. Clone the repository:
```
git clone https://github.com/Joelfm4/synchronize-folders
cd synchronize-folders
```

#### 2. Install dependencies:
```
pip install -r requirements.txt
```
## How to Use
``` 
python main.py <Source Directory Path> <Destination Directory Path> <Synchronization interval in Seconds> <Log file Location>
```

## ⚠️ WARNING ⚠️
- **Avoid setting the interval too low**, as it may cause instability.
- **Recommendation**: Set the interval to **at least 5 seconds** to prevent issues.
- **Windows Compatibility**: Not fully compatible with Windows 

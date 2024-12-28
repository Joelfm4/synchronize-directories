import sys
import os


def show_error_text():
    print("Error: Incorrect number of arguments \n")
    print("Usage: python main.py <Source Folder Path> <Replica Folder Path> <Synchronization interval in Seconds> <Log File Location>")
    print("\nArguments:")
    print("  1. Source Folder Path - Path to the source folder.")
    print("  2. Replica Folder Path - Path to the destination folder.")
    print("  3. Synchronization interval - Time interval (in seconds) for synchronization.")
    print("  4. Log File Location - Path to the log file. \n")
    print("     (Enter 0 if you don't have a log file and a default 'app.log' will be created)\n")


def valid_path(path:str) -> bool:
    if os.path.exists(path):
        return True

    try:
        os.makedirs(path)
        return True

    except OSError:
        return False 


def input_validation() -> bool:

    errors = []

    if len(sys.argv) < 5:
        show_error_text()
        return False

    else:
        if not os.path.exists(sys.argv[1]):
            errors.append(f"Error: The Original Folder Path '{sys.argv[1]}' is invalid.")
        
        if not valid_path(sys.argv[2]):
            errors.append(f"Error: The Replica Folder Path '{sys.argv[2]}' is invalid or could not be created.")
        
        try:
            interval = int(sys.argv[3])
            if interval <= 0:
                errors.append(f"Error: The Sync Interval '{sys.argv[3]}' is invalid. It should be a positive integer.")
        except ValueError:
            errors.append(f"Error: The Sync Interval '{sys.argv[3]}' is invalid. It should be an integer.")

        if not os.path.isfile(sys.argv[4]) or not sys.argv[4].endswith('.log'):
            if sys.argv[4] == '0':
                open("app.log", "w").close()
            else:
                errors.append(f"Error: The Log File Path '{sys.argv[4]}' is invalid or not a .log file.")

    if errors:
        for error in errors:
            print(error)
        return False

    return True


def validation() -> tuple:
    if input_validation():
        log_file = "app.log" if sys.argv[4] == "0" else sys.argv[4]
        return sys.argv[1], sys.argv[2], int(sys.argv[3]), log_file
    else:
        sys.exit(1)


if __name__ == "__main__":
    validation()

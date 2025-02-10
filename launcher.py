import os
import sys
import subprocess

def launch_application():
    # Get the directory where the launcher script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to mainconsole.py
    main_console_path = os.path.join(current_dir, 'mainconsole.py')
    
    # Add debug print
    print(f"Attempting to launch: {main_console_path}")
    
    try:
        # Launch mainconsole.py using the current Python interpreter
        subprocess.run([sys.executable, main_console_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching application: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    launch_application() 
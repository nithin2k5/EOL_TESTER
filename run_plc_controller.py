"""
PLC Process Controller Launcher
Easy launcher for the PLC process status controller
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🎮 PLC PROCESS STATUS CONTROLLER")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Purpose: Control PLC process status in continuous loop")
    print("⚠️  Press Ctrl+C to stop")
    print("=" * 60)

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['pymodbus', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages installed")
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'plc_process_controller.py',
        'plc_config.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def show_menu():
    """Show main menu"""
    print("\n📋 CONTROLLER OPTIONS:")
    print("1. Start PLC Process Controller")
    print("2. Test PLC Connection Only")
    print("3. View Configuration")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\n👉 Select option (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return 4
        except Exception:
            print("❌ Invalid input. Please try again.")

def start_controller():
    """Start the main PLC controller"""
    try:
        print("\n🚀 Starting PLC Process Controller...")
        print("⚠️  Press Ctrl+C to stop")
        print("-" * 40)
        
        # Run the controller
        subprocess.run([sys.executable, 'plc_process_controller.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ Controller stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Controller failed with exit code: {e.returncode}")
    except Exception as e:
        print(f"\n❌ Error starting controller: {e}")

def test_connection():
    """Test PLC connection only"""
    try:
        print("\n🧪 Testing PLC Connection...")
        
        # Import and test connection
        from plc_process_controller import PLCProcessController
        
        controller = PLCProcessController()
        
        if controller.connect_plc():
            print("✅ PLC Connection Test: SUCCESS")
            
            # Test basic communication
            controller.set_plc_enable(True)
            can_control = controller.test_process_control()
            
            print(f"🎮 Process Control: {'YES' if can_control else 'NO'}")
            
            controller.disconnect_plc()
        else:
            print("❌ PLC Connection Test: FAILED")
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")

def view_config():
    """View current configuration"""
    try:
        print("\n📋 CURRENT CONFIGURATION:")
        print("-" * 40)
        
        from plc_config import get_plc_settings, get_process_settings, get_process_steps
        
        # PLC Settings
        plc_settings = get_plc_settings()
        print("🔗 PLC Connection:")
        for key, value in plc_settings.items():
            print(f"   {key}: {value}")
        
        # Process Settings
        process_settings = get_process_settings()
        print("\n⚙️ Process Settings:")
        for key, value in process_settings.items():
            print(f"   {key}: {value}")
        
        # Process Steps
        process_steps = get_process_steps()
        print("\n📝 Process Steps:")
        for i, (addr, name) in enumerate(zip(process_steps['addresses'], process_steps['names'])):
            print(f"   {i+1}. {name} ({addr})")
            
    except Exception as e:
        print(f"❌ Error viewing config: {e}")

def main():
    """Main launcher function"""
    try:
        # Print banner
        print_banner()
        
        # Check requirements
        if not check_requirements():
            input("\nPress Enter to exit...")
            return
        
        # Check files
        if not check_files():
            input("\nPress Enter to exit...")
            return
        
        # Main loop
        while True:
            choice = show_menu()
            
            if choice == 1:
                start_controller()
            elif choice == 2:
                test_connection()
            elif choice == 3:
                view_config()
            elif choice == 4:
                print("\n👋 Goodbye!")
                break
            
            # Pause before showing menu again
            if choice != 4:
                input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

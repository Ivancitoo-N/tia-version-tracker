import sys
import os
import clr  # pythonnet

# Path to TIA Portal V20 Openness DLL
# Adjust if installation path differs, but user confirmed default
OPENNESS_DLL_PATH = r"C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll"

def test_connection():
    print(f"Checking for DLL at: {OPENNESS_DLL_PATH}")
    if not os.path.exists(OPENNESS_DLL_PATH):
        print("ERROR: DLL not found at the specified path.")
        return

    try:
        # Load the assembly
        sys.path.append(os.path.dirname(OPENNESS_DLL_PATH))
        clr.AddReference("Siemens.Engineering")
        
        # Import TIA Portal namespace
        import Siemens.Engineering as Tia
        from Siemens.Engineering import TiaPortal, TiaPortalMode

        print("DLL loaded successfully. Attempting to start TIA Portal (without UI)...")
        print("This may take a minute...")

        # Start TIA Portal in non-GUI mode
        # Using 'WithUserInterface' = False for background processing
        # Note: Valid modes are TiaPortalMode.WithUserInterface or TiaPortalMode.WithoutUserInterface
        mytia = TiaPortal(TiaPortalMode.WithoutUserInterface)
        
        print(f"SUCCESS! Connected to TIA Portal.")
        
        # Get generic info to prove it works
        # (Exact property names depend on API, usually we iterate processes)
        # But instantiating TiaPortal() is enough proof of concept.
        
        print("Cleaning up...")
        mytia.Dispose()
        print("TIA Portal instance disposed.")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        # Print detailed error info if available
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check if pythonnet is installed
    try:
        import clr
    except ImportError:
        print("ERROR: 'pythonnet' is not installed.")
        print("Please run: pip install pythonnet")
        sys.exit(1)

    success = test_connection()
    if success:
        print("\nTest PASSED. We can use Openness.")
    else:
        print("\nTest FAILED.")

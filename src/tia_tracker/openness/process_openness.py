import sys
import os
import shutil
import time
from pathlib import Path

# Force STA execution for TIA Portal Openness (COM)
# This MUST be set before importing clr
sys.coinit_flags = 2 

print("Openness Script initializing...", flush=True)

# Path to TIA Portal V20 Openness DLL
OPENNESS_DLL_PATH = r"C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll"

# Check dependencies
try:
    import clr
    print("pythonnet imported successfully.", flush=True)
except ImportError:
    print("ERROR: pythonnet not installed", flush=True)
    sys.exit(1)

# Load TIA Portal DLL
if not os.path.exists(OPENNESS_DLL_PATH):
    print(f"ERROR: DLL not found at {OPENNESS_DLL_PATH}", flush=True)
    sys.exit(1)

try:
    print(f"Loading DLL from {OPENNESS_DLL_PATH}...", flush=True)
    
    # CRITICAL FIX: Add directory to sys.path AND os.environ['PATH']
    dll_dir = os.path.dirname(OPENNESS_DLL_PATH)
    # Found contract DLL in Bin/PublicAPI
    bin_public_api = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(OPENNESS_DLL_PATH))), "Bin", "PublicAPI")
    
    search_dirs = [dll_dir, bin_public_api]
    
    for d in search_dirs:
        if os.path.exists(d):
            sys.path.append(d)
            os.environ["PATH"] = d + ";" + os.environ["PATH"]
            print(f"Added search path: {d}", flush=True)

    import clr
    from System import AppDomain, Reflection
    
    # --- ADVANCED RESOLVER ---
    def resolve_assembly(sender, args):
        # args.Name is the full assembly name
        name = args.Name.split(',')[0]
        # print(f"Resolving: {name}", flush=True)
        
        for folder in search_dirs:
            dll_path = os.path.join(folder, name + ".dll")
            if os.path.exists(dll_path):
                # print(f"Resolved {name} -> {dll_path}", flush=True)
                return Reflection.Assembly.LoadFrom(dll_path)
        return None

    AppDomain.CurrentDomain.AssemblyResolve += resolve_assembly
    # -------------------------

    # Explicitly verify contract exists
    contract_dll = os.path.join(bin_public_api, "Siemens.Engineering.Contract.dll")
    if os.path.exists(contract_dll):
         print(f"Verified Contract DLL at: {contract_dll}", flush=True)
    else:
         print(f"WARNING: Contract DLL NOT found at expected location: {contract_dll}", flush=True)


    print(f"Loading main assembly: {OPENNESS_DLL_PATH}", flush=True)
    clr.AddReference(OPENNESS_DLL_PATH)

    print("DLL reference added. Importing Siemens.Engineering namespace...", flush=True)
    
    import Siemens.Engineering as Tia
    from Siemens.Engineering import TiaPortal, TiaPortalMode, Project
    print("Siemens.Engineering imported successfully.", flush=True)

except Exception as e:
    print(f"ERROR loading TIA DLL: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Additional imports for specific types might be needed
from Siemens.Engineering.HW.Features import SoftwareContainer

def cleanup_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)

def export_plc_blocks(plc_software, export_dir):
    """Export blocks from a PLC software container."""
    from System.IO import FileInfo
    
    print(f"Exporting blocks from {plc_software.Name}...", flush=True)
    block_group = plc_software.BlockGroup
    
    # Recursive function to export blocks
    def export_recursive(group):
        # Export blocks
        for block in group.Blocks:
            try:
                # We only want to export standard blocks (OB, FB, FC, DB)
                # Skip system blocks if needed
                if not block.IsConsistent:
                     print(f"Skipping inconsistent block: {block.Name}", flush=True)
                     continue
                
                export_path = os.path.join(export_dir, f"{block.Name}.xml")
                # CRITICAL FIX: Use FileInfo
                file_info = FileInfo(str(export_path))
                
                block.Export(file_info, Tia.ExportOptions.WithDefaults)
                print(f"Exported: {block.Name}", flush=True)
            except Exception as e:
                print(f"Failed to export block {block.Name}: {e}", flush=True)

        # Recurse groups
        for subgroup in group.Groups:
            export_recursive(subgroup)

    export_recursive(block_group)

def export_plc_tags(plc_software, export_dir):
    """Export tags from a PLC software container."""
    from System.IO import FileInfo
    
    print(f"Exporting tags from {plc_software.Name}...", flush=True)
    tag_group = plc_software.TagTableGroup
    
    def export_recursive(group):
        for table in group.TagTables:
            try:
                export_path = os.path.join(export_dir, f"{table.Name}.xml")
                # CRITICAL FIX: Use FileInfo
                file_info = FileInfo(str(export_path))
                
                table.Export(file_info, Tia.ExportOptions.WithDefaults)
                print(f"Exported: {table.Name}", flush=True)
            except Exception as e:
                print(f"Failed to export tag table {table.Name}: {e}", flush=True)
                
        for subgroup in group.Groups:
            export_recursive(subgroup)

    export_recursive(tag_group)

def process_archive(archive_path, output_dir):
    start_time = time.time()
    print(f"Starting TIA Portal processing for: {archive_path}", flush=True)
    
    # Create temp dir for retrieving the project
    temp_project_dir = os.path.join(os.path.dirname(output_dir), "temp_project_v20")
    cleanup_directory(temp_project_dir)
    cleanup_directory(output_dir)

    mytia = None
    project = None
    
    try:
        # 1. Start TIA Portal (Without User Interface for production)
        print("Launching TIA Portal (Without User Interface)...", flush=True)
        # Using WithoutUserInterface to avoid blocking dialogs
        mytia = TiaPortal(TiaPortalMode.WithoutUserInterface)
        print("TIA Portal launched successfully.", flush=True)
        
        # 2. Retrieve Project
        # Note: Retrieve usually takes FileInfo and DirectoryInfo
        print(f"Retrieving project to {temp_project_dir}...", flush=True)
        print("This operation can take several minutes depending on project size.", flush=True)
        
        # CRITICAL FIX: explicit .NET types
        from System.IO import FileInfo, DirectoryInfo
        
        # Ensure directories exist (DirectoryInfo needs existing path for some ops, but Retrieve creates it? 
        # Actually Retrieve usually creates the target dir, but let's be safe on the object creation)
        # However, checking Openness docs: Retrieve(FileInfo, DirectoryInfo)
        
        archive_file_info = FileInfo(str(archive_path))
        target_dir_info = DirectoryInfo(str(temp_project_dir))
        
        project = mytia.Projects.Retrieve(archive_file_info, target_dir_info)
        
        print(f"Project opened: {project.Name}", flush=True)
        
        # 3. Iterate Devices
        for device in project.Devices:
            print(f"Found Device: {device.Name}", flush=True)
            
            # Find PLC Software
            # Logic: Iterate device items to find SoftwareContainer
            for item in device.DeviceItems:
                service = item.GetService[SoftwareContainer]()
                if service:
                    software = service.Software
                    if software:
                        print(f"Found Software in {item.Name}", flush=True)
                        
                        # Export Blocks
                        # Check if it's a PLC (has BlockGroup)
                        try:
                            if hasattr(software, "BlockGroup"):
                                    export_plc_blocks(software, output_dir)
                            else:
                                    print(f"Skipping blocks for {item.Name} (Not a PLC or no BlockGroup)", flush=True)
                        except Exception as e:
                            print(f"Error checking BlockGroup for {item.Name}: {e}", flush=True)
                        
                        # Export Tags
                        try:
                            if hasattr(software, "TagTableGroup"):
                                    export_plc_tags(software, output_dir)
                            else:
                                    print(f"Skipping tags for {item.Name} (Not a PLC or no TagTableGroup)", flush=True)
                        except Exception as e:
                            print(f"Error checking TagTableGroup for {item.Name}: {e}", flush=True)
        
        print(f"Processing completed in {time.time() - start_time:.2f} seconds", flush=True)
        
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        print("Starting cleanup...", flush=True)
        try:
            if project:
                print("Closing project...", flush=True)
                project.Close()
                print("Project closed.", flush=True)
            if mytia:
                print("Disposing TIA Portal...", flush=True)
                mytia.Dispose()
                print("TIA Portal disposed.", flush=True)
        except Exception as e:
            print(f"Error during cleanup: {e}", flush=True)
        
        # Cleanup temp project files (optional, can leave for debug)
        # shutil.rmtree(temp_project_dir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_openness.py <zap_path> <output_dir>")
        sys.exit(1)
        
    zap_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    process_archive(zap_path, output_dir)
    print("Script finished. Exiting.", flush=True)
    sys.exit(0)

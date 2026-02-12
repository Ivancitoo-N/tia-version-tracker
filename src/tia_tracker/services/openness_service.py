import logging
import subprocess
import tempfile
import shutil
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class OpennessService:
    """Manages TIA Portal Openness automation via external script."""

    def __init__(self, script_path: str | Path):
        """Initialize the service.
        
        Args:
            script_path: Path to the process_openness.py script
        """
        self.script_path = Path(script_path)
        if not self.script_path.exists():
            raise FileNotFoundError(f"Openness script not found: {self.script_path}")

    def process_archive(self, archive_path: str | Path) -> Path:
        """Process a .zap/.zap20 archive using TIA Portal Openness.
        
        Args:
            archive_path: Path to the .zap/.zap20 file
            
        Returns:
            Path to directory containing exported XML files
            
        Raises:
            RuntimeError: If Openness processing fails
        """
        archive_path = Path(archive_path).resolve()
        
        # Create a unique output directory for this process
        output_dir = Path(tempfile.mkdtemp(prefix="tia_openness_"))
        
        logger.info(f"Starting Openness processing for {archive_path}")
        logger.info(f"Output directory: {output_dir}")
        
        try:
            # Run the external script
            # We use python from the current environment
            cmd = [sys.executable, "-u", str(self.script_path), str(archive_path), str(output_dir)]
            
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Run and stream output
            with subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1,
                universal_newlines=True
            ) as process:
                # Stream stdout to logger
                if process.stdout:
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            logger.info(f"[OPENNESS] {line}")
                
                # Check for errors after completion
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Openness script failed with code {process.returncode}")
                    if stderr:
                        logger.error(f"[OPENNESS ERROR] {stderr}")
                    
                    # Cleanup on failure
                    shutil.rmtree(output_dir, ignore_errors=True)
                    raise RuntimeError(f"TIA Portal processing failed. Check logs.")

            logger.info("Openness processing completed successfully")
            return output_dir

        except Exception as e:
            logger.error(f"Unexpected error interfacing with Openness: {e}")
            if 'output_dir' in locals():
                shutil.rmtree(output_dir, ignore_errors=True)
            raise

    def cleanup(self, directory: Path):
        """Clean up temporary directory."""
        if directory.exists():
            try:
                shutil.rmtree(directory)
                logger.debug(f"Cleaned up directory {directory}")
            except Exception as e:
                logger.warning(f"Failed to cleanup directory {directory}: {e}")

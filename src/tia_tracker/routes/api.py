"""API routes for TIA Version Tracker."""

import os
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from ..config import settings
from ..database.db_manager import DatabaseManager
from ..services.zap_extractor import ZapExtractor
from ..services.snapshot_service import SnapshotService
from ..services.comparison_service import ComparisonService
from ..services.report_generator import ReportGenerator

# Create blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Initialize services
db_manager = DatabaseManager(settings.database_path)
zap_extractor = ZapExtractor()
snapshot_service = SnapshotService(db_manager)
comparison_service = ComparisonService(snapshot_service)
report_generator = ReportGenerator(settings.report_folder)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed.

    Args:
        filename: Name of the file

    Returns:
        True if extension is allowed
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in settings.allowed_extensions
    )


@api_bp.route("/projects", methods=["GET"])
def get_projects():
    """Get all projects.

    Returns:
        JSON list of projects
    """
    try:
        projects = snapshot_service.get_all_projects()
        return jsonify({"success": True, "projects": projects})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/projects", methods=["POST"])
def create_project():
    """Create a new project.

    Request JSON:
        - name: Project name

    Returns:
        JSON with project ID
    """
    try:
        data = request.get_json()
        project_name = data.get("name")

        if not project_name:
            return jsonify({"success": False, "error": "Project name required"}), 400

        project_id = snapshot_service.create_or_get_project(project_name)
        return jsonify({"success": True, "project_id": project_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/projects/<int:project_id>/snapshots", methods=["GET"])
def get_project_snapshots(project_id: int):
    """Get all snapshots for a project.

    Args:
        project_id: Project ID

    Returns:
        JSON list of snapshots
    """
    try:
        snapshots = snapshot_service.list_snapshots_for_project(project_id)
        return jsonify({"success": True, "snapshots": snapshots})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/snapshots", methods=["POST"])
def upload_snapshot():
    """Upload a .zap15 file and create a snapshot.

    Form data:
        - file: .zap15 file
        - project_name: Project name
        - operator: Operator name

    Returns:
        JSON with snapshot ID
    """
    try:
        # Check if file is present
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        project_name = request.form.get("project_name")
        operator = request.form.get("operator")

        # Validate inputs
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not project_name:
            return jsonify({"success": False, "error": "Project name required"}), 400

        if not operator:
            return jsonify({"success": False, "error": "Operator name required"}), 400

        if not allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Invalid file extension. Allowed: {settings.allowed_extensions}",
                    }
                ),
                400,
            )

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_folder = Path(settings.upload_folder)
        upload_folder.mkdir(parents=True, exist_ok=True)
        file_path = upload_folder / filename
        file.save(file_path)

        try:
            print(f"Processing upload: {filename}")
            extracted_data = None
            
            # --- OPENNESS INTEGRATION START ---
            # Try to use TIA Openness for .zap20 (and .zap15) files
            # This is slow but handles the binary format correctly
            use_openness = True 
            
            if use_openness and file_path.suffix.lower() in [".zap15", ".zap20"]:
                print("Attempting to use TIA Portal Openness...")
                from ..services.openness_service import OpennessService
                
                # Path to our script
                script_path = Path(__file__).parent.parent / "openness" / "process_openness.py"
                openness_service = OpennessService(script_path)
                
                try:
                    # 1. Export to XML using Openness
                    xml_dir = openness_service.process_archive(file_path)
                    
                    # 2. Extract data from XML directory
                    extracted_data = zap_extractor.extract_from_directory(xml_dir)
                    
                    # 3. Cleanup
                    openness_service.cleanup(xml_dir)
                    
                except Exception as e:
                    # Fallback or Error?
                    # If Openness fails (e.g. no TIA installed), we might want to try legacy method
                    # But legacy method for .zap20 (binary) will return 0 results as seen before.
                    # So we should report the Openness error.
                    print(f"Openness processing failed: {e}")
                    raise ValueError(f"Failed to process TIA Portal project: {e}")

            if not extracted_data:
                 # Legacy extraction (direct ZIP reading)
                 extracted_data = zap_extractor.extract_zap_file(file_path)

            # --- OPENNESS INTEGRATION END ---

            # Create snapshot in database
            if not extracted_data:
                print("ERROR: extracted_data is None!", flush=True)
            else:
                print(f"Extracted Data: Tags={len(extracted_data.tags)}, Blocks={len(extracted_data.blocks)}", flush=True)

            snapshot_id = snapshot_service.create_snapshot(
                project_name, operator, filename, extracted_data
            )
            print(f"Snapshot created successfully: ID {snapshot_id}", flush=True)

            return jsonify({"success": True, "snapshot_id": snapshot_id})

        finally:
            # Clean up uploaded file
            if file_path.exists():
                file_path.unlink()

    except ValueError as e:
        print(f"API ERROR (400): {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        print(f"API ERROR (500): {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/compare", methods=["POST"])
def compare_snapshots():
    """Compare two snapshots.

    Request JSON:
        - snapshot_a_id: ID of first snapshot
        - snapshot_b_id: ID of second snapshot

    Returns:
        JSON with comparison results
    """
    try:
        data = request.get_json()
        snapshot_a_id = data.get("snapshot_a_id")
        snapshot_b_id = data.get("snapshot_b_id")

        if not snapshot_a_id or not snapshot_b_id:
            return (
                jsonify({"success": False, "error": "Both snapshot IDs required"}),
                400,
            )

        # Perform comparison
        result = comparison_service.compare_snapshots(snapshot_a_id, snapshot_b_id)

        # Convert to dict for JSON serialization
        return jsonify(
            {
                "success": True,
                "comparison": {
                    "new_tags": [tag.model_dump() for tag in result.new_tags],
                    "modified_tags": result.modified_tags,
                    "deleted_tags": [tag.model_dump() for tag in result.deleted_tags],
                    "new_blocks": [block.model_dump() for block in result.new_blocks],
                    "deleted_blocks": [
                        block.model_dump() for block in result.deleted_blocks
                    ],
                    "new_hardware": [hw.model_dump() for hw in result.new_hardware],
                    "deleted_hardware": [
                        hw.model_dump() for hw in result.deleted_hardware
                    ],
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/compare/pdf", methods=["POST"])
def generate_comparison_pdf():
    """Generate PDF report from comparison.

    Request JSON:
        - snapshot_a_id: ID of first snapshot
        - snapshot_b_id: ID of second snapshot
        - project_name: Project name

    Returns:
        PDF file download
    """
    try:
        data = request.get_json()
        snapshot_a_id = data.get("snapshot_a_id")
        snapshot_b_id = data.get("snapshot_b_id")
        project_name = data.get("project_name", "Unknown Project")

        if not snapshot_a_id or not snapshot_b_id:
            return (
                jsonify({"success": False, "error": "Both snapshot IDs required"}),
                400,
            )

        # Perform comparison
        result = comparison_service.compare_snapshots(snapshot_a_id, snapshot_b_id)

        # Get snapshot info
        conn = db_manager.get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT snapshot_date, operator FROM snapshots WHERE id = ?",
                (snapshot_a_id,),
            )
            snapshot_a_info = dict(cursor.fetchone())

            cursor.execute(
                "SELECT snapshot_date, operator FROM snapshots WHERE id = ?",
                (snapshot_b_id,),
            )
            snapshot_b_info = dict(cursor.fetchone())

        finally:
            conn.close()

        # Generate PDF
        pdf_path = report_generator.generate_comparison_report(
            result, project_name, snapshot_a_info, snapshot_b_info
        )

        return send_file(pdf_path, as_attachment=True, download_name=Path(pdf_path).name)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

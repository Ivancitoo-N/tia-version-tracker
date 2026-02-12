"""Snapshot storage service.

Manages storing and retrieving project snapshots in the database.
"""

from datetime import datetime
from typing import Optional

from ..database.db_manager import DatabaseManager
from ..models import ExtractedData, ProjectModel, SnapshotModel, TagData, BlockData, HardwareData


class SnapshotService:
    """Service for managing project snapshots."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize snapshot service.

        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager

    def create_or_get_project(self, project_name: str) -> int:
        """Create a new project or get existing project ID.

        Args:
            project_name: Name of the project

        Returns:
            Project ID
        """
        # Check if project exists
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
            row = cursor.fetchone()

            if row:
                return row["id"]

            # Create new project
            cursor.execute(
                "INSERT INTO projects (name) VALUES (?)", (project_name,)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def check_duplicate_snapshot(self, file_hash: str) -> Optional[int]:
        """Check if a snapshot with the same file hash already exists.

        Args:
            file_hash: SHA256 hash of the file

        Returns:
            Snapshot ID if duplicate found, None otherwise
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM snapshots WHERE file_hash = ?", (file_hash,))
            row = cursor.fetchone()
            return row["id"] if row else None
        finally:
            conn.close()

    def create_snapshot(
        self,
        project_name: str,
        operator: str,
        file_name: str,
        extracted_data: ExtractedData,
    ) -> int:
        """Create a new snapshot with extracted data.

        Args:
            project_name: Name of the project
            operator: Name of the operator who created this snapshot
            file_name: Original filename
            extracted_data: Extracted metadata from .zap15 file

        Returns:
            Snapshot ID

        Raises:
            ValueError: If snapshot with same file hash already exists
        """
        # Check for duplicates
        existing_id = self.check_duplicate_snapshot(extracted_data.file_hash)
        if existing_id:
            raise ValueError(
                f"Snapshot with this file already exists (ID: {existing_id})"
            )

        # Get or create project
        project_id = self.create_or_get_project(project_name)

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # Create snapshot
            cursor.execute(
                """
                INSERT INTO snapshots (project_id, operator, file_name, file_hash)
                VALUES (?, ?, ?, ?)
                """,
                (project_id, operator, file_name, extracted_data.file_hash),
            )
            snapshot_id = cursor.lastrowid

            # Store tags
            for tag in extracted_data.tags:
                cursor.execute(
                    """
                    INSERT INTO tags 
                    (snapshot_id, tag_name, tag_type, tag_address, tag_description, 
                     hardware_reference, block_reference)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        tag.tag_name,
                        tag.tag_type,
                        tag.tag_address,
                        tag.tag_description,
                        tag.hardware_reference,
                        tag.block_reference,
                    ),
                )

            # Store blocks
            for block in extracted_data.blocks:
                cursor.execute(
                    """
                    INSERT INTO blocks (snapshot_id, block_name, block_type, block_number)
                    VALUES (?, ?, ?, ?)
                    """,
                    (snapshot_id, block.block_name, block.block_type, block.block_number),
                )

            # Store hardware
            for hw in extracted_data.hardware:
                cursor.execute(
                    """
                    INSERT INTO hardware 
                    (snapshot_id, device_name, device_type, ip_address, rack_slot)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        hw.device_name,
                        hw.device_type,
                        hw.ip_address,
                        hw.rack_slot,
                    ),
                )

            conn.commit()
            return snapshot_id

        finally:
            conn.close()

    def list_snapshots_for_project(self, project_id: int) -> list[dict]:
        """List all snapshots for a project.

        Args:
            project_id: Project ID

        Returns:
            List of snapshot dictionaries
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, snapshot_date, operator, file_name
                FROM snapshots
                WHERE project_id = ?
                ORDER BY snapshot_date DESC
                """,
                (project_id,),
            )

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_projects(self) -> list[dict]:
        """Get all projects.

        Returns:
            List of project dictionaries
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, created_at,
                       (SELECT COUNT(*) FROM snapshots WHERE project_id = projects.id) as snapshot_count
                FROM projects
                ORDER BY created_at DESC
                """
            )

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_tags_for_snapshot(self, snapshot_id: int) -> list[TagData]:
        """Get all tags for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of TagData objects
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT tag_name, tag_type, tag_address, tag_description,
                       hardware_reference, block_reference
                FROM tags
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            )

            return [TagData(**dict(row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_blocks_for_snapshot(self, snapshot_id: int) -> list[BlockData]:
        """Get all blocks for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of BlockData objects
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT block_name, block_type, block_number
                FROM blocks
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            )

            return [BlockData(**dict(row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_hardware_for_snapshot(self, snapshot_id: int) -> list[HardwareData]:
        """Get all hardware for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of HardwareData objects
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT device_name, device_type, ip_address, rack_slot
                FROM hardware
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            )

            return [HardwareData(**dict(row)) for row in cursor.fetchall()]
        finally:
            conn.close()

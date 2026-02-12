"""Comparison service for detecting changes between snapshots.

Implements the core comparison logic for tags, blocks, and hardware.
"""

from ..models import ComparisonResult, TagData, BlockData, HardwareData
from .snapshot_service import SnapshotService


class ComparisonService:
    """Service for comparing project snapshots."""

    def __init__(self, snapshot_service: SnapshotService):
        """Initialize comparison service.

        Args:
            snapshot_service: Snapshot service instance
        """
        self.snapshot_service = snapshot_service

    def compare_snapshots(self, snapshot_a_id: int, snapshot_b_id: int) -> ComparisonResult:
        """Compare two snapshots and detect changes.

        Args:
            snapshot_a_id: ID of the first (older) snapshot
            snapshot_b_id: ID of the second (newer) snapshot

        Returns:
            ComparisonResult object with detected changes
        """
        # Fetch tags from both snapshots
        tags_a = self.snapshot_service.get_tags_for_snapshot(snapshot_a_id)
        tags_b = self.snapshot_service.get_tags_for_snapshot(snapshot_b_id)

        # Fetch blocks from both snapshots
        blocks_a = self.snapshot_service.get_blocks_for_snapshot(snapshot_a_id)
        blocks_b = self.snapshot_service.get_blocks_for_snapshot(snapshot_b_id)

        # Fetch hardware from both snapshots
        hardware_a = self.snapshot_service.get_hardware_for_snapshot(snapshot_a_id)
        hardware_b = self.snapshot_service.get_hardware_for_snapshot(snapshot_b_id)

        # Compare tags
        tag_changes = self._compare_tags(tags_a, tags_b)

        # Compare blocks
        block_changes = self._compare_blocks(blocks_a, blocks_b)

        # Compare hardware
        hardware_changes = self._compare_hardware(hardware_a, hardware_b)

        return ComparisonResult(
            new_tags=tag_changes["new"],
            modified_tags=tag_changes["modified"],
            deleted_tags=tag_changes["deleted"],
            new_blocks=block_changes["new"],
            deleted_blocks=block_changes["deleted"],
            new_hardware=hardware_changes["new"],
            deleted_hardware=hardware_changes["deleted"],
        )

    def _compare_tags(
        self, tags_a: list[TagData], tags_b: list[TagData]
    ) -> dict:
        """Compare tags between two snapshots.

        Args:
            tags_a: Tags from first snapshot
            tags_b: Tags from second snapshot

        Returns:
            Dictionary with 'new', 'modified', and 'deleted' tag lists
        """
        # Create dictionaries indexed by tag name
        tags_a_dict = {tag.tag_name: tag for tag in tags_a}
        tags_b_dict = {tag.tag_name: tag for tag in tags_b}

        # Detect new tags (in B but not in A)
        new_tags = [tag for name, tag in tags_b_dict.items() if name not in tags_a_dict]

        # Detect deleted tags (in A but not in B)
        deleted_tags = [tag for name, tag in tags_a_dict.items() if name not in tags_b_dict]

        # Detect modified tags (in both but with different attributes)
        modified_tags = []
        for name, tag_b in tags_b_dict.items():
            if name in tags_a_dict:
                tag_a = tags_a_dict[name]
                if self._has_tag_changed(tag_a, tag_b):
                    modified_tags.append(
                        {
                            "tag_name": name,
                            "old": tag_a.model_dump(),
                            "new": tag_b.model_dump(),
                            "changes": self._get_tag_differences(tag_a, tag_b),
                        }
                    )

        return {"new": new_tags, "modified": modified_tags, "deleted": deleted_tags}

    def _compare_blocks(
        self, blocks_a: list[BlockData], blocks_b: list[BlockData]
    ) -> dict:
        """Compare blocks between two snapshots.

        Args:
            blocks_a: Blocks from first snapshot
            blocks_b: Blocks from second snapshot

        Returns:
            Dictionary with 'new' and 'deleted' block lists
        """
        blocks_a_dict = {block.block_name: block for block in blocks_a}
        blocks_b_dict = {block.block_name: block for block in blocks_b}

        new_blocks = [
            block for name, block in blocks_b_dict.items() if name not in blocks_a_dict
        ]
        deleted_blocks = [
            block for name, block in blocks_a_dict.items() if name not in blocks_b_dict
        ]

        return {"new": new_blocks, "deleted": deleted_blocks}

    def _compare_hardware(
        self, hardware_a: list[HardwareData], hardware_b: list[HardwareData]
    ) -> dict:
        """Compare hardware between two snapshots.

        Args:
            hardware_a: Hardware from first snapshot
            hardware_b: Hardware from second snapshot

        Returns:
            Dictionary with 'new' and 'deleted' hardware lists
        """
        hardware_a_dict = {hw.device_name: hw for hw in hardware_a}
        hardware_b_dict = {hw.device_name: hw for hw in hardware_b}

        new_hardware = [
            hw for name, hw in hardware_b_dict.items() if name not in hardware_a_dict
        ]
        deleted_hardware = [
            hw for name, hw in hardware_a_dict.items() if name not in hardware_b_dict
        ]

        return {"new": new_hardware, "deleted": deleted_hardware}

    def _has_tag_changed(self, tag_a: TagData, tag_b: TagData) -> bool:
        """Check if a tag has changed between snapshots.

        Args:
            tag_a: Tag from first snapshot
            tag_b: Tag from second snapshot

        Returns:
            True if tag has changed, False otherwise
        """
        return (
            tag_a.tag_type != tag_b.tag_type
            or tag_a.tag_address != tag_b.tag_address
            or tag_a.tag_description != tag_b.tag_description
            or tag_a.hardware_reference != tag_b.hardware_reference
            or tag_a.block_reference != tag_b.block_reference
        )

    def _get_tag_differences(self, tag_a: TagData, tag_b: TagData) -> list[dict]:
        """Get specific field differences between two tags.

        Args:
            tag_a: Tag from first snapshot
            tag_b: Tag from second snapshot

        Returns:
            List of dictionaries describing each change
        """
        differences = []

        if tag_a.tag_type != tag_b.tag_type:
            differences.append(
                {"field": "Type", "old": tag_a.tag_type, "new": tag_b.tag_type}
            )

        if tag_a.tag_address != tag_b.tag_address:
            differences.append(
                {"field": "Address", "old": tag_a.tag_address, "new": tag_b.tag_address}
            )

        if tag_a.tag_description != tag_b.tag_description:
            differences.append(
                {
                    "field": "Description",
                    "old": tag_a.tag_description,
                    "new": tag_b.tag_description,
                }
            )

        if tag_a.hardware_reference != tag_b.hardware_reference:
            differences.append(
                {
                    "field": "Hardware Reference",
                    "old": tag_a.hardware_reference,
                    "new": tag_b.hardware_reference,
                }
            )

        if tag_a.block_reference != tag_b.block_reference:
            differences.append(
                {
                    "field": "Block Reference",
                    "old": tag_a.block_reference,
                    "new": tag_b.block_reference,
                }
            )

        return differences

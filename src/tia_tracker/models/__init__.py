"""Data models for TIA Version Tracker.

Pydantic models for type-safe data handling.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TagData(BaseModel):
    """Tag metadata extracted from TIA Portal project."""

    tag_name: str
    tag_type: Optional[str] = None
    tag_address: Optional[str] = None
    tag_description: Optional[str] = None
    hardware_reference: Optional[str] = None
    block_reference: Optional[str] = None


class BlockData(BaseModel):
    """PLC block information."""

    block_name: str
    block_type: Optional[str] = None
    block_number: Optional[int] = None


class HardwareData(BaseModel):
    """Hardware configuration data."""

    device_name: str
    device_type: Optional[str] = None
    ip_address: Optional[str] = None
    rack_slot: Optional[str] = None


class ExtractedData(BaseModel):
    """Complete extracted data from .zap15 file."""

    tags: list[TagData] = []
    blocks: list[BlockData] = []
    hardware: list[HardwareData] = []
    file_hash: str


class ProjectModel(BaseModel):
    """Project database model."""

    id: Optional[int] = None
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SnapshotModel(BaseModel):
    """Snapshot database model."""

    id: Optional[int] = None
    project_id: int
    snapshot_date: Optional[datetime] = None
    operator: str
    file_name: Optional[str] = None
    file_hash: str


class ComparisonResult(BaseModel):
    """Results from comparing two snapshots."""

    new_tags: list[TagData] = []
    modified_tags: list[dict] = []
    deleted_tags: list[TagData] = []
    new_blocks: list[BlockData] = []
    deleted_blocks: list[BlockData] = []
    new_hardware: list[HardwareData] = []
    deleted_hardware: list[HardwareData] = []

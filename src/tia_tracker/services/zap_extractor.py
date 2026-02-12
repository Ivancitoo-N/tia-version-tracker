""".zap15 file extraction service.

Extracts metadata from TIA Portal .zap15 archive files.
"""

import hashlib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional

from ..models import BlockData, ExtractedData, HardwareData, TagData


import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ZapExtractor:
    """Extracts metadata from .zap15 files."""

    def __init__(self):
        """Initialize the extractor."""
        pass

    def extract_from_directory(self, directory_path: str | Path) -> ExtractedData:
        """Extract metadata from a directory containing XML files (Openness export)."""
        directory_path = Path(directory_path)
        tags = []
        blocks = []
        hardware = []
        
        # Provide a dummy hash for directory-based extractions or calculate from XML content
        # For now, we can hash the files content sorted by name for consistency
        file_hash = "openness_export_" + str(hash(str(directory_path)))

        try:
            # List all XML files
            xml_files = list(directory_path.glob("*.xml"))
            logger.info(f"Processing {len(xml_files)} XML files from directory")
            
            for file_path in xml_files:
                try:
                    xml_content = file_path.read_text(encoding="utf-8")
                    file_name = file_path.name
                    logger.debug(f"Processing {file_name}")

                    # Try parsing (logic reused from extract_zap_file, essentially)
                    # Since Openness exports usually name files by block/tag name, checking content is safer
                    
                    found_tags = self.parse_tags_xml(xml_content)
                    if found_tags:
                        tags.extend(found_tags)
                        
                    found_blocks = self.parse_blocks_xml(xml_content)
                    if found_blocks:
                        blocks.extend(found_blocks)
                        
                    found_hw = self.parse_hardware_xml(xml_content)
                    if found_hw:
                         hardware.extend(found_hw)

                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

        except Exception as e:
             logger.error(f"Directory extraction error: {e}")
             raise

        return ExtractedData(
            tags=tags, blocks=blocks, hardware=hardware, file_hash=file_hash
        )

    def extract_zap_file(self, file_path: str | Path) -> ExtractedData:
        """Service for extracting data from .zap15/.zap20 files."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in {".zap15", ".zap20"}:
            raise ValueError(f"Invalid file extension: {file_path.suffix}")

        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)

        # Extract archive
        tags = []
        blocks = []
        hardware = []

        try:
            with zipfile.ZipFile(file_path, "r") as zap_archive:
                # List all files in the archive
                file_list = zap_archive.namelist()
                logger.info(f"Files in archive: {len(file_list)}")
                
                # Log first 10 files to understand structure
                for i, f in enumerate(file_list[:20]):
                    logger.debug(f"File {i}: {f}")

                # Extract and parse XML files
                for file_name in file_list:
                    # Generic TIA Portal XML export structure
                    if file_name.endswith(".xml"):
                        logger.info(f"Processing XML: {file_name}")
                        try:
                            xml_content = zap_archive.read(file_name).decode("utf-8")
                            
                            # Debug: print first 200 chars to identify file type
                            print(f"[DEBUG] XML Start: {xml_content[:200]}...")

                            # Try to parse as tags
                            # Expanded keywords for detection
                            if any(k in file_name.lower() for k in ["tag", "variable", "global"]):
                                found_tags = self.parse_tags_xml(xml_content)
                                if found_tags:
                                    print(f"[DEBUG] Found {len(found_tags)} tags in {file_name}")
                                    tags.extend(found_tags)

                            # Try to parse as blocks
                            if any(k in file_name.lower() for k in ["block", "program", "ob", "fb", "fc", "db"]):
                                found_blocks = self.parse_blocks_xml(xml_content)
                                if found_blocks:
                                    print(f"[DEBUG] Found {len(found_blocks)} blocks in {file_name}")
                                    blocks.extend(found_blocks)

                            # Try to parse as hardware
                            if any(k in file_name.lower() for k in ["hardware", "device", "station"]):
                                found_hw = self.parse_hardware_xml(xml_content)
                                if found_hw:
                                    print(f"[DEBUG] Found {len(found_hw)} hardware items in {file_name}")
                                    hardware.extend(found_hw)
                        except Exception as e:
                            print(f"[ERROR] Failed to process {file_name}: {e}")

        except zipfile.BadZipFile:
            raise ValueError(f"Invalid ZIP archive: {file_path}")

        print(f"[DEBUG] Total extracted: {len(tags)} tags, {len(blocks)} blocks, {len(hardware)} hardware")
        
        return ExtractedData(
            tags=tags, blocks=blocks, hardware=hardware, file_hash=file_hash
        )

    def parse_tags_xml(self, xml_content: str) -> list[TagData]:
        """Parse tag definitions from XML content."""
        tags = []
        try:
            # Remove namespaces to simplify parsing
            import re
            xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content, count=1)
            
            root = ET.fromstring(xml_content)
            
            # TIA Portal XML structure varies. Often it's Document > Engineering > ...
            # We search for any element that looks like a PlcTag
            
            # Strategy 1: Look for "AttributeList" containing "Name", "DataType", etc.
            # Strategy 2: Look for specific XML tag names like <PlcTag> or <Tag>
            
            for element in root.iter():
                # Check for standard TIA Portal XML export structure (often SW.Tags.PlcTag)
                if "PlcTag" in element.tag or element.tag == "Tag":
                    # Extract attributes from child elements or attributes
                    name = element.findtext("Name") or element.get("Name")
                    
                    # Sometimes data is in AttributeList
                    attr_list = element.find("AttributeList")
                    if attr_list is not None:
                        name = attr_list.findtext("Name") or name
                        data_type = attr_list.findtext("DataTypeName") # Often DataTypeName in XML
                        address = attr_list.findtext("LogicalAddress")
                        comment = attr_list.findtext("Comment")
                    else:
                        data_type = element.findtext("DataType") or element.get("DataType")
                        address = element.findtext("LogicalAddress") or element.findtext("Address") or element.get("Address")
                        comment = element.findtext("Comment") or element.get("Comment")

                    if name:
                        tags.append(TagData(
                            tag_name=name,
                            tag_type=data_type,
                            tag_address=address,
                            tag_description=comment
                        ))
                        
        except Exception as e:
            print(f"[ERROR] XML parsing error: {e}")
            pass

        return tags

    def parse_blocks_xml(self, xml_content: str) -> list[BlockData]:
        """Parse block definitions from XML content."""
        blocks = []
        try:
            import re
            xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content, count=1)
            root = ET.fromstring(xml_content)

            # Look for block elements. In TIA Openness XML, blocks are often root elements or under generic containers
            # We look for elements that have a "Number" and "Type" or are named like standard blocks
            
            for element in root.iter():
                # Check for various block types
                # SW.Blocks.OB, SW.Blocks.FB, etc.
                tag_name = element.tag.lower()
                if any(x in tag_name for x in ["ob", "fb", "fc", "db", "block"]):
                    
                    # Name is often an attribute or a child 'Name' element
                    # In some XMLs (TIA Openness), Name is in <AttributeList><Name>...</Name></AttributeList>
                    name = None
                    block_type = None
                    number = None
                    
                    # Check AttributeList first (common in V15+)
                    attr_list = element.find("AttributeList")
                    if attr_list is not None:
                        name = attr_list.findtext("Name")
                        block_type = attr_list.findtext("Type") or attr_list.findtext("Interface/Type") # Accessing deep structure blindly is hard, assume flat for now or mapped
                        
                        # Type might be inferred from tag name (e.g. <OB> -> OB)
                        if not block_type:
                            if "ob" in tag_name: block_type = "OB"
                            elif "fb" in tag_name: block_type = "FB"
                            elif "fc" in tag_name: block_type = "FC"
                            elif "db" in tag_name: block_type = "DB"
                        
                        number_str = attr_list.findtext("Number")
                        if number_str:
                             try: number = int(number_str)
                             except: pass
                    
                    # Fallback to direct attributes/children
                    if not name:
                         name = element.get("Name") or element.findtext("Name")
                    
                    if not block_type:
                         block_type = element.get("Type") or element.findtext("Type")
                    
                    if number is None:
                        num_str = element.get("Number") or element.findtext("Number")
                        if num_str:
                            try: number = int(num_str)
                            except: pass

                    if name and block_type:
                        blocks.append(BlockData(
                            block_name=name,
                            block_type=block_type,
                            block_number=number
                        ))

        except Exception as e:
            print(f"[ERROR] Block parsing error: {e}")
            pass

        return blocks

    def parse_hardware_xml(self, xml_content: str) -> list[HardwareData]:
        """Parse hardware configuration from XML content."""
        hardware = []
        try:
            import re
            xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content, count=1)
            root = ET.fromstring(xml_content)

            # Hardware usually in <Device> or <Module>
            for element in root.iter():
                if "Device" in element.tag or "Module" in element.tag:
                    name = None
                    device_type = None
                    ip = None
                    slot = None
                    
                    # Check AttributeList
                    attr_list = element.find("AttributeList")
                    if attr_list is not None:
                        name = attr_list.findtext("Name")
                        device_type = attr_list.findtext("TypeName")
                    
                    # Direct attributes
                    if not name:
                        name = element.get("Name") or element.findtext("Name")
                    
                    if not device_type:
                        device_type = element.get("Type") or element.findtext("Type")
                        
                    # IP Address often deeper in structure, keep simple check for now
                    # Slot often in 'Designation' or 'Position'
                    
                    if name:
                        hardware.append(HardwareData(
                            device_name=name,
                            device_type=device_type,
                            ip_address=ip, # Extraction logic for IP is complex in random XMLs
                            rack_slot=slot
                        ))

        except Exception as e:
            print(f"[ERROR] Hardware parsing error: {e}")
            pass

        return hardware

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

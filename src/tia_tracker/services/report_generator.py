"""PDF report generation service.

Generates professional PDF reports from comparison results using reportlab.
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from ..models import ComparisonResult


class ReportGenerator:
    """Generates PDF reports from comparison results."""

    def __init__(self, output_folder: str = "reports"):
        """Initialize report generator.

        Args:
            output_folder: Folder to save generated reports
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()

    def generate_comparison_report(
        self,
        comparison_result: ComparisonResult,
        project_name: str,
        snapshot_a_info: dict,
        snapshot_b_info: dict,
    ) -> str:
        """Generate a PDF report from comparison results.

        Args:
            comparison_result: Results from snapshot comparison
            project_name: Name of the project
            snapshot_a_info: Information about first snapshot
            snapshot_b_info: Information about second snapshot

        Returns:
            Path to generated PDF file
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project_name}_comparison_{timestamp}.pdf"
        output_path = self.output_folder / filename

        # Create PDF document
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a73e8"),
            spaceAfter=30,
        )
        story.append(Paragraph(f"TIA Portal Version Comparison Report", title_style))
        story.append(Spacer(1, 12))

        # Project information
        story.append(Paragraph(f"<b>Project:</b> {project_name}", self.styles["Normal"]))
        story.append(Spacer(1, 6))

        # Snapshot information
        info_data = [
            ["Snapshot A", f"{snapshot_a_info['snapshot_date']} by {snapshot_a_info['operator']}"],
            ["Snapshot B", f"{snapshot_b_info['snapshot_date']} by {snapshot_b_info['operator']}"],
        ]
        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 1), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(info_table)
        story.append(Spacer(1, 20))

        # Executive summary
        story.append(Paragraph("Executive Summary", self.styles["Heading2"]))
        story.append(Spacer(1, 12))

        summary_data = [
            ["Change Type", "Count"],
            ["✅ New Tags", str(len(comparison_result.new_tags))],
            ["⚠️ Modified Tags", str(len(comparison_result.modified_tags))],
            ["❌ Deleted Tags", str(len(comparison_result.deleted_tags))],
            ["New Blocks", str(len(comparison_result.new_blocks))],
            ["Deleted Blocks", str(len(comparison_result.deleted_blocks))],
            ["New Hardware", str(len(comparison_result.new_hardware))],
            ["Deleted Hardware", str(len(comparison_result.deleted_hardware))],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(summary_table)
        story.append(PageBreak())

        # New Tags Section
        if comparison_result.new_tags:
            story.append(Paragraph("✅ New Tags", self.styles["Heading2"]))
            story.append(Spacer(1, 12))

            tags_data = [["Tag Name", "Type", "Address", "Description"]]
            for tag in comparison_result.new_tags:
                tags_data.append(
                    [
                        tag.tag_name,
                        tag.tag_type or "",
                        tag.tag_address or "",
                        tag.tag_description or "",
                    ]
                )

            tags_table = Table(tags_data, colWidths=[1.5 * inch, 1.2 * inch, 1.2 * inch, 2.6 * inch])
            tags_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34a853")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#e6f4ea")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ]
                )
            )
            story.append(tags_table)
            story.append(Spacer(1, 20))

        # Modified Tags Section
        if comparison_result.modified_tags:
            story.append(Paragraph("⚠️ Modified Tags", self.styles["Heading2"]))
            story.append(Spacer(1, 12))

            for mod in comparison_result.modified_tags:
                story.append(
                    Paragraph(f"<b>{mod['tag_name']}</b>", self.styles["Heading3"])
                )

                changes_data = [["Field", "Old Value", "New Value"]]
                for change in mod["changes"]:
                    changes_data.append(
                        [change["field"], str(change["old"]), str(change["new"])]
                    )

                changes_table = Table(
                    changes_data, colWidths=[1.5 * inch, 2.25 * inch, 2.25 * inch]
                )
                changes_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fbbc04")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 9),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fef7e0")),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ]
                    )
                )
                story.append(changes_table)
                story.append(Spacer(1, 12))

        # Deleted Tags Section
        if comparison_result.deleted_tags:
            story.append(PageBreak())
            story.append(Paragraph("❌ Deleted Tags", self.styles["Heading2"]))
            story.append(Spacer(1, 12))

            deleted_data = [["Tag Name", "Type", "Address", "Description"]]
            for tag in comparison_result.deleted_tags:
                deleted_data.append(
                    [
                        tag.tag_name,
                        tag.tag_type or "",
                        tag.tag_address or "",
                        tag.tag_description or "",
                    ]
                )

            deleted_table = Table(
                deleted_data, colWidths=[1.5 * inch, 1.2 * inch, 1.2 * inch, 2.6 * inch]
            )
            deleted_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ea4335")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fce8e6")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ]
                )
            )
            story.append(deleted_table)

        # Build PDF
        doc.build(story)

        return str(output_path)

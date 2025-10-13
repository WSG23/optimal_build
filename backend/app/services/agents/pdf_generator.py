"""PDF generation service for professional packs."""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle

from app.services.storage import StorageService, get_storage_service


class PageNumberCanvas(canvas.Canvas):
    """Custom canvas to add page numbers and headers/footers."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.company_name = kwargs.get("company_name", "Commercial Property Advisors")
        self.document_title = kwargs.get("document_title", "Professional Pack")

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add page numbers to each page."""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_header_footer(self, page_count):
        """Draw headers and footers on each page."""
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.grey)

        # Footer
        self.drawString(
            A4[0] / 2, 0.5 * inch, f"Page {self._pageNumber} of {page_count}"
        )

        # Header (except first page)
        if self._pageNumber > 1:
            self.drawString(0.75 * inch, A4[1] - 0.5 * inch, self.company_name)
            self.drawRightString(
                A4[0] - 0.75 * inch, A4[1] - 0.5 * inch, self.document_title
            )

            # Header line
            self.setStrokeColor(colors.grey)
            self.setLineWidth(0.5)
            self.line(
                0.75 * inch, A4[1] - 0.6 * inch, A4[0] - 0.75 * inch, A4[1] - 0.6 * inch
            )


class CoverPage(Flowable):
    """Custom flowable for cover page."""

    def __init__(self, title, subtitle, property_info, logo_path=None):
        Flowable.__init__(self)
        self.title = title
        self.subtitle = subtitle
        self.property_info = property_info
        self.logo_path = logo_path
        self.width = A4[0]
        self.height = A4[1]

    def draw(self):
        """Draw the cover page."""
        canvas = self.canv

        # Background color
        canvas.setFillColor(colors.HexColor("#f8f9fa"))
        canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Logo
        if self.logo_path and os.path.exists(self.logo_path):
            canvas.drawImage(
                self.logo_path,
                self.width / 2 - inch,
                self.height - 2.5 * inch,
                width=2 * inch,
                height=inch,
                mask="auto",
                preserveAspectRatio=True,
            )

        # Title
        canvas.setFont("Helvetica-Bold", 36)
        canvas.setFillColor(colors.HexColor("#2c3e50"))
        title_y = self.height - 4 * inch
        for line in self.title.split("\n"):
            canvas.drawCentredString(self.width / 2, title_y, line)
            title_y -= 48

        # Subtitle
        canvas.setFont("Helvetica", 18)
        canvas.setFillColor(colors.HexColor("#34495e"))
        canvas.drawCentredString(self.width / 2, title_y - 24, self.subtitle)

        # Property info box
        box_y = self.height / 2
        box_height = 2 * inch
        canvas.setFillColor(colors.white)
        canvas.roundRect(
            inch,
            box_y - box_height,
            self.width - 2 * inch,
            box_height,
            10,
            fill=1,
            stroke=1,
        )

        # Property details
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor("#2c3e50"))
        text_y = box_y - 0.5 * inch

        for key, value in self.property_info.items():
            canvas.drawString(1.5 * inch, text_y, f"{key}:")
            canvas.setFont("Helvetica", 14)
            canvas.drawString(3.5 * inch, text_y, str(value))
            canvas.setFont("Helvetica-Bold", 14)
            text_y -= 0.3 * inch

        # Date
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            self.width / 2, 1.5 * inch, datetime.now().strftime("%B %Y")
        )

        # Confidentiality notice
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(
            self.width / 2,
            inch,
            "CONFIDENTIAL - This document contains proprietary information",
        )


class PDFGenerator:
    """Base PDF generator with common functionality."""

    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage_service = storage_service or get_storage_service()
        self.styles = self._setup_styles()

    def _setup_styles(self) -> Dict[str, ParagraphStyle]:
        """Setup custom paragraph styles."""
        styles = getSampleStyleSheet()

        # Custom styles
        styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=30,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CustomHeading1",
                parent=styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=20,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CustomHeading2",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#34495e"),
                spaceAfter=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="Disclaimer",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_JUSTIFY,
                borderWidth=1,
                borderColor=colors.grey,
                borderPadding=10,
                backColor=colors.HexColor("#f8f9fa"),
            )
        )

        styles.add(
            ParagraphStyle(
                name="Executive",
                parent=styles["Normal"],
                fontSize=11,
                alignment=TA_JUSTIFY,
                leading=16,
                spaceAfter=12,
            )
        )

        return styles

    def _create_header_table(self, title: str, subtitle: str = "") -> Table:
        """Create a standard header table."""
        data = [[title]]
        if subtitle:
            data.append([subtitle])

        table = Table(data, colWidths=[7 * inch])
        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 16),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
            ]
        )

        if subtitle:
            style.add("FONT", (0, 1), (-1, 1), "Helvetica", 12)
            style.add("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#34495e"))

        table.setStyle(style)
        return table

    def _create_data_table(
        self,
        data: List[List[str]],
        col_widths: Optional[List[float]] = None,
        highlight_header: bool = True,
    ) -> Table:
        """Create a styled data table."""
        table = Table(data, colWidths=col_widths)

        style = TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )

        if highlight_header and len(data) > 0:
            style.add("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e"))
            style.add("TEXTCOLOR", (0, 0), (-1, 0), colors.white)
            style.add("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
            style.add("FONTSIZE", (0, 0), (-1, 0), 11)

        # Alternate row colors
        for i in range(1, len(data), 2):
            style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8f9fa"))

        table.setStyle(style)
        return table

    def _create_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        width: float = 400,
        height: float = 200,
    ) -> Drawing:
        """Create various chart types."""
        drawing = Drawing(width, height)

        if chart_type == "bar":
            chart = VerticalBarChart()
            chart.x = 50
            chart.y = 50
            chart.height = height - 100
            chart.width = width - 100
            chart.data = data["values"]
            chart.categoryAxis.categoryNames = data["categories"]
            chart.valueAxis.valueMin = 0
            chart.valueAxis.valueMax = (
                max(max(series) for series in data["values"]) * 1.1
            )
            chart.bars[0].fillColor = colors.HexColor("#2c3e50")
            drawing.add(chart)

        elif chart_type == "pie":
            chart = Pie()
            chart.x = width / 2 - 75
            chart.y = height / 2 - 75
            chart.width = 150
            chart.height = 150
            chart.data = data["values"]
            chart.labels = data["labels"]
            chart.slices.strokeWidth = 0.5
            drawing.add(chart)

        elif chart_type == "line":
            chart = HorizontalLineChart()
            chart.x = 50
            chart.y = 50
            chart.height = height - 100
            chart.width = width - 100
            chart.data = data["values"]
            chart.categoryAxis.categoryNames = data["categories"]
            drawing.add(chart)

        return drawing

    def _add_disclaimer(
        self, disclaimer_type: str, custom_text: Optional[str] = None
    ) -> Paragraph:
        """Add appropriate disclaimer based on type."""
        disclaimers = {
            "acquisition": (
                "IMPORTANT NOTICE: This document represents an illustrative feasibility "
                "analysis and is subject to detailed technical study. All projections, "
                "calculations, and assessments are preliminary and based on available "
                "information at the time of preparation. Prospective purchasers/developers "
                "must conduct their own due diligence including but not limited to legal, "
                "technical, environmental, and financial investigations."
            ),
            "development": (
                "DISCLAIMER: This development analysis is for illustrative purposes only "
                "and subject to detailed technical feasibility studies, regulatory approvals, "
                "and market conditions. All development parameters, cost estimates, and "
                "financial projections are indicative and may vary significantly. "
                "Professional advice should be sought before making any investment decisions."
            ),
            "sales": (
                "NOTICE: The indicative layouts, specifications, and visualizations presented "
                "are subject to final documentation and regulatory approvals. All information "
                "is provided in good faith but without warranty. Prospective buyers/tenants "
                "are advised to verify all details independently and seek professional advice."
            ),
            "leasing": (
                "LEASING DISCLAIMER: All layouts, specifications, and rental information are "
                "indicative only and subject to final lease documentation. Availability, "
                "pricing, and terms are subject to change without notice. Interested parties "
                "should conduct their own inspections and negotiations."
            ),
        }

        text = custom_text or disclaimers.get(
            disclaimer_type, disclaimers["acquisition"]
        )

        return Paragraph(text, self.styles["Disclaimer"])

    async def save_to_storage(
        self, pdf_buffer: io.BytesIO, filename: str, property_id: Optional[str] = None
    ) -> str:
        """Save PDF to storage and return URL."""
        key = f"reports/{property_id or 'general'}/{filename}"

        # Use store_bytes which is the correct StorageService method
        result = self.storage_service.store_bytes(
            key=key, payload=pdf_buffer.getvalue(), content_type="application/pdf"
        )

        return result.uri

    def format_currency(self, value: Union[int, float], currency: str = "SGD") -> str:
        """Format currency values."""
        if currency == "SGD":
            return f"S${value:,.0f}"
        return f"{currency} {value:,.0f}"

    def format_area(self, value: Union[int, float], unit: str = "sqm") -> str:
        """Format area values."""
        return f"{value:,.0f} {unit}"

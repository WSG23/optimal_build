"""Marketing Materials generator for selling/leasing completed projects."""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
from uuid import UUID

from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property, PropertyPhoto, PropertyType, RentalListing
from app.services.agents.investment_memorandum import InvestmentHighlight
from app.services.agents.pdf_generator import PageNumberCanvas, PDFGenerator


class FloorPlanDiagram(Flowable):
    """Custom flowable for floor plan visualization."""

    def __init__(
        self,
        floor_data: Dict[str, Any],
        width: float = 6 * inch,
        height: float = 4 * inch,
    ):
        Flowable.__init__(self)
        self.floor_data = floor_data
        self.width = width
        self.height = height

    def draw(self):
        """Draw simplified floor plan."""
        # Background
        self.canv.setFillColor(colors.HexColor("#f8f9fa"))
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=1)

        # Title
        self.canv.setFont("Helvetica-Bold", 14)
        self.canv.setFillColor(colors.HexColor("#2c3e50"))
        self.canv.drawString(
            10, self.height - 20, f"Floor {self.floor_data.get('floor', 'Typical')}"
        )

        # Floor plate outline
        margin = 20
        plate_width = self.width - 2 * margin
        plate_height = self.height - 60

        self.canv.setStrokeColor(colors.HexColor("#34495e"))
        self.canv.setLineWidth(2)
        self.canv.rect(margin, 20, plate_width, plate_height, fill=0)

        # Units/spaces
        if "units" in self.floor_data:
            unit_width = plate_width / len(self.floor_data["units"])
            for i, unit in enumerate(self.floor_data["units"]):
                x = margin + i * unit_width
                self.canv.setFillColor(
                    colors.HexColor("#e8f4fd")
                    if unit["available"]
                    else colors.HexColor("#f0f0f0")
                )
                self.canv.rect(
                    x + 2, 22, unit_width - 4, plate_height - 4, fill=1, stroke=1
                )

                # Unit label
                self.canv.setFont("Helvetica", 10)
                self.canv.setFillColor(colors.black)
                self.canv.drawCentredString(
                    x + unit_width / 2, 20 + plate_height / 2, unit["name"]
                )

                # Size
                self.canv.setFont("Helvetica", 8)
                self.canv.drawCentredString(
                    x + unit_width / 2,
                    20 + plate_height / 2 - 15,
                    f"{unit['size']} sqm",
                )


class AmenityIcons(Flowable):
    """Custom flowable for amenity icons grid."""

    def __init__(self, amenities: List[str], width: float = 6 * inch):
        Flowable.__init__(self)
        self.amenities = amenities
        self.width = width
        self.height = 2 * inch

    def draw(self):
        """Draw amenity icons."""
        icons_per_row = 4
        icon_size = 40
        spacing = (self.width - icons_per_row * icon_size) / (icons_per_row + 1)

        for i, amenity in enumerate(self.amenities[:8]):  # Max 8 icons
            row = i // icons_per_row
            col = i % icons_per_row

            x = spacing + col * (icon_size + spacing)
            y = self.height - 60 - row * 60

            # Icon background
            self.canv.setFillColor(colors.HexColor("#e8f4fd"))
            self.canv.circle(
                x + icon_size / 2, y + icon_size / 2, icon_size / 2, fill=1, stroke=1
            )

            # Icon symbol (simplified)
            self.canv.setFont("Helvetica-Bold", 20)
            self.canv.setFillColor(colors.HexColor("#2c3e50"))
            symbol = self._get_icon_symbol(amenity)
            self.canv.drawCentredString(
                x + icon_size / 2, y + icon_size / 2 - 7, symbol
            )

            # Label
            self.canv.setFont("Helvetica", 8)
            self.canv.drawCentredString(x + icon_size / 2, y - 10, amenity[:12])

    def _get_icon_symbol(self, amenity: str) -> str:
        """Get symbol for amenity."""
        symbols = {
            "parking": "P",
            "gym": "G",
            "security": "S",
            "cafe": "C",
            "meeting": "M",
            "reception": "R",
            "wifi": "W",
            "elevator": "E",
        }

        for key, symbol in symbols.items():
            if key in amenity.lower():
                return symbol
        return amenity[0].upper()


class MarketingMaterialsGenerator(PDFGenerator):
    """Generate marketing materials for selling/leasing."""

    async def generate_sales_brochure(
        self,
        property_id: UUID,
        session: AsyncSession,
        material_type: str = "sale",  # 'sale' or 'lease'
        contact_info: Optional[Dict[str, str]] = None,
    ) -> io.BytesIO:
        """Generate sales/leasing brochure."""
        # Load property data
        property_data = await self._load_property_data(property_id, session)
        photos = await self._load_property_photos(property_id, session)

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build content
        story = []

        # 1. Cover Page with hero image
        story.extend(self._create_marketing_cover(property_data, material_type))
        story.append(PageBreak())

        # 2. Property Overview
        story.extend(self._create_property_highlights(property_data, material_type))
        story.append(PageBreak())

        # 3. Location & Connectivity
        story.extend(self._create_location_benefits(property_data))
        story.append(PageBreak())

        # 4. Floor Plans & Specifications
        story.extend(self._create_floor_plans(property_data))
        story.append(PageBreak())

        # 5. Amenities & Features
        story.extend(self._create_amenities_section(property_data))
        story.append(PageBreak())

        # 6. Photo Gallery
        if photos:
            story.extend(self._create_photo_gallery(photos))
            story.append(PageBreak())

        # 7. Availability & Pricing
        story.extend(self._create_availability_section(property_data, material_type))
        story.append(PageBreak())

        # 8. Contact & Next Steps
        story.extend(self._create_contact_section(contact_info, material_type))

        # Build PDF
        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: PageNumberCanvas(
                *args,
                company_name="Commercial Property Advisors",
                document_title=f"{'For Sale' if material_type == 'sale' else 'For Lease'}",
                **kwargs,
            ),
        )

        buffer.seek(0)
        return buffer

    async def generate_email_flyer(
        self, property_id: UUID, session: AsyncSession, material_type: str = "lease"
    ) -> io.BytesIO:
        """Generate single-page email flyer."""
        # Load property data
        property_data = await self._load_property_data(property_id, session)
        photos = await self._load_property_photos(property_id, session, limit=1)

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create single-page document
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Background
        c.setFillColor(colors.white)
        c.rect(0, 0, width, height, fill=1)

        # Header banner
        c.setFillColor(colors.HexColor("#2c3e50"))
        c.rect(0, height - 2 * inch, width, 2 * inch, fill=1)

        # Property name
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(colors.white)
        c.drawCentredString(
            width / 2, height - 1 * inch, property_data["property"].name
        )

        # Tagline
        c.setFont("Helvetica", 14)
        tagline = (
            "Premium Space Available"
            if material_type == "lease"
            else "Exceptional Investment Opportunity"
        )
        c.drawCentredString(width / 2, height - 1.4 * inch, tagline)

        # Main content area
        y_position = height - 2.5 * inch

        # Key highlights box
        c.setFillColor(colors.HexColor("#f8f9fa"))
        c.roundRect(
            0.5 * inch, y_position - 2 * inch, width - inch, 1.8 * inch, 10, fill=1
        )

        # Highlights content
        highlights = self._get_key_highlights(property_data, material_type)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2c3e50"))

        x_positions = [1 * inch, 3 * inch, 5 * inch]
        for i, (label, value) in enumerate(highlights[:3]):
            if i < len(x_positions):
                c.drawString(x_positions[i], y_position - 0.5 * inch, label)
                c.setFont("Helvetica", 20)
                c.drawString(x_positions[i], y_position - 1 * inch, value)
                c.setFont("Helvetica-Bold", 12)

        y_position -= 2.5 * inch

        # Property image placeholder
        if photos:
            # In production, load and insert actual image
            c.setFillColor(colors.HexColor("#e0e0e0"))
            c.rect(0.5 * inch, y_position - 3 * inch, width - inch, 2.5 * inch, fill=1)
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.grey)
            c.drawCentredString(width / 2, y_position - 1.5 * inch, "[Property Image]")

        y_position -= 3.5 * inch

        # Call to action
        c.setFillColor(colors.HexColor("#3498db"))
        c.roundRect(
            2 * inch, y_position - 0.7 * inch, width - 4 * inch, 0.6 * inch, 5, fill=1
        )

        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.white)
        cta_text = (
            "Schedule a Viewing"
            if material_type == "lease"
            else "Request Investment Pack"
        )
        c.drawCentredString(width / 2, y_position - 0.5 * inch, cta_text)

        # Footer contact
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#7f8c8d"))
        c.drawCentredString(
            width / 2,
            0.5 * inch,
            "Commercial Property Advisors | +65 6XXX XXXX | info@cpAdvisors.com",
        )

        # Generate QR code for property link
        qr_code = qr.QrCodeWidget(f"https://cpAdvisors.com/property/{property_id}")
        bounds = qr_code.getBounds()
        width_qr = bounds[2] - bounds[0]
        height_qr = bounds[3] - bounds[1]
        d = Drawing(45, 45, transform=[45.0 / width_qr, 0, 0, 45.0 / height_qr, 0, 0])
        d.add(qr_code)
        d.drawOn(c, width - 1.5 * inch, 0.5 * inch)

        c.save()
        buffer.seek(0)
        return buffer

    async def _load_property_data(
        self, property_id: UUID, session: AsyncSession
    ) -> Dict[str, Any]:
        """Load property data for marketing."""
        # Load property
        stmt = select(Property).where(Property.id == property_id)
        result = await session.execute(stmt)
        property_obj = result.scalar_one()

        # Load active rentals
        stmt = (
            select(RentalListing)
            .where(
                RentalListing.property_id == property_id,
                RentalListing.is_active,
            )
            .order_by(RentalListing.floor_level)
        )
        result = await session.execute(stmt)
        rentals = result.scalars().all()

        return {
            "property": property_obj,
            "rentals": rentals,
            "total_available": sum(r.floor_area_sqm or 0 for r in rentals),
            "available_units": len(rentals),
        }

    async def _load_property_photos(
        self, property_id: UUID, session: AsyncSession, limit: Optional[int] = None
    ) -> List[PropertyPhoto]:
        """Load property photos."""
        stmt = (
            select(PropertyPhoto)
            .where(PropertyPhoto.property_id == property_id)
            .order_by(PropertyPhoto.capture_date.desc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

    def _create_marketing_cover(
        self, property_data: Dict[str, Any], material_type: str
    ) -> List[Any]:
        """Create attractive marketing cover."""
        story = []
        property_obj = property_data["property"]

        # Hero section
        hero_style = ParagraphStyle(
            "HeroStyle",
            parent=self.styles["Title"],
            fontSize=36,
            textColor=colors.HexColor("#2c3e50"),
            alignment=TA_CENTER,
            spaceAfter=20,
        )

        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph(property_obj.name, hero_style))

        # Subtitle
        subtitle = "AVAILABLE FOR LEASE" if material_type == "lease" else "FOR SALE"
        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=self.styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#3498db"),
            alignment=TA_CENTER,
            spaceAfter=40,
        )
        story.append(Paragraph(subtitle, subtitle_style))

        # Property type and location
        location_text = (
            f"{property_obj.property_type.value.replace('_', ' ').title()} • "
            f"{property_obj.district} • Singapore"
        )
        story.append(Paragraph(location_text, self.styles["Heading2"]))

        story.append(Spacer(1, inch))

        # Key stats
        stats_data = [
            [
                f"{self.format_area(property_data['total_available'])}\nAvailable",
                f"{property_data['available_units']}\nUnits",
                f"{property_obj.floors_above_ground or 'Multiple'}\nFloors",
                "Immediate\nAvailability",
            ]
        ]

        stats_table = Table(stats_data, colWidths=[1.5 * inch] * 4)
        stats_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 14),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                    ("LINEBELOW", (0, 0), (-1, -1), 2, colors.HexColor("#3498db")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                ]
            )
        )
        story.append(stats_table)

        return story

    def _create_property_highlights(
        self, property_data: Dict[str, Any], material_type: str
    ) -> List[Any]:
        """Create property highlights section."""
        story = []
        property_obj = property_data["property"]

        story.append(self._create_header_table("PROPERTY HIGHLIGHTS"))
        story.append(Spacer(1, 0.3 * inch))

        # Create highlight boxes
        highlights = InvestmentHighlight(
            [
                {
                    "label": "Total GFA",
                    "value": f"{property_obj.gross_floor_area_sqm/1000:.0f}k sqm",
                },
                {
                    "label": "Available",
                    "value": f"{property_data['total_available']:,.0f} sqm",
                },
                {
                    "label": "Floor Plate",
                    "value": f"{(property_obj.gross_floor_area_sqm or 0)/(property_obj.floors_above_ground or 1)/1000:.1f}k sqm",
                },
            ]
        )
        story.append(highlights)
        story.append(Spacer(1, 0.3 * inch))

        # Building features
        story.append(Paragraph("Building Features", self.styles["CustomHeading2"]))

        features = [
            f"Modern {property_obj.property_type.value.replace('_', ' ')} building",
            f"Built in {property_obj.year_built or 'recent years'} with recent renovations",
            "Efficient floor plates with flexible configurations",
            "High ceiling heights and natural lighting",
            "Green building certified",
            "24/7 security and access control",
            "Ample parking provisions",
            "Backup power and redundant systems",
        ]

        features_list = ListFlowable(
            [
                ListItem(Paragraph(f, self.styles["Normal"]), leftIndent=20)
                for f in features
            ],
            bulletType="bullet",
        )
        story.append(features_list)
        story.append(Spacer(1, 0.2 * inch))

        # Ideal for section
        story.append(Paragraph("Ideal For", self.styles["CustomHeading2"]))

        ideal_for = self._get_ideal_tenants(property_obj.property_type)
        ideal_text = (
            f"The property is ideally suited for {', '.join(ideal_for[:-1])} "
            f"and {ideal_for[-1]}. The flexible layout and modern amenities "
            "support various business requirements."
        )
        story.append(Paragraph(ideal_text, self.styles["Executive"]))

        return story

    def _create_location_benefits(self, property_data: Dict[str, Any]) -> List[Any]:
        """Create location and connectivity section."""
        story = []
        property_obj = property_data["property"]

        story.append(self._create_header_table("LOCATION & CONNECTIVITY"))
        story.append(Spacer(1, 0.3 * inch))

        # Location overview
        story.append(Paragraph("Strategic Location", self.styles["CustomHeading2"]))

        location_text = (
            f"Situated in the heart of {property_obj.district or 'the business district'}, "
            f"{property_obj.name} enjoys unparalleled connectivity and accessibility. "
            "The location offers the perfect balance of business convenience and lifestyle amenities."
        )
        story.append(Paragraph(location_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Transport connectivity
        story.append(Paragraph("Transportation", self.styles["CustomHeading2"]))

        transport_data = [
            ["Mode", "Details", "Distance/Time"],
            ["MRT", "Circle/Downtown Line", "3 min walk"],
            ["Bus", "Multiple routes available", "Bus stop at doorstep"],
            ["Expressway", "CTE/PIE access", "5 min drive"],
            ["Airport", "Changi Airport", "25 min drive"],
            ["CBD", "Raffles Place/Marina Bay", "10 min by MRT"],
        ]

        table = self._create_data_table(transport_data)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Nearby amenities
        story.append(Paragraph("Nearby Amenities", self.styles["CustomHeading2"]))

        amenities_data = [
            ["Category", "Options", "Walking Time"],
            ["Dining", "50+ restaurants and cafes", "1-5 min"],
            ["Banking", "Major banks and ATMs", "2-5 min"],
            ["Hotels", "5-star hotels nearby", "5-10 min"],
            ["Retail", "Shopping malls", "5-10 min"],
            ["Recreation", "Parks and fitness centers", "5-15 min"],
        ]

        table = self._create_data_table(amenities_data)
        story.append(table)

        return story

    def _create_floor_plans(self, property_data: Dict[str, Any]) -> List[Any]:
        """Create floor plans section."""
        story = []

        story.append(self._create_header_table("FLOOR PLANS & SPECIFICATIONS"))
        story.append(Spacer(1, 0.3 * inch))

        # Available units summary
        if property_data["rentals"]:
            story.append(Paragraph("Available Spaces", self.styles["CustomHeading2"]))

            units_data = [
                ["Floor", "Unit", "Size (sqm)", "Configuration", "Availability"]
            ]

            for rental in property_data["rentals"][:10]:  # Show max 10
                units_data.append(
                    [
                        rental.floor_level or "Ground",
                        rental.unit_number or "-",
                        f"{rental.floor_area_sqm:,.0f}",
                        "Open plan",
                        "Immediate",
                    ]
                )

            table = self._create_data_table(units_data)
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

        # Typical floor plan
        story.append(
            Paragraph("Typical Floor Configuration", self.styles["CustomHeading2"])
        )

        floor_data = {
            "floor": "Typical",
            "units": [
                {"name": "Unit A", "size": 500, "available": True},
                {"name": "Unit B", "size": 600, "available": False},
                {"name": "Unit C", "size": 550, "available": True},
            ],
        }

        floor_plan = FloorPlanDiagram(floor_data)
        story.append(floor_plan)
        story.append(Spacer(1, 0.2 * inch))

        # Specifications
        story.append(
            Paragraph("Technical Specifications", self.styles["CustomHeading2"])
        )

        specs = [
            "Floor to ceiling height: 3.0m (typical floor)",
            "Floor loading: 5.0 kN/m² + partitions",
            "Air-conditioning: VAV system with fresh air handling",
            "Power supply: 150W/m² with UPS backup for critical systems",
            "Telecommunications: Fiber optic ready with multiple telco options",
            "Fire protection: Sprinkler and smoke detection systems",
            "Security: CCTV, card access, and 24/7 security personnel",
        ]

        specs_list = ListFlowable(
            [
                ListItem(Paragraph(s, self.styles["Normal"]), leftIndent=20)
                for s in specs
            ],
            bulletType="bullet",
        )
        story.append(specs_list)

        return story

    def _create_amenities_section(self, property_data: Dict[str, Any]) -> List[Any]:
        """Create amenities and features section."""
        story = []

        story.append(self._create_header_table("AMENITIES & FEATURES"))
        story.append(Spacer(1, 0.3 * inch))

        # Amenity icons
        amenities = [
            "Parking",
            "24/7 Security",
            "High-Speed WiFi",
            "Meeting Rooms",
            "Cafeteria",
            "Gym Access",
            "Reception",
            "Elevators",
        ]

        amenity_icons = AmenityIcons(amenities)
        story.append(amenity_icons)
        story.append(Spacer(1, 0.3 * inch))

        # Building amenities detail
        story.append(Paragraph("Full Amenity List", self.styles["CustomHeading2"]))

        amenity_categories = {
            "Business Services": [
                "Professional reception and concierge",
                "Meeting rooms and conference facilities",
                "High-speed fiber internet connectivity",
                "Mail handling and courier services",
            ],
            "Convenience": [
                "Ample parking for cars and motorcycles",
                "Food court and cafeteria",
                "ATM and banking facilities",
                "Convenience store",
            ],
            "Wellness & Safety": [
                "24/7 security with CCTV monitoring",
                "Automated fire detection and suppression",
                "First aid and AED stations",
                "Shower and locker facilities",
            ],
        }

        for category, items in amenity_categories.items():
            story.append(Paragraph(f"<b>{category}</b>", self.styles["Normal"]))
            items_list = ListFlowable(
                [
                    ListItem(Paragraph(item, self.styles["Normal"]), leftIndent=40)
                    for item in items
                ],
                bulletType="bullet",
            )
            story.append(items_list)
            story.append(Spacer(1, 0.1 * inch))

        return story

    def _create_photo_gallery(self, photos: List[PropertyPhoto]) -> List[Any]:
        """Create photo gallery section."""
        story = []

        story.append(self._create_header_table("PHOTO GALLERY"))
        story.append(Spacer(1, 0.3 * inch))

        # Photo grid placeholder
        photo_data = []
        for i in range(0, min(6, len(photos)), 2):
            row = []
            for j in range(2):
                if i + j < len(photos):
                    photo = photos[i + j]
                    # In production, would load actual image
                    row.append(f"[Photo {i+j+1}]\n{photo.filename or 'Property Image'}")
                else:
                    row.append("")
            photo_data.append(row)

        if photo_data:
            photo_table = Table(photo_data, colWidths=[3 * inch, 3 * inch])
            photo_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.grey),
                        ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 0),
                            (-1, -1),
                            [colors.HexColor("#f8f9fa")],
                        ),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 60),
                        ("TOPPADDING", (0, 0), (-1, -1), 60),
                    ]
                )
            )
            story.append(photo_table)

        # Virtual tour callout
        story.append(Spacer(1, 0.2 * inch))
        virtual_tour_style = ParagraphStyle(
            "VirtualTour",
            parent=self.styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#3498db"),
            alignment=TA_CENTER,
            borderWidth=1,
            borderColor=colors.HexColor("#3498db"),
            borderPadding=10,
            backColor=colors.HexColor("#e8f4fd"),
        )
        story.append(
            Paragraph(
                "🎥 Virtual Tour Available - Contact us for access", virtual_tour_style
            )
        )

        return story

    def _create_availability_section(
        self, property_data: Dict[str, Any], material_type: str
    ) -> List[Any]:
        """Create availability and pricing section."""
        story = []

        title = (
            "AVAILABILITY & RENTAL RATES"
            if material_type == "lease"
            else "PRICING & TERMS"
        )
        story.append(self._create_header_table(title))
        story.append(Spacer(1, 0.3 * inch))

        if material_type == "lease":
            # Rental rates
            story.append(Paragraph("Rental Rates", self.styles["CustomHeading2"]))

            rental_data = [
                ["Floor Level", "Size Range", "Asking Rent", "Service Charge"],
                ["High Floor", "500-1000 sqm", "$12-14 psf/month", "$3.50 psf/month"],
                ["Mid Floor", "500-1500 sqm", "$10-12 psf/month", "$3.50 psf/month"],
                ["Low Floor", "1000-2000 sqm", "$8-10 psf/month", "$3.50 psf/month"],
            ]

            table = self._create_data_table(rental_data)
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

            # Lease terms
            story.append(
                Paragraph("Standard Lease Terms", self.styles["CustomHeading2"])
            )

            terms = [
                "Minimum lease term: 3 years",
                "Option to renew: 3+3 years",
                "Security deposit: 3 months rent",
                "Rent review: Every 3 years",
                "Fitting out period: 2 months rent-free",
                "Early termination: Subject to conditions",
            ]

        else:  # Sale
            # Sale price
            story.append(Paragraph("Investment Summary", self.styles["CustomHeading2"]))

            price_data = [
                ["Component", "Amount"],
                ["Asking Price", "$150,000,000"],
                ["Price PSF (GFA)", "$3,000"],
                ["Current NOI", "$6,750,000"],
                ["Indicative Yield", "4.5%"],
                ["Occupancy", "92%"],
                ["WALT", "3.5 years"],
            ]

            table = self._create_data_table(price_data, col_widths=[3 * inch, 2 * inch])
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

            # Transaction terms
            story.append(Paragraph("Transaction Terms", self.styles["CustomHeading2"]))

            terms = [
                "Vacant possession or with existing tenancies",
                "Completion within 12 weeks",
                "Due diligence period: 6 weeks",
                "Option fee: 1% (non-refundable)",
                "Exercise fee: 4% (less option fee)",
                "Balance: 95% on completion",
            ]

        terms_list = ListFlowable(
            [
                ListItem(Paragraph(t, self.styles["Normal"]), leftIndent=20)
                for t in terms
            ],
            bulletType="bullet",
        )
        story.append(terms_list)

        # Disclaimer
        story.append(Spacer(1, 0.3 * inch))
        story.append(
            self._add_disclaimer("leasing" if material_type == "lease" else "sales")
        )

        return story

    def _create_contact_section(
        self, contact_info: Optional[Dict[str, str]], material_type: str
    ) -> List[Any]:
        """Create contact and next steps section."""
        story = []

        story.append(self._create_header_table("CONTACT & NEXT STEPS"))
        story.append(Spacer(1, 0.3 * inch))

        # Next steps
        story.append(Paragraph("Next Steps", self.styles["CustomHeading2"]))

        steps = [
            (
                "Contact our leasing team to discuss requirements"
                if material_type == "lease"
                else "Request comprehensive investment memorandum"
            ),
            "Schedule a property viewing",
            "Review detailed floor plans and specifications",
            "Negotiate terms and conditions",
            "Execute letter of intent",
            "Complete due diligence",
            "Finalize documentation",
        ]

        steps_list = ListFlowable(
            [
                ListItem(
                    Paragraph(s, self.styles["Normal"]), leftIndent=20, value=str(i + 1)
                )
                for i, s in enumerate(steps)
            ],
            bulletType="1",
        )
        story.append(steps_list)
        story.append(Spacer(1, 0.3 * inch))

        # Contact information
        story.append(Paragraph("Contact Information", self.styles["CustomHeading2"]))

        if not contact_info:
            contact_info = {
                "company": "Commercial Property Advisors",
                "phone": "+65 6XXX XXXX",
                "email": (
                    "leasing@cpAdvisors.com"
                    if material_type == "lease"
                    else "sales@cpAdvisors.com"
                ),
                "website": "www.commercialpropertyadvisors.com",
            }

        contact_table_data = [
            ["Company:", contact_info.get("company", "Commercial Property Advisors")],
            ["Phone:", contact_info.get("phone", "+65 6XXX XXXX")],
            ["Email:", contact_info.get("email", "info@cpAdvisors.com")],
            ["Website:", contact_info.get("website", "www.cpAdvisors.com")],
        ]

        contact_table = Table(contact_table_data, colWidths=[1.5 * inch, 4 * inch])
        contact_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(contact_table)
        story.append(Spacer(1, 0.3 * inch))

        # Call to action
        cta_style = ParagraphStyle(
            "CTA",
            parent=self.styles["Normal"],
            fontSize=14,
            textColor=colors.white,
            alignment=TA_CENTER,
            borderWidth=0,
            borderPadding=15,
            backColor=colors.HexColor("#3498db"),
        )

        cta_text = (
            "SCHEDULE A VIEWING TODAY"
            if material_type == "lease"
            else "REQUEST INVESTMENT PACK"
        )
        story.append(Paragraph(cta_text, cta_style))

        return story

    def _get_key_highlights(
        self, property_data: Dict[str, Any], material_type: str
    ) -> List[tuple]:
        """Get key highlights for flyer."""
        property_obj = property_data["property"]

        if material_type == "lease":
            return [
                ("Available", f"{property_data['total_available']:,.0f} sqm"),
                ("Rental", "$10-14 psf"),
                ("Occupancy", "Immediate"),
            ]
        else:
            return [
                ("Price", "$150M"),
                ("Yield", "4.5%"),
                ("GFA", f"{property_obj.gross_floor_area_sqm:,.0f} sqm"),
            ]

    def _get_ideal_tenants(self, property_type: PropertyType) -> List[str]:
        """Get ideal tenant types based on property type."""
        tenant_map = {
            PropertyType.OFFICE: [
                "Technology companies",
                "Financial services",
                "Professional services",
                "Regional headquarters",
            ],
            PropertyType.RETAIL: [
                "F&B operators",
                "Fashion retailers",
                "Lifestyle brands",
                "Service providers",
            ],
            PropertyType.INDUSTRIAL: [
                "Logistics operators",
                "Light manufacturing",
                "R&D facilities",
                "Data centers",
            ],
            PropertyType.WAREHOUSE: [
                "3PL providers",
                "E-commerce fulfillment",
                "Distribution centers",
                "Cold storage operators",
            ],
        }

        return tenant_map.get(
            property_type, ["Corporate tenants", "Service providers", "Retailers"]
        )

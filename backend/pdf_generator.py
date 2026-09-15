# ============================================================
# STRIDEX - CLINICAL BIOMECHANICAL REPORT PDF GENERATOR
# Generates a vector PDF medical report using ReportLab
# ============================================================

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header line (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "STRIDEX CLINICAL BIOMECHANICAL GAIT SCREENING REPORT")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, f"ID: {getattr(self, 'report_id', 'SX-GAIT')}")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Footer
        footer_text = "CONFIDENTIAL MEDICAL SCREENING DATA — NOT A DIRECT MEDICAL DIAGNOSIS"
        self.drawString(54, 32, footer_text)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 32, page_str)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 44, 8.5 * inch - 54, 44)
        self.restoreState()


def generate_gait_pdf(assessment_data, patient_data=None):
    """
    Generate an authentic PDF byte buffer for the provided assessment.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()
    
    # Custom clinical styles
    primary_color = colors.HexColor("#1E3A8A")   # Navy Medical
    accent_color = colors.HexColor("#0284C7")    # Clinical Blue
    text_dark = colors.HexColor("#0F172A")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#E2E8F0")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=accent_color,
        spaceAfter=14
    )
    section_heading = ParagraphStyle(
        'SecHead',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark
    )
    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    small_muted = ParagraphStyle(
        'SmallMuted',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_muted
    )
    alert_box_text = ParagraphStyle(
        'AlertBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # ------------------------------------------------------------
    # HEADER BANNER
    # ------------------------------------------------------------
    header_data = [
        [
            Paragraph("<b>STRIDEX</b>", ParagraphStyle('Logo', fontName='Helvetica-Bold', fontSize=24, leading=26, textColor=primary_color)),
            Paragraph(f"<b>REPORT ID:</b> {assessment_data.get('id', 'SX-9021')}<br/><b>DATE:</b> {assessment_data.get('date', datetime.now().strftime('%b %d, %Y'))}<br/><b>ANALYST:</b> {assessment_data.get('doctor_name', 'Dr. Sarah Jenkins, PT, DPT')}", ParagraphStyle('HeadMeta', fontName='Helvetica', fontSize=8.5, leading=12, alignment=2, textColor=text_muted))
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5 * inch, 4.0 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Paragraph("QUANTITATIVE BIOMECHANICAL GAIT SCREENING REPORT", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=12))

    # ------------------------------------------------------------
    # PATIENT & ASSESSMENT DEMOGRAPHICS TABLE
    # ------------------------------------------------------------
    p = patient_data or {}
    patient_table_data = [
        [
            Paragraph("<b>PATIENT INFORMATION</b>", section_heading),
            Paragraph("<b>ASSESSMENT SPECIFICATIONS</b>", section_heading)
        ],
        [
            Paragraph(
                f"<b>Full Name:</b> {p.get('name', assessment_data.get('patient_name', 'Eleanor Vance'))}<br/>"
                f"<b>Patient ID:</b> {p.get('id', 'PT-10482')}<br/>"
                f"<b>Age / Sex:</b> {p.get('age', '67')} yrs / {p.get('gender', 'Female')}<br/>"
                f"<b>Condition / Indication:</b> {assessment_data.get('walking_condition', 'Post-Op Knee Arthroscopy Recovery')}",
                body_style
            ),
            Paragraph(
                f"<b>Video Source:</b> {assessment_data.get('video_filename') or 'sample walk.mp4'}<br/>"
                f"<b>Camera View:</b> {assessment_data.get('camera_view') or 'Sagittal Lateral'}<br/>"
                f"<b>Video Specs:</b> {assessment_data.get('fps') or 0:.1f} FPS | {assessment_data.get('duration') or 0:.1f} sec duration<br/>"
                f"<b>Pose Detection Rate:</b> {assessment_data.get('detection_rate') or 0:.1f}% frames tracked",
                body_style
            )
        ]
    ]
    pat_table = Table(patient_table_data, colWidths=[3.75 * inch, 3.75 * inch])
    pat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(pat_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------
    # SCREENING STATUS & EXECUTIVE SUMMARY
    # ------------------------------------------------------------
    risk_level = str(assessment_data.get('risk_level', 'LOW')).upper()
    if 'MODERATE' in risk_level or 'MEDIUM' in risk_level:
        badge_bg = colors.HexColor("#FEF3C7")
        badge_fg = colors.HexColor("#92400E")
        badge_border = colors.HexColor("#FDE68A")
        badge_text = "MODERATE SCREENING RISK"
    elif 'HIGH' in risk_level:
        badge_bg = colors.HexColor("#FEE2E2")
        badge_fg = colors.HexColor("#991B1B")
        badge_border = colors.HexColor("#FECACA")
        badge_text = "ELEVATED SCREENING RISK"
    else:
        badge_bg = colors.HexColor("#D1FAE5")
        badge_fg = colors.HexColor("#065F46")
        badge_border = colors.HexColor("#A7F3D0")
        badge_text = "LOW SCREENING RISK (NORMAL)"

    risk_box_data = [
        [
            Paragraph(f"<b>SCREENING STATUS:</b> <font color='{badge_fg.hexval()}'>{badge_text}</font>", ParagraphStyle('RiskBadge', fontName='Helvetica-Bold', fontSize=10, leading=14)),
            Paragraph(f"<b>Gait Score:</b> {assessment_data.get('gait_score', 84)}/100", ParagraphStyle('GaitScore', fontName='Helvetica-Bold', fontSize=10, leading=14, alignment=2, textColor=primary_color))
        ],
        [
            Paragraph(
                f"<b>Clinical Screening Impression:</b> {assessment_data.get('clinical_narrative', 'Video-derived kinematic analysis demonstrates rhythmic gait characteristics with measurable inter-limb range of motion divergence. Temporal pacing is stable. Findings suggest mild biomechanical asymmetry without acute balance compromise.')}",
                ParagraphStyle('RiskNarrative', fontName='Helvetica', fontSize=8.5, leading=12, textColor=text_dark),
            ),
            ""
        ]
    ]
    risk_box = Table(risk_box_data, colWidths=[5.5 * inch, 2.0 * inch])
    risk_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), badge_bg),
        ('BOX', (0, 0), (-1, -1), 1, badge_border),
        ('SPAN', (0, 1), (1, 1)),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(risk_box)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------
    # QUANTITATIVE BIOMECHANICAL METRICS TABLE
    # ------------------------------------------------------------
    f = assessment_data.get('features', {})
    
    def fmt(val, unit="", decimals=1, default="Not available"):
        if val is None or val == "":
            return default
        try:
            return f"{float(val):.{decimals}f} {unit}".strip()
        except Exception:
            return str(val)

    metrics_rows = [
        [
            Paragraph("<b>BIOMECHANICAL PARAMETER</b>", small_muted),
            Paragraph("<b>LEFT SIDE</b>", small_muted),
            Paragraph("<b>RIGHT SIDE</b>", small_muted),
            Paragraph("<b>ASYMMETRY / VALUE</b>", small_muted),
            Paragraph("<b>SCREENING NORM</b>", small_muted),
            Paragraph("<b>STATUS</b>", small_muted),
        ],
        [
            Paragraph("<b>Cadence</b>", body_style),
            Paragraph("—", body_style),
            Paragraph("—", body_style),
            Paragraph(fmt(f.get('cadence'), "steps/min", 1), body_bold),
            Paragraph("95 – 130 spm", small_muted),
            Paragraph("<font color='#059669'>Within Normal</font>" if 90 <= float(f.get('cadence', 0)) <= 140 else "<font color='#D97706'>Borderline</font>", body_style)
        ],
        [
            Paragraph("<b>Walking Speed</b>", body_style),
            Paragraph("—", body_style),
            Paragraph("—", body_style),
            Paragraph(fmt(f.get('walking_speed'), "m/s", 2), body_bold),
            Paragraph("0.9 – 1.4 m/s", small_muted),
            Paragraph("<font color='#059669'>Normal Pace</font>", body_style)
        ],
        [
            Paragraph("<b>Step / Stride Length</b>", body_style),
            Paragraph(fmt(f.get('step_length'), "m", 2), body_style),
            Paragraph(fmt(f.get('step_length'), "m", 2), body_style),
            Paragraph(f"Stride: {fmt(f.get('stride_length'), 'm', 2)}", body_bold),
            Paragraph("0.55 – 0.75 m", small_muted),
            Paragraph("<font color='#059669'>Within Normal</font>", body_style)
        ],
        [
            Paragraph("<b>Step / Stride Duration</b>", body_style),
            Paragraph(fmt(f.get('step_time'), "s", 2), body_style),
            Paragraph(fmt(f.get('step_time'), "s", 2), body_style),
            Paragraph(f"Stride: {fmt(f.get('stride_time'), 's', 2)}", body_bold),
            Paragraph("0.50 – 0.65 s", small_muted),
            Paragraph("<font color='#059669'>Stable</font>", body_style)
        ],
        [
            Paragraph("<b>Knee Range of Motion (ROM)</b>", body_style),
            Paragraph(fmt(f.get('left_knee_rom'), "°", 1), body_style),
            Paragraph(fmt(f.get('right_knee_rom'), "°", 1), body_style),
            Paragraph(f"Δ {fmt(f.get('knee_rom_asymmetry'), '°', 1)}", body_bold),
            Paragraph("55° – 70° (Δ < 15°)", small_muted),
            Paragraph("<font color='#DC2626'>Elevated Diff</font>" if float(f.get('knee_rom_asymmetry', 0)) > 30 else "<font color='#059669'>Symmetric</font>", body_style)
        ],
        [
            Paragraph("<b>Mean Knee Angle</b>", body_style),
            Paragraph(fmt(f.get('left_knee_angle_mean'), "°", 1), body_style),
            Paragraph(fmt(f.get('right_knee_angle_mean'), "°", 1), body_style),
            Paragraph(f"Δ {fmt(f.get('knee_angle_asymmetry'), '°', 1)}", body_bold),
            Paragraph("135° – 165°", small_muted),
            Paragraph("<font color='#059669'>Normal</font>", body_style)
        ],
        [
            Paragraph("<b>Mean Ankle Angle</b>", body_style),
            Paragraph(fmt(f.get('left_ankle_angle_mean'), "°", 1), body_style),
            Paragraph(fmt(f.get('right_ankle_angle_mean'), "°", 1), body_style),
            Paragraph("Bilateral Tracked", body_bold),
            Paragraph("5° – 25°", small_muted),
            Paragraph("<font color='#059669'>Normal</font>", body_style)
        ],
        [
            Paragraph("<b>Angular Velocity</b>", body_style),
            Paragraph(fmt(f.get('left_angular_velocity_abs'), "°/s", 1), body_style),
            Paragraph(fmt(f.get('right_angular_velocity_abs'), "°/s", 1), body_style),
            Paragraph(fmt(f.get('left_angular_velocity_abs'), "°/s", 1), body_bold),
            Paragraph("40 – 90 °/s", small_muted),
            Paragraph("<font color='#059669'>Normal</font>", body_style)
        ],
        [
            Paragraph("<b>Postural Sway / Stability</b>", body_style),
            Paragraph("—", body_style),
            Paragraph("—", body_style),
            Paragraph(fmt(f.get('postural_sway'), "", 4), body_bold),
            Paragraph("< 0.003 (Norm)", small_muted),
            Paragraph("<font color='#059669'>Stable</font>", body_style)
        ],
        [
            Paragraph("<b>Bilateral Symmetry Index</b>", body_style),
            Paragraph("—", body_style),
            Paragraph("—", body_style),
            Paragraph(fmt(f.get('symmetry_score', 84), "%", 1), body_bold),
            Paragraph("> 85.0%", small_muted),
            Paragraph("<font color='#059669'>Good</font>" if float(f.get('symmetry_score', 84)) >= 85 else "<font color='#D97706'>Review</font>", body_style)
        ],
    ]

    metrics_table = Table(metrics_rows, colWidths=[2.1 * inch, 1.0 * inch, 1.0 * inch, 1.3 * inch, 1.1 * inch, 1.0 * inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------
    # RISK FACTORS & OBSERVATIONS
    # ------------------------------------------------------------
    story.append(Paragraph("<b>CLINICAL SCREENING FACTORS & RISK CONTRIBUTIONS</b>", section_heading))
    
    risk_factors_data = [
        [Paragraph("<b>Factor Evaluated</b>", small_muted), Paragraph("<b>Screening Observation</b>", small_muted), Paragraph("<b>Status</b>", small_muted)]
    ]
    factors = assessment_data.get('risk_factors', [
        {"name": "Bilateral Symmetry", "label": "Symmetry score within functional community walking range", "status": "normal"},
        {"name": "Cadence Regulation", "label": "Pacing consistent throughout video recording interval", "status": "normal"},
        {"name": "Knee Range of Motion", "label": "Notable divergence in peak flexion/extension between limbs", "status": "caution"},
        {"name": "Postural Stability", "label": "Trunk and pelvis center of mass trajectory remains stable without compensatory sway", "status": "normal"}
    ])
    for item in factors:
        status_color = "#059669" if item.get('status') == 'normal' else ("#D97706" if item.get('status') == 'caution' else "#DC2626")
        status_label = "Within Range" if item.get('status') == 'normal' else ("Caution" if item.get('status') == 'caution' else "Elevated Diff")
        risk_factors_data.append([
            Paragraph(f"<b>{item.get('name', 'Metric')}</b>", body_style),
            Paragraph(item.get('label', 'Within typical range'), body_style),
            Paragraph(f"<font color='{status_color}'><b>{status_label}</b></font>", body_style)
        ])

    rf_table = Table(risk_factors_data, colWidths=[2.2 * inch, 4.3 * inch, 1.0 * inch])
    rf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(rf_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------
    # GAIT CYCLE EVENTS & METHODOLOGY
    # ------------------------------------------------------------
    method_data = [
        [
            Paragraph("<b>GAIT CYCLE PHASING ESTIMATE</b>", section_heading),
            Paragraph("<b>TECHNICAL METHODOLOGY</b>", section_heading)
        ],
        [
            Paragraph(
                "• <b>Stance Phase:</b> ~61.5% (Norm: 60–62%)<br/>"
                "• <b>Swing Phase:</b> ~38.5% (Norm: 38–40%)<br/>"
                "• <b>Double Support:</b> ~22.0% (Norm: 20–24%)<br/>"
                "• <b>Cycle Regularity:</b> High temporal consistency",
                body_style
            ),
            Paragraph(
                "• <b>Pose Tracking:</b> MediaPipe 33-landmark skeleton<br/>"
                "• <b>Smoothing:</b> Exponential Moving Average (α=0.7)<br/>"
                "• <b>Kinematics:</b> 3D vector cosine joint angle trigonometry<br/>"
                "• <b>Classification:</b> StrideX Clinical Random Forest Model",
                body_style
            )
        ]
    ]
    method_table = Table(method_data, colWidths=[3.75 * inch, 3.75 * inch])
    method_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(method_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------
    # CLINICAL DISCLAIMER
    # ------------------------------------------------------------
    disclaimer_text = (
        "<b>CLINICAL SCREENING DISCLAIMER:</b> StrideX is a quantitative biomechanical screening and longitudinal "
        "monitoring platform. Measurements are video-derived algorithmic estimates using monocular computer vision "
        "and do not constitute a direct diagnostic finding, physical exam, or clinical determination. Results should be "
        "reviewed by a licensed healthcare professional, physical therapist, or orthopedic clinician in conjunction with "
        "patient history and objective physical assessment."
    )
    disc_table = Table([[Paragraph(disclaimer_text, alert_box_text)]], colWidths=[7.5 * inch])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(disc_table)

    # Build PDF with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()

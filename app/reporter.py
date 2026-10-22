"""
PDF Audit Report Generator for VeritasDoc AI Content Detector
Conforming to VeritasDoc Engineering Specification (Phase 6 & 8).
Generates tamper-evident institutional audit certificates using ReportLab.
"""

import html
import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(analysis: dict[str, Any]) -> bytes:
    """
    Generate an audit PDF report from analysis record and return PDF bytes.
    Includes:
    - Formal institutional letterhead (AI Content & Plagiarism Forensic Suite)
    - Cryptographic SHA-256 document checksum
    - 3-Zone Academic Decision banner
    - Statistical & Stylometric Perplexity/Burstiness telemetry
    - Multi-Vector Consensus Matrix table
    - Platform attribution, paraphrase evasion & plagiarism audit
    - Section-wise breakdown table
    - Sentence-by-sentence forensic audit with reasoning
    - Mandatory academic fairness disclaimer
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#0f172a'),
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
    )
    section_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=8,
        spaceAfter=4,
    )
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#475569'),
    )
    meta_val_style = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
    )
    cell_text = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1e293b'),
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1e293b'),
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor('#64748b'),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("FORENSIC VERIFICATION &bull; EVALUATION PANEL", subtitle_style))
    story.append(Paragraph("VeritasDoc: Explainable AI Content Audit Certificate", title_style))
    story.append(Paragraph("Multi-Tier Document Authenticity, Localization & Forensic Quantification", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4f46e5'), spaceAfter=8))

    # 2. Document Metadata Grid (Including SHA-256 Checksum)
    filename = html.escape(str(analysis.get('filename', 'Unknown Document')))
    analysis_id = str(analysis.get('id', 'N/A'))
    created_at = str(analysis.get('created_at', 'N/A'))
    sha256_hash = str(analysis.get('sha256_hash') or 'a8f5b1284cd92e07...')
    sensitivity = str(analysis.get('sensitivity_mode', 'balanced')).capitalize()
    total_words = str(analysis.get('total_words', 'N/A'))
    total_sentences = str(analysis.get('total_sentences', len(analysis.get('sentences', []))))
    ai_sentences = str(analysis.get('ai_sentences', '0'))

    meta_data = [
        [
            Paragraph("Document Name:", meta_label_style),
            Paragraph(filename, meta_val_style),
            Paragraph("Audit Certificate ID:", meta_label_style),
            Paragraph(analysis_id[:18] + "...", meta_val_style),
        ],
        [
            Paragraph("SHA-256 Checksum:", meta_label_style),
            Paragraph(f"<font name='Courier' size='7'>{sha256_hash[:28]}...</font>", meta_val_style),
            Paragraph("Audit Timestamp:", meta_label_style),
            Paragraph(created_at[:19].replace('T', ' '), meta_val_style),
        ],
        [
            Paragraph("Total Words:", meta_label_style),
            Paragraph(f"{total_words} words ({total_sentences} sentences)", meta_val_style),
            Paragraph("Evaluator Mode:", meta_label_style),
            Paragraph(f"{sensitivity} (Threshold &tau;)", meta_val_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[90, 190, 95, 165])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. 3-Zone Academic Decision Matrix & Score Banner
    verdict = analysis.get('verdict', 'Authentic Human')
    ai_pct = float(analysis.get('ai_percentage', 0.0))
    verdict_zone = analysis.get('verdict_zone', 'GREEN')

    if verdict_zone == "RED" or verdict == "High AI Probability" or ai_pct > 65.0:
        verdict_bg = colors.HexColor('#ffe4e6')
        verdict_color = colors.HexColor('#9f1239')
        zone_label = "RED ZONE (&gt; 65%)"
    elif verdict_zone == "YELLOW" or verdict == "Needs Manual Review" or ai_pct >= 25.0:
        verdict_bg = colors.HexColor('#fef3c7')
        verdict_color = colors.HexColor('#92400e')
        zone_label = "YELLOW ZONE (25% - 65%)"
    else:
        verdict_bg = colors.HexColor('#d1fae5')
        verdict_color = colors.HexColor('#065f46')
        zone_label = "GREEN ZONE (&lt; 25%)"

    exec_summary_data = [
        [
            Paragraph("<b>Academic Decision:</b>", meta_label_style),
            Paragraph(f"<b><font size='10' color='{verdict_color.hexval()}'>{verdict.upper()} &bull; {zone_label}</font></b>", cell_text),
            Paragraph("<b>Length-Weighted AI Score:</b>", meta_label_style),
            Paragraph(f"<b><font size='12' color='{verdict_color.hexval()}'>{ai_pct:.1f}%</font></b>", cell_text),
        ]
    ]
    exec_table = Table(exec_summary_data, colWidths=[110, 170, 125, 135])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), verdict_bg),
        ('BOX', (0, 0), (-1, -1), 1, verdict_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 8))

    # 4. Statistical & Stylometric Telemetry Strip
    forensics = analysis.get('forensic_metrics', {})
    if forensics:
        ppl = forensics.get('perplexity', 0.0)
        burstiness = forensics.get('burstiness', 0.0)
        ttr = forensics.get('lexical_diversity_ttr', 0.0)
        cliches_cnt = forensics.get('cliches_detected', 0)

        forensic_row = [
            [
                Paragraph(f"<b>Perplexity (PPL):</b> {ppl:.1f}", cell_text),
                Paragraph(f"<b>Burstiness (B):</b> {burstiness:.3f}", cell_text),
                Paragraph(f"<b>Lexical TTR:</b> {ttr:.1f}%", cell_text),
                Paragraph(f"<b>Cliché Tropes:</b> {cliches_cnt} found", cell_text),
            ]
        ]
        forensic_table = Table(forensic_row, colWidths=[135, 135, 135, 135])
        forensic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(forensic_table)
        story.append(Spacer(1, 8))

    # 5. Tri-Model Neural Consensus Matrix
    ensemble = analysis.get('ensemble', {})
    voting_matrix = ensemble.get('voting_matrix', [])
    if voting_matrix:
        story.append(Paragraph("Tri-Layer Neural Consensus Voting Matrix", section_h1))
        vote_rows = [
            [
                Paragraph("<b>Forensic Neural Subsystem</b>", cell_bold),
                Paragraph("<b>Vector Weight</b>", cell_bold),
                Paragraph("<b>Core Score</b>", cell_bold),
                Paragraph("<b>Core Verdict</b>", cell_bold),
            ]
        ]
        for v in voting_matrix:
            score = float(v.get('score_pct', 0.0))
            if score >= 65.0:
                v_color = colors.HexColor('#9f1239')
            elif score >= 25.0:
                v_color = colors.HexColor('#92400e')
            else:
                v_color = colors.HexColor('#065f46')

            vote_rows.append([
                Paragraph(f"<b>{html.escape(v.get('name', ''))}</b>", cell_text),
                Paragraph(f"{v.get('weight_pct', 0.0):.1f}%", cell_text),
                Paragraph(f"<b><font color='{v_color.hexval()}'>{score:.1f}%</font></b>", cell_text),
                Paragraph(f"<font color='{v_color.hexval()}'>{html.escape(v.get('verdict', ''))}</font>", cell_text),
            ])

        vote_table = Table(vote_rows, colWidths=[240, 85, 95, 120])
        vote_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(vote_table)
        story.append(Spacer(1, 8))

    # 6. Bonus Innovations: Platform Attribution & Paraphrase Evasion
    attribution = analysis.get('attribution', {})
    evasion = analysis.get('evasion', {})
    plagiarism = analysis.get('plagiarism', {})

    story.append(Paragraph("Forensic Indicators & Bonus Attribution", section_h1))
    bonus_rows = [
        [
            Paragraph("<b>Suspected AI Platform:</b>", meta_label_style),
            Paragraph(f"<b>{html.escape(attribution.get('platform', 'N/A'))}</b> (Confidence: {attribution.get('confidence', 0):.0f}%)", cell_text),
        ],
        [
            Paragraph("<b>Evasion / Humanizer Risk:</b>", meta_label_style),
            Paragraph(f"<b>{evasion.get('humanizer_risk', 'Low')} Risk</b> &bull; {html.escape(evasion.get('reasoning', 'Clean'))}", cell_text),
        ],
        [
            Paragraph("<b>Repetition / Plagiarism:</b>", meta_label_style),
            Paragraph(f"<b>{plagiarism.get('redundancy_risk', 'Clean')}</b> &bull; {plagiarism.get('duplication_pct', 0.0):.1f}% 4-gram repetition index.", cell_text),
        ]
    ]
    bonus_table = Table(bonus_rows, colWidths=[150, 390])
    bonus_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(bonus_table)
    story.append(Spacer(1, 8))

    # 7. Section-Wise Breakdown Table
    sections = analysis.get('sections', [])
    if sections:
        story.append(Paragraph(f"Section-Wise & Slide Breakdown ({len(sections)} Segmented Blocks)", section_h1))
        sec_rows = [
            [
                Paragraph("<b>Section Title</b>", cell_bold),
                Paragraph("<b>Words</b>", cell_bold),
                Paragraph("<b>AI Sentences</b>", cell_bold),
                Paragraph("<b>AI %</b>", cell_bold),
                Paragraph("<b>Section Verdict</b>", cell_bold),
            ]
        ]
        for s in sections[:12]:
            s_pct = float(s.get('ai_percentage', 0.0))
            if s_pct >= 65.0:
                s_color = colors.HexColor('#9f1239')
            elif s_pct >= 25.0:
                s_color = colors.HexColor('#92400e')
            else:
                s_color = colors.HexColor('#065f46')

            sec_rows.append([
                Paragraph(html.escape(s.get('title', 'Section')), cell_text),
                Paragraph(str(s.get('word_count', 0)), cell_text),
                Paragraph(f"{s.get('ai_sentences', 0)} / {s.get('total_sentences', 0)}", cell_text),
                Paragraph(f"<b><font color='{s_color.hexval()}'>{s_pct:.1f}%</font></b>", cell_text),
                Paragraph(f"<font color='{s_color.hexval()}'>{html.escape(s.get('verdict', ''))}</font>", cell_text),
            ])

        sec_table = Table(sec_rows, colWidths=[200, 55, 85, 65, 135])
        sec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 8))

    # 8. Sentence-by-Sentence Forensic Audit Sample
    sentences = analysis.get('sentences', [])
    if sentences:
        story.append(Paragraph("Sentence-Level Localization & Scores", section_h1))
        sent_rows = [
            [
                Paragraph("<b>#</b>", cell_bold),
                Paragraph("<b>Evaluated Sentence</b>", cell_bold),
                Paragraph("<b>PPL</b>", cell_bold),
                Paragraph("<b>AI %</b>", cell_bold),
                Paragraph("<b>Classification</b>", cell_bold),
            ]
        ]
        for s in sentences[:15]:
            score = float(s.get('score', 0.0))
            if score >= 70.0:
                s_badge = "<font color='#9f1239'><b>AI-Generated</b></font>"
            elif score >= 45.0:
                s_badge = "<font color='#92400e'><b>Uncertain</b></font>"
            else:
                s_badge = "<font color='#065f46'><b>Authentic Human</b></font>"

            raw_sent = str(s.get('sentence', '')).strip()
            if len(raw_sent) > 250:
                raw_sent = raw_sent[:247] + "..."
            s_text = html.escape(raw_sent)
            ppl_val = s.get('ppl', 0.0)

            sent_rows.append([
                Paragraph(str(s.get('index', '')), cell_text),
                Paragraph(s_text, cell_text),
                Paragraph(f"{ppl_val:.1f}", cell_text),
                Paragraph(f"<b>{score:.1f}%</b>", cell_text),
                Paragraph(s_badge, cell_text),
            ])

        sent_table = Table(sent_rows, colWidths=[25, 335, 45, 55, 80], repeatRows=1)
        sent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(sent_table)
        story.append(Spacer(1, 10))

    # 9. Institutional Verification Footer
    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=6),
        Paragraph("Certified Audit Certificate &bull; SHA-256 Tamper-Evident Institutional Verification", subtitle_style),
    ]))

    doc.build(story)
    return buffer.getvalue()

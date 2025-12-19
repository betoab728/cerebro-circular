from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models import AnalysisResult
import os

def generate_pdf_report(data: AnalysisResult) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Logo Logic
    # File structure:
    # project_root/
    #   backend/utils/report_generator.py
    #   static/logoazul.png
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) # utils
    backend_dir = os.path.dirname(current_dir) # backend
    project_root = os.path.dirname(backend_dir) # project_root
    
    logo_path = os.path.join(project_root, "static", "logoazul.png")
    
    print(f"DEBUG: Calculated Logo Path: {logo_path}")
    print(f"DEBUG: File Exists? {os.path.exists(logo_path)}")

    if os.path.exists(logo_path):
        im = Image(logo_path, width=150, height=50) 
        im.hAlign = 'LEFT'
        story.append(im)
        story.append(Spacer(1, 12))
    else:
        print(f"Warning: Logo not found at {logo_path}")

    # Custom Styles
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['BodyText']
    
    # Define italics style for summary
    italic_style = ParagraphStyle(
        'ItalicStyle',
        parent=styles['BodyText'],
        fontName='Helvetica-Oblique'
    )

    # Title
    story.append(Paragraph("Informe Técnico de Caracterización", title_style))
    story.append(Paragraph("CEREBRO CIRCULAR - Análisis de Residuos", styles['Normal']))
    story.append(Spacer(1, 12))

    # Material Summary
    story.append(Paragraph(f"Material Detectado: <b>{data.materialName}</b>", heading_style))
    story.append(Paragraph(f"Categoría: {data.category}", normal_style))
    story.append(Paragraph(f"Confianza IA: {data.confidence}%", normal_style))
    story.append(Spacer(1, 12))

    # Engineering Context
    story.append(Paragraph("Contexto de Ingeniería", heading_style))
    story.append(Paragraph(f"<b>Estructura:</b> {data.engineeringContext.structure}", normal_style))
    story.append(Paragraph(f"<b>Procesabilidad:</b> {data.engineeringContext.processability}", normal_style))
    if data.engineeringContext.impurities:
        story.append(Paragraph(f"<b>Impurezas:</b> {data.engineeringContext.impurities}", normal_style))
    story.append(Spacer(1, 12))

    # Physicochemical Properties
    story.append(Paragraph("Propiedades Físico-Químicas", heading_style))
    
    table_data = [["Propiedad", "Valor", "Método"]]
    
    # Define a custom style for table cells
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['BodyText'],
        fontSize=9,
        leading=11,
        spaceAfter=0,
    )

    for prop in data.physicochemical:
        # Wrap each cell content in a Paragraph to allow multiline
        row = [
            Paragraph(prop.name, cell_style),
            Paragraph(prop.value, cell_style),
            Paragraph(prop.method, cell_style)
        ]
        table_data.append(row)

    # Allow row heights to be automatic based on content
    t = Table(table_data, colWidths=[200, 150, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Elemental Composition
    story.append(Paragraph("Composición Elemental", heading_style))
    elem_text = ", ".join([f"{el.label}: {el.value}%" for el in data.elemental])
    story.append(Paragraph(elem_text, normal_style))
    
    # Add Elemental Summary
    if data.elementalSummary:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Resumen:</b> {data.elementalSummary}", italic_style))

    story.append(Spacer(1, 12))

    # Valorization Routes
    story.append(Paragraph("Rutas de Valorización", heading_style))
    for route in data.valorizationRoutes:
        story.append(Paragraph(f"<b>{route.role} ({route.score}%):</b> {route.method}", normal_style))
        story.append(Paragraph(f"Output: {route.output}", styles['Italic']))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer

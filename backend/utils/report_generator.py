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
    #   static/logocerebro.png
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) # utils
    backend_dir = os.path.dirname(current_dir) # backend
    project_root = os.path.dirname(backend_dir) # project_root
    
    # Try finding logo in static folder first
    logo_path = os.path.join(project_root, "static", "logocerebro.png")
    
    # Fallback to backend dir if deployed with flat structure
    if not os.path.exists(logo_path):
        logo_path = os.path.join(backend_dir, "logocerebro.png")
    
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

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
    # Use Paragraphs to allow text wrapping for long detected content names
    p_prod = Paragraph(data.productOverview.productName, styles['Normal'])
    p_pack = Paragraph(data.productOverview.detectedPackaging, styles['Normal'])
    p_cont = Paragraph(data.productOverview.detectedContent, styles['Normal'])

    data_summary = [
        ["Producto", p_prod],
        ["Empaque Detectado", p_pack],
        ["Contenido Detectado", p_cont]
    ]
    t_summary = Table(data_summary, colWidths=[150, 300])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0,0), (0,-1), colors.black),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), # Align top for multiline
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    # --- 1. Lifecycle Metrics (Chart) ---
    story.append(Paragraph("1. Métricas de Ciclo de Vida", styles['Heading2']))
    story.append(Paragraph(f"Vida Útil Estimada: {data.lifecycleMetrics.estimatedLifespan}", styles['Normal']))
    
    # Generate Horizontal Bar Chart for Durability
    plt.figure(figsize=(6, 1.5))
    plt.barh(['Durabilidad'], [data.lifecycleMetrics.durabilityScore], color='#3B82F6', height=0.5)
    plt.xlim(0, 100)
    plt.title(f"Score de Durabilidad: {data.lifecycleMetrics.durabilityScore}/100")
    plt.tight_layout()
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    img_buffer.seek(0)
    plt.close()
    
    story.append(Image(img_buffer, width=400, height=100))
    story.append(Paragraph("<i>* 0-30: Bajo (Un uso) | 31-70: Medio (Reciclable) | 71-100: Alto (Reutilizable/Durable)</i>", styles['Normal']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<i>Disposición: {data.lifecycleMetrics.disposalStage}</i>", styles['Normal']))
    story.append(Spacer(1, 12))

    # --- 2. Environmental Impact ---
    story.append(Paragraph("2. Impacto Ambiental", styles['Heading2']))
    
    # Helper to create styled paragraphs for the table
    def get_impact_color_style(level):
        color = colors.green
        if 'High' in level or 'Alto' in level: color = colors.red
        elif 'Medium' in level or 'Medio' in level: color = colors.orange
        
        return ParagraphStyle(
            'ImpactStyle',
            parent=styles['Normal'],
            textColor=color,
            fontName='Helvetica-Bold'
        )

    p_carbon = Paragraph(data.environmentalImpact.carbonFootprintLevel, get_impact_color_style(data.environmentalImpact.carbonFootprintLevel))
    p_hazard = Paragraph(data.environmentalImpact.hazardLevel, styles['Normal'])
    p_recycle = Paragraph(data.environmentalImpact.recycledContentPotential, styles['Normal'])

    impact_data = [
        ["Huella de Carbono", p_carbon],
        ["Peligrosidad", p_hazard],
        ["Potencial Reciclado", p_recycle]
    ]
    t_impact = Table(impact_data, colWidths=[150, 300])
    t_impact.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_impact)
    story.append(Spacer(1, 12))

    # --- 3. Economic Analysis ---
    story.append(Paragraph("3. Análisis Económico (Estimado)", styles['Heading2']))
    story.append(Paragraph(f"Valor estimado de Recuperación: <b>{data.economicAnalysis.estimatedRecyclingValue}</b>", styles['Normal']))
    
    story.append(Spacer(1, 6))
    p_action = Paragraph(f"Recomendación: {data.economicAnalysis.costBenefitAction}", styles['Normal'])
    p_action_style = TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF3C7')), ('BOX', (0,0), (-1,-1), 1, colors.orange)])
    t_action = Table([[p_action]], colWidths=[450])
    t_action.setStyle(p_action_style)
    story.append(t_action)

    story.append(Spacer(1, 20))

    # --- 4. Circular Strategy ---
    story.append(Paragraph("4. Estrategia Circular Recomendada", styles['Heading2']))
    
    strat_text = f'''
    <b>Ruta: {data.circularStrategy.recommendedRoute}</b><br/><br/>
    {data.circularStrategy.justification}
    '''
    story.append(Paragraph(strat_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # --- 5. Regulatory Compliance ---
    story.append(Paragraph("5. Cumplimiento Normativo (Obligatorio)", styles['Heading2']))
    
    comp_data = [
        ["MRSP (Manejo de Residuos)", Paragraph(data.compliance.mrsp_applicability, styles['Normal'])],
        ["Reporte SIGERSOL", Paragraph(data.compliance.sigersol_reporting, styles['Normal'])],
        ["Entidad Competente", Paragraph(data.compliance.competent_authority, styles['Normal'])]
    ]
    
    t_comp = Table(comp_data, colWidths=[150, 300])
    t_comp.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F3F4F6')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_comp)

    doc.build(story)
    buffer.seek(0)
    return buffer

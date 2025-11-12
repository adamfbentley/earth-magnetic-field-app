from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO
from PIL import Image as PILImage
import numpy as np

def generate_pdf_report(coefficients: dict, metrics: dict, plots_data: list[bytes]) -> bytes:
    """
    Generates a PDF report containing structured data (Gauss coefficients, metrics)
    and embedded plots.

    Args:
        coefficients (dict): A dictionary of Gauss coefficients, e.g.,
                             {'g_1^0': {'value': 0.1, 'uncertainty': 0.01}}.
        metrics (dict): A dictionary of model validation metrics, e.g., {'RMSE_total': 1.23}.
        plots_data (list[bytes]): A list of image data (e.g., PNG bytes) for embedding.

    Returns:
        bytes: The content of the generated PDF report as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom style for bold text
    styles.add(ParagraphStyle(name='BoldHeading', parent=styles['h2'], fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='BoldText', parent=styles['Normal'], fontName='Helvetica-Bold'))

    # Title
    story.append(Paragraph("Magnetic Field Analysis Report", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Gauss Coefficients
    story.append(Paragraph("Gauss Coefficients", styles['BoldHeading']))
    story.append(Spacer(1, 0.1 * inch))

    coeff_data = [['Coefficient', 'Value', 'Uncertainty']]
    for coeff_name, data in coefficients.items():
        value = f"{data.get('value', np.nan):.6e}"
        uncertainty = f"{data.get('uncertainty', np.nan):.6e}"
        coeff_data.append([coeff_name, value, uncertainty])

    if len(coeff_data) > 1:
        coeff_table = Table(coeff_data)
        coeff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(coeff_table)
    else:
        story.append(Paragraph("No Gauss coefficients available.", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Model Validation Metrics
    story.append(Paragraph("Model Validation Metrics", styles['BoldHeading']))
    story.append(Spacer(1, 0.1 * inch))

    metrics_data = [['Metric', 'Value']]
    for metric_name, value in metrics.items():
        if isinstance(value, (float, np.floating)):
            metrics_data.append([metric_name, f"{value:.4f}"])
        else:
            metrics_data.append([metric_name, str(value)])

    if len(metrics_data) > 1:
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
    else:
        story.append(Paragraph("No model validation metrics available.", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Plots
    if plots_data:
        story.append(Paragraph("Visualizations", styles['BoldHeading']))
        story.append(Spacer(1, 0.1 * inch))
        for i, plot_bytes in enumerate(plots_data):
            try:
                img_buffer = BytesIO(plot_bytes)
                img = PILImage.open(img_buffer)
                # Resize image to fit page width, maintaining aspect ratio
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
                
                # Max width for letter page (8.5 inch) with 1 inch margins on each side
                max_width = (letter[0] - 2 * inch)
                
                if img_width > max_width:
                    new_width = max_width
                    new_height = max_width * aspect_ratio
                else:
                    new_width = img_width
                    new_height = img_height

                # Ensure image is not too tall for the page
                max_height = (letter[1] - 2 * inch) # Max height with margins
                if new_height > max_height:
                    new_height = max_height
                    new_width = max_height / aspect_ratio

                reportlab_img = Image(img_buffer, width=new_width, height=new_height)
                story.append(reportlab_img)
                story.append(Spacer(1, 0.1 * inch))
            except Exception as e:
                story.append(Paragraph(f"Error embedding plot {i+1}: {e}", styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))
    else:
        story.append(Paragraph("No visualizations provided for the report.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

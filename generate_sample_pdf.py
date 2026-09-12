import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import pypdfium2 as pdfium
from PIL import Image

def generate_sample_pdfs():
    output_dir = os.path.join(os.path.dirname(__file__), "sample_invoices")
    os.makedirs(output_dir, exist_ok=True)
    
    text_pdf_path = os.path.join(output_dir, "imran_air_express_text.pdf")
    scanned_pdf_path = os.path.join(output_dir, "imran_air_express_scanned.pdf")
    
    doc = SimpleDocTemplate(
        text_pdf_path,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        alignment=1, # Center
        fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        alignment=1 # Center
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10
    )
    
    story = []
    story.append(Paragraph("IMRAN AIR EXPRESS", title_style))
    story.append(Paragraph("SHOP NO. 2, VASTU RADHE APARTMENT, OPP POLICE STATION, DHANTOLI, NAGPUR - 440012, MAHARASHTRA", sub_style))
    story.append(Paragraph("Phone: 9011544844 | Email: imransheikh2707@gmail.com | SAC Code: 996812 | Type Of Service: Courier Service", sub_style))
    story.append(Spacer(1, 10))
    
    meta_data = [
        ["Invoice No: MACS/1113", "Date: 07/07/2026", "Bill: June-2026"],
        ["Customer: ZIPL - ZEBRONICS INDIA PVT. LTD.", "PAN: LAPSL6462G", "CIN: -"],
        ["Location: DHANTOLI NAGPUR - 440012", "", ""]
    ]
    meta_table = Table(meta_data, colWidths=[240, 160, 145])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))
    
    headers = ["Sr No", "Doc No", "Date", "Dest. City", "Mode", "I", "PC", "Weight", "Amount"]
    rows = [
        ["1", "219906752", "01/06/26", "BULDHANA", "SURFACE", "P", "1", "22.200", "345.00"],
        ["2", "219906753", "01/06/26", "BHADRAWATI", "SURFACE", "P", "1", "21.300", "440.00"],
        ["3", "219906754", "02/06/26", "CHANDRAPUR", "SURFACE", "P", "2", "15.500", "520.00"],
        ["4", "219906755", "02/06/26", "WARDHA", "AIR", "D", "1", "2.500", "250.00"],
        ["5", "219906756", "03/06/26", "YAVATMAL", "SURFACE", "P", "3", "31.000", "680.00"],
        ["6", "219906757", "03/06/26", "AMRAVATI", "SURFACE", "P", "1", "12.000", "310.00"],
        ["7", "219906758", "04/06/26", "AKOLA", "AIR", "P", "1", "5.800", "410.00"],
        ["8", "219906759", "05/06/26", "GADCHIROLI", "SURFACE", "P", "2", "18.400", "490.00"],
        ["9", "219906760", "06/06/26", "GONDIA", "SURFACE", "D", "1", "9.750", "280.00"],
        ["10", "219906761", "07/06/26", "BHANDARA", "SURFACE", "P", "4", "45.200", "950.00"],
    ]
    
    table_data = [headers] + rows
    col_widths = [35, 75, 55, 110, 60, 25, 30, 65, 90]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2F2F2')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
        ('ALIGN', (5, 0), (5, -1), 'CENTER'),
        ('ALIGN', (6, 0), (6, -1), 'CENTER'),
        ('ALIGN', (7, 0), (7, -1), 'RIGHT'),
        ('ALIGN', (8, 0), (8, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333333')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(table)
    doc.build(story)
    print(f"Generated text PDF: {text_pdf_path}")
    
    pdf = pdfium.PdfDocument(text_pdf_path)
    page = pdf[0]
    pil_image = page.render(scale=2.0).to_pil()
    scanned_image = pil_image.convert('L').convert('RGB')
    scanned_image.save(scanned_pdf_path, "PDF")
    print(f"Generated scanned PDF: {scanned_pdf_path}")

if __name__ == "__main__":
    generate_sample_pdfs()

import io
from flask import render_template, make_response
from app.utils.helpers import format_currency

def generate_invoice_pdf(order):
    """
    Generate professional invoice for an order.
    Attempts ReportLab PDF generation; falls back to printable HTML view with print headers if ReportLab is missing.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1e3a8a'), spaceAfter=10)
        h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#111827'), spaceAfter=6)
        body_style = ParagraphStyle('BodyStyle', parent=styles['BodyText'], fontSize=10, textColor=colors.HexColor('#374151'), leading=14)
        bold_style = ParagraphStyle('BoldStyle', parent=body_style, fontName='Helvetica-Bold')
        
        # Title & Header
        story.append(Paragraph("FANCY STORE - TAX INVOICE", title_style))
        story.append(Paragraph("100 Premium Retail Blvd, Cyber City, Bangalore, KA 560001, India<br/>GSTIN: 29ABCDE1234F1Z5 | Support: support@fancystore.in", body_style))
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#e5e7eb'), spaceAfter=15))
        
        # Order & Customer Meta Info
        meta_data = [
            [Paragraph(f"<b>Invoice No:</b> INV-{order.order_number}", body_style), Paragraph(f"<b>Customer Name:</b> {order.shipping_address.get('full_name', 'N/A')}", body_style)],
            [Paragraph(f"<b>Order Date:</b> {order.created_at.strftime('%d-%b-%Y') if order.created_at else 'N/A'}", body_style), Paragraph(f"<b>Phone:</b> {order.shipping_address.get('phone', 'N/A')}", body_style)],
            [Paragraph(f"<b>Payment Mode:</b> {order.payment_method} ({order.payment_status})", body_style), Paragraph(f"<b>Delivery Address:</b> {order.shipping_address.get('address_line1', '')}, {order.shipping_address.get('city', '')} - {order.shipping_address.get('postal_code', '')}", body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[260, 270])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("Order Items Breakdown", h2_style))
        story.append(Spacer(1, 8))
        
        # Items Table
        table_data = [[
            Paragraph("<b>#</b>", bold_style),
            Paragraph("<b>Product Description</b>", bold_style),
            Paragraph("<b>Qty</b>", bold_style),
            Paragraph("<b>Unit Price</b>", bold_style),
            Paragraph("<b>Total Amount</b>", bold_style)
        ]]
        
        for idx, item in enumerate(order.items, 1):
            desc = item['name']
            if item.get('variant'):
                desc += f" ({item['variant']})"
            table_data.append([
                Paragraph(str(idx), body_style),
                Paragraph(desc, body_style),
                Paragraph(str(item['quantity']), body_style),
                Paragraph(format_currency(item['price']), body_style),
                Paragraph(format_currency(item['total']), body_style)
            ])
            
        # Summary Rows
        table_data.append(["", "", "", Paragraph("<b>Subtotal:</b>", bold_style), Paragraph(format_currency(order.subtotal), body_style)])
        table_data.append(["", "", "", Paragraph("<b>Shipping:</b>", bold_style), Paragraph(format_currency(order.shipping_charge) if order.shipping_charge > 0 else "FREE", body_style)])
        if order.discount_amount > 0:
            table_data.append(["", "", "", Paragraph("<b>Discount:</b>", bold_style), Paragraph(f"-{format_currency(order.discount_amount)}", body_style)])
        table_data.append(["", "", "", Paragraph("<b>Tax (18% GST):</b>", bold_style), Paragraph(format_currency(order.tax_amount), body_style)])
        table_data.append(["", "", "", Paragraph("<b>GRAND TOTAL:</b>", bold_style), Paragraph(f"<b>{format_currency(order.grand_total)}</b>", bold_style)])
        
        item_table = Table(table_data, colWidths=[30, 240, 50, 100, 110])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#111827')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('GRID', (0,0), (-1, -6), 0.5, colors.HexColor('#d1d5db')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LINEABOVE', (3, -5), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('BACKGROUND', (3,-1), (-1,-1), colors.HexColor('#eff6ff')),
        ]))
        story.append(item_table)
        
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceAfter=15))
        story.append(Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold can only be returned within 7 days under our standard return policy.<br/>2. This is a computer-generated tax invoice and does not require a physical signature.", ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=colors.HexColor('#6b7280'))))
        
        doc.build(story)
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Invoice_{order.order_number}.pdf'
        return response

    except ImportError:
        # Fallback to printable HTML view if ReportLab is not installed
        html = render_template('orders/invoice_template.html', order=order, auto_print=True)
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        return response

def generate_orders_list_pdf(orders):
    """
    Generate professional PDF report for a list of orders.
    """
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1e3a8a'), spaceAfter=15)
        body_style = ParagraphStyle('BodyStyle', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#374151'))
        bold_style = ParagraphStyle('BoldStyle', parent=body_style, fontName='Helvetica-Bold')
        
        story.append(Paragraph("Customer Orders Report", title_style))
        
        table_data = [[
            Paragraph("<b>Order Ref</b>", bold_style),
            Paragraph("<b>Date</b>", bold_style),
            Paragraph("<b>Customer Name</b>", bold_style),
            Paragraph("<b>Items</b>", bold_style),
            Paragraph("<b>Total</b>", bold_style),
            Paragraph("<b>Payment</b>", bold_style),
            Paragraph("<b>Status</b>", bold_style)
        ]]
        
        for order in orders:
            dt_str = order.created_at.strftime('%d-%b-%Y') if order.created_at else 'N/A'
            name = order.shipping_address.get('full_name', 'N/A')
            num_items = sum(item['quantity'] for item in order.items)
            
            table_data.append([
                Paragraph(order.order_number, body_style),
                Paragraph(dt_str, body_style),
                Paragraph(name, body_style),
                Paragraph(str(num_items), body_style),
                Paragraph(format_currency(order.grand_total), body_style),
                Paragraph(f"{order.payment_method} ({order.payment_status})", body_style),
                Paragraph(order.order_status, body_style)
            ])
            
        col_widths = [100, 80, 160, 50, 90, 120, 100]
        item_table = Table(table_data, colWidths=col_widths)
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#111827')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(item_table)
        
        doc.build(story)
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=Orders_Report.pdf'
        return response

    except ImportError:
        return "ReportLab is not installed to generate PDF", 500

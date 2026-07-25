"""
Bluetooth/USB Thermal Printer Utility
Uses python-escpos library for ESC/POS thermal printers.
"""

import datetime
from decimal import Decimal


def get_printer(settings_obj=None):
    """
    Get printer instance based on restaurant settings.
    Returns None if no printer configured or connection fails.
    """
    try:
        from escpos.printer import Bluetooth, Usb, Serial
        
        if settings_obj and settings_obj.printer_mac:
            # Bluetooth printer
            mac = settings_obj.printer_mac.replace(':', '').replace('-', '')
            p = Bluetooth(settings_obj.printer_mac)
            return p
        elif settings_obj and settings_obj.printer_port:
            # USB/Serial printer  
            p = Serial(settings_obj.printer_port)
            return p
        else:
            # Default: try USB auto-detect
            p = Usb(0x04b8, 0x0e15)  # Epson TM-T20
            return p
    except Exception as e:
        print(f"Printer connection failed: {e}")
        return None


def print_bill(bill, settings_obj=None):
    """
    Print a bill receipt to the thermal printer.
    Falls back to generating a text receipt if printer unavailable.
    """
    receipt_text = generate_receipt_text(bill, settings_obj)
    
    printer = get_printer(settings_obj)
    if printer:
        try:
            # Header
            printer.set(align='center', bold=True, height=2, width=2)
            printer.text(f"{settings_obj.restaurant_name if settings_obj else 'RESTAURANT'}\n")
            printer.set(align='center', bold=False, height=1, width=1)
            if settings_obj:
                if settings_obj.address:
                    printer.text(f"{settings_obj.address}\n")
                if settings_obj.phone:
                    printer.text(f"Tel: {settings_obj.phone}\n")
                if settings_obj.gstin:
                    printer.text(f"GSTIN: {settings_obj.gstin}\n")
            
            printer.text("-" * 32 + "\n")
            
            # Order info
            printer.set(align='left', bold=True)
            printer.text(f"Order: #{bill.order.order_number}\n")
            printer.text(f"Table: {bill.order.table.number}\n")
            printer.text(f"Date:  {bill.created_at.strftime('%d-%m-%Y %I:%M %p')}\n")
            if bill.order.waiter:
                printer.text(f"Waiter: {bill.order.waiter.name}\n")
            
            printer.text("-" * 32 + "\n")
            printer.set(align='left', bold=True)
            printer.text(f"{'ITEM':<18} {'QTY':>3} {'AMT':>8}\n")
            printer.text("-" * 32 + "\n")
            
            # Items
            printer.set(align='left', bold=False)
            for item in bill.order.items.all():
                name = item.menu_item.name[:18]
                printer.text(f"{name:<18} {item.quantity:>3} {item.subtotal:>7.2f}\n")
                if item.notes:
                    printer.text(f"  * {item.notes}\n")
            
            printer.text("-" * 32 + "\n")
            
            # Totals
            printer.set(align='right', bold=False)
            printer.text(f"Subtotal:        {bill.subtotal:>8.2f}\n")
            printer.text(f"Tax ({bill.tax_percent}%):      {bill.tax_amount:>8.2f}\n")
            if bill.discount_percent > 0:
                printer.text(f"Discount ({bill.discount_percent}%):  {bill.discount_amount:>8.2f}\n")
            
            printer.set(align='right', bold=True, height=1, width=1)
            printer.text(f"TOTAL:           {bill.total:>8.2f}\n")
            
            printer.text("-" * 32 + "\n")
            printer.set(align='left', bold=False)
            printer.text(f"Payment: {bill.get_payment_method_display()}\n")
            
            # Footer
            printer.text("-" * 32 + "\n")
            printer.set(align='center', bold=False)
            if settings_obj and settings_obj.footer_message:
                printer.text(f"{settings_obj.footer_message}\n")
            printer.text("\n\n\n")
            printer.cut()
            
            return True, "Bill printed successfully!"
        except Exception as e:
            return False, f"Print error: {str(e)}"
    else:
        return False, receipt_text  # Return text for display


def generate_receipt_text(bill, settings_obj=None):
    """Generate receipt as plain text (for display when no printer)."""
    name = settings_obj.restaurant_name if settings_obj else "RESTAURANT"
    lines = [
        "=" * 40,
        name.center(40),
    ]
    if settings_obj:
        if settings_obj.address:
            lines.append(settings_obj.address[:40].center(40))
        if settings_obj.phone:
            lines.append(f"Tel: {settings_obj.phone}".center(40))
        if settings_obj.gstin:
            lines.append(f"GSTIN: {settings_obj.gstin}".center(40))
    
    lines += [
        "=" * 40,
        f"Order: #{bill.order.order_number}",
        f"Table: {bill.order.table.number}",
        f"Date:  {bill.created_at.strftime('%d-%m-%Y %I:%M %p')}",
        "-" * 40,
        f"{'ITEM':<22} {'QTY':>3} {'AMOUNT':>10}",
        "-" * 40,
    ]
    
    for item in bill.order.items.all():
        lines.append(f"{item.menu_item.name[:22]:<22} {item.quantity:>3} {item.subtotal:>10.2f}")
        if item.notes:
            lines.append(f"  Note: {item.notes}")
    
    lines += [
        "-" * 40,
        f"{'Subtotal:':>30} {bill.subtotal:>8.2f}",
        f"{'Tax (' + str(bill.tax_percent) + '%):':>30} {bill.tax_amount:>8.2f}",
    ]
    
    if bill.discount_percent > 0:
        lines.append(f"{'Discount (' + str(bill.discount_percent) + '%):':>30} -{bill.discount_amount:>7.2f}")
    
    lines += [
        "=" * 40,
        f"{'TOTAL:':>30} {bill.total:>8.2f}",
        "=" * 40,
        f"Payment Method: {bill.get_payment_method_display()}",
        "-" * 40,
    ]
    
    if settings_obj and settings_obj.footer_message:
        lines.append(settings_obj.footer_message.center(40))
    
    lines.append("=" * 40)
    return "\n".join(lines)

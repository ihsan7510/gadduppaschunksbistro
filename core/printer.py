"""
Bluetooth/USB Thermal Printer Utility
Uses python-escpos library for ESC/POS thermal printers.
"""

import datetime
from decimal import Decimal
import socket
from escpos.escpos import Escpos


class BluetoothPrinter(Escpos):
    """
    Custom Bluetooth Printer class that uses Python's native socket support
    for AF_BLUETOOTH. This bypasses the pybluez dependency on Windows.
    """
    def __init__(self, mac, port=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac = mac
        self.port = port
        self.socket = None
        self.open()

    def open(self):
        if not self.socket:
            if not hasattr(socket, 'AF_BLUETOOTH'):
                raise OSError("Bluetooth (AF_BLUETOOTH) is not supported on this platform/environment.")
            
            # Form socket connection
            bt_proto = getattr(socket, 'BTPROTO_RFCOMM', 3)
            self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, bt_proto)
            self.socket.settimeout(10)
            
            # Format MAC address correctly to have colons if it doesn't
            mac_formatted = self.mac
            if len(mac_formatted) == 12 and ':' not in mac_formatted:
                mac_formatted = ":".join(mac_formatted[i:i+2] for i in range(0, 12, 2)).upper()
            
            self.socket.connect((mac_formatted, self.port))

    def _raw(self, msg: bytes) -> None:
        if not self.socket:
            self.open()
        self.socket.sendall(msg)

    def close(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    def __del__(self):
        self.close()


def get_printer(settings_obj=None):
    """
    Get printer instance based on restaurant settings.
    Returns None if no printer configured or connection fails.
    """
    try:
        from escpos.printer import Usb, Serial
        
        if settings_obj and settings_obj.printer_mac:
            # Bluetooth printer
            p = BluetoothPrinter(settings_obj.printer_mac)
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


def format_bill_receipt(printer, bill, settings_obj=None):
    """Format and send print commands to the printer instance."""
    # Header
    printer.set(align='center', bold=True, height=2, width=2)
    printer.text(f"{settings_obj.restaurant_name if settings_obj else 'Gadduppas'}\n")
    printer.set(align='center', bold=False, height=1, width=1)
    if settings_obj:
        if settings_obj.address:
            printer.text(f"{settings_obj.address}\n")
        if settings_obj.phone:
            printer.text(f"Phone: {settings_obj.phone}\n")
    
    printer.text("-" * 32 + "\n")
    printer.set(align='center', bold=True)
    printer.text("Bill of Supply\n\n")
    
    # Order info
    printer.set(align='left', bold=False)
    printer.text("Cash\n")
    
    # Align right for Date, Time, Invoice no
    date_str = bill.created_at.strftime('%d/%m/%Y')
    time_str = bill.created_at.strftime('%I:%M %p').lower()
    invoice_no = str(bill.pk)
    
    printer.text(f"{'Date:':>32}\n")
    printer.text(f"{date_str:>32}\n")
    printer.text(f"Time: {time_str:>26}\n")
    printer.text(f"Invoice no:\n")
    printer.text(f"{invoice_no:>32}\n")
    
    printer.text("-" * 32 + "\n")
    printer.set(align='left', bold=True)
    printer.text(f"{'Item Name':<16}{'Price':>8}{'Amount':>8}\n")
    printer.text(f"{'Qty':<32}\n")
    printer.text("-" * 32 + "\n")
    
    # Items
    printer.set(align='left', bold=False)
    for item in bill.order.items.all():
        name = item.menu_item.name
        price = item.price
        amount = item.subtotal
        qty = item.quantity
        
        # Print item name, price, amount
        printer.text(f"{name[:16]:<16}{price:>8.2f}{amount:>8.2f}\n")
        printer.text(f"x{qty:<31}\n")
    
    printer.text("-" * 32 + "\n")
    
    # Totals
    printer.set(align='left', bold=False)
    printer.text(f"{'Subtotal':<16} : {bill.subtotal:>13.2f}\n")
    printer.set(align='left', bold=True)
    printer.text(f"{'Total':<16} : {bill.total:>13.2f}\n")
    
    # QR code section
    printer.text("\n")
    try:
        upi_id = settings_obj.upi_id if (settings_obj and settings_obj.upi_id) else 'merchant@upi'
        restaurant_name = settings_obj.restaurant_name if settings_obj else 'Gadduppas'
        printer.qr(f"upi://pay?pa={upi_id}&pn={restaurant_name}&am={bill.total}&cu=INR", size=6)
    except Exception:
        printer.set(align='center')
        printer.text("[ QR Code to Pay ]\n")
    
    printer.set(align='center', bold=False)
    printer.text("\nScan this QR code to pay\n")
    printer.text("-" * 32 + "\n")
    
    # Footer
    printer.set(align='center', bold=True)
    printer.text("Terms & Conditions\n")
    printer.set(align='center', bold=False)
    if settings_obj and settings_obj.footer_message:
        # Wrap footer message to fit 32 chars
        msg = settings_obj.footer_message
        words = msg.split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 <= 32:
                line += (" " if line else "") + w
            else:
                printer.text(f"{line}\n")
                line = w
        if line:
            printer.text(f"{line}\n")
    else:
        printer.text("FOOD SHOULD BE CONSUMED\nWITH IN 1 HOURS OF DELIVERY IN\nHYGIENIC ENVIRONMENT\n")
    
    printer.text("\n\n\n")
    printer.cut()


def print_bill(bill, settings_obj=None):
    """
    Print a bill receipt to the thermal printer.
    Falls back to generating a text receipt if printer unavailable.
    """
    receipt_text = generate_receipt_text(bill, settings_obj)
    
    printer = get_printer(settings_obj)
    if printer:
        try:
            format_bill_receipt(printer, bill, settings_obj)
            return True, "Bill printed successfully!"
        except Exception as e:
            return False, f"Print error: {str(e)}"
        finally:
            try:
                printer.close()
            except Exception:
                pass
    else:
        return False, receipt_text  # Return text for display


def get_bill_escpos_bytes(bill, settings_obj=None):
    """
    Get the raw ESC/POS bytes for the bill.
    Used for Web Bluetooth printing.
    """
    from escpos.printer import Dummy
    printer = Dummy()
    format_bill_receipt(printer, bill, settings_obj)
    return printer.output




def generate_receipt_text(bill, settings_obj=None):
    """Generate receipt as plain text (for display when no printer)."""
    name = settings_obj.restaurant_name if settings_obj else "GADDUPPAS CHUNKS BISTRO"
    addr = settings_obj.address if settings_obj else "Ashokapuram"
    phone = settings_obj.phone if settings_obj else "+91 9048444991"
    
    lines = [
        name.center(32),
        addr.center(32),
        f"Phone: {phone}".center(32),
        "-" * 32,
        "Bill of Supply".center(32),
        "",
        f"{'Cash':<16}",
        f"{'Date:':>32}",
        f"{bill.created_at.strftime('%d/%m/%Y'):>32}",
        f"Time: {bill.created_at.strftime('%I:%M %p').lower():>26}",
        f"Invoice no:",
        f"{bill.pk:>32}",
        "-" * 32,
        f"{'Item Name':<16}{'Price':>8}{'Amount':>8}",
        f"{'Qty':<32}",
        "-" * 32,
    ]
    
    for item in bill.order.items.all():
        lines.append(f"{item.menu_item.name[:16]:<16}{item.price:>8.2f}{item.subtotal:>8.2f}")
        lines.append(f"x{item.quantity:<31}")
        
    lines += [
        "-" * 32,
        f"{'Subtotal':<16} : {bill.subtotal:>13.2f}",
        f"{'Total':<16} : {bill.total:>13.2f}",
        "",
        "[QR CODE PLACEHOLDER]".center(32),
        "",
        "Scan this QR code to pay".center(32),
        "-" * 32,
        "Terms & Conditions".center(32),
    ]
    
    footer_msg = settings_obj.footer_message if settings_obj else "FOOD SHOULD BE CONSUMED WITH IN 1 HOURS OF DELIVERY IN HYGIENIC ENVIRONMENT"
    # Wrap footer to 32 chars
    words = footer_msg.split()
    line = ""
    for w in words:
        if len(line) + len(w) + 1 <= 32:
            line += (" " if line else "") + w
        else:
            lines.append(line.center(32))
            line = w
    if line:
        lines.append(line.center(32))
        
    return "\n".join(lines)

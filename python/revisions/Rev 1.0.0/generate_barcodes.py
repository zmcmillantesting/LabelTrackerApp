from barcode import Code128
from barcode.writer import ImageWriter
import os

def generate_barcodes():
    # Create a directory for the barcodes if it doesn't exist
    if not os.path.exists('barcodes'):
        os.makedirs('barcodes')
    
    # Generate PASS barcode
    pass_code = Code128('__PASS__', writer=ImageWriter())
    pass_code.save('barcodes/pass_barcode')
    
    # Generate FAIL barcode
    fail_code = Code128('__FAIL__', writer=ImageWriter())
    fail_code.save('barcodes/fail_barcode')
    
    print("Barcodes generated successfully!")
    print("PASS barcode saved as: barcodes/pass_barcode.png")
    print("FAIL barcode saved as: barcodes/fail_barcode.png")

if __name__ == "__main__":
    generate_barcodes() 
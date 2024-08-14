import sys
import logging
from PIL import Image
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
import tempfile
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def split_pdf(input_pdf, output_pdf):
    try:
        # Open the input PDF
        doc = fitz.open(input_pdf)

        # List to store paths of temporary image files
        temp_image_files = []

        width = height = 0

        for page_num in range(len(doc)):
            logger.info(f"Processing page {page_num + 1}")

            try:
                # Convert PDF page to image with higher resolution
                page = doc.load_page(page_num)
                zoom = 2  # Increase this for higher quality, but larger file size
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                # Get image dimensions
                width, height = img.size

                # Split the image
                left_half = img.crop((0, 0, width // 2, height))
                right_half = img.crop((width // 2, 0, width, height))

                # Save split images to temporary files
                for half in [left_half, right_half]:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    half.save(temp_file.name, format='JPEG')
                    temp_image_files.append(temp_file.name)

                logger.info(f"Split page {page_num + 1} into two halves")
            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                continue

        doc.close()

        # Create a new PDF with the split images
        c = canvas.Canvas(output_pdf, pagesize=(width // 2, height))
        for img_path in temp_image_files:
            c.drawImage(img_path, 0, 0, width // 2, height)
            c.showPage()
        c.save()

        # Clean up temporary files
        for temp_file in temp_image_files:
            os.remove(temp_file)

        logger.info(f"Successfully split {input_pdf} into {output_pdf}")
        logger.info(f"Total pages in output PDF: {len(temp_image_files)}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        logger.exception("Exception details:")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.error("Usage: python script.py input.pdf output.pdf")
    else:
        split_pdf(sys.argv[1], sys.argv[2])
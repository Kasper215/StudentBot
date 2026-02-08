import img2pdf
import os

def convert_images_to_pdf(image_paths: list[str], output_pdf_path: str) -> bool:
    """
    Принимает список путей к картинкам и сохраняет их в один PDF.
    """
    try:
        # Склеиваем картинки в байты PDF
        pdf_bytes = img2pdf.convert(image_paths)
        
        # Записываем в файл
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        return True
    except Exception as e:
        print(f"Ошибка конвертации: {e}")
        return False
    
def clean_up_files(file_paths: list[str]):
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)
            
from pdf2image import convert_from_path

def convert_pdf_to_jpgs(pdf_path: str, output_folder: str):
    images = convert_from_path(pdf_path)
    image_paths = []

    for i, image in enumerate(images):
        img_path = os.path.join(output_folder, f"page_{i}.jpg")
        image.save(image.path, "JPEG")
        image_paths.append(img_path)

        return image_paths
    
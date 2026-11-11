import io
import qrcode
from django.core.files.base import ContentFile


def generate_qr_code_image(token_str: str, booking_reference: str) -> ContentFile:
    """
    Generates a secure QR code encoding the verification payload.
    Uses high error correction and returns a Django ContentFile ready to save.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=3,
    )
    # The payload is the secure token and booking reference
    payload = f"UNIBOOK:{token_str}:{booking_reference}"
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#172554", back_color="#FFFFFF")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    file_name = f"qr_{booking_reference}.png"
    return ContentFile(buffer.getvalue(), name=file_name)

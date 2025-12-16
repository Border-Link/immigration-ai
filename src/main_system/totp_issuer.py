import base64
from io import BytesIO
from helpers.totp import TOTPAuthenticator
import qrcode

TOTP_ISSUER = "Borderlink"

class QRCodeGenerator:
    @staticmethod
    def generate(secret: str, user_email: str) -> str:
        otp_uri = TOTPAuthenticator.generate_totp_uri(
            secret=secret,
            user_email=user_email,
            issuer=TOTP_ISSUER,
        )

        qr = qrcode.make(otp_uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        return qr_base64
import pyotp


class TOTPAuthenticator:

    @staticmethod
    def verify_totp(secret, otp, valid_window=0):
        totp = pyotp.TOTP(secret)
        return totp.verify(otp, valid_window=valid_window)

    @staticmethod
    def generate_totp():
        return pyotp.random_base32(length=32)

    @staticmethod
    def generate_totp_uri(secret, user_email, issuer):
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer)

import logging
import wincertstore
import base64
import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import ssl
import subprocess
from pathlib import Path

import io

def load_cert(certname: str) -> str | None:
    def hex_string_readable(bytes):
        return ["{:02X}".format(x) for x in bytes]
    logging.debug(f"Attempting to load certificate '{certname}'")

    if os.name == 'nt':
        for storename in ("ROOT", "CA", "MY"):
            with wincertstore.CertSystemStore(storename) as store:
                for cert in store.itercerts(usage=wincertstore.SERVER_AUTH):
                    logging.debug(f"found: {cert.get_name()}")
                    if cert.get_name() == certname:
                        try:
                            logging.debug(f"Acquiring certificate {cert.get_name()}")
                            pem = cert.get_pem()
                            encodedDer = ''.join(pem.split("\n")[1:-2])

                            cert_bytes = base64.b64decode(encodedDer)
                            cert_pem = ssl.DER_cert_to_PEM_cert(cert_bytes)
                            cert_details = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'), default_backend())

                            fingerprint = hex_string_readable(cert_details.fingerprint(hashes.SHA1()))
                            fingerprint_string = ''.join(fingerprint)

                            logging.debug(f"Found certificate for '{certname}' with thumbprint '{fingerprint_string.lower()}'")
                            return fingerprint_string.lower()
                        except Exception as e:
                            logging.warning(f"A matching certificate was found but an unknown exception happened: {e}")
        logging.warning(f"Could not find a certificate with name {certname}")
        logging.info("This program will not be able to communicate with IoTHub")
        logging.info("Review the certificate store and/or certificate name and ensure it matches in Azure")
        return None

    else:
        logging.warning("This program is not running in a Windows environment. It will not be able to find the certificate file")
    return None


def export_cert(thumbprint: str) -> bool:
    path_obj = Path(__file__).parent.parent.parent / "data" / "certificate_python.pfx"
    filepath = str(path_obj)
    logging.debug(f"temp_cert_filepath: {filepath}")
    
    powershell_command = f"""
    $thumb = "{thumbprint}"
    $cert = Get-ChildItem -Path Cert:\\CurrentUser\\My | Where-Object {{ $_.Thumbprint -eq $thumb }}
    $password = New-Object -TypeName System.Security.SecureString
    Export-PfxCertificate -Cert $cert -FilePath "{filepath}" -Password $password
    """

    try:
        _ = subprocess.run(["powershell", "-Command", powershell_command], stdout=subprocess.DEVNULL)
        logging.debug("Successfully exported certificate")
        return True
    except Exception as e:
        logging.warning(f"Unexpected error attempting to export certificate: {e}")
        return False


def add_cert(certname: str):
    thumbprint = load_cert(certname)
    if thumbprint is not None:
        _ = export_cert(thumbprint)


def remove_cert():
    path_obj = Path(__file__).parent.parent.parent / "data" / "certificate_python.pfx"
    try:
        os.remove(path_obj)
        logging.debug(f"Removed certificate information from data cache")
    except Exception as e:
        logging.warning(f"Error attempting to remove certificate from data: {e}")

if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.DEBUG)
    thumbprint = load_cert("albertsons-test-certificate")
    cert = export_cert(thumbprint)
    print(cert)
    if thumbprint is not None:
        _ = export_cert(thumbprint)
    time.sleep(3)
    remove_cert()

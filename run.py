"""Launcher that patches the Windows SSL cert-store bug before starting Streamlit."""
import ssl

# Patch SSLContext.load_default_certs so that a corrupt Windows cert-store
# entry doesn't abort the tornado import (ssl.SSLError: nested asn1 error).
_orig_load = ssl.SSLContext.load_default_certs
def _safe_load(self, purpose=ssl.Purpose.SERVER_AUTH):
    try:
        _orig_load(self, purpose)
    except ssl.SSLError:
        pass
ssl.SSLContext.load_default_certs = _safe_load

from streamlit.web import cli as stcli
import sys

sys.argv = ["streamlit", "run", "app.py", "--server.headless=false"]
stcli.main()

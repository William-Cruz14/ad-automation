import ssl, socket

HOST = "DC-SERVER.addc.local"
PORT = 636
CA_FILE = r"D:\Python\AD-Automation-Python\certicate\cert_CA.cer"

ctx = ssl.create_default_context(cafile=CA_FILE)
with socket.create_connection((HOST, PORT), timeout=5) as sock:
    with ctx.wrap_socket(sock, server_hostname=HOST) as ssock:
        cert = ssock.getpeercert()
        print("TLS OK!")
        print("Protocolo:", ssock.version())
        print("Subject:", dict(x[0] for x in cert["subject"]))
        print("SAN:", cert.get("subjectAltName"))
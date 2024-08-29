import eventlet
eventlet.monkey_patch()

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from hashlib import sha1
import base64
import requests
import uuid


# Generate the keypair, always do this at the start of your program, as it can take a while on slower computers.

print("Generating keypair")


private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
    backend=default_backend()
)
public_key = private_key.public_key()

public_der = public_key.public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

def get_public_der_base64() -> str:
    return base64.b64encode(public_der).decode("utf-8")

def auth_finish(secretKeyText, username):
    secretKeyEncrypted = base64.b64decode(secretKeyText)
    # Decrypt the secret key using your private key, note the padding used.
    secretKey = private_key.decrypt(secretKeyEncrypted, padding.PKCS1v15())
    # Create the server hash in the same way FireClient did, note this is different to the way Minecraft does it as it uses a regular hexdigest on the hash.
    serverHash = sha1(secretKey + public_der).hexdigest()[0:30]
    # Send a request to the authentication servers, if you get back a sucessfull response the player has logged in successfully.
    r = requests.get("https://sessionserver.mojang.com/session/minecraft/hasJoined?username="+username+"&serverId="+serverHash)
    u = uuid.UUID(hex=r.json()["id"])
    return u.__str__()
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend




def generateInitialkey():
    key = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, \
    key_size=2048)
    return key

def publicKeyBytes(initial_key):
    public_key = initial_key.public_key().public_bytes(serialization.Encoding.OpenSSH, \
    serialization.PublicFormat.OpenSSH)
    return public_key

def privateKeyBytes(initial_key):
    pem = initial_key.private_bytes(encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption())
    return pem


key = generateInitialkey()


# generate private/public key pair

#public_key = publicKeyBytes(key)



pem = privateKeyBytes(key)


loaded_key = serialization.load_pem_private_key(
        pem,
        backend=default_backend(),
        password=None,
    )


public_key = publicKeyBytes(loaded_key)

 


# private_key_str = pem.decode('utf-8')

# public_key_str = public_key.decode('utf-8')



# print('Private key = ')
# print(pem)
# print('Public key = ')
# print(public_key_str)


# Verification 
message = b"A message I want to sign"
signature = key.sign(
    message,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

key.public_key().verify(
    signature,
    message,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)



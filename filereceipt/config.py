import hashlib

# Dictionary of hash algorithms and their corresponding hashlib functions
HASH_ALGORITHMS = {
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512,
    'sha1': hashlib.sha1,
    'md5': hashlib.md5,
    'sha3_224': hashlib.sha3_224,
    'sha3_256': hashlib.sha3_256,
    'sha3_384': hashlib.sha3_384,
    'sha3_512': hashlib.sha3_512,
    'blake2s': hashlib.blake2s,
    'blake2b': hashlib.blake2b
}

# UI Hash Algorithm Display Names
HASH_ALGORITHM_DISPLAY_NAMES = [
    'SHA256',
    'SHA512',
    'SHA1',
    'MD5',
    'SHA3_224',
    'SHA3_256',
    'SHA3_384',
    'SHA3_512',
    'BLAKE2s',
    'BLAKE2b'
]

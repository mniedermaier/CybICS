import logging
from pathlib import Path
from typing import Union

from asyncua.crypto import uacrypto
from asyncua.server.users import User, UserRole

admin_db =  {
               #'admin1': 'adminpw1'
            }

users_db =  {
                #pw with hash-key 678 and hmac_sha256-algorithm: test
                'user1': '5ef3db05618bedf7732de684affe503257db5a76c7986568d3ca81d214cdb6d9' 
            }

class Pw_Cert_UserManager:
    """
    Handel user management: 
    Add certificates for allowing authentication on the server with it; Add roles user/admin to the certificate
    Checks during login a certificate or username/password if a sign in is allowed and returns the corresponding role.     
    """
    def __init__(self):
        self._trusted_certificates = {}

    def get_user(self, iserver, username=None, password=None, certificate=None):
        """
        Checks during login a certificate or username/password if a sign in is allowed and returns the corresponding role.     
        """
        if username in users_db and (uacrypto.hmac_sha256(b'678',bytes(password, 'UTF-8'))).hex() == users_db[username]:
            return User(role=UserRole.User)
        if username in admin_db and (uacrypto.hmac_sha256(b'678',bytes(password, 'UTF-8'))).hex() == admin_db[username]:
            return User(role=UserRole.Admin)
        if certificate is None:
            return None
        correct_users = [prospective_certificate['user'] for prospective_certificate in self._trusted_certificates.values()
                         if certificate == prospective_certificate['certificate']]
        if len(correct_users) == 0:
            return None
        else:
            return correct_users[0]

    async def add_role(self, certificate_path: Path, user_role: UserRole, name: str, format: Union[str, None] = None):
        """
        Internal function that adds a role to a given certificate while registering the certificate for login     
        """
        certificate = await uacrypto.load_certificate(certificate_path, format)
        if name is None:
            raise KeyError

        user = User(role=user_role, name=name)

        if name in self._trusted_certificates:
            logging.warning("certificate with name %s "
                            "attempted to be added multiple times, only the last version will be kept.", name)
        self._trusted_certificates[name] = {'certificate': uacrypto.der_from_x509(certificate), 'user': user}

    async def add_user(self, certificate_path: Path, name: str, format: Union[str, None] = None):
        """
        Register a certificate for authentication in the server and link it with the role user    
        """
        await self.add_role(certificate_path=certificate_path, user_role=UserRole.User, name=name, format=format)

    async def add_admin(self, certificate_path: Path, name: str, format: Union[str, None] = None):
        """
        Register a certificate for authentication in the server and link it with the role admin    
        """
        await self.add_role(certificate_path=certificate_path, user_role=UserRole.Admin, name=name, format=format)

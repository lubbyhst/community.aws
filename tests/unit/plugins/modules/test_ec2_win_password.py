from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

'''
Commands to encrypt a message that can be decrypted:
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
import base64

path = '/path/to/rsa_public_key.pem'
with open(path, 'r') as f:
    rsa_public_key_pem = to_text(f.read())
load_pem_public_key(rsa_public_key_pem = , default_backend())
base64_cipher = public_key.encrypt('Ansible_AWS_EC2_Win_Password', PKCS1v15())
string_cipher = base64.b64encode(base64_cipher)
'''

import datetime
import pytest

from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

from ansible_collections.community.aws.tests.unit.compat.mock import patch
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import AnsibleExitJson
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import ModuleTestCase
from ansible_collections.community.aws.tests.unit.plugins.modules.utils import set_module_args

from ansible_collections.community.aws.plugins.modules.ec2_win_password import setup_module_object
from ansible_collections.community.aws.plugins.modules.ec2_win_password import ec2_win_password

fixture_prefix = 'tests/unit/plugins/modules/fixtures/certs'

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_api_gateway.py requires the `boto3` and `botocore` modules")


class TestEc2WinPasswordModule(ModuleTestCase):

    # Future: It would be good to generate this data on the fly and use a
    # temporary certificate and password.
    PEM_PATH = fixture_prefix + '/ec2_win_password.pem'
    UNENCRYPTED_DATA = 'Ansible_AWS_EC2_Win_Password'
    ENCRYPTED_DATA = 'L2k1iFiu/TRrjGr6Rwco/T3C7xkWxUw4+YPYpGGOmP3KDdy3hT1' \
                     '8RvdDJ2i0e+y7wUcH43DwbRYSlkSyALY/nzjSV9R5NChUyVs3W5' \
                     '5oiVuyTKsk0lor8dFJ9z9unq14tScZHvyQ3Nx1ggOtS18S9Pk55q' \
                     'IaCXfx26ucH76VRho='
    INSTANCE_ID = 'i-12345'

    @patch('ansible_collections.community.aws.plugins.modules.s3_bucket_notification.AnsibleAWSModule.client')
    def test_decryption(self, mock_client):

        path = self.PEM_PATH
        with open(path, 'r') as f:
            pem = to_text(f.read())

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({'instance_id': self.INSTANCE_ID,
                             'key_data': pem,
                             })
            module = setup_module_object()
            mock_client().get_password_data.return_value = {
                'InstanceId': self.INSTANCE_ID,
                'PasswordData': self.ENCRYPTED_DATA,
                'Timestamp': datetime.datetime.now(),
            }
            ec2_win_password(module)

        self.assertEqual(
            exec_info.exception.args[0]['win_password'],
            to_bytes(self.UNENCRYPTED_DATA),
        )

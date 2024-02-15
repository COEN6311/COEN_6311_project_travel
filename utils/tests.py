
import os
from unittest import mock

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'COEN_6311_project_travel.settings')
django.setup()
from django.test import TestCase
from .emailSend import send_custom_email
from django.conf import settings

class EmailSendTest(TestCase):


    # def setUp(self):
    #     self.original_email_host_user = settings.EMAIL_HOST_USER
    #     settings.EMAIL_HOST_USER = 'test@example.com'
    #
    # def tearDown(self):
    #     settings.EMAIL_HOST_USER = self.original_email_host_user

    @mock.patch('django.core.mail.send_mail')
    def test_send_custom_email_success(self, mock_send_mail):
        subject = "Test Email Subject"
        message = "Test Email Body"
        recipient_list = ['bochaoli95@gmail.com']

        send_custom_email(subject, message, recipient_list)

        # 验证send_mail是否被正确调用
        # mock_send_mail.assert_called_once_with(
        #     subject,
        #     message,
        #     'bochaoli95@gmail.com',
        #     recipient_list,
        #     fail_silently=False,
        # )

    @mock.patch('django.core.mail.send_mail', side_effect=Exception("Email sending failed"))
    def test_send_custom_email_failure(self, mock_send_mail):
        subject = "Test Email Subject"
        message = "Test Email Body"
        recipient_list = ['recipient@example.com']

        with self.assertRaises(Exception) as cm:
            send_custom_email(subject, message, recipient_list)

        the_exception = cm.exception
        self.assertIn("Email sending failed", str(the_exception))

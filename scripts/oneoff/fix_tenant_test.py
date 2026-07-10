# -*- coding: utf-8 -*-
# Fix the hanging test_campaign_runner_injects_tenant_smtp_to_user_details test
# by patching _discover_jobs and _send_campaign_emails to prevent real network calls

with open('tests/test_tenant_smtp.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The old patch decorator only patches get_tenant_smtp_provider
# We need to ALSO patch _discover_jobs and _send_campaign_emails
# to prevent real MultiSourceSearch/EmailEngine calls that hang the test

old_decorator = '    @patch("core.multi_tenant.MultiTenantRunner.get_tenant_smtp_provider")\n    def test_campaign_runner_injects_tenant_smtp_to_user_details(self, mock_get_smtp):'

new_decorator = '''    @patch("core.campaign_runner._discover_jobs", new_callable=AsyncMock)
    @patch("core.campaign_runner._send_campaign_emails", new_callable=AsyncMock)
    @patch("core.multi_tenant.MultiTenantRunner.get_tenant_smtp_provider")
    def test_campaign_runner_injects_tenant_smtp_to_user_details(
            self, mock_get_smtp, mock_send, mock_discover):'''

if old_decorator in content:
    content = content.replace(old_decorator, new_decorator)
    # Also set return values for the new mocks
    old_discover_return = "        mock_get_smtp.return_value = {"
    new_discover_return = (
        "        # Prevent real job discovery and email sending\n"
        "        mock_discover.return_value = []\n"
        "        mock_send.return_value = (0, 0, None)\n"
        "        mock_get_smtp.return_value = {"
    )
    content = content.replace(old_discover_return, new_discover_return)
    with open('tests/test_tenant_smtp.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Decorator not found - already fixed or different format")
    idx = content.find("test_campaign_runner_injects_tenant_smtp")
    print(repr(content[max(0, idx-50):idx+300]))

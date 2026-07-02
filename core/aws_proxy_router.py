import os
import random
import logging

logger = logging.getLogger("AWSProxyRouter")


class AWSProxyRouter:
    """
    Manages IP rotation using AWS API Gateway as a dynamic proxy.
    This exploits the 1 million free requests/month on AWS to route
    Camoufox traffic through ever-changing AWS Lambda IPs.
    """

    def __init__(self):
        # The list of deployed AWS API Gateway endpoint URLs.
        # Format: https://<api-id>.execute-api.<region>.amazonaws.com/<stage>
        self.endpoints = os.getenv("AWS_PROXY_ENDPOINTS", "").split(",")
        self.endpoints = [e.strip() for e in self.endpoints if e.strip()]

        if not self.endpoints:
            logger.warning(
                "No AWS API Gateway endpoints configured. Direct connection will be used."
            )

    def get_random_proxy(self) -> dict | None:
        """
        Returns a formatted proxy dictionary for httpx or Camoufox,
        using a random AWS API Gateway endpoint if available.
        """
        if not self.endpoints:
            return None

        endpoint = random.choice(self.endpoints)
        logger.info(f"Selected AWS Proxy Endpoint: {endpoint}")

        # Depending on how the AWS Lambda proxy is implemented,
        # it might act as an HTTP proxy or a REST forwarding service.
        # Assuming an HTTP proxy format here:
        return {"server": endpoint}

    def format_camoufox_proxy(self) -> str | None:
        """
        Formats the proxy string specifically for Camoufox launch parameters.
        """
        proxy = self.get_random_proxy()
        if proxy:
            return proxy["server"]
        return None

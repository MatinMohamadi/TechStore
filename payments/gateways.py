"""
Payment gateway abstraction — Strategy/Adapter pattern.

To add a new gateway:
1. Create a class implementing PaymentGatewayInterface
2. Register it in GATEWAY_MAP below
"""

import logging
from abc import ABC, abstractmethod
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger("payments")


class PaymentGatewayInterface(ABC):
    """Abstract interface for all payment gateways."""

    @abstractmethod
    def initiate_payment(
        self, amount: Decimal, order_id: int, callback_url: str, description: str = ""
    ) -> dict:
        """
        Create a payment request and return gateway info.

        Returns:
            {
                "authority": str,   # gateway transaction ID
                "payment_url": str, # URL to redirect user for payment
            }
        Raises:
            PaymentGatewayError on failure.
        """
        pass

    @abstractmethod
    def verify_payment(self, authority: str, amount: Decimal) -> dict:
        """
        Verify a payment after callback.

        Returns:
            {
                "success": bool,
                "transaction_ref": str | None,  # gateway ref code
                "card_pan": str | None,         # masked card number
                "raw": dict,                    # full gateway response
            }
        """
        pass


class PaymentGatewayError(Exception):
    """Raised when gateway communication fails."""

    pass


class ZarinpalGateway(PaymentGatewayInterface):
    """
    Zarinpal payment gateway (Sandbox).

    Sandbox: https://sandbox.zarinpal.com
    Production: https://api.zarinpal.com

    Docs: https://docs.zarinpal.com/
    """

    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.sandbox = settings.ZARINPAL_SANDBOX
        if self.sandbox:
            self.base_url = "https://sandbox.zarinpal.com/pg/rest/WebGate"
            self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay"
        else:
            self.base_url = "https://api.zarinpal.com/pg/rest/WebGate"
            self.payment_url = "https://www.zarinpal.com/pg/StartPay"

    def initiate_payment(self, amount, order_id, callback_url, description=""):
        """Request payment from Zarinpal and get authority token."""
        # Zarinpal expects amount in Tomans (1 IRR = 10 Toman)
        amount_toman = int(amount // 10)

        payload = {
            "MerchantID": self.merchant_id,
            "Amount": amount_toman,
            "CallbackURL": callback_url,
            "Description": description or f"Order #{order_id}",
        }

        try:
            resp = requests.post(
                f"{self.base_url}/PaymentRequest.json",
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error(f"Zarinpal initiate error: {e}")
            raise PaymentGatewayError(f"Gateway communication failed: {e}") from e

        if data.get("Status") == 100:
            authority = data["Authority"]
            payment_url = f"{self.payment_url}/ZPAY:{self.merchant_id}/{authority}"
            return {
                "authority": authority,
                "payment_url": payment_url,
            }
        else:
            status_code = data.get("Status")
            logger.error(f"Zarinpal initiate failed with status: {status_code}")
            raise PaymentGatewayError(f"Zarinpal error code: {status_code}")

    def verify_payment(self, authority, amount):
        """Verify payment with Zarinpal after callback."""
        amount_toman = int(amount // 10)

        payload = {
            "MerchantID": self.merchant_id,
            "Amount": amount_toman,
            "Authority": authority,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/PaymentVerify.json",
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error(f"Zarinpal verify error: {e}")
            raise PaymentGatewayError(f"Gateway verification failed: {e}") from e

        # Status 100 = success, 101 = already verified
        success = data.get("Status") in (100, 101)
        card_pan = data.get("CardPan", "")
        if card_pan and len(card_pan) >= 6:
            card_pan = f"{card_pan[:6]}***{card_pan[-4:]}"

        return {
            "success": success,
            "transaction_ref": data.get("RefID"),
            "card_pan": card_pan,
            "raw": data,
        }


# ── Gateway Registry ──────────────────────────────────────
# Add new gateways here to make them available system-wide.

GATEWAY_MAP = {
    "zarinpal": ZarinpalGateway,
    # "idpay": IDPayGateway,  # future
    # "stripe": StripeGateway,  # future
}


def get_gateway(name: str) -> PaymentGatewayInterface:
    """Factory function to get a payment gateway by name."""
    gateway_cls = GATEWAY_MAP.get(name)
    if not gateway_cls:
        raise ValueError(f"Unknown payment gateway: {name}")
    return gateway_cls()

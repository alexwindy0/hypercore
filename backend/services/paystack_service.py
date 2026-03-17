"""
Paystack Payment Service - Handle payments and transactions
"""

import os
import requests
from flask import current_app


class PaystackService:
    """Service for Paystack API integration"""

    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.secret_key = os.getenv("PAYSTACK_SECRET_KEY")
        self.public_key = os.getenv("PAYSTACK_PUBLIC_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initialize_transaction(
        self, email, amount, reference, callback_url=None, metadata=None
    ):
        """
        Initialize a Paystack transaction

        Args:
            email: Customer email
            amount: Amount in kobo (multiply Naira by 100)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional transaction data

        Returns:
            dict: Paystack response
        """
        url = f"{self.BASE_URL}/transaction/initialize"

        payload = {
            "email": email,
            "amount": int(amount),
            "reference": reference,
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"],
        }

        if callback_url:
            payload["callback_url"] = callback_url

        if metadata:
            payload["metadata"] = metadata

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack initialize error: {str(e)}")
            return {"status": False, "message": str(e)}

    def verify_transaction(self, reference):
        """
        Verify a Paystack transaction

        Args:
            reference: Transaction reference

        Returns:
            dict: Paystack response with transaction details
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack verify error: {str(e)}")
            return {"status": False, "message": str(e)}

    def get_transaction(self, transaction_id):
        """
        Get transaction details by ID

        Args:
            transaction_id: Paystack transaction ID

        Returns:
            dict: Transaction details
        """
        url = f"{self.BASE_URL}/transaction/{transaction_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack get transaction error: {str(e)}")
            return {"status": False, "message": str(e)}

    def list_transactions(self, per_page=50, page=1, customer=None, status=None):
        """
        List transactions

        Args:
            per_page: Number of results per page
            page: Page number
            customer: Filter by customer ID
            status: Filter by status

        Returns:
            dict: List of transactions
        """
        url = f"{self.BASE_URL}/transaction"
        params = {"perPage": per_page, "page": page}

        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status

        try:
            response = requests.get(
                url, params=params, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack list transactions error: {str(e)}")
            return {"status": False, "message": str(e)}

    def create_refund(self, transaction, amount=None):
        """
        Create a refund for a transaction

        Args:
            transaction: Transaction reference or ID
            amount: Amount to refund (in kobo), None for full refund

        Returns:
            dict: Refund response
        """
        url = f"{self.BASE_URL}/refund"

        payload = {"transaction": transaction}
        if amount:
            payload["amount"] = int(amount)

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack refund error: {str(e)}")
            return {"status": False, "message": str(e)}

    def get_bank_list(self, country="nigeria"):
        """
        Get list of supported banks

        Args:
            country: Country code

        Returns:
            dict: List of banks
        """
        url = f"{self.BASE_URL}/bank"
        params = {"country": country}

        try:
            response = requests.get(
                url, params=params, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack bank list error: {str(e)}")
            return {"status": False, "message": str(e)}

    def resolve_account_number(self, account_number, bank_code):
        """
        Resolve account number to verify it exists

        Args:
            account_number: Bank account number
            bank_code: Bank code

        Returns:
            dict: Account details
        """
        url = f"{self.BASE_URL}/bank/resolve"
        params = {"account_number": account_number, "bank_code": bank_code}

        try:
            response = requests.get(
                url, params=params, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Paystack resolve account error: {str(e)}")
            return {"status": False, "message": str(e)}

    @staticmethod
    def amount_to_kobo(amount_naira):
        """
        Convert Naira amount to kobo (Paystack uses kobo)

        Args:
            amount_naira: Amount in Naira

        Returns:
            int: Amount in kobo
        """
        return int(float(amount_naira) * 100)

    @staticmethod
    def kobo_to_naira(amount_kobo):
        """
        Convert kobo amount to Naira

        Args:
            amount_kobo: Amount in kobo

        Returns:
            float: Amount in Naira
        """
        return float(amount_kobo) / 100

    def verify_webhook_signature(self, signature, request_body):
        """
        Verify Paystack webhook signature

        Args:
            signature: Signature from header
            request_body: Raw request body

        Returns:
            bool: Whether signature is valid
        """
        import hmac
        import hashlib

        if not self.secret_key or not signature:
            return False

        expected_signature = hmac.new(
            self.secret_key.encode("utf-8"), request_body, hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)


# Aliases to allow direct import of these utility functions
amount_to_kobo = PaystackService.amount_to_kobo
kobo_to_naira = PaystackService.kobo_to_naira

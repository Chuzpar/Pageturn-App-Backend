import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PesapalError(Exception):
    pass


class PesapalClient:
    def __init__(self):
        self.base_url = os.environ.get(
            "PESAPAL_BASE_URL", "https://pay.pesapal.com/v3"
        ).rstrip("/")
        self.consumer_key = os.environ.get("PESAPAL_CONSUMER_KEY")
        self.consumer_secret = os.environ.get("PESAPAL_CONSUMER_SECRET")
        self.ipn_id = os.environ.get("PESAPAL_IPN_ID")
        self.currency = os.environ.get("PESAPAL_CURRENCY", "KES")

    def _request(self, method, path, payload=None, token=None):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, ValueError) as exc:
            raise PesapalError("Pesapal request failed") from exc

    def _require_credentials(self):
        if not self.consumer_key or not self.consumer_secret:
            raise PesapalError("Pesapal credentials are not configured")

    def access_token(self):
        self._require_credentials()
        response = self._request(
            "POST",
            "/api/Auth/RequestToken",
            {"consumer_key": self.consumer_key, "consumer_secret": self.consumer_secret},
        )
        token = response.get("token")
        if not token:
            raise PesapalError("Pesapal did not return an access token")
        return token

    def submit_order(self, order, callback_url, billing_address):
        if not self.ipn_id:
            raise PesapalError("PESAPAL_IPN_ID is not configured")
        token = self.access_token()
        payload = {
            "id": order.merchant_reference,
            "currency": self.currency,
            "amount": float(order.total),
            "description": f"PageTurn order {order.id}",
            "callback_url": callback_url,
            "notification_id": self.ipn_id,
            "billing_address": billing_address,
        }
        response = self._request("POST", "/api/Transactions/SubmitOrderRequest", payload, token)
        if not response.get("order_tracking_id") or not response.get("redirect_url"):
            raise PesapalError("Pesapal returned an invalid payment response")
        return response

    def transaction_status(self, tracking_id):
        token = self.access_token()
        return self._request(
            "GET",
            f"/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}",
            token=token,
        )
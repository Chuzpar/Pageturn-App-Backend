# Pesapal setup

Set these environment variables before starting the API:

```text
PESAPAL_CONSUMER_KEY=your-consumer-key
PESAPAL_CONSUMER_SECRET=your-consumer-secret
PESAPAL_IPN_ID=the-registered-ipn-id
PESAPAL_CALLBACK_URL=https://your-api.example.com/api/orders/pesapal/callback
PESAPAL_CURRENCY=KES
```

Use `https://cybqa.pesapal.com/pesapalv3` for sandbox requests and set
`PESAPAL_BASE_URL` accordingly. Register the IPN URL
`https://your-api.example.com/api/orders/pesapal/ipn` with Pesapal and use its
returned ID as `PESAPAL_IPN_ID`.

Checkout is `POST /api/orders/checkout` with a JWT and JSON containing
`shipping_address` and, optionally, `billing_address`. The response contains
`redirect_url`; redirect the customer there to complete payment. The API marks
the order paid only after it verifies the transaction status with Pesapal.

The order model gained payment columns. For an existing database, create and
apply a migration after pulling this change:

```bash
flask db migrate -m "add Pesapal payment fields"
flask db upgrade
```
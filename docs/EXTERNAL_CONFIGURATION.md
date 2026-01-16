## Feature-by-feature external configuration

### AI / LLM (rule extraction, AI decisions, embeddings)
- **How to get credentials**
  - Create an OpenAI account and generate an API key in the OpenAI dashboard.
  - Docs: [OpenAI API keys](https://platform.openai.com/docs/)
- **Env**
  - `OPENAI_API_KEY` (required to actually call OpenAI)
  - `AI_CALLS_LLM_MODEL` (default: `gpt-5.2`)
- **Code paths**
  - LLM calls are wrapped via `data_ingestion.helpers.llm_client` and `external_services.request.llm_client`.

### Voice (AI Calls: speech-to-text + text-to-speech)
- **How to get credentials (Google recommended)**
  - Create/select a Google Cloud project in [Google Cloud Console](https://console.cloud.google.com/).
  - Enable APIs:
    - Speech-to-Text
    - Text-to-Speech
  - Create a **Service Account** and download a **JSON key** (preferred).
  - Docs: [Speech-to-Text](https://cloud.google.com/speech-to-text/docs) and [Text-to-Speech](https://cloud.google.com/text-to-speech/docs)
- **Env**
  - `SPEECH_TO_TEXT_PROVIDER` (`google` or `aws`)
  - `TEXT_TO_SPEECH_PROVIDER` (`google` or `aws`)
  - For **Google**:
    - `GOOGLE_APPLICATION_CREDENTIALS` (path to service-account json inside the container) **or**
    - `GOOGLE_SPEECH_API_KEY` / `GOOGLE_TTS_API_KEY` (fallback validation; client still uses Google libs)
  - For **AWS Polly**:
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- **Important**
  - AWS STT path currently raises a “requires S3 upload / streaming” error (see `external_services/request/speech_client.py`), so **Google is the only fully working STT path right now**.

### Email
- **Local/dev**: configure SMTP to `mailhog` (see minimal `.env` above).
- **Production**:
  - **How to get credentials**: create a SendGrid API key in the SendGrid dashboard.
    - Docs: [SendGrid API keys](https://docs.sendgrid.com/ui/account-and-settings/api-keys)
  - Code uses SendGrid SDK, with **API key taken from `EMAIL_HOST_PASSWORD`** (see `src/emails/send.py`).
  - Ensure `DEFAULT_FROM_EMAIL`, `EMAIL_HOST_PASSWORD` (SendGrid API key), and templates are correct.

### Payments (Stripe / PayPal / Adyen)
- **How to get credentials**
  - Stripe: create API keys + webhook signing secret in [Stripe Dashboard](https://dashboard.stripe.com/) → Developers.
    - Docs: [Stripe API keys](https://docs.stripe.com/keys) and [Stripe webhooks](https://docs.stripe.com/webhooks)
  - PayPal: create an app in [PayPal Developer](https://developer.paypal.com/) and configure webhooks.
    - Docs: [PayPal REST apps](https://developer.paypal.com/api/rest/) and [PayPal webhooks](https://developer.paypal.com/api/rest/webhooks/)
  - Adyen: get API key + HMAC key from the Adyen customer area / developer section.
    - Docs: [Adyen API credentials](https://docs.adyen.com/development-resources/api-credentials/) and [Adyen webhooks](https://docs.adyen.com/development-resources/webhooks/)
- **Env**
  - Stripe: `STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY`, `STRIPE_WEBHOOK_SECRET`
  - PayPal: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`, `PAYPAL_MODE`
  - Adyen: `ADYEN_API_KEY`, `ADYEN_MERCHANT_ACCOUNT`, `ADYEN_HMAC_KEY`, `ADYEN_ENVIRONMENT`
- **Webhooks**
  - Webhook routes live under `/api/v1/payments/webhooks/...`
  - In non-debug, webhook signature headers are required (see `payments/views/webhooks/base.py` + gateway implementations).

### Document upload/storage
- **Local filesystem**
  - Default is `BASE_DIR/media` if `MEDIA_ROOT` is unset.
  - `MEDIA_URL` defaults to `/media/`
- **S3 / Spaces**
  - **How to get credentials (AWS S3)**:
    - Create an AWS account, then create an IAM user/role with programmatic access to S3.
    - Create an S3 bucket.
    - Docs: [AWS IAM access keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) and [Creating a bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)
  - **How to get credentials (DigitalOcean Spaces)**:
    - Create a Space and generate Spaces access keys in DigitalOcean.
    - Docs: [DigitalOcean Spaces](https://docs.digitalocean.com/products/spaces/)
  - Set `USE_S3_STORAGE=True`
  - Provide `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`
  - Optionally set `AWS_S3_ENDPOINT_URL` for DigitalOcean Spaces / non-AWS S3 endpoints

### Virus scanning
- **Disabled by default**: `VIRUS_SCAN_BACKEND=none`
- **ClamAV**
  - **How to get it**: install/run a ClamAV daemon (no API key; this is an infrastructure dependency).
  - Docs: [ClamAV documentation](https://docs.clamav.net/)
  - `VIRUS_SCAN_BACKEND=clamav`
  - Run a ClamAV daemon and ensure `CLAMAV_SOCKET` matches where the API container can reach it.
- **AWS Macie**
  - **How to get it**: enable Amazon Macie in your AWS account/region and provide a temporary S3 bucket for scanning uploads.
  - Docs: [Amazon Macie](https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html)
  - `VIRUS_SCAN_BACKEND=aws_macie`
  - Requires AWS creds + `AWS_MACIE_TEMP_BUCKET` (temporary upload bucket)

### UK ingestion
- **Env**
  - `UK_GOV_API_BASE_URL` (gov.uk content API base; typically public/no key required)
- **Scheduling**
  - Periodic tasks are configured in `src/main_system/utils/celery_beat_schedule.py` and stored in Redis via Redbeat.

### Observability
- **Sentry**
  - **How to get it**: create a Sentry project and copy the DSN.
  - Docs: [Sentry DSN](https://docs.sentry.io/product/sentry-basics/dsn-explainer/)
  - `SENTRY_DSN` is required when `APP_ENV` is `production` or `staging` (settings enforces it).
- **Structured logging**
  - `SERVICE_NAME`, `VERSION`, `RELEASE` annotate logs.
- **Prometheus**
  - There is a prometheus export route configured in `src/main_system/urls.py`.

---

## Common “gotchas” when running locally

### Redis auth mismatch (most common)
Redis is started with `--requirepass ${REDIS_PASSWORD}` in docker-compose, but Django cache defaults to `redis://redis:6379/0`.

Fix: ensure **both** `REDIS_URL` and `CELERY_BROKER_URL` include the password:
- `redis://:${REDIS_PASSWORD}@redis:6379/0`

### Secure cookies vs HTTP (local)
`SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are set to `True` in settings.
- If your frontend is on plain `http://localhost`, browsers will not send secure cookies.
- You may need to run through HTTPS (e.g., a TLS-terminating proxy) for fully cookie-based auth flows.

---

## Production notes (docker-compose.yml)

`docker-compose.yml` is wired for Traefik:
- It attaches to an **external** network named `web`
- It sets labels using `APP_DOMAIN` and `APP_WWW_DOMAIN`

To run production compose end-to-end you need:
- Traefik (or compatible reverse proxy) already running and attached to the `web` docker network
- Valid TLS resolver configuration (Traefik config is not in this repo)


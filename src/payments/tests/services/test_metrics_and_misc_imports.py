import importlib


def test_metrics_functions_are_safe_to_call():
    from payments.helpers import metrics

    # Should be no-ops if prometheus isn't installed/metrics not registered.
    metrics.track_payment_creation("USD", "stripe", 10.0)
    metrics.track_payment_status_transition("pending", "processing")
    metrics.track_payment_processing("stripe", "completed", 0.5)
    metrics.track_payment_provider_call("stripe", "verify", "success", 0.1)
    metrics.track_payment_failure("declined", "stripe")
    metrics.track_payment_refund("success", "stripe", 10.0, "USD")
    metrics.track_payment_revenue("USD", 10.0)
    metrics.update_payments_by_status("pending", 1)


def test_misc_modules_import_cleanly():
    # These modules are mostly configuration/registration; smoke import ensures no import-time errors.
    importlib.import_module("payments.constants")
    importlib.import_module("payments.apps")
    importlib.import_module("payments.admin")
    importlib.import_module("payments.urls")
    importlib.import_module("payments.views")


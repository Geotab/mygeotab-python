import warnings

from ..py3.api_async import API
from ..api import MyGeotabException, AuthenticationException, Credentials

warnings.warn(
    "Please use `from mygeotab import X`. Imports using `from mygeotab.async import X` have been deprecated.",
    DeprecationWarning,
)

__all__ = ["API", "Credentials", "MyGeotabException", "AuthenticationException"]

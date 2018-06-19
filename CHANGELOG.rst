.. :changelog:

Changes
-------

0.8.0 (2018-06-18)
++++++++++++++++++

**Improvements**

- Python 3.7 support.
- Raises an exception when request was not successful.
- Documentation improvements.

**Bug Fixes**

- Since all MyGeotab servers enforce the use of TLS1.2, Python 2.7.9 or greater is required.
- Fix issue where the password was not provided when retrying authentication. Should better handle `#92 <https://github.com/Geotab/mygeotab-python/issues/92>`__.


0.6.2 (2017-07-04)
++++++++++++++++++

**Bug Fixes**

- Revert the change to stop compilation in setup.cfg.


0.6.1 (2017-07-03)
++++++++++++++++++

**Bug Fixes**

- Don't compile to prevent issues when installing via setup.py on Python 2.7.


0.6.0 (2017-06-29)
++++++++++++++++++

**Improvements**

- Configurable timeouts when making calls.
- Removed `verify` parameter from API objects as SSL is required when calling a MyGeotab server.
- Removed `run` command from the CLI.
- Removed deprecated `API.search` and `API.search_async` methods.
- Refactored setup.py for async API. The async/awaitable methods are now automatically a part of the `API` object if using Python 3.5 or higher
- Code linting and cleanup


0.5.4 (2017-06-05)
++++++++++++++++++

**Bug Fixes**

- Ensure all dates are timezone aware and are always UTC-localized.


0.5.3 (2017-05-30)
++++++++++++++++++

**Bug Fixes**

- Fixed intermittent timeout errors due to `upstream changes <https://github.com/requests/requests/blob/master/HISTORY.rst#2161-2017-05-27>`_ in the 'requests' module


0.5.2 (2017-02-02)
++++++++++++++++++

**Bug Fixes**

- Switched back to using abstract dependencies in setup.py (recommended by `this guide <https://caremad.io/posts/2013/07/setup-vs-requirement/>`_)

0.5.1 (2017-01-04)
++++++++++++++++++

**Bug Fixes**

- Fix for search parameter not being properly handled in 'get()' call


0.5 (2017-01-02)
++++++++++++++++

**Enhancements**

- Deprecated the 'search()' and 'search_async()' functions. Replaced by folding the previous functionality into 'run()'.
- Removed 'tzlocal' dependency. Always deal with dates in UTC by default.
- Prefer functions instead of making static methods in classes.
- Added helper to run async calls and collect their results
- Add ability to quickly run simple python scripts from the 'myg' console with no need for any authentication handling. Similar to 'console', but for running scripts rather than creating an interactive console.


0.4.4 (2016-07-10)
++++++++++++++++++

**Enhancements**

- Added the ability to make unauthenticated calls (like "GetVersion") with the static "API.server_call" method
- Added asyncio-based API query methods (Python 3.5+ only) into the "ext" package
- Moved the datafeed to the "ext" package, as well

**Bug Fixes**

- MyGeotab never returns 3 digits of milliseconds, so follow that format as well to allow the use of "dates.format_iso_datetime" to create MyGeotab URLs

0.4.2 (2016-03-17)
++++++++++++++++++

**Bug Fixes**

- Use a custom User-Agent when making requests

0.4 (2016-02-25)
++++++++++++++++

**Enhancements**

- Extension for facilitating use of the MyGeotab `Data Feed <https://my.geotab.com/sdk/#/dataFeed>`_
- Allow Pythonic underscore-separated parameters mapped to camelcase ones
- Force the use of TLS 1.2 for `upcoming strict security requirements <https://www.geotab.com/blog/securing-mygeotab-with-tls/>`_ in MyGeotab
  (Note that TLS 1.2 is only supported in Python 2.7.9+ and 3.4+)

**Bug Fixes**

- Fixed issue with CLI console startup
- Use the system's default user location for config files

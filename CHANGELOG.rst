.. :changelog:

Changes
-------

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

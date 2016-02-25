.. :changelog:

Changes
-------

0.4 (2016-02-25)
++++++++++++++++

**Enhancements**

- Extension for facilitating use of the MyGeotab `Data Feed <https://my.geotab.com/sdk/#/dataFeed>`_
- Allow Pythonic underscore-separated parameters mapped to camelcase ones
- Force the use of TLS 1.2 for `upcoming strict security requirements <https://www.geotab.com/blog/securing-mygeotab-with-tls/>`_ in MyGeotab.
  (Note that TLS 1.2 is only supported in Python 2.7.9+ and 3.4+)

**Bug Fixes**

- Fixed issue with CLI console startup
- Use the system's default user location for config files

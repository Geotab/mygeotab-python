from importlib.metadata import requires, version

from packaging.requirements import Requirement
from packaging.version import Version

from aiohttp.compression_utils import brotli as aiohttp_brotli
from urllib3.response import brotli as urllib3_brotli


def test_http_clients_select_patched_brotli_decoders():
    for decoder in (aiohttp_brotli, urllib3_brotli):
        assert decoder is not None

        if decoder.__name__ == "brotlicffi":
            package, patched_version = "brotlicffi", "1.2.1.0"
        else:
            assert decoder.__name__ == "brotli"
            package, patched_version = "Brotli", "1.2.1"

        assert Version(version(package)) >= Version(patched_version)


def test_distribution_requires_patched_brotlicffi_without_marker():
    distribution_requirements = [Requirement(item) for item in requires("mygeotab") or ()]
    broker_requirement = next(
        item for item in distribution_requirements if item.name.lower() == "brotlicffi"
    )
    lower_bounds = [
        Version(specifier.version)
        for specifier in broker_requirement.specifier
        if specifier.operator in {">=", ">", "~="}
    ]

    assert lower_bounds and max(lower_bounds) >= Version("1.2.1.0")
    assert not broker_requirement.specifier.contains("1.2.0.0")
    assert broker_requirement.marker is None

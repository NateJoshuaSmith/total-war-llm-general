import os

import pytest


def test_imports_every_layer_package() -> None:
    import tw_general.clients
    import tw_general.controllers
    import tw_general.models
    import tw_general.repositories
    import tw_general.services

    assert (
        tw_general.clients
        and tw_general.controllers
        and tw_general.models
        and tw_general.repositories
        and tw_general.services
    )
    assert True


@pytest.mark.live
def test_live_marker_makes_no_api_call() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY is not set")

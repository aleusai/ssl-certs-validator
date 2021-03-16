import tempfile

import pytest

from flaskr import flaskr


@pytest.fixture
def client():
    flaskr.app.config['TESTING'] = True

    with flaskr.app.test_client() as client:
        with flaskr.app.app_context():
            yield client

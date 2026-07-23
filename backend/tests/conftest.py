"""Test setup for the backend unit tests.

`agent.tools` constructs an Exa client at import time, which raises without
EXA_API_KEY. The unit tests here exercise pure routing/message helpers that
never touch Exa, so provide a dummy key to make import-time collection succeed
without depending on real credentials.
"""

import os

os.environ.setdefault("EXA_API_KEY", "test-dummy-key")

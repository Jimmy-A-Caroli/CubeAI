"""Launch the accepted local FastAPI application with caller-local state."""

import os
from pathlib import Path

import uvicorn

from cubeai.api.app import create_default_application


def main() -> None:
    state_directory = Path(os.environ.get("CUBEAI_STATE_DIRECTORY", "cubeai-local"))
    uvicorn.run(
        create_default_application(state_directory), host="127.0.0.1", port=8000
    )


if __name__ == "__main__":
    main()

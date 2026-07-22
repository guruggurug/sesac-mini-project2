from app.core.config import RUNTIME_STATE_DB_PATH
from app.repositories.runtime_state_repository import RuntimeStateRepository


runtime_state_repository = RuntimeStateRepository(RUNTIME_STATE_DB_PATH)


def recover_runtime_state_after_restart() -> None:
    runtime_state_repository.recover_interrupted_syncs()

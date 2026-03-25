from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    settings = get_settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


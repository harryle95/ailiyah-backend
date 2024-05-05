from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin

from src.helpers import create_db_config, provide_storage, provide_transaction
from src.router import ImageController, ProjectController, PromptController, RequestController

db_config = create_db_config("db.sqlite")

cors_config = CORSConfig(allow_origins=["*"])

app = Litestar(
    [ProjectController, RequestController, PromptController, ImageController],
    dependencies={"transaction": provide_transaction, "storage": provide_storage},
    plugins=[SQLAlchemyPlugin(db_config)],
    cors_config=cors_config,
)

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin

from src.helpers import create_db_config, provide_transaction
from src.router.project import ProjectController
from src.router.request import RequestController

db_config = create_db_config("db.sqlite")

cors_config = CORSConfig(allow_origins=["*"])

app = Litestar(
    [ProjectController, RequestController],
    dependencies={"transaction": provide_transaction},
    plugins=[SQLAlchemyPlugin(db_config)],
    cors_config=cors_config,
)

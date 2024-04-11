from typing import Any, Generic, TypeVar

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.exceptions import InvalidAnnotationException
from litestar.typing import FieldDefinition
from sqlalchemy.orm import DeclarativeBase

__all__ = ("DTOGenerator",)

T = TypeVar("T", bound=DeclarativeBase)


class DTOGenerator(Generic[T]):
    model_type: type[T]
    base_read_kwargs: dict[str, Any] = {"max_nested_depth": 0}
    base_write_kwargs: dict[str, Any] = {"max_nested_depth": 0, "partial": True}

    def __class_getitem__(cls, model_type: type[T]) -> type:
        field_definition = FieldDefinition.from_annotation(model_type)

        if (field_definition.is_optional and len(field_definition.args) > 2) or (
            field_definition.is_union and not field_definition.is_optional
        ):
            raise InvalidAnnotationException("Unions are currently not supported as type argument to DTOs.")

        if field_definition.is_forward_ref:
            raise InvalidAnnotationException("Forward references are not supported as type argument to DTO")

        cls_dict: dict[str, Any] = {}
        if not field_definition.is_type_var:
            cls_dict.update(model_type=field_definition.annotation)

        return type(
            f"DTOGen[{model_type.__name__}]",
            (cls,),
            cls_dict,
        )

    def __init__(self, read_kwargs: dict[str, Any] | None = None, write_kwargs: dict[str, Any] | None = None) -> None:
        if write_kwargs is None:
            write_kwargs = {}
        if read_kwargs is None:
            read_kwargs = {}
        self.read_kwargs = self._update_kwargs(read_kwargs, self.base_read_kwargs)
        self.write_kwargs = self._update_kwargs(write_kwargs, self.base_write_kwargs)

    def _update_kwargs(self, base_kwargs: dict[str, Any], update_kwargs: dict[str, Any]) -> dict[str, Any]:
        for field, value in update_kwargs.items():
            if field not in base_kwargs:
                base_kwargs[field] = value
        return base_kwargs

    @property
    def read_dto(self) -> type:
        class ReadDTO(SQLAlchemyDTO[self.model_type]):  # type: ignore[name-defined]
            config = SQLAlchemyDTOConfig(**self.read_kwargs)

        return ReadDTO

    @property
    def write_dto(self) -> type:
        class WriteDTO(SQLAlchemyDTO[self.model_type]):  # type: ignore[name-defined]
            config = SQLAlchemyDTOConfig(**self.write_kwargs)

        return WriteDTO

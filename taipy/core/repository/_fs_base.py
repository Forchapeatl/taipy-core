import json
import pathlib
import shutil
from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, Iterator, List, Optional, Type, TypeVar, Union

from taipy.core.exceptions.repository import ModelNotFound

ModelType = TypeVar("ModelType")
Entity = TypeVar("Entity")
Json = Union[dict, list, str, int, float, bool, None]


class _CustomEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Json:
        result: Json
        if isinstance(o, Enum):
            result = o.value
        elif isinstance(o, datetime):
            result = {"__type__": "Datetime", "__value__": o.isoformat()}
        else:
            result = json.JSONEncoder.default(self, o)
        return result


class _CustomDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, source):
        if source.get("__type__") == "Datetime":
            return datetime.fromisoformat(source.get("__value__"))
        else:
            return source


class _FileSystemRepository(Generic[ModelType, Entity]):
    """
    Holds common methods to be used and extended when the need for saving
    dataclasses as JSON files in local storage emerges.

    Some lines have type: ignore because MyPy won't recognize some generic attributes. This
    should be revised in the future.

    Attributes:
        model (ModelType): Generic dataclass.
        dir_name (str): Folder that will hold the files for this dataclass model.
    """

    @abstractmethod
    def _to_model(self, obj):
        """
        Converts the object to be saved to its model.
        """
        ...

    @property
    @abstractmethod
    def _storage_folder(self) -> pathlib.Path:
        """
        Base folder used by repository to store data
        """
        ...

    @abstractmethod
    def _from_model(self, model):
        """
        Converts a model to its functional object.
        """
        ...

    def __init__(self, model: Type[ModelType], dir_name: str):
        self.model = model
        self.dir_name = dir_name

    @property
    def _directory(self) -> pathlib.Path:
        dir_path = self._storage_folder / self.dir_name

        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

        return dir_path

    def load(self, model_id: str) -> Entity:
        return self.__to_entity(self.__get_model(model_id))

    def _load_all(self) -> List[Entity]:
        return [self.__to_entity(f) for f in self._directory.glob("*.json")]

    def _save(self, model):
        model = self._to_model(model)
        self.__get_model(model.id, False).write_text(
            json.dumps(model.to_dict(), ensure_ascii=False, indent=4, cls=_CustomEncoder)
        )

    def _delete_all(self):
        shutil.rmtree(self._directory)

    def _delete(self, model_id: str):
        self.__get_model(model_id).unlink()

    def _search(self, attribute: str, value: str) -> Optional[Entity]:
        return next(self.__search(attribute, value), None)

    def _search_all(self, attribute: str, value: str) -> List[Entity]:
        return list(self.__search(attribute, value))

    def _build_model(self, model_data: Dict) -> ModelType:
        return self.model.from_dict(model_data)  # type: ignore

    def __search(self, attribute: str, value: str) -> Iterator[Entity]:
        return filter(lambda e: hasattr(e, attribute) and getattr(e, attribute) == value, self._load_all())

    def __get_model(self, model_id, raise_if_not_exist=True) -> pathlib.Path:
        filepath = self._directory / f"{model_id}.json"

        if not filepath.exists() and raise_if_not_exist:
            raise ModelNotFound(str(self._directory), model_id)

        return filepath

    def __to_entity(self, filepath):
        with open(filepath, "r") as f:
            data = json.load(f, cls=_CustomDecoder)
        model = self.model.from_dict(data)  # type: ignore
        return self._from_model(model)
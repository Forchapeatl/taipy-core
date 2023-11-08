# Copyright 2023 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

from dataclasses import dataclass
from typing import Any, Dict, List

from sqlalchemy import JSON, Column, Enum, String, Table

from .._repository._base_taipy_model import _BaseModel
from .._repository.db._sql_base_model import mapper_registry
from .submission_status import SubmissionStatus


@mapper_registry.mapped
@dataclass
class _SubmissionModel(_BaseModel):
    __table__ = Table(
        "submission",
        mapper_registry.metadata,
        Column("id", String, primary_key=True),
        Column("entity_id", String),
        Column("job_ids", JSON),
        Column("creation_date", String),
        Column("submission_status", Enum(SubmissionStatus)),
    )
    id: str
    entity_id: str
    job_ids: List[str]
    creation_date: str
    submission_status: SubmissionStatus

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return _SubmissionModel(
            id=data["id"],
            entity_id=data["entity_id"],
            job_ids=data["job_ids"],
            creation_date=data["creation_date"],
            submission_status=SubmissionStatus._from_repr(data["submission_status"]),
        )

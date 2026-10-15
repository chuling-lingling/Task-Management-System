"""ORM 模型集中导出。

导入本包即保证全部模型注册进 Base.metadata，建表脚本依赖这一点。
新增模型时请把类加到这里。
"""

from app.models.task import Task
from app.models.user import User

__all__ = ["Task", "User"]

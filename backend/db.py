# -*- coding: utf-8 -*-
"""数据库访问辅助模块

提供 get_db() 便捷函数，供各业务模块使用。
实际连接在 memory 模块中管理。
"""

from memory import db


def get_db():
    """获取 MongoDB 数据库实例（motor AsyncIOMotorDatabase）"""
    if db is None:
        raise RuntimeError("MongoDB 未初始化，请确保应用已启动")
    return db

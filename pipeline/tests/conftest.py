"""测试夹具：确保所有测试使用独立临时数据库，不受本地 geo_data.db 影响。"""

import os
import tempfile


_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

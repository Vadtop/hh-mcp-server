"""
B.13: Тест дедупликации откликов.
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from src.services.applied_db import (
    is_applied,
    mark_applied,
    get_applied_count_today,
    check_daily_limit,
    init_db,
)


def test_dedup(tmp_path):
    db_path = tmp_path / ".applied.db"
    with patch("src.services.applied_db.DB_PATH", db_path):
        init_db()
        assert not is_applied("123456")
        mark_applied("123456", title="Dev", company="Co", letter=True)
        assert is_applied("123456")
        assert get_applied_count_today() == 1


def test_daily_limit(tmp_path):
    db_path = tmp_path / ".applied.db"
    with patch("src.services.applied_db.DB_PATH", db_path):
        with patch("src.services.applied_db.MAX_APPLIES_PER_DAY", 2):
            init_db()
            assert check_daily_limit()
            mark_applied("111111")
            mark_applied("222222")
            assert not check_daily_limit()

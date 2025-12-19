import pytest
import datetime
import pytz
from freezegun import freeze_time
from bot.utils.parser import parse_task_text  


@pytest.fixture
def moscow_tz():
    return "Europe/Moscow"

@pytest.fixture
def utc_tz():
    return "UTC"

class TestTaskParser:
    @freeze_time("2025-01-01 12:00:00")
    def test_parse_simple_text_no_date(self):
        """Test without dates"""
        text = "Buy milk"
        title, dt = parse_task_text(text)
        
        assert title == "Buy milk"
        assert dt is None

    @freeze_time("2025-01-01 12:00:00")
    def test_parse_relative_date_english(self):
        """Test english date (tomorrow)"""
        text = "Buy milk tomorrow"
        title, dt = parse_task_text(text)
        
        assert title == "Buy milk"
        assert dt is not None
        expected = datetime.datetime(2025, 1, 2, 12, 0, 0, tzinfo=pytz.utc)
        assert dt == expected

    @freeze_time("2025-01-01 12:00:00")
    def test_parse_relative_date_russian(self):
        """Test russian date (after 2 hours)"""
        text = "Позвонить маме через 2 часа" 
        title, dt = parse_task_text(text)
        
        assert title == "Позвонить маме"
        assert dt == datetime.datetime(2025, 1, 1, 14, 0, 0, tzinfo=pytz.utc)

    @freeze_time("2025-01-01 12:00:00")
    def test_timezone_conversion(self, moscow_tz):
        """
        A user in Moscow (UTC+3) writes 'at 18:00'.
        The bot should save this as 15:00 UTC.
        """
        text = "Meeting in 18:00"
        
        title, dt = parse_task_text(text, user_timezone=moscow_tz)
        
        assert title == "Meeting"
        # 18:00 MSK (UTC+3) -> 15:00 UTC
        expected_utc = datetime.datetime(2025, 1, 1, 15, 0, 0, tzinfo=pytz.utc)
        assert dt == expected_utc

    @freeze_time("2025-01-01 12:00:00")
    def test_absolute_date_explicit(self):
        """Explicit Date Test"""
        text = "Report December 25"
        title, dt = parse_task_text(text)
        
        assert title == "Report"
        assert dt.day == 25
        assert dt.month == 12
        assert dt.year == 2025

    def test_strip_prepositions(self):
        """Checking for clearing prepositions at the end (in, on, at, в, на)"""
        
        cases = [
            ("Meeting at 5pm", "Meeting"),
            ("Сходить в магазин в субботу", "Сходить в магазин"),
            ("Задача на завтра", "Задача"), 
        ]
        
        for text, expected_title in cases:
            title, _ = parse_task_text(text)
            assert title == expected_title

    def test_empty_result_fallback(self):
        """If there is nothing left after removing the date, the original or something reasonable should return"""
        text = "tomorrow" 
        title, dt = parse_task_text(text)
        
        assert title == "tomorrow"
        assert dt is not None
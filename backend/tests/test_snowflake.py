import time

import pytest

from backend.apps.core.snowflake import SnowflakeGenerator


class TestSnowflakeGenerator:
    @pytest.fixture
    def generator(self):
        return SnowflakeGenerator(machine_id=1)

    def test_ids_are_unique(self, generator):
        ids = set()
        count = 1000

        for _ in range(count):
            ids.add(generator.next_id())

        assert len(ids) == count

    def test_ids_are_sorted_by_time(self, generator):
        id1 = generator.next_id()
        id2 = generator.next_id()

        assert id2 > id1

    def test_id_structure(self, generator):
        uid = generator.next_id()

        extracted_machine_id = (uid >> 12) & 0x3FF  # 0x3FF = 1023

        assert extracted_machine_id == 1

    def test_clock_backwards_protection(self, generator):
        generator.last_timestamp = int(time.time() * 1000) + 5000

        with pytest.raises(Exception) as excinfo:
            generator.next_id()

        assert "Clock moved backwards" in str(excinfo.value)

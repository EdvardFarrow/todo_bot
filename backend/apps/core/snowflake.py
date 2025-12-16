import time
from threading import Lock
from typing import Optional

class SnowflakeGenerator:
    """
    Thread-safe Snowflake ID generator.
    Format (64 bits): [1 unused] [41 timestamp] [10 machine_id] [12 sequence]
    """
    EPOCH = 1735689600000  # 2025-01-01 00:00:00 UTC

    def __init__(self, machine_id: int):
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = Lock()

        # bit config
        self.timestamp_bits = 41
        self.machine_id_bits = 10
        self.sequence_bits = 12

        self.max_machine_id = -1 ^ (-1 << self.machine_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)

        self.machine_id_shift = self.sequence_bits
        self.timestamp_shift = self.sequence_bits + self.machine_id_bits

        if self.machine_id > self.max_machine_id or self.machine_id < 0:
            raise ValueError(f"Machine ID must be between 0 and {self.max_machine_id}")

    def _current_timestamp(self) -> int:
        return int(time.time() * 1000)

    def next_id(self) -> int:
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards!")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_timestamp()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return (
                ((timestamp - self.EPOCH) << self.timestamp_shift) |
                (self.machine_id << self.machine_id_shift) |
                self.sequence
            )

generator: Optional[SnowflakeGenerator] = None
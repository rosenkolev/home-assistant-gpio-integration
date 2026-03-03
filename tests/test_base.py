from unittest.mock import Mock

from custom_components.gpio_integration._base import AutoReadLoop


def test_auto_read_loop_stops():
    loop = AutoReadLoop()

    loop._read = Mock()

    # 1st wait -> timeout (False) → triggers _read
    # 2nd wait -> timeout (False) → triggers _read
    # 3rd wait -> stop event set (True) → loop exits
    loop._loop_stop_event.wait = Mock(side_effect=[False, False, True])

    loop.start_auto_read_loop(interval_sec=999)

    loop._loop_thread.join()

    assert loop._read.call_count == 2


def test_stop_sets_event():
    loop = AutoReadLoop()

    loop._loop_stop_event.set = Mock()
    loop._loop_thread = Mock()
    loop._loop_thread.is_alive.return_value = False

    loop.stop_auto_read_loop()

    loop._loop_stop_event.set.assert_called_once()

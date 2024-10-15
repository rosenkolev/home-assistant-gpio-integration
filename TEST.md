if self._running:
            _LOGGER.warning(f"{self!r}: already running")
            return
        # self._state_index = 0
        # self._last_state = self.pin.value
        # self._last_event = perf_counter_ns()
        self._running = True
        last_event = perf_counter_ns()
        last_state = self.pin.value

        _LOGGER.debug(f"{self!r}: reading")
        self.pin.function = "input"
        # self.pin.when_changed = self._pin_changed

        while self._running:
            while self.pin.value == last_state:
                sleep(0.000_001)  # 1us

            time = perf_counter_ns()
            self._state_changed(BitInfo(last_state, (time - last_event) / 1_000_000.0))
            last_state = not last_state
            last_event = time
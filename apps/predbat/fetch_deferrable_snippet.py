        # Deferrable load model
        self.deferrable_enable = self.get_arg("deferrable_enable")
        self.deferrable_max_energy = self.get_arg("deferrable_max_energy")
        self.deferrable_today = self.get_arg("deferrable_today")
        self.deferrable_max_power = self.get_arg("deferrable_max_power") / MINUTE_WATT
        self.deferrable_min_power = self.get_arg("deferrable_min_power") / MINUTE_WATT
        self.deferrable_rate_threshold = self.get_arg("deferrable_rate_threshold")
        self.deferrable_smart = self.get_arg("deferrable_smart")
        self.deferrable_smart_min_length = self.get_arg("deferrable_smart_min_length")
        self.deferrable_solar_priority = self.get_arg("deferrable_solar_priority")
        self.deferrable_value_scaling = self.get_arg("deferrable_value_scaling")
        self.deferrable_next = self.deferrable_today
        self.deferrable_running = False
        self.deferrable_plan = []

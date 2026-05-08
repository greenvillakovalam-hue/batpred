    def plan_deferrable_load(self):
        """
        Smart deferrable load planning - schedule flexible loads at cheapest times
        """
        plan = []
        deferrable_today = self.deferrable_today
        deferrable_max = self.deferrable_max_energy
        deferrable_power = self.deferrable_max_power * 60
        deferrable_min_length = max(
            int((self.deferrable_smart_min_length + self.plan_interval_minutes - 1) / self.plan_interval_minutes) * self.plan_interval_minutes,
            self.plan_interval_minutes,
        )

        self.log(
            "Create deferrable load plan, max {} kWh, power {} kW, min length {} minutes".format(
                deferrable_max, deferrable_power, deferrable_min_length
            )
        )

        low_rates = []
        start_minute = int(self.minutes_now / self.plan_interval_minutes) * self.plan_interval_minutes

        # Build list of available slots with their rates and PV availability
        for minute in range(start_minute, start_minute + self.forecast_minutes, self.plan_interval_minutes):
            import_rate = 0
            slot_length = 0
            slot_count = 0
            pv_available = 0
            for slot_start in range(minute, minute + deferrable_min_length, self.plan_interval_minutes):
                import_rate += self.rate_import.get(slot_start, self.rate_min)
                pv_available += self.pv_forecast_minute.get(slot_start - self.minutes_now, 0)
                slot_length += self.plan_interval_minutes
                slot_count += 1
            if slot_count:
                avg_import = import_rate / slot_count
                low_rates.append({"start": minute, "end": minute + slot_length, "average": avg_import, "pv": pv_available / slot_count})

        # Sort by price (lowest first) if smart mode
        if self.deferrable_smart:
            price_sorted = self.sort_window_by_price(low_rates, reverse_time=False)
        else:
            price_sorted = [n for n in range(len(low_rates))]

        total_days = int((self.forecast_minutes + self.minutes_now + 24 * 60 - 1) / (24 * 60))
        deferrable_soc = [0 for n in range(total_days)]
        deferrable_soc[0] = deferrable_today

        used_slots = {}

        for window_n in price_sorted:
            window = low_rates[window_n]
            price = window["average"]
            pv_available = window["pv"]

            for day in range(0, total_days):
                day_start_minutes = day * 24 * 60
                day_end_minutes = day_start_minutes + 24 * 60

                slot_start = max(window["start"], self.minutes_now, day_start_minutes)
                slot_end = min(window["end"], day_end_minutes)

                if slot_start < slot_end:
                    rate_okay = True

                    for start in range(slot_start, slot_end, self.plan_interval_minutes):
                        end = min(start + self.plan_interval_minutes, slot_end)

                        # Avoid duplicate slots
                        if start in used_slots:
                            rate_okay = False
                            break

                        # Check rate threshold
                        if price > self.deferrable_rate_threshold:
                            rate_okay = False
                            break

                    if not rate_okay:
                        continue

                    # Calculate charging amount for the full slot
                    length = slot_end - slot_start
                    hours = length / 60
                    kwh = deferrable_power * hours
                    deferrable_left = max(deferrable_max - deferrable_soc[day], 0)

                    # Scale down if exceeds max
                    if kwh > deferrable_left and kwh > 0:
                        percent = deferrable_left / kwh
                        length = min(round(((length * percent) / 5) + 0.5, 0) * 5, slot_end - slot_start)
                        end = slot_start + length
                        hours = length / 60
                        kwh = min(deferrable_power * hours, deferrable_left)

                    if kwh > 0:
                        deferrable_soc[day] = dp3(deferrable_soc[day] + kwh)
                        new_slot = {"start": slot_start, "end": slot_start + length, "kwh": dp3(kwh), "average": window["average"], "cost": dp2(window["average"] * kwh), "pv": pv_available}
                        plan.append(new_slot)
                        for s in range(slot_start, slot_start + length, self.plan_interval_minutes):
                            used_slots[s] = True

        # Return sorted back in time order
        plan = self.sort_window_by_time(plan)
        return plan

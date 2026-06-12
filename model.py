from collections import deque

class Tamagotchi:
    def __init__(
        self,
        energy=70,
        health=85,
        happiness=75,
        stress=20,
        hunger=30,
        age=1,
        level=1,
        sick=False,
        dead=False,
        message="I feel good.",
        mood="Okay",
    ):
        self.energy = energy
        self.health = health
        self.happiness = happiness
        self.stress = stress
        self.hunger = hunger
        self.age = age
        self.level = level
        self.sick = sick
        self.dead = dead
        self.message = message
        self._mood = mood
        self.mood_lock = 0
        self.message_timer = 0
        self.battery_history = deque(maxlen=30)
        self.cpu_history = deque(maxlen=30)
        self.memory_history = deque(maxlen=30)
        self.latency_history = deque(maxlen=30)
        self.health_rate = 0.0
        self.happiness_rate = 0.0
        self.stress_rate = 0.0
        self._last_network_online = None
        self._refresh_state()

    @staticmethod
    def _clamp(value):
        return max(0, min(100, value))

    @property
    def mood(self):
        if self.dead:
            return "RIP"
        if self.sick:
            return "Sick"
        return self._mood

    @property
    def battery_avg(self):
        return sum(self.battery_history) / len(self.battery_history) if self.battery_history else None

    @property
    def cpu_avg(self):
        return sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else None

    @property
    def memory_avg(self):
        return sum(self.memory_history) / len(self.memory_history) if self.memory_history else None

    @property
    def latency_avg(self):
        return sum(self.latency_history) / len(self.latency_history) if self.latency_history else None

    def _refresh_state(self):
        self.energy = self._clamp(self.energy)
        self.health = self._clamp(self.health)
        self.happiness = self._clamp(self.happiness)
        self.stress = self._clamp(self.stress)
        self.hunger = self._clamp(self.hunger)
        self.sick = self.health < 40 or self.stress > 75

        if not self.dead and (self.health <= 0 or self.energy <= 0 or self.happiness <= 0):
            self.dead = True
            self._mood = "RIP"
            self.push_message("Your Tamagotchi has passed...", 5)
        elif self.dead and self.message_timer <= 0:
            self.message = "Your Tamagotchi has passed..."

    def push_message(self, text, duration=4):
        self.message = text
        self.message_timer = duration

    def _record_history(self, battery_pct, cpu_pct, memory_pct, latency):
        if battery_pct is not None:
            self.battery_history.append(battery_pct)
        if cpu_pct is not None:
            self.cpu_history.append(cpu_pct)
        if memory_pct is not None:
            self.memory_history.append(memory_pct)
        if latency is not None:
            self.latency_history.append(latency)

    def _update_mood(self):
        if self.dead:
            return

        if self.health < 35:
            desired = "Sick"
        elif self.energy < 30:
            desired = "Tired"
        elif self.stress > 70:
            desired = "Stressed"
        elif self.happiness > 80 and self.energy > 50:
            desired = "Happy"
        elif self.happiness < 40:
            desired = "Lonely"
        else:
            desired = "Okay"

        if desired == self._mood:
            self.mood_lock = min(5, self.mood_lock + 1)
            return

        if self.mood_lock >= 5:
            self._mood = desired
            self.mood_lock = 0
        else:
            self.mood_lock += 1

    def apply_device(self, device_stats):
        if self.dead:
            return

        battery_pct = device_stats.get("battery_pct")
        cpu_pct = device_stats.get("cpu_pct")
        memory_pct = device_stats.get("memory_pct")
        disk_free_pct = device_stats.get("disk_free_pct")
        temperature = device_stats.get("temperature")
        network_online = device_stats.get("network_online")
        latency = device_stats.get("network_latency")
        is_charging = device_stats.get("is_charging")

        self._record_history(battery_pct, cpu_pct, memory_pct, latency)

        # Direct hardware-to-stat mapping
        if battery_pct is not None:
            self.energy = battery_pct
        
        if disk_free_pct is not None:
            disk_used_pct = 100 - disk_free_pct
            self.health = max(0, 100 - disk_used_pct)
        
        # Rate modifiers for other stats
        self.stress_rate = 0.0
        self.happiness_rate = 0.0

        if is_charging:
            self.stress_rate -= 0.5
            self.happiness_rate += 0.5
            if self.message_timer <= 0:
                self.push_message("Charging: thermal relief engaged.", 3)

        if cpu_pct is not None:
            cpu_load = self.cpu_avg if self.cpu_avg is not None else cpu_pct
            self.stress_rate += max(0.0, (cpu_load - 60) * 0.05)
            if cpu_load > 80:
                if self.message_timer <= 0:
                    self.push_message("CPU load critical: thermal throttling risk.", 4)

        if temperature is not None:
            if temperature > 85:
                self.stress_rate += 1.5
                if self.message_timer <= 0:
                    self.push_message("System overheating! Cooling required.", 4)
            elif temperature > 75:
                self.stress_rate += 0.8
                if self.message_timer <= 0:
                    self.push_message("Temperature elevated. Monitoring thermal state.", 3)

        if disk_free_pct is not None and disk_free_pct < 15:
            if self.message_timer <= 0:
                self.push_message("Storage critical! Purge cached data immediately.", 5)

        if network_online is False:
            self.happiness_rate -= 1.0
            if self.message_timer <= 0:
                self.push_message("Network offline. Attempting to decongest.", 4)
        elif network_online is True and latency is not None:
            if latency > 1.5:
                self.happiness_rate -= 0.7
                if self.message_timer <= 0:
                    self.push_message("Network congestion detected. Decongest protocol recommended.", 4)
            else:
                self.happiness_rate += 0.3

        self._refresh_state()

    def tick(self, dt=1):
        if self.dead:
            return

        self.hunger += 0.4 * dt

        # Energy is directly mapped from battery in apply_device(), don't drain it here
        # Just apply health, happiness, and stress rates

        self.health += self.health_rate * dt
        self.happiness += self.happiness_rate * dt
        self.stress += self.stress_rate * dt

        if self.hunger > 80:
            self.health -= 0.8 * dt
            if self.message_timer <= 0:
                self.push_message("Storage fragmented. Purge recommended.", 4)

        if self.stress > 65 and self.health > 20:
            self.health -= 0.15 * dt

        if self.happiness < 30 and self.message_timer <= 0:
            self.push_message("Network connectivity lost. Check signal.", 4)

        self.age += dt
        self.level = 1 + int(self.age // 30)

        if self.message_timer > 0:
            self.message_timer = max(0, self.message_timer - dt)
            if self.message_timer == 0:
                self.message = self.status_text()

        self._refresh_state()
        self._update_mood()

    def purge(self):
        """Execute cache purge protocol."""
        if self.dead:
            return
        import gc
        gc.collect()
        self.health += 15
        self.stress -= 10
        self.push_message("Purge complete. Cache cleared. System optimized.", 4)
        self._refresh_state()

    def cool_down(self):
        """Execute thermal management protocol."""
        if self.dead:
            return
        self.stress -= 15
        self.health += 8
        self.push_message("Thermal management active. Stress reduced.", 4)
        self._refresh_state()

    def decongest(self):
        """Execute network optimization protocol."""
        if self.dead:
            return
        self.happiness += 12
        self.stress -= 5
        self.push_message("Network stack refreshed. Latency optimized.", 4)
        self._refresh_state()

    def revive(self):
        if not self.dead:
            return

        self.dead = False
        self.health = 25
        self.energy = 20
        self.happiness = 25
        self.stress = 20
        self.hunger = 50
        self.message = "I am back with a new start."
        self._refresh_state()

    def status_text(self):
        if self.dead:
            return "The Tamagotchi is gone. Tap Purge to revive."
        if self.sick:
            return "Not feeling well. Take care of the phone."
        if self.energy < 30:
            return "Low energy — keep it charged and calm."
        if self.stress > 60:
            return "Too much load. Relax the phone and lower stress."
        if self.health < 50:
            return "The device needs attention: lower memory and CPU usage."
        if self.happiness < 40:
            return "Feeling a little lonely or bored. Check the network."
        return "Feeling stable and responsive."

    def to_dict(self):
        return {
            "energy": self.energy,
            "health": self.health,
            "happiness": self.happiness,
            "stress": self.stress,
            "hunger": self.hunger,
            "age": self.age,
            "level": self.level,
            "sick": self.sick,
            "dead": self.dead,
            "message": self.message,
            "mood": self._mood,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            energy=data.get("energy", 70),
            health=data.get("health", 85),
            happiness=data.get("happiness", 75),
            stress=data.get("stress", 20),
            hunger=data.get("hunger", 30),
            age=data.get("age", 1),
            level=data.get("level", 1),
            sick=data.get("sick", False),
            dead=data.get("dead", False),
            message=data.get("message", "I feel good."),
            mood=data.get("mood", "Okay"),
        )

    @classmethod
    def load(cls, store):
        if store.exists("pet"):
            return cls.from_dict(store.get("pet"))
        return cls()

    def save(self, store):
        store.put("pet", **self.to_dict())

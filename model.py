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
        if self.health < 40:
            return "Weak"
        if self.stress > 60:
            return "Stressed"
        if self.energy < 30:
            return "Tired"
        if self.happiness > 70 and self.energy > 50:
            return "Happy"
        return "Okay"

    def _refresh_state(self):
        self.energy = self._clamp(self.energy)
        self.health = self._clamp(self.health)
        self.happiness = self._clamp(self.happiness)
        self.stress = self._clamp(self.stress)
        self.hunger = self._clamp(self.hunger)
        self.sick = self.health < 40 or self.stress > 70

        if not self.dead and (self.health <= 0 or self.energy <= 0 or self.happiness <= 0):
            self.dead = True
            self.message = "Your Tamagotchi has passed..."

    def apply_device(self, device_stats):
        if self.dead:
            return

        battery_pct = device_stats.get("battery_pct")
        if battery_pct is not None:
            self.energy += (battery_pct - 50) * 0.05
            if battery_pct < 20:
                self.energy -= 3
                self.happiness -= 2
                self.message = "I'm low on power."
            elif battery_pct > 80:
                self.energy += 2

        if device_stats.get("is_charging"):
            self.energy += 4
            self.happiness += 1
            self.message = "Charging helps me recover."

        cpu_pct = device_stats.get("cpu_pct")
        if cpu_pct is not None:
            if cpu_pct > 80:
                self.stress += 4
                self.health -= 1
                self.message = "The phone is working hard."
            elif cpu_pct > 50:
                self.stress += 2
            else:
                self.stress -= 1

        memory_pct = device_stats.get("memory_pct")
        if memory_pct is not None:
            if memory_pct > 85:
                self.health -= 2
                self.message = "Memory is tight."
            else:
                self.health += 0.5

        if not device_stats.get("network_online", True):
            self.happiness -= 3
            self.message = "I miss the network."
        else:
            latency = device_stats.get("network_latency")
            if latency is not None:
                if latency > 1.2:
                    self.happiness -= 1
                    self.message = "The network feels slow."
                else:
                    self.happiness += 1

        self._refresh_state()

    def tick(self):
        if self.dead:
            return

        self.hunger += 1
        self.energy -= 1
        self.health -= self.stress * 0.01
        self.happiness -= 0.5

        if self.hunger > 80:
            self.health -= 1
            self.energy -= 1
            self.message = "I'm too hungry."

        self.age += 1
        self.level = 1 + self.age // 30

        if self.happiness < 30:
            self.message = "I need some attention."

        self._refresh_state()

    def feed(self):
        if self.dead:
            return

        self.hunger -= 15
        self.energy += 10
        self.happiness += 8
        self.message = "Yum, I feel better!"
        self._refresh_state()

    def rest(self):
        if self.dead:
            return

        self.energy += 12
        self.stress -= 8
        self.happiness += 3
        self.message = "Thank you for the rest."
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
            return "The Tamagotchi is gone. Tap Feed to revive."
        if self.sick:
            return "Not feeling well. Take care of the phone."
        if self.energy < 30:
            return "Low energy, keep it charged."
        return "Feeling stable."

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
        )

    @classmethod
    def load(cls, store):
        if store.exists("pet"):
            return cls.from_dict(store.get("pet"))
        return cls()

    def save(self, store):
        store.put("pet", **self.to_dict())

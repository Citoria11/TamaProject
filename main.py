from kivy.app import App
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout

from device_stats import DeviceStats
from model import Tamagotchi


class TamagotchiLayout(BoxLayout):
    pass


class TamagotchiApp(App):
    def build(self):
        self.store = JsonStore("tamagotchi_store.json")
        self.pet = Tamagotchi.load(self.store)
        self.device_stats = DeviceStats()
        self.animation_frame = 0

        self.root = TamagotchiLayout()
        Clock.schedule_interval(self.update_state, 1)
        Clock.schedule_once(self.update_state, 0)
        return self.root

    def on_stop(self):
        self.save_state()

    def update_state(self, dt):
        device = self.device_stats.read_device_stats()
        self.pet.apply_device(device)
        self.pet.tick(dt)
        self.animation_frame = (self.animation_frame + 1) % 4
        self.update_ui(device)
        self.save_state()

    def update_ui(self, device):
        if not self.root:
            return

        self.root.ids.energy_value.text = f"{self.pet.energy:.0f}%"
        self.root.ids.health_value.text = f"{self.pet.health:.0f}%"
        self.root.ids.happiness_value.text = f"{self.pet.happiness:.0f}%"
        self.root.ids.stress_value.text = f"{self.pet.stress:.0f}%"

        self.root.ids.energy_bar.value = self.pet.energy
        self.root.ids.health_bar.value = self.pet.health
        self.root.ids.happiness_bar.value = self.pet.happiness
        self.root.ids.stress_bar.value = self.pet.stress

        battery_text = "N/A"
        if device.get("battery_pct") is not None:
            battery_text = f"{device['battery_pct']:.0f}%"
        self.root.ids.battery_value.text = battery_text
        self.root.ids.charge_value.text = "Yes" if device.get("is_charging") else "No"
        self.root.ids.cpu_value.text = f"{device['cpu_pct']:.0f}%" if device.get("cpu_pct") is not None else "N/A"
        self.root.ids.memory_value.text = f"{device['memory_pct']:.0f}%" if device.get("memory_pct") is not None else "N/A"
        network_online = device.get("network_online")
        if network_online is True:
            self.root.ids.network_value.text = "Online"
        elif network_online is False:
            self.root.ids.network_value.text = "Offline"
        else:
            self.root.ids.network_value.text = "Unknown"

        self.root.ids.network_latency.text = f"{device['network_latency']:.2f}s" if device.get("network_latency") is not None else "N/A"

        self.root.ids.mood.text = f"Mood: {self.pet.mood}"
        self.root.ids.current_status.text = self.pet.status_text()
        self.root.ids.device_status.text = self.pet.message
        self.root.ids.pet_face.text = self._pet_face_text()
        self.root.ids.pet_face.color = self._pet_face_color()
        self.root.ids.level_text.text = f"Level {self.pet.level}\nAge {self.pet.age}"

    def _pet_face_text(self):
        blink = self.animation_frame % 4 < 2
        if self.pet.dead:
            return "(x_x)\n CRITICAL FAIL"
        if self.pet.sick:
            return "( ¬_¬ )\n  BLOATED"
        if self.pet.health < 30:
            return "(>_<)\n STORAGE CRITICAL"
        if self.pet.stress > 70:
            return "( ;>_< ;)\n OVERHEATING" if blink else "( ;>_<;)\n THERMAL ALERT"
        if self.pet.happiness < 40:
            return "( ⊙_⊙ )\n NO SIGNAL" if blink else "( ⊙⊙ )\n DISCONNECTED"
        if self.pet.energy < 30:
            return "(~_~)\n  LOW BATT" if blink else "(~_-)\n  CRITICAL"
        if self.pet.mood == "Happy":
            return "( ＾∇＾)\n OPTIMIZED" if blink else "( ^_^)\n  RUNNING"
        return "( ◕ᴗ◕ )\n  STABLE" if blink else "( ◕_◕ )\n  NORMAL"

    def _pet_face_color(self):
        if self.pet.dead:
            return (0.5, 0.5, 0.5, 1)
        if self.pet.sick:
            return (0.8, 0.2, 0.2, 1)
        if self.pet.mood == "Happy":
            return (0.1, 0.5, 0.2, 1)
        if self.pet.mood == "Stressed":
            return (0.7, 0.15, 0.15, 1)
        if self.pet.mood == "Tired":
            return (0.3, 0.3, 0.6, 1)
        if self.pet.mood == "Lonely":
            return (0.3, 0.3, 0.4, 1)
        return (0.1, 0.2, 0.4, 1)

    def on_purge(self):
        if self.pet.dead:
            self.pet.revive()
        else:
            self.pet.purge()
        self.update_ui(self.device_stats.read_device_stats())

    def on_cool_down(self):
        self.pet.cool_down()
        self.update_ui(self.device_stats.read_device_stats())

    def on_decongest(self):
        self.pet.decongest()
        self.update_ui(self.device_stats.read_device_stats())

    def on_diagnose(self):
        self.pet.push_message("Checked device state.", 3)
        self.update_ui(self.device_stats.read_device_stats())

    def save_state(self):
        self.pet.save(self.store)


if __name__ == "__main__":
    TamagotchiApp().run()

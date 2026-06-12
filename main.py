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

        self.root = TamagotchiLayout()
        Clock.schedule_interval(self.update_state, 5)
        Clock.schedule_once(self.update_state, 0)
        return self.root

    def on_stop(self):
        self.save_state()

    def update_state(self, dt):
        device = self.device_stats.read_device_stats()
        self.pet.apply_device(device)
        self.pet.tick()
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
        self.root.ids.network_value.text = "Online" if device.get("network_online") else "Offline"
        self.root.ids.network_latency.text = f"{device['network_latency']:.2f}s" if device.get("network_latency") is not None else "N/A"

        self.root.ids.mood.text = f"Mood: {self.pet.mood}"
        self.root.ids.current_status.text = self.pet.message
        self.root.ids.pet_face.text = self._pet_face_text()
        self.root.ids.level_text.text = f"Level {self.pet.level}\nAge {self.pet.age}"

    def _pet_face_text(self):
        if self.pet.dead:
            return "(x_x)\n  RIP"
        if self.pet.sick:
            return "(>_<)\n  ?"
        if self.pet.mood == "Happy":
            return "(^_^)\n  ~"
        if self.pet.mood == "Stressed":
            return "(-_-)\n  !!"
        if self.pet.mood == "Tired":
            return "(~_~)\n  zz"
        return "(◕‿◕)\n  ||  ||"

    def on_feed(self):
        if self.pet.dead:
            self.pet.revive()
        else:
            self.pet.feed()
        self.update_ui(self.device_stats.read_device_stats())

    def on_rest(self):
        self.pet.rest()
        self.update_ui(self.device_stats.read_device_stats())

    def on_check(self):
        self.pet.message = "Checked device state."
        self.update_ui(self.device_stats.read_device_stats())

    def save_state(self):
        self.pet.save(self.store)


if __name__ == "__main__":
    TamagotchiApp().run()

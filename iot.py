import time
import math
import json
import random
import paho.mqtt.publish as publish

# ==============================
# CONFIGURAÇÕES
# ==============================

BROKER         = "localhost"
TOPIC          = "cubesat/telemetry"

ORBIT_PERIOD   = 90 * 60   # segundos
SUN_TIME       = 60 * 60   # segundos iluminado
ECLIPSE_TIME   = 30 * 60   # segundos em eclipse
UPDATE_PERIOD  = 5         # segundos entre publicações

# ==============================
# ESTADO INICIAL
# ==============================

battery     = 80.0   # %
temperature = 20.0   # °C

# ==============================
# FUNÇÕES
# ==============================

def get_solar_power(orbit_time):
    illuminated = orbit_time < SUN_TIME
    if not illuminated:
        return 0.0
    power = 4.5 * math.sin(math.pi * orbit_time / SUN_TIME)
    return max(0.0, power)


def get_mode(battery, illuminated):
    if battery < 20:
        return "SAFE MODE"
    if illuminated:
        return "NOMINAL"
    return "ECLIPSE"


def get_current(mode):
    if mode == "SAFE MODE":
        return random.uniform(80, 150)
    if mode == "NOMINAL":
        return random.uniform(200, 350)
    return random.uniform(250, 400)


def update_temperature(temperature, illuminated):
    target = 55.0 if illuminated else -35.0
    temperature += (target - temperature) * 0.01
    temperature += random.uniform(-0.15, 0.15)
    return temperature


def update_battery(battery, solar_power, current):
    generated = (solar_power / 7.2) * 1000  # mA gerados (P/V × 1000)
    net = generated - current
    battery += net * UPDATE_PERIOD / 600_000
    return max(0.0, min(100.0, battery))


def get_voltage(battery):
    return 6.4 + battery * 0.016  # 6.4 V vazia → 8.0 V cheia (2S LiPo)


def build_payload(mode, temperature, battery, solar_power, voltage, current):
    return {
        "mode":        mode,
        "temperature": round(temperature, 2),
        "battery":     round(battery, 2),
        "solar_power": round(solar_power, 2),
        "voltage":     round(voltage, 3),
        "current":     round(current, 1),
    }

# ==============================
# LOOP PRINCIPAL
# ==============================

while True:
    orbit_time  = time.time() % ORBIT_PERIOD
    illuminated = orbit_time < SUN_TIME

    solar_power = get_solar_power(orbit_time)
    temperature = update_temperature(temperature, illuminated)
    mode        = get_mode(battery, illuminated)
    current     = get_current(mode)
    battery     = update_battery(battery, solar_power, current)
    voltage     = get_voltage(battery)

    payload = build_payload(mode, temperature, battery, solar_power, voltage, current)

    publish.single(TOPIC, json.dumps(payload), hostname=BROKER)
    print(payload)

    time.sleep(UPDATE_PERIOD)
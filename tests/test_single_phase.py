"""Single-phase profile, decoded from a live SUN-8K-SG05LP1-EU-SM2 capture.

TELEMETRY/CONFIG are raw register words read over BLE through a DL1000B logger
(serial number replaced). Expected values are the same-minute Deye Cloud readings
where the cloud reports them; live AC values drift between reads, so only exact
matches are asserted.
"""
from datetime import datetime

import pytest

from custom_components.deye_ble import registers as r
from custom_components.deye_ble import protocol as p
from custom_components.deye_ble.helpers import (
    async_detect_profile,
    async_poll,
    infer_grid_connected,
)

DEVICE_TYPE = 0x0003

TELEMETRY: dict[int, list[int]] = {
    59: [2, 30, 250, 0, 27, 0, 940, 2947, 220, 940, 0, 0, 35, 1950, 0, 1553],
    75: [0, 6, 0, 3878, 5000, 0, 0, 0, 0, 37, 3914, 0, 3367, 0, 1000, 1332],
    91: [1290, 1, 0, 2000, 0, 999, 0],
    101: [0, 0, 0, 0, 0, 0, 314, 0, 2278, 4, 59, 0],
    # Not in the capture: PV3/PV4 voltage + current. This unit has two MPPTs, so
    # they are taken to read 0, as PV3/PV4 power (188/189) do in the 182 block.
    113: [0, 0, 0, 0],
    150: [2411, 0, 2411, 0, 2410, 0, 2410, 2442, 0, 0, 158, 0, 213, 0, 210, 0],
    166: [0, 19, 0, 19, 0, 0, 0, 466, 0, 466, 485, 0, 485, 485, 0, 932],
    182: [1166, 5223, 52, 485, 101, 0, 0, 0, 389, 745, 5000, 5000, 1, 20752, 5062],
    312: [5520, 0, 160, 170, 52, 5229, 65529, 1166, 0, 0, 0, 0, 0],
}

CONFIG: dict[int, list[int]] = {
    2: [513, 12594, 13108, 13622, 14136, 14640, 16, 33026, 0, 5398, 0, 21384, 50050, 0, 14464, 1],
    18: [513, 0, 255, 0, 6666, 7944, 2858],
    200: [1, 5760, 5760, 5520, 314, 4500, 20, 90, 0, 0, 160, 170, 0, 1, 0, 8],
    216: [990, 15, 35, 25, 4600, 5200, 4750, 240, 1440, 4900, 90, 25, 4900, 30, 35, 1],
    232: [1, 0, 0, 0, 5100, 95, 5400, 100, 0, 0, 2, 1, 1, 500, 0, 0],
    248: [255, 0, 100, 500, 900, 1300, 1700, 2000, 8000, 8000, 8000, 8000, 8000, 8000, 4900, 4900],
    264: [4900, 4900, 4900, 4900, 50, 50, 95, 95, 100, 75, 6, 6, 6, 6, 7, 6],
    280: [273, 0, 60, 0, 0, 0, 0, 2650, 1950, 5150, 4800, 0, 2300, 5000],
    325: [0],
}


def _decode(config: bool = True):
    return r.decode_single_phase({**TELEMETRY, **CONFIG} if config else TELEMETRY)


def test_device_type_selects_single_phase():
    assert r.profile_from_device_type(DEVICE_TYPE) == r.PROFILE_SINGLE_PHASE
    assert r.profile_from_device_type(0x0005) == r.PROFILE_THREE_PHASE


@pytest.mark.parametrize("blocks", [r.SP_LIVE_BLOCKS + r.SP_FAST_BLOCKS + r.SP_SLOW_BLOCKS])
def test_blocks_fit_ble_reads_and_do_not_overlap(blocks):
    covered = set()
    for start, count in blocks:
        assert 1 <= count <= 16  # larger reads get no BLE reply
        span = set(range(start, start + count))
        assert not covered & span
        covered |= span


@pytest.mark.parametrize("key,expected", [
    # matched against Deye Cloud, same minute
    ("battery_soc", 52),
    ("battery_voltage", 52.23),
    ("battery_current", 7.45),
    ("battery_power", 389),
    ("battery_temp", 16.6),
    ("inverter_temp", 33.2),
    ("inverter_ac_temp", 29.0),
    ("pv1_voltage", 227.8),
    ("pv2_voltage", 5.9),
    ("grid_frequency", 50.0),
    ("grid_power", 19),
    ("gen_frequency", 50.62),
    ("total_solar", 99.9),
    ("total_grid_import", 387.8),
    ("total_grid_export", 0.0),
    ("total_consumption", 391.4),
    ("total_battery_charge", 195.0),
    ("total_battery_discharge", 155.3),
    ("daily_grid_import", 0.6),
    ("daily_battery_discharge", 3.5),
    ("bms_charge_voltage", 55.2),
    ("bms_charge_current_limit", 160),
    ("bms_discharge_current_limit", 170),
    ("bms_soc", 52),
    ("bms_current", -7),
    ("bms_temp", 16.6),
    ("max_sell_power", 500),
    ("max_charge_current", 160),
    ("max_discharge_current", 170),
    ("smartload_off_soc", 95),
    ("smartload_on_soc", 100),
    ("smartload_min_solar_power", 0),
    ("rated_power", 800.0 * 10),
    ("total_gen", 0.1),
    # inverter identity and settings
    ("inverter_serial", "1234567890"),
    ("protocol_version", "0201"),   # as the Deye Cloud shows it
    ("mppt_count", 2),
    ("phase_count", 1),
    ("battery_capacity", 314),
    ("battery_float_voltage", 55.2),
    ("batt_shutdown_soc", 15),
    ("batt_restart_soc", 35),
    ("batt_low_soc", 25),
    ("grid_charge_start_soc", 30),
    ("grid_charge_current", 35),
    ("grid_charge_enabled", True),
    ("energy_pattern", "Load First"),
    ("work_mode", "Zero Export to Load"),
    ("io_mode", "Generator"),
    ("bms_protocol", "PYLON"),
    ("grid_voltage_high_limit", 265.0),
    ("grid_voltage_low_limit", 195.0),
    ("grid_peak_power", 5000),
    ("gen_peak_power", 2300),
    # status words
    ("device_state", "Normal"),
    ("alarm", "OK"),
    ("fault", "OK"),
    ("inverter_problem", False),
    ("bms_problem", False),
    ("grid_connected", True),
    # inverter energy: daily 60, lifetime 63-64
    ("daily_inverter_energy", 3.0),
    ("total_inverter_energy", 2.7),
    ("inverter_clock", datetime(2026, 10, 31, 8, 11, 42)),
])
def test_decode(key, expected):
    assert _decode()[key] == expected


def test_generator_total_high_word_is_95():
    # ha-solarman's map (0x005C, 0x005F); 93 and 94 are not part of it. Every
    # capture so far reads 0 at both 93 and 95, so this one is synthetic.
    assert r.decode_single_phase({91: [0, 5, 7, 2000, 1, 0, 0]})["total_gen"] == 6554.1


def test_inverter_energy_is_signed():
    # Reg 60 is load minus grid import, negative after grid-charging (PR #8).
    telemetry = dict(TELEMETRY)
    block = list(telemetry[59])
    block[60 - 59] = 0x10000 - 25                          # -2.5 kWh
    block[63 - 59], block[64 - 59] = 0x10000 - 120, 0xFFFF  # -12.0 kWh
    telemetry[59] = block
    data = r.decode_single_phase(telemetry)
    assert data["daily_inverter_energy"] == -2.5
    assert data["total_inverter_energy"] == -12.0


def test_unreliable_counters_are_not_decoded():
    # 179 is power (W), not current (it is ups_power); month/year words
    # undercount (PR #8).
    data = _decode()
    for key in ("load_current", "month_solar", "month_load",
                "month_grid_import", "year_solar", "year_load"):
        assert key not in data


def test_solar_power_on_a_two_string_unit():
    data = _decode()
    assert data["solar_power"] == data["pv1_power"] + data["pv2_power"] == 101


# --- SUN-16K-SG01LP1-EU capture: three MPPTs ---------------------------------
# deye_ble.dump_registers over a DL1000B, 2026-11-02 12:22 Asia/Beirut, battery
# full so PV was curtailed, zero export to CT feeding grid-side loads. Deye
# Cloud at 12:21:52: PV3 403.9 V / 2.9 A / 1127 W, PV cumulative 14458.8 kWh,
# total consumption 3520 W, UPS load 80 W, grid 170 W.
SUN16K: dict[int, list[int]] = {
    16: [28928, 2],                             # rated power 16000.0 W
    18: [769, 14, 255, 0, 6667, 525, 5634],
    59: [2, 231, 0, 0, 298, 2, 1049, 1099, 871, 9977, 2, 125, 73, 62082, 0, 58868],
    75: [0, 8, 0, 10112, 4942, 1, 1533, 0, 0, 239, 11013, 3, 57457, 0, 1000, 495],
    91: [1485, 198, 0, 2000, 0, 13516, 2],
    101: [0, 0, 0, 0, 0, 0, 800, 299],
    109: [4338, 30, 4334, 30, 4033, 30, 0, 0],
    150: [2383, 0, 2383, 2367, 2379, 0, 2379, 2367, 0, 0, 1504, 0, 552, 0, 1420, 0],
    166: [0, 65182, 0, 13, 13, 0, 13, 3623, 0, 3623, 376, 0, 376, 8, 0, 54],
    182: [1230, 5700, 100, 8, 1294, 1292, 1219, 0, 65515, 65533, 4942, 4942, 1, 16, 4958],
}


@pytest.mark.parametrize("key,expected", [
    # Grid, CT and load power count in 10 W on the 12-16 kW units (ha-solarman's
    # "scale: [1, 10]" registers). Same-minute cloud: grid 170, total
    # consumption 3520, UPS 80; grid port 15.04 A x 238.3 V = 3.58 kVA.
    ("grid_power", 130),
    ("external_ct_power", 130),
    ("grid_inverter_side_power", -3540),
    ("house_load", 3760),
    ("ups_power", 80),
    # Battery current is 0.1 A there (cloud -0.3/-0.4 A while BLE read -0.03;
    # 573 W at 54.5 V is the cloud's 10.5 A). Grid/inverter currents agree as-is.
    ("battery_current", -0.3),
    ("grid_current", 15.04),
    ("inverter_output_current", 14.2),
    # Inverter output, PV and battery power stay in W.
    ("inverter_output_power", 3623),
    ("solar_power", 1294 + 1292 + 1219),
    ("battery_power", -21),
    ("rated_power", 16000.0),
])
def test_sun16k_grid_and_load_power_count_in_10w(key, expected):
    data = r.PROFILES[r.PROFILE_SINGLE_PHASE_HP].decode(SUN16K)
    assert data[key] == expected


# Same unit, grid off and Gen Force on, 2026-11-02 15:04 (dump_registers).
SUN16K_GEN: dict[int, list[int]] = {
    150: [26, 0, 26, 2226, 2226, 0, 2226, 2226, 0, 0, 0, 0, 0, 0, 60, 0],
    166: [773, 0, 0, 0, 0, 0, 0, 812, 0, 812, 158, 0, 158, 158, 0, 2203],
    182: [1210, 5948, 100, 158, 272, 301, 452, 0, 65522, 65534, 5000, 5000, 0, 273, 5000],
}


@pytest.mark.parametrize("key,expected", [
    # Generator power stays in W: load 1580 W - inverter output 812 W = 768 W
    # from the GEN port. Positive while the generator feeds in.
    ("gen_power", 773),
    ("house_load", 1580),
    ("ups_power", 1580),        # grid off: the whole house is on the LOAD port
    ("inverter_output_power", 812),
    ("gen_voltage", 220.3),
    ("gen_frequency", 50.0),
    ("grid_connected", False),
])
def test_sun16k_generator_power_counts_in_watts(key, expected):
    assert r.PROFILES[r.PROFILE_SINGLE_PHASE_HP].decode(SUN16K_GEN)[key] == expected


def test_ups_power_is_the_load_port_not_the_total_load():
    # 176 and 178 carry the whole house (inverter output + grid) once a CT
    # puts loads on the grid side; 179 is the LOAD port alone. The 6K and 8K
    # captures read the same value in all three.
    data = r.decode_single_phase(SUN16K)
    assert (data["house_load"], data["ups_power"]) == (376, 8)


@pytest.mark.parametrize("rated_words,profile", [
    ([28928, 2], r.PROFILE_SINGLE_PHASE_HP),   # 16 kW
    ([54464, 1], r.PROFILE_SINGLE_PHASE_HP),   # 12 kW
    ([14464, 1], r.PROFILE_SINGLE_PHASE),      # 8 kW (the SG05LP1 capture)
    ([60000, 0], r.PROFILE_SINGLE_PHASE),      # 6 kW
])
@pytest.mark.asyncio
async def test_detection_picks_the_10w_map_from_the_rated_power(rated_words, profile):
    t = _Transport()
    t.words[16], t.words[17] = rated_words
    assert await async_detect_profile(t) == profile
    assert t.reads == [(r.REG_DEVICE_TYPE, 1), (r.REG_SP_RATED_POWER, 2)]


def test_the_10w_map_shares_the_single_phase_blocks_and_controls():
    sp, hp = r.PROFILES[r.PROFILE_SINGLE_PHASE], r.PROFILES[r.PROFILE_SINGLE_PHASE_HP]
    assert (hp.live, hp.fast, hp.slow, hp.controls, hp.clock_reg) == (
        sp.live, sp.fast, sp.slow, sp.controls, sp.clock_reg)
    assert r.SINGLE_PHASE_PROFILES == {r.PROFILE_SINGLE_PHASE, r.PROFILE_SINGLE_PHASE_HP}
    assert set(r.PROFILE_LABELS) == set(r.PROFILES)


@pytest.mark.parametrize("key,expected", [
    ("mppt_count", 3),
    ("pv1_power", 1294),
    ("pv1_voltage", 433.8),
    ("pv1_current", 3.0),
    ("pv2_power", 1292),
    ("pv2_voltage", 433.4),
    ("pv3_power", 1219),
    ("pv3_voltage", 403.3),
    ("pv3_current", 3.0),
    # No fourth MPPT: its registers read 0, so the sum below is safe.
    ("pv4_power", 0),
    ("pv4_voltage", 0),
    ("pv4_current", 0),
    ("solar_power", 1294 + 1292 + 1219),
    ("total_solar", 14458.8),
    # Cloud "total/daily active production" is PV plus the GEN port: cloud
    # 14478.6 kWh at 12:21:52 = 14458.8 PV + 19.8 generator (92/95).
    ("total_gen", 19.8),
    ("total_production", 14478.6),
    ("daily_solar", 29.9),
    ("daily_gen", 0),
    ("daily_production", 29.9),
    # The cloud's "Daily Consumption" is an energy balance, not register 84
    # (metered load, 23.9): PV 29.9 + import 0.8 + discharge 7.3 - charge
    # 12.5 - export 0 = 25.5 (cloud 25.1 at 12:15 with PV 29.6, import 0.7).
    ("daily_load", 23.9),
    ("daily_consumption_balance", 25.5),
])
def test_sun16k_capture_decodes(key, expected):
    assert r.decode_single_phase(SUN16K)[key] == expected


def _four_strings() -> dict[int, list[int]]:
    """The 16K capture with a fourth string added. SYNTHETIC: no capture yet."""
    words = dict(SUN16K)
    live = list(words[182])
    live[189 - 182] = 4320                    # PV4 power, W
    words[182] = live
    words[109] = words[109][:6] + [3600, 120]  # PV4 360.0 V / 12.0 A
    words[18] = [0x0401] + words[18][1:]       # 4 MPPTs, 1 phase
    return words


@pytest.mark.parametrize("key,expected", [
    ("pv3_power", 1219),
    ("pv4_power", 4320),
    ("pv4_voltage", 360.0),
    ("pv4_current", 12.0),
    ("mppt_count", 4),
])
def test_pv4_decodes(key, expected):
    assert r.decode_single_phase(_four_strings())[key] == expected


def test_solar_power_sums_every_string():
    # pv1 + pv2 alone would miss PV3, the biggest string on the 16K.
    assert r.decode_single_phase(_four_strings())["solar_power"] == 1294 + 1292 + 1219 + 4320


def test_every_pv_string_is_read_on_the_live_tier():
    live = {reg for start, n in r.SP_LIVE_BLOCKS for reg in range(start, start + n)}
    assert set(range(186, 190)) <= live   # PV1-PV4 power
    assert set(range(109, 117)) <= live   # PV1-PV4 voltage, current


@pytest.mark.parametrize("mppt_count,strings", [
    (2, [1, 2]),
    (3, [1, 2, 3]),
    (4, [1, 2, 3, 4]),
    # Register 18 unread at setup: show every string rather than hide a real one.
    (None, [1, 2, 3, 4]),
    # PV1 and PV2 always exist (their entities predate the MPPT count); a
    # nonsense count is clamped to the four strings the map has.
    (1, [1, 2]),
    (0, [1, 2]),
    (9, [1, 2, 3, 4]),
])
def test_pv_strings_follow_the_mppt_count(mppt_count, strings):
    assert r.sp_pv_strings(mppt_count) == strings


class _FakeHass:
    def __init__(self, coordinator):
        self.data = {"deye_ble": {"entry": coordinator}}


class _FakeCoordinator:
    is_single_phase = True
    register_profile = r.PROFILES[r.PROFILE_SINGLE_PHASE]

    def __init__(self, data):
        self.data = data


class _FakeEntry:
    entry_id = "entry"
    data = {"logger_sn": "SN"}


@pytest.mark.asyncio
async def test_cloud_parity_values_have_sensors():
    # The cloud's "active production" figures, generator total, battery version.
    pytest.importorskip("homeassistant")
    from custom_components.deye_ble import sensor

    added = []
    await sensor.async_setup_entry(
        _FakeHass(_FakeCoordinator({"mppt_count": 3})), _FakeEntry(), added.extend,
    )
    ids = {e.unique_id for e in added}
    assert {"SN_total_gen", "SN_daily_production", "SN_total_production", "SN_bms_version",
            "SN_daily_consumption_balance"} <= ids


@pytest.mark.parametrize("mppt_count,strings", [
    (2, {1, 2}), (3, {1, 2, 3}), (4, {1, 2, 3, 4}), (None, {1, 2, 3, 4}),
])
@pytest.mark.asyncio
async def test_pv_string_sensors_follow_the_mppt_count(mppt_count, strings):
    pytest.importorskip("homeassistant")
    from custom_components.deye_ble import sensor

    data = {} if mppt_count is None else {"mppt_count": mppt_count}
    added = []
    await sensor.async_setup_entry(
        _FakeHass(_FakeCoordinator(data)), _FakeEntry(), added.extend,
    )
    ids = {e.unique_id for e in added}
    assert len(ids) == len(added)  # HA rejects a duplicate unique id
    for n in range(1, 5):
        keys = {f"SN_pv{n}_{q}" for q in ("power", "voltage", "current")}
        assert (keys <= ids) == (n in strings), n
        assert (keys & ids) in (set(), keys), n


def test_tou_schedule():
    data = _decode()
    assert data["tou_enabled"] is True
    assert data["tou_days"] == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    slots = data["tou_slots"]
    assert [(s["start"], s["end"], s["soc"]) for s in slots] == [
        ("01:00", "05:00", 50), ("05:00", "09:00", 50), ("09:00", "13:00", 95),
        ("13:00", "17:00", 95), ("17:00", "20:00", 100), ("20:00", "01:00", 75),
    ]
    assert [s["grid_charge"] for s in slots] == [False] * 4 + [True, False]
    assert all(s["gen_charge"] for s in slots)
    assert r.active_tou_slot(slots, "08:11") == 1
    assert r.active_tou_slot(slots, "23:30") == 5
    assert r.active_tou_slot(slots, "00:59") == 5


def test_energy_balance_counts_the_generator_and_export():
    # Synthetic: no capture yet has generator energy or export on the day.
    day = [0] * 16
    day[62 - 59], day[70 - 59], day[71 - 59] = 15, 40, 20   # gen 1.5, charge 4.0, discharge 2.0
    grid = [0] * 16
    grid[76 - 75], grid[77 - 75] = 30, 10                    # import 3.0, export 1.0
    pv = [0] * 7 + [100]                                     # 108: PV 10.0
    data = r.decode_single_phase({59: day, 75: grid, 101: pv})
    assert data["daily_consumption_balance"] == 10.0 + 1.5 + 3.0 + 2.0 - 4.0 - 1.0


def test_battery_version_reads_like_the_cloud():
    # 418-419 on the SUN-16K (2026-11-02): the cloud's "Lithium Battery
    # Version Number" read 0000200A.
    assert r.decode_single_phase({418: [0, 0x200A]})["bms_version"] == "0000200A"
    assert any(start <= 418 and 419 < start + n for start, n in r.SP_SLOW_BLOCKS)


def test_each_tou_program_has_flat_keys():
    # One entity per program field, like the Deye Cloud's prog_N_* entities.
    data = _decode()
    assert [data[f"tou_{n}_time"] for n in range(1, 7)] == [
        "01:00", "05:00", "09:00", "13:00", "17:00", "20:00"]
    assert [data[f"tou_{n}_soc"] for n in range(1, 7)] == [50, 50, 95, 95, 100, 75]
    assert [data[f"tou_{n}_grid_charge"] for n in range(1, 7)] == [False] * 4 + [True, False]
    assert all(data[f"tou_{n}_gen_charge"] for n in range(1, 7))


@pytest.mark.asyncio
async def test_each_tou_program_has_entities():
    pytest.importorskip("homeassistant")
    from custom_components.deye_ble import binary_sensor, sensor

    added = []
    hass, entry = _FakeHass(_FakeCoordinator({"mppt_count": 3})), _FakeEntry()
    await sensor.async_setup_entry(hass, entry, added.extend)
    await binary_sensor.async_setup_entry(hass, entry, added.extend)
    ids = {e.unique_id for e in added}
    for n in range(1, 7):
        for field in ("time", "soc", "grid_charge", "gen_charge"):
            assert f"SN_tou_{n}_{field}" in ids, (n, field)


def test_fault_bits_are_named():
    assert r._bit_texts(0, r.SP_FAULT_BITS) == "OK"
    assert r._bit_texts(1 << 22 | 1 << 40, r.SP_FAULT_BITS) == "AC current leakage, bit 40"


def test_telemetry_alone_has_no_settings():
    data = _decode(config=False)
    assert "battery_capacity" not in data and "tou_slots" not in data
    assert data["battery_soc"] == 52


def test_grid_relay_drives_grid_connected():
    data = _decode()
    assert infer_grid_connected(data) is True
    relay_off = dict(TELEMETRY)
    block = list(relay_off[182])
    block[194 - 182] = 0
    relay_off[182] = block
    assert infer_grid_connected(r.decode_single_phase(relay_off)) is False


def test_no_three_phase_keys():
    assert not any(k.endswith(("_l1", "_l2", "_l3")) for k in _decode())


class _Transport:
    def __init__(self):
        self.reads: list[tuple[int, int]] = []
        # Served by address, so any block layout covering the capture reads the
        # same; a register outside the capture raises instead of reading 0.
        self.words = {
            start + i: w
            for start, block in {**TELEMETRY, **CONFIG}.items()
            for i, w in enumerate(block)
        }

    async def handshake(self):
        pass

    async def read(self, address, count):
        self.reads.append((address, count))
        if address == r.REG_DEVICE_TYPE:
            return [DEVICE_TYPE]
        return [self.words[address + i] for i in range(count)]


@pytest.mark.asyncio
async def test_detect_profile_reads_the_device_type_and_rated_power():
    t = _Transport()
    assert await async_detect_profile(t) == r.PROFILE_SINGLE_PHASE
    assert t.reads == [(r.REG_DEVICE_TYPE, 1), (r.REG_SP_RATED_POWER, 2)]


@pytest.mark.asyncio
async def test_full_poll_reads_every_tier_and_never_the_device_type():
    t = _Transport()
    data = await async_poll(t, profile=r.PROFILE_SINGLE_PHASE)
    assert t.reads == r.SP_LIVE_BLOCKS + r.SP_FAST_BLOCKS + r.SP_SLOW_BLOCKS
    assert data["battery_capacity"] == 314


@pytest.mark.asyncio
async def test_live_only_poll_reads_live_blocks():
    t = _Transport()
    data = await async_poll(t, profile=r.PROFILE_SINGLE_PHASE, tiers={r.TIER_LIVE})
    assert t.reads == r.SP_LIVE_BLOCKS
    # The live set is what a 5 s dashboard needs.
    assert {"battery_soc", "battery_power", "grid_power", "house_load", "solar_power"} <= data.keys()
    assert {f"pv{n}_{q}" for n in range(1, 5) for q in ("power", "voltage", "current")} <= data.keys()


def test_every_single_phase_control_reads_back_on_the_slow_tier():
    # A control whose register is never polled would show a value it cannot see.
    for key, reg in r.PROFILES[r.PROFILE_SINGLE_PHASE].controls.items():
        assert any(start <= reg < start + n for start, n in r.SP_SLOW_BLOCKS), key
        assert key in _decode(), key


@pytest.mark.asyncio
async def test_settings_read_failure_keeps_telemetry():
    class Flaky(_Transport):
        async def read(self, address, count):
            if address == 200:
                raise TimeoutError
            return await super().read(address, count)

    data = await async_poll(Flaky(), profile=r.PROFILE_SINGLE_PHASE)
    assert data["battery_soc"] == 52 and "battery_capacity" not in data


# --- SUN-6K-SG04LP1-EU capture (PR #3, logger reply 21511) --------------------
# Raw +ok= frames at the app's block starts, which differ from ours: the decoder
# looks registers up by address, so any covering blocks decode the same.
SUN6K_FRAMES = {
    76: "+ok=01030800460000987C138B11FC",
    108: "+ok=01030A00470B3D0013001500000A32",
    150: "+ok=01030A09D3000009D3000009D4FEE8",
    164: "+ok=01032000B400000008002400000024000000000000018F0000018F01B3000001B301B3D810",
    180: "+ok=01031E000009DA04E216AA006401B30217000000000000FFC4FF97138D138D00018EDC",
}


@pytest.mark.parametrize("key,expected", [
    ("battery_voltage", 58.02),
    ("battery_soc", 100),
    ("battery_temp", 25.0),
    ("battery_power", -60),
    ("solar_power", 535),
    ("house_load", 435),
    ("grid_power", 36),
    ("inverter_output_power", 399),
    ("grid_voltage", 251.5),
    ("grid_frequency", 50.03),
    ("daily_solar", 7.1),
    ("daily_grid_import", 7.0),
])
def test_sun6k_capture_decodes(key, expected):
    words = {start: p.parse_read(frame) for start, frame in SUN6K_FRAMES.items()}
    assert r.decode_single_phase(words)[key] == expected

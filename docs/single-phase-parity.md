# Single-phase parity: Deye Cloud vs BLE (SUN-16K-SG01LP1)

Every entity of the `deye_cloud` integration (91: 67 sensors, 6 numbers,
12 switches, 6 selects) mapped to its `deye_ble` counterpart on a
SUN-16K-SG01LP1-EU (3 MPPT, logger DL1000B) running the
**single-phase 12–16 kW** register map.

How the comparison was made: every cloud state change in the HA recorder was
paired with the BLE value current at that moment (and at BLE lags of 0–300 s,
keeping the best), over grid-on and grid-off periods on 2026-11-02. "Typical
difference" is the median |cloud − BLE|. Fast-moving powers differ mostly
because the two sources sample at different moments, not because they
disagree: the cloud value is minutes old when it lands (see the latency study).

The 12–16 kW map went live during the 14:11 outage, so the grid-on figures for
the five scaled values (house load, grid, CT, battery current, grid-port power)
come from the earlier recording, 12:15–14:06, with the × 10 applied to the BLE
side. `ups_power` moved from 176 to 179 in the same release, so its grid-on
figure comes from four timed register dumps instead (13:25–13:27).

BLE entity ids are `sensor.deye_inverter_ble_<name>` unless shown otherwise.

Status: **matched**: same quantity, unit and sign; **derived**: computed
from registers the same way the cloud computes it; **missing**: no BLE
counterpart yet; **cloud-only**: the cloud reports something with no
identified register, explained in the notes.

**Result: 83 matched, 4 derived, 0 missing, 4 cloud-only** (91). The cloud-only
four are a generator run-time that never changes, a power factor stuck at
1.00, and two "reactive power" figures with no identified register.

Two cloud values are wrong rather than merely different: "Cumulative
Consumption" shows only the low 16 bits of its counter, and "Total Generator
Production" froze at 14.5 kWh while its twin kept counting.

## Sensors (67)

| Cloud entity | BLE entity | Register | Typical difference | Status |
|---|---|---|---|---|
| `sensor.ac_current_rua` | `inverter_output_current` | 164 | grid on: 0.6 A (n=73); grid off: 0.1 A (n=21, cloud 60 s behind) | matched |
| `sensor.ac_output_frequency_r` | `inverter_output_frequency` | 193 | grid on: 0.02 Hz (n=59); grid off: 0 (n=1) | matched |
| `sensor.ac_temperature` | `inverter_ac_temperature` | 91 | grid on: 0.3 ℃ (n=74, cloud 30 s behind); grid off: 0 (n=21) | matched |
| `sensor.ac_voltage_rua` | `inverter_output_voltage` | 154 | grid on: 0.2 V (n=66); grid off: 0.1 V (n=17) | matched |
| `sensor.battery_current` | `battery_current` | 191 (×0.1 A) | grid on: 0 (n=30); grid off: 0.65 A (n=16, cloud 120 s behind) | matched (scaled) |
| `sensor.battery_power` | `battery_power` | 190 | grid on: 1 W (n=59); grid off: 5 W (n=22, cloud 30 s behind) | matched |
| `sensor.battery_rated_capacity` | `battery_capacity` | 204 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.battery_voltage` | `battery_voltage` | 183 | grid on: 0.04 V (n=67, cloud 90 s behind); grid off: 0.08 V (n=22, cloud 90 s behind) | matched |
| `sensor.cumulative_consumption` | `consumption_total` | 85/86 | −19660.8 kWh (3 × 6553.6): cloud shows the low 16 bits only | matched (wrap) |
| `sensor.cumulative_energy_purchased` | `grid_import_total` | 78/80 | grid on: 0 (n=4); grid off: 0 (n=1) | matched |
| `sensor.cumulative_grid_feed_in` | `grid_export_total` | 81/82 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.daily_active_production` | `production_today` | 108 + 62 | grid off: 0 (n=14) | derived (production) |
| `sensor.daily_charging_energy` | `battery_charge_today` | 70 | grid on: 0 (n=1); grid off: 0 (n=2) | matched |
| `sensor.daily_consumption` | `consumption_today_energy_balance` | 108+62+76+71−70−77 | grid off: 0 (n=14) | derived (balance) |
| `sensor.daily_discharging_energy` | `battery_discharge_today` | 71 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.daily_energy_purchased` | `grid_import_today` | 76 | grid on: 0 (n=4); grid off: 0 (n=1) | matched |
| `sensor.daily_grid_feed_in` | `grid_export_today` | 77 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.dc_current_pv1` | `pv1_current` | 110 | grid on: 0.15 A (n=64); grid off: 0.1 A (n=19, cloud 60 s behind) | matched |
| `sensor.dc_current_pv2` | `pv2_current` | 112 | grid on: 0.1 A (n=63); grid off: 0.2 A (n=18, cloud 60 s behind) | matched |
| `sensor.dc_current_pv3` | `pv3_current` | 114 | grid on: 0.2 A (n=65); grid off: 0.2 A (n=19, cloud 60 s behind) | matched |
| `sensor.dc_power_pv1` | `pv1_power` | 186 | grid on: 29.5 W (n=74, cloud 30 s behind); grid off: 66.5 W (n=22, cloud 180 s behind) | matched |
| `sensor.dc_power_pv2` | `pv2_power` | 187 | grid on: 30.5 W (n=74, cloud 30 s behind); grid off: 78.5 W (n=22, cloud 120 s behind) | matched |
| `sensor.dc_power_pv3` | `pv3_power` | 188 | grid on: 40 W (n=73, cloud 30 s behind); grid off: 24 W (n=22, cloud 90 s behind) | matched |
| `sensor.dc_temperature` | `inverter_temperature` | 90 | grid on: 0 (n=40); grid off: 0 (n=1) | matched (dctemp) |
| `sensor.dc_voltage_pv1` | `pv1_voltage` | 109 | grid on: 1.75 V (n=72, cloud 30 s behind); grid off: 1.55 V (n=22, cloud 60 s behind) | matched |
| `sensor.dc_voltage_pv2` | `pv2_voltage` | 111 | grid on: 1.5 V (n=71); grid off: 1.15 V (n=22, cloud 60 s behind) | matched |
| `sensor.dc_voltage_pv3` | `pv3_voltage` | 113 | grid on: 0.7 V (n=73); grid off: 0.4 V (n=21) | matched |
| `sensor.external_ct_power_l1l2` | `external_ct_power` | 170 (×10 W) | grid on: 50 W (n=74, cloud 60 s behind); grid off: 0 (n=1) | matched (scaled) |
| `sensor.gen_voltage` | `generator_voltage` | 181 | grid on: 0.1 V (n=48); grid off: 0.4 V (n=11, cloud 30 s behind) | matched |
| `sensor.generator_frequency` | `generator_frequency` | 196 | grid on: 0 (n=1); grid off: 0.01 Hz (n=2) | matched |
| `sensor.grid_current_l1l2` | `grid_current` | 160 | grid on: 0.29 A (n=73, cloud 30 s behind); grid off: 0 (n=1) | matched |
| `sensor.grid_frequency` | `grid_frequency` | 79 | grid on: 0.02 Hz (n=60); grid off: 0 (n=1) | matched |
| `sensor.grid_voltage_l1l2` | `grid_voltage` | 150 | grid on: 0.2 V (n=69, cloud 30 s behind); grid off: 0 (n=15) | matched |
| `sensor.inverter_output_power_l1l2` | `inverter_output` | 175 | grid on: 75.5 W (n=74, cloud 30 s behind); grid off: 15 W (n=21) | matched |
| `sensor.load_voltage_l1l2` | `load_voltage` | 157 | grid on: 0.4 V (n=64, cloud 30 s behind); grid off: 0.2 V (n=20, cloud 90 s behind) | matched |
| `sensor.mechanical_deye16_bms_charge_voltage` | `bms_charge_voltage` | 312 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.mechanical_deye16_bms_current` | `bms_current` | 318 | grid on: 0 (n=1); grid off: 1 A (n=14) | matched |
| `sensor.mechanical_deye16_bms_discharge_voltage` | `bms_discharge_voltage` | 313 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.mechanical_deye16_bms_soc` | `bms_soc` | 316 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.mechanical_deye16_bms_temperature` | `bms_temperature` | 319 | grid on: 0 (n=2); grid off: 0 (n=1) | matched |
| `sensor.mechanical_deye16_bms_voltage` | `bms_voltage` | 317 | grid on: 0 (n=3); grid off: 0 (n=16) | matched |
| `sensor.mechanical_deye16_charge_current_limit` | `bms_charge_current_limit` | 314 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.mechanical_deye16_daily_production_generator` | `generator_today` | 62 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.mechanical_deye16_discharge_current_limit` | `bms_discharge_current_limit` | 315 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.mechanical_deye16_gen_daily_run_time` | — | — | cloud reads 0.00 h | cloud-only (runtime) |
| `sensor.mechanical_deye16_grid_total_reactive_power` | `grid_power_inverter_side` | — (not identified) | tracks grid-port power at ~0.8×, ~700 var below 167 × 10 | cloud-only (reactive) |
| `sensor.mechanical_deye16_hmi` | `comms_board_firmware` | 14, 10 | same words, different format | matched (firmware) |
| `sensor.mechanical_deye16_inverter_total_reactive_power` | — | — | cloud read 0, then 260 | cloud-only (see constant) |
| `sensor.mechanical_deye16_lithium_battery_version_number` | `battery_version` | 418–419 | equal (0000200A) | matched |
| `sensor.mechanical_deye16_main` | `control_board_firmware` | 13, 12, 11 | same words, different format | matched (firmware) |
| `sensor.mechanical_deye16_power_factor` | — | — | cloud reads 1.00 | cloud-only (constant) |
| `sensor.mechanical_deye16_protocol_version` | `modbus_protocol` | 2 | equal (0201) | matched |
| `sensor.mechanical_deye16_pv_cumulative_power_generation_active` | `solar_total` | 96/97 | grid on: 0 (n=22); grid off: 0 (n=13) | matched |
| `sensor.mechanical_deye16_pv_daily_power_generation_active` | `solar_today` | 108 | grid on: 0 (n=22); grid off: 0 (n=14) | matched |
| `sensor.mechanical_deye16_total_gen_power` | `generator_power` | 166 | grid on: 0 (n=1); grid off: 218 W (n=7, cloud 90 s behind) | matched (gen) |
| `sensor.mechanical_deye16_total_production_generator` | `generator_total` | 92/95 | grid off: 0 (n=3) | matched |
| `sensor.rated_power` | `rated_power` | 16/17 | grid on: 0 (n=1); grid off: 0 (n=1) | matched |
| `sensor.soc` | `battery_soc` | 184 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.temperature_battery` | `battery_temperature` | 182 | grid on: 0 (n=2); grid off: 0 (n=1) | matched |
| `sensor.total_active_production` | `production_total` | 96/97 + 92/95 | grid off: 0 (n=14) | derived (production) |
| `sensor.total_charge_energy` | `battery_charge_total` | 72/73 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.total_consumption_power` | `house_load` | 178 (×10 W) | grid on: 30 W (n=69, cloud 30 s behind); grid off: 10 W (n=20) | matched (scaled) |
| `sensor.total_dc_input_power` | `solar_power` | 186–189 summed | grid on: 79.5 W (n=74, cloud 30 s behind); grid off: 130 W (n=22, cloud 120 s behind) | derived |
| `sensor.total_discharge_energy` | `battery_discharge_total` | 74/75 | grid on: 0 (n=1); grid off: 0 (n=3) | matched |
| `sensor.total_generator_production` | `generator_total` | 92/95 | cloud frozen at 14.5 kWh; its twin matches | matched (stalegen) |
| `sensor.total_grid_power` | `grid_power` | 169 (×10 W) | grid on: 50 W (n=74, cloud 60 s behind); grid off: 0 (n=1) | matched (scaled) |
| `sensor.ups_load_power` | `ups_power` | 179 (×10 W) | grid on: raw 179 × 10 = 90–100 W vs cloud 80–90 W (4 dumps); grid off: 10 W (n=20) | matched (ups) |

## Time-of-use programs: numbers, selects, switches (24)

The cloud's are writable; the BLE ones are read-only (Read Only blocks writes
anyway). N = 1–6.

| Cloud entity | BLE entity | Register | Typical difference | Status |
|---|---|---|---|---|
| `number.prog_1_battery` | `program_1_soc` | 268 | 0 (equal) | matched |
| `select.prog_1_time` | `program_1_start` | 250 (HHMM) | equal | matched |
| `switch.prog_1_grid_charge` | `binary_sensor.…_program_1_grid_charge` | 274 bit 0 | equal | matched |
| `switch.prog_1_generation` | `binary_sensor.…_program_1_generator_charge` | 274 bit 1 | equal | matched |
| `number.prog_2_battery` | `program_2_soc` | 269 | 0 (equal) | matched |
| `select.prog_2_time` | `program_2_start` | 251 (HHMM) | equal | matched |
| `switch.prog_2_grid_charge` | `binary_sensor.…_program_2_grid_charge` | 275 bit 0 | equal | matched |
| `switch.prog_2_generation` | `binary_sensor.…_program_2_generator_charge` | 275 bit 1 | equal | matched |
| `number.prog_3_battery` | `program_3_soc` | 270 | 0 (equal) | matched |
| `select.prog_3_time` | `program_3_start` | 252 (HHMM) | equal | matched |
| `switch.prog_3_grid_charge` | `binary_sensor.…_program_3_grid_charge` | 276 bit 0 | equal | matched |
| `switch.prog_3_generation` | `binary_sensor.…_program_3_generator_charge` | 276 bit 1 | equal | matched |
| `number.prog_4_battery` | `program_4_soc` | 271 | 0 (equal) | matched |
| `select.prog_4_time` | `program_4_start` | 253 (HHMM) | equal | matched |
| `switch.prog_4_grid_charge` | `binary_sensor.…_program_4_grid_charge` | 277 bit 0 | equal | matched |
| `switch.prog_4_generation` | `binary_sensor.…_program_4_generator_charge` | 277 bit 1 | equal | matched |
| `number.prog_5_battery` | `program_5_soc` | 272 | 0 (equal) | matched |
| `select.prog_5_time` | `program_5_start` | 254 (HHMM) | equal | matched |
| `switch.prog_5_grid_charge` | `binary_sensor.…_program_5_grid_charge` | 278 bit 0 | equal | matched |
| `switch.prog_5_generation` | `binary_sensor.…_program_5_generator_charge` | 278 bit 1 | equal | matched |
| `number.prog_6_battery` | `program_6_soc` | 273 | 0 (equal) | matched |
| `select.prog_6_time` | `program_6_start` | 255 (HHMM) | equal | matched |
| `switch.prog_6_grid_charge` | `binary_sensor.…_program_6_grid_charge` | 279 bit 0 | equal | matched |
| `switch.prog_6_generation` | `binary_sensor.…_program_6_generator_charge` | 279 bit 1 | equal | matched |

## Freshness

Measured 2026-11-02; details in the latency study.

| Source | Updates | Lag behind a load switching (median) |
|---|---|---|
| Zigbee meters (heater, pump) | ~5 s reports | reference |
| BLE, Standard | every 74 s (p90 79 s) | 21 s and 71 s on the two heater events; ≤ 73 s on the grid drop |
| BLE, Live | every 6.0 s (p90 6.4–6.6 s); 119/119 polls carried new values, so the logger's response cache does not hold frames back at this rate | not yet measured on a real step (no load switched in the window); bounded by one poll |
| Deye Cloud, polled every 60 s | every 61–244 s | 150 s on 245 pump starts, 143–182 s on heaters; 158–231 s on the grid drop |
| Deye Cloud while BLE is Live + Cloud | every 301–363 s | — |

## Notes

- **scaled**: on the 12–16 kW units, grid (167, 169), CT (170) and load
  (178, 179) power count in 10 W, and battery current (191) in 0.1 A. The
  `single_phase_hp` map applies the factor; it is picked at setup from the
  rated power (≥ 12 kW). Evidence: register 178 × 10 tracked the cloud's
  total consumption within one 10 W step at the same timestamps; the grid-port
  current (160: 15.04 A at 238 V) agrees with 167 × 10; the 6K and 8K
  captures count in W and 0.01 A.
- **ups**: the cloud's "UPS Load Power" is the LOAD port (179), not 176. With
  the grid on, the house sits behind the CT on the grid side and 179 reads
  ~80–130 W. When the grid dropped at 14:11 the changeover moved the house onto
  the LOAD port and 179 rose to equal 178 (5.1 kW), as the cloud did.
- **wrap**: the cloud's "Cumulative Consumption" is only the low 16 bits of
  85/86: it reads 1101.6 kWh where the counter holds 20762.1 kWh (3 × 6553.6
  short). BLE decodes the full 32 bits; the energy balance (PV 14458.8 +
  import 7565.1 − export 153.3 − battery and inverter losses) supports it.
  The difference is constant at 19660.8 kWh until the next wrap.
- **production**: "Daily/Total Active Production" is PV plus the GEN port.
  Total: 14458.8 PV + 19.8 generator = 14478.6, the cloud's figure to 0.1 kWh;
  the gap moved from 14.5 to 19.8 kWh when the generator ran on 10-28.
- **balance**: the cloud's "Daily Consumption" is an energy balance, PV +
  generator + grid import + battery discharge − battery charge − export, so it
  includes the inverter's own losses. Register 84 (`consumption_today`, kept
  as its own sensor) is the metered load and runs ~2 kWh/day lower.
- **dctemp**: the inverter itself reports −50.5 °C on register 90 (raw 495);
  the cloud has shown the same for at least 10 days. Most likely an absent or
  faulty DC-side probe, not a decoding error.
- **reactive**: the cloud's "Grid Total Reactive Power" moves with the
  grid-port power (167 × 10, the inverter feeding grid-side loads through its
  grid port) with the sign agreeing on 73/73 grid-on samples, but runs at about
  0.8 × that, ~700 below it, and reads 0 with the grid off. It is not true
  reactive power either: the grid-port current × voltage leaves only ~500 var
  for that. No register in 0–639 holds it. The closest BLE quantity is
  `grid_power_inverter_side` (167 × 10, negative = out of the grid port).
- **firmware**: MAIN and HMI are the same firmware words BLE reads, formatted
  differently: cloud MAIN `9028-1727-0000` = BLE `9028.0000.1727` (13, 12, 11);
  cloud HMI `0000-C37B-0001` = BLE `C37B.0000` (14, 10).
- **gen**: generator power (166) is plain W on the 16K, not 10 W, and positive
  while the generator feeds in. Verified 2026-11-02 15:04 with Gen Force on:
  166 = 773 while load 178 × 10 = 1580 W and inverter output 175 = 812 W
  (1580 − 812 = 768 W from the GEN port). ha-solarman does not scale 166
  either. The cloud reports the same positive magnitude, so the power-flow
  card's `invert_aux: true` stays right.
- **stalegen**: the cloud stopped returning this key at HA's 12:14 restart (it
  is `unavailable` since); it duplicated "Total Production Generator".
- **runtime**: "Gen Daily Run Time" has never changed on the cloud (0.00 h);
  no register identified in 0–639.
- **constant**: "Power Factor" has read 1.00 throughout. "Inverter Total
  Reactive Power" read 0 for days, then 260 on 2026-11-02. No register
  identified in 0–639 for either. Low value; if one turns out to matter, a
  `deye_ble.dump_registers` sweep while it changes would find it.

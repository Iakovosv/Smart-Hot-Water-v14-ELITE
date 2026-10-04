# 🔥 GSW: Smart Hot Water ELITE

Έξυπνος έλεγχος θερμοσίφωνα / ηλιακού για **Home Assistant**, σχεδιασμένος για
ελληνικές συνθήκες (κρύα/ήπια κλίματα, ηλιακός, πολλαπλοί χρήστες).

Smart electric water heater / solar boiler controller for **Home Assistant**,
designed for Greek conditions (cold/mild weather, solar collectors, multiple
users).

- 👨‍💻 Developer: **Iakovos Venieris**
- 📡 Project: **Greece Sky and Weather**
- ▶ https://www.youtube.com/@GreeceSkyandWeather

> ⚠️ **Άδεια / License:** Δωρεάν για **προσωπική, μη-εμπορική** χρήση.
> **Απαγορεύεται** η εμπορική χρήση, η τροποποίηση και η αναδιανομή χωρίς γραπτή
> άδεια. Δείτε το [LICENSE](LICENSE).
> Free for **personal, non-commercial** use. **Commercial use, modification and
> redistribution are not permitted** without written permission. See [LICENSE](LICENSE).

---

## 🇬🇷 Τι κάνει

| Λειτουργία | Περιγραφή |
|---|---|
| **Έλεγχος θερμοκρασίας νερού** | Σβήνει τον θερμοσίφωνα όταν το νερό φτάσει τον στόχο. |
| **Λογική Κρύο / Ήπιο** | Ξεχωριστός **στόχος** ΚΑΙ ξεχωριστός **μέγιστος χρόνος** ανάλογα με την εξωτερική θερμοκρασία (όριο `cold_threshold`). |
| **Μέγιστος χρόνος ασφαλείας** | Αν δεν φτάσει τον στόχο, σβήνει μετά από `max_time_cold` / `max_time_warm`. |
| **Παρουσία χρηστών** | Ανάβει μόνο αν τουλάχιστον ένας επιλεγμένος χρήστης είναι σε επιλεγμένη ζώνη. Ο User 2 είναι προαιρετικός. |
| **Defrost ηλιακού** | Χρονικό παράθυρο + όρια θερμοκρασίας νερού/εξωτερικής. Υποστηρίζει και παράθυρο που περνά τα μεσάνυχτα. |
| **3 προγράμματα** | Το καθένα με **δικό του διακόπτη ενεργοποίησης** και θερμοκρασία στόχο (`0` = αυτόματο, με βάση το κρύο/ήπιο). |
| **Ηλιακός (4 επιλογές)** | `off` / `flag` / `temperature` / `both` — ο χρήστης διαλέγει **κανένα, ένα ή και τα δύο**. |
| **Χειροκίνητο Boost** | Κουμπί για **άμεσο** άναμμα με δικό του στόχο και μέγιστο χρόνο. |
| **Ζωντανή κατάσταση & πρόοδος** | Ενημερώνει `input_select` (κατάσταση), `input_number` (πρόοδος %) και `input_datetime` (τελευταία ενεργοποίηση). |
| **Ασφάλεια** | Δεν θερμαίνει αν ο αισθητήρας νερού είναι `unknown/unavailable`, αν το νερό είναι ήδη ζεστό, ή αν το `water_temperature_check` είναι ON. |

**Όλες οι οντότητες επιλέγονται από το UI** — χωρίς κώδικα. Τίποτα δεν είναι
hardcoded.

### Γιατί η παλιά έκδοση «δεν δούλευε»
- `mode: restart` + έλεγχος κάθε 5 λεπτά → κάθε νέο tick **ακύρωνε** την εκτέλεση πριν σβήσει/ανάψει.
- Ο έλεγχος παρουσίας στο `zone.home` αποτύγχανε (το state του person είναι `home`, όχι το friendly name).
- Το κουμπί Boost δεν ήταν συνδεδεμένο πουθενά.
- Τα προγράμματα έπιαναν μόνο αν το λεπτό ήταν ακριβώς πολλαπλάσιο του 5.
- Τα schedules 2/3 με `00:00:00` έτρεχαν τα μεσάνυχτα αντί να είναι ανενεργά.

Όλα τα παραπάνω **διορθώθηκαν** σε αυτή την έκδοση.

---

## 🇬🇧 What it does

Water temperature control, cold/warm logic (separate target **and** max run time),
presence check, solar defrost with a time window, 3 schedules each with its own
enable switch, solar skip (flag / collector temperature / both / off), manual
boost, live status & progress helpers, and safety guards. **Every entity is
selected from the UI** — no code required.

---

## Απαιτήσεις / Requirements

- Home Assistant **2024.4+**
- Ένα `switch` για τον θερμοσίφωνα / a `switch` for the boiler
- `sensor` θερμοκρασίας νερού / water temperature `sensor`
- `sensor` εξωτερικής θερμοκρασίας / outdoor temperature `sensor`
- Τουλάχιστον 1 `person` + `zone` / at least 1 `person` + `zone`
- (Προαιρετικά) Οι βοηθητικές οντότητες από το `helpers/gsw_hotwater.yaml`

---

## Εγκατάσταση / Installation

### Μέθοδος A — HACS (προτείνεται) 🏆

Το repo είναι **custom integration** που εγκαθιστά **αυτόματα** το blueprint.

1. HACS → **Integrations** → ⋮ (πάνω δεξιά) → **Custom repositories**.
2. Βάλε το URL: `https://github.com/Iakovosv/Smart-Hot-Water-v14-ELITE`
   και **Category: Integration** → **Add**.
3. Αναζήτησε **GSW Smart Hot Water** → **Download**.
4. **Restart** το Home Assistant (υποχρεωτικό για νέο integration).
5. **Settings → Devices & Services → Add Integration** → αναζήτησε
   **GSW Smart Hot Water** → **Submit**. Αυτό εγκαθιστά/ενημερώνει αυτόματα
   **και τα δύο** blueprints.
6. **Settings → Automations & Scenes → Blueprints** → άνοιξε το
   **🔥 GSW: Smart Hot Water ELITE** → **Create automation**.
7. Κάνε το ίδιο και για το **🛡️ GSW: Boiler Safety Watchdog** → **Create automation**
   (και άφησέ το **πάντα ενεργό** — δες την ενότητα Ασφάλεια).

> ℹ️ **Restart vs Quick Reload:** το **Quick Reload** (Developer Tools → YAML →
> Reload) **δεν** φορτώνει νέα integrations — χρειάζεται **Restart**. Αν ενημερώσεις
> μόνο τα blueprints (χωρίς αλλαγή integration), αρκεί Reload/restart των automations.

> Γιατί HACS Integration και όχι απευθείας blueprint; Το HACS **δεν** έχει
> κατηγορία «blueprint». Αυτό το μικρό integration απλώς αντιγράφει το blueprint
> στη σωστή θέση και το κρατά ενημερωμένο.

### Μέθοδος B — Χειροκίνητα (blueprint μόνο)

1. Κατέβασε τα δύο blueprints:
   `custom_components/gsw_hotwater/blueprints/gsw_smart_hot_water.yaml` και
   `gsw_boiler_safety.yaml`.
2. Αντίγραψέ τα στο `<config>/blueprints/automation/gsw_hotwater/`.
   (Ή: **Blueprints → Import Blueprint** και δώσε το raw URL κάθε αρχείου.)
3. **Developer Tools → YAML → Reload Automations** (ή restart).
4. Δημιούργησε automation από κάθε blueprint (κύριος + watchdog).

### Βοηθητικές οντότητες / Helpers

Είτε:
- Αντίγραψε το `helpers/gsw_hotwater.yaml` στο `<config>/packages/` και πρόσθεσε
  στο `configuration.yaml`:
  ```yaml
  homeassistant:
    packages: !include_dir_named packages
  ```
- Ή δημιούργησέ τες χειροκίνητα από **Settings → Devices & Services → Helpers**.

> Οι οντότητες αυτές είναι **προαιρετικές** — το blueprint δουλεύει και χωρίς
> αυτές, αρκεί να αφήσεις τα αντίστοιχα πεδία κενά.

---

## Ρύθμιση / Configuration

Άνοιξε το automation και συμπλήρωσε τα πεδία (όλα από το UI):

| Πεδίο (Input) | Ελληνικά | Default |
|---|---|---|
| `master_enable` | Γενικός διακόπτης | `input_boolean.gsw_smart_hotwater_enable` |
| `boiler_switch` | Διακόπτης θερμοσίφωνα | — |
| `water_temp_sensor` | Αισθητήρας θερμοκρασίας νερού | — |
| `outdoor_temp_sensor` | Αισθητήρας εξωτερικής θερμοκρασίας | — |
| `water_temperature_check` | Μπλοκάρισμα θέρμανσης | `input_boolean.water_temperature_check` |
| `user_1` / `user_1_zones` | Χρήστης 1 / Ζώνες | — |
| `user_2` / `user_2_zones` | Χρήστης 2 (προαιρετικός) | κενό |
| `require_presence` | Απαίτηση παρουσίας | `true` |
| `cold_threshold` | Όριο κρύου | `16 °C` |
| `target_temp_cold` / `target_temp_warm` | Στόχος κρύου / ήπιου | `58` / `50 °C` |
| `max_time_cold` / `max_time_warm` | Μέγιστος χρόνος κρύου / ήπιου | `70` / `55 min` |
| `schedule_N_enabled/time/temp` | Πρόγραμμα N ενεργό/ώρα/στόχος | off / 06:00 / 0=auto |
| `solar_mode` | Λειτουργία ηλιακού | `off` |
| `solar_flag` | Boolean παράλειψης ηλιακού | κενό |
| `solar_temp_sensor` | Αισθητήρας θερμοκρασίας συλλέκτη | κενό |
| `solar_temp_threshold` | Όριο θερμοκρασίας συλλέκτη | `45 °C` |
| `defrost_enable` | Ενεργοποίηση defrost | `false` |
| `defrost_water_temp` / `defrost_outdoor_temp` | Όρια defrost | `4` / `2 °C` |
| `defrost_start_time` / `defrost_end_time` | Παράθυρο defrost | `03:00` / `05:00` |
| `defrost_check_interval` | Διάρκεια defrost | `5 min` |
| `boost_button` | Κουμπί boost | `input_button.gsw_hotwater_boost` |
| `boost_target_temp` / `boost_minutes` | Στόχος / λεπτά boost | helpers |
| `status_entity` | Helper κατάστασης | `input_select.gsw_hotwater_status` |
| `progress_entity` | Helper προόδου | `input_number.gsw_hotwater_progress` |
| `last_on_entity` | Helper τελευταίας ενεργοποίησης | `input_datetime.water_heater_on` |
| `notify_service` | Υπηρεσία ειδοποίησης (προαιρετική) | κενό |
| `hysteresis` | Υστέρηση επανάναψης (αποφυγή short cycling) | `3 °C` |

### Κενά / προαιρετικά πεδία — ο αυτοματισμός δουλεύει πάντα

Μπορείς να αφήσεις **κενά** τα προαιρετικά πεδία — δεν «σπάει» ποτέ:

| Αν αφήσεις κενό… | Τι συμβαίνει |
|---|---|
| `require_presence = false` (ή κενές ζώνες) | Αγνοείται εντελώς ο έλεγχος παρουσίας → θερμαίνει κανονικά. |
| `user_2` / `user_2_zones` | Χρησιμοποιείται μόνο ο χρήστης 1. |
| `outdoor_temp_sensor` | Χρησιμοποιείται ο στόχος/χρόνος **ήπιου** καιρού (χωρίς σύγκριση εξωτερικής). |
| `solar_flag` (με mode `flag`) | Δεν παραλείπεται θέρμανση → θερμαίνει κανονικά. |
| `solar_temp_sensor` (με mode `temperature`) | Δεν παραλείπεται θέρμανση → θερμαίνει κανονικά. |
| `status_entity` / `progress_entity` / `last_on_entity` | Απλώς δεν ενημερώνεται ο αντίστοιχος helper. |
| `boost_target_temp` / `boost_minutes` | Χρησιμοποιείται ο στόχος/χρόνος **ήπιου** καιρού. |
| `hysteresis` | `3 °C` — μετά τον στόχο, επανάναψη όταν πέσει 3° κάτω (αποφυγή short cycling). |

> ⚠️ **Προσοχή:** αν αφήσεις κενό `boiler_switch` ή `water_temp_sensor`, ο
> αυτοματισμός **δεν κάνει τίποτα** (σωστά — δεν θερμαίνει «στα τυφλά»).
> Αν έχεις `require_presence = true` με **κενές ζώνες**, δεν θερμαίνει ποτέ.
> Αν δεν θέλεις έλεγχο τοποθεσίας, βάλε `require_presence = false`.

### Καταστάσεις / Status values

Ο `input_select` πρέπει να έχει **ακριβώς** αυτές τις επιλογές (εμφανίζονται
ως έχουν· η ελληνική σημασία σε παρένθεση):

`Idle` (Σε αναμονή) · `Heating` (Θέρμανση) · `Target reached` (Στόχος) ·
`Blocked` (Μπλοκαρισμένο) · `Solar skip` (Παράλειψη ηλιακού) · `Defrost` ·
`Boost`

---

## Πώς λειτουργεί / How it works

- **Trigger `tick`** — κάθε **5 λεπτά**: ελέγχει defrost + προγράμματα.
- **Trigger `heartbeat`** — κάθε **1 λεπτό**: ενημερώνει την **πρόοδο %** όταν θερμαίνει.
- **Trigger `boost`** — όταν πατηθεί το κουμπί: θερμαίνει άμεσα (αν ο γενικός διακόπτης είναι ON).

**Σειρά ελέγχων για θέρμανση:** παρουσία → αισθητήρας διαθέσιμος → `water_temperature_check` off → όχι «ήδη ζεστό» → όχι παράλειψη ηλιακού → ανάβει → περιμένει στόχο/χρόνο → σβήνει.

Το `mode: single` εγγυάται ότι μια εκτέλεση **δεν ακυρώνεται** από τα επόμενα ticks.

---

## 🛡️ Ασφάλεια — Ανεξάρτητος watchdog / Safety watchdog

**ΣΗΜΑΝΤΙΚΟ:** Μαζί με τον κύριο αυτοματισμό εγκαθίσταται και ένας **ανεξάρτητος
αυτοματισμός ασφαλείας**: `🛡️ GSW: Boiler Safety Watchdog`.

**Κράτα τον ΠΑΝΤΑ ΕΝΕΡΓΟ**, ακόμη κι αν απενεργοποιήσεις τον κύριο αυτοματισμό.
Αν ο θερμοσίφωνας μείνει αναμμένος πάνω από τον μέγιστο χρόνο, **σβήνει με το
ζόρι** και (προαιρετικά) στέλνει ειδοποίηση. Προστατεύει από:

- τον κύριο αυτοματισμό να σταματήσει / τροποποιηθεί / «πέσει»·
- **κολλημένο αισθητήρα** θερμοκρασίας νερού·
- πρόγραμμα ή boost που δεν φτάνει ποτέ τον στόχο·
- επανεκκίνηση του Home Assistant στη μέση της θέρμανσης.

**Ρύθμιση:** όρισε το `max_on_minutes` **λίγο πιο πάνω** από τον μεγαλύτερο χρόνο
του κύριου αυτοματισμού (π.χ. αν `max_time_cold = 70`, βάλε `max_on_minutes = 90`).

> 💡 **Προαιρετικά, ακόμη πιο ισχυρό:** πρόσθεσε ένα φυσικό θερμικό όριο (θερμοστάτη
> ασφαλείας) στη τροφοδοσία του θερμοσίφωνα. Ο watchdog του λογισμικού δεν
> αντικαθιστά την ηλεκτρολογική ασφάλεια.

> 💡 **Προαιρετικό «hard limit» στο hardware:** αν θέλεις απόλυτη σιγουριά, βάλε
> στον διακόπτη/πρίζα (π.χ. Sonoff) ένα **auto-off** (π.χ. 2 ώρες) ώστε ακόμη κι
> αν το Home Assistant είναι κάτω, να σβήσει μόνος του.

---

## Αντιμετώπιση προβλημάτων / Troubleshooting

| Σύμπτωμα | Πιθανή αιτία / Λύση |
|---|---|
| Δεν ανάβει καθόλου | Έλεγξε ότι ο `master_enable` είναι ON και ότι ο αισθητήρας νερού δεν είναι `unknown`. |
| Δεν ανάβει ενώ είσαι σπίτι | Βεβαιώσου ότι το `zone.home` είναι στις ζώνες του χρήστη (πλέον υποστηρίζεται). |
| Ανάβει και δεν σβήνει | Έλεγξε τον αισθητήρα νερού· αν κολλάει σε χαμηλή τιμή, σβήνει με τον μέγιστο χρόνο. |
| Το Boost δεν κάνει τίποτα | Πρέπει ο γενικός διακόπτης να είναι ON και ο θερμοσίφωνας σβηστός. |
| «Already heating» στο trace | Ο θερμοσίφωνας ήταν ήδη ON — φυσιολογικό. |

**Έλεγχος:** Settings → Automations → το automation → **Traces**.

---

## Δομή / Structure

```
custom_components/gsw_hotwater/
  __init__.py            # installs the blueprint on startup
  installer.py           # pure-python blueprint installer (tested)
  const.py
  config_flow.py         # UI setup (required so HA loads the integration)
  strings.json           # UI text (English)
  translations/          # el.json, en.json
  manifest.json
  version.json
  blueprints/
    gsw_smart_hot_water.yaml   # the main automation blueprint
    gsw_boiler_safety.yaml     # independent safety watchdog blueprint
  translations/
blueprints/automation/gsw_hotwater/   # installed location (created at runtime)
helpers/gsw_hotwater.yaml             # optional helper entities (package)
tests/
  run_tests.py           # structure / inputs / jinja / installer / manifest
  test_logic.py          # functional logic simulation
```

### Τεστ / Tests

```bash
pip install pyyaml jinja2
python3 tests/run_tests.py
python3 tests/test_logic.py
```

---

## Άδεια / License

Personal, non-commercial use only. **No commercial use, no modification, no
redistribution** without written permission. See [LICENSE](LICENSE).

© 2025 Iakovos Venieris — Greece Sky and Weather

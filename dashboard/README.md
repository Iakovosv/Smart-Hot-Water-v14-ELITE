# 📊 GSW Smart Hot Water — Dashboard & Κάρτες

Έτοιμα Lovelace αρχεία για τον **GSW Smart Hot Water ELITE**.
Όλα χρησιμοποιούν **μόνο built-in κάρτες** — δεν χρειάζεται HACS frontend.

---

## Περιεχόμενα φακέλου

```
dashboard/
├── README.md                        ← αυτό το αρχείο
├── gsw_hotwater_dashboard.yaml      ← ΠΛΗΡΕΣ dashboard (2 views)
├── gsw_hotwater_card.yaml           ← ΜΙΑ κάθετη κάρτα με τα πάντα
└── cards/                           ← ΞΕΧΩΡΙΣΤΕΣ κάρτες (copy-paste μία-μία)
    ├── 01-status-header.yaml
    ├── 02-gauges.yaml
    ├── 03-controls.yaml
    ├── 04-boost.yaml
    ├── 05-tiles-temps.yaml
    ├── 06-helpers.yaml
    ├── 07-consumption.yaml
    ├── 08-history.yaml
    ├── 09-consumption-graph.yaml
    ├── 10-automations.yaml
    ├── 11-conditional-heating.yaml      ← conditional + αντίστροφη μέτρηση
    ├── 12-conditional-countdown.yaml    ← conditional countdown (απλή)
    └── 13-conditional-time-bar.yaml     ← conditional μπάρα υπολοίπου
```

---

## 1) Πλήρες dashboard — `gsw_hotwater_dashboard.yaml`

Δύο views:

| View | Τι δείχνει |
|---|---|
| **Κατάσταση** | Επικεφαλίδα, gauges (νερό/συλλέκτης/πρόοδος/έξω), χειριστήρια, boost, βοηθητικές οντότητες, κατανάλωση, ιστορικό 24h, στατιστικά, αυτοματισμοί |
| **Ρυθμίσεις** | Αναφορά **όλων** των παραμέτρων: cold_threshold, targets, max times, solar, defrost, presence, χρήστες/ζώνες, ειδοποιήσεις, κανόνες ασφαλείας |

### Εγκατάσταση
1. **Settings → Dashboards → + Add dashboard** → δώσε όνομα → άνοιξέ το.
2. **Edit** (μολύβι, πάνω δεξιά) → **⋮** → **Raw configuration editor**.
3. Επικόλλησε **όλο** το περιεχόμενο του `gsw_hotwater_dashboard.yaml`.
4. **Save**.

---

## 2) Μία κάθετη κάρτα — `gsw_hotwater_card.yaml`

Μία **vertical-stack** με τα πάντα σε σειρά: header, gauges, χειριστήρια, boost,
expandable λίστα λεπτομερειών, ιστορικό. Ιδανική για να την ρίξεις σε
**υπάρχον** dashboard.

### Εγκατάσταση
Edit → **+ Add card** → **Manual** → επικόλλησε το περιεχόμενο → **Save**.

---

## 3) Ξεχωριστές κάρτες — `cards/`

Κάθε αρχείο είναι **ανεξάρτητη** κάρτα. Βάλε **όποια θέλεις**, με όποια σειρά
θέλεις. Όλες μπαίνουν με: Edit → **+ Add card** → **Manual** → επικόλλησε.

| # | Αρχείο | Τύπος | Τι κάνει |
|---|---|---|---|
| 01 | `01-status-header.yaml` | markdown | Επικεφαλίδα: κατάσταση λέβητα στα ελληνικά με emoji, θερμοκρασίες, πρόοδος, υπόλοιπο, λόγος |
| 02 | `02-gauges.yaml` | gauge ×3 | Ρολόγια: νερό (χρωματικό), συλλέκτης, πρόοδος |
| 03 | `03-controls.yaml` | entities | Ρελέ θερμοσίφωνα, master enable, μπλοκάρισμα, solar skip |
| 04 | `04-boost.yaml` | entities | Κουμπί boost + στόχος + λεπτά + λειτουργία |
| 05 | `05-tiles-temps.yaml` | grid tiles | Ίδια με 02 αλλά σε tiles — καλή για κινητό (διάλεξε **02 Ή 05**) |
| 06 | `06-helpers.yaml` | entities | Όλες οι βοηθητικές οντότητες (status EN/EL, χρόνος, λόγος) |
| 07 | `07-consumption.yaml` | entities | Ισχύς, cloud, τροφοδοσία Pi, uptime |
| 08 | `08-history.yaml` | history-graph | Γράφημα θερμοκρασιών 24h |
| 09 | `09-consumption-graph.yaml` | statistics-graph | Στατιστικά κατανάλωσης ανά ώρα |
| 10 | `10-automations.yaml` | entities | Κατάσταση των 2 αυτοματισμών (main + watchdog) |
| 11 | `11-conditional-heating.yaml` | conditional | **Εμφανίζεται μόνο όταν θερμαίνει** — live αντίστροφη μέτρηση mm:ss + μπάρα |
| 12 | `12-conditional-countdown.yaml` | conditional | Countdown ανά κατάσταση (Θέρμανση/Boost/Defrost) |
| 13 | `13-conditional-time-bar.yaml` | conditional | Μπάρα που **γεμίζει ανάποδα** + μεγάλο mm:ss |
| 14 | `14-progress-status-boost.yaml` | vertical-stack | **Όμορφη** εκδοχή: κεφαλίδα κατάστασης (εικονίδιο+χρώμα) + χρωματικό gauge προόδου + tiles (ρελέ/master/νερό/μπλοκάρισμα) + Boost |

> **Σημείωση:** τα `02` και `05` δείχνουν τα ίδια δεδομένα με διαφορετικό στυλ.
> Χρησιμοποίησε **ένα** από τα δύο.

---

## ⏳ Αντίστροφη μέτρηση (υπόλοιπος χρόνος)

Ο αυτοματισμός **αποφασίζει τον μέγιστο χρόνο** από την **εξωτερική
θερμοκρασία**:

| Συνθήκη | Μέγιστος χρόνος |
|---|---|
| `outdoor < cold_threshold` (κρύο) | `max_time_cold` (π.χ. 70 min) |
| αλλιώς (ήπιο) | `max_time_warm` (π.χ. 55 min) |
| Boost | `boost_minutes` (input_number) |

Μετά, **κάθε 30s** γράφει το **υπόλοιπο** στα προαιρετικά helpers:
- `input_number.gsw_time_left_minutes` — λεπτά που απομένουν (μετρά **αντίστροφα**)
- `input_number.gsw_time_left_pct` — το ίδιο ως % (για μπάρα)

Οι κάρτες **11 / 12 / 13** διαβάζουν αυτά + το `input_datetime.water_heater_on`
και δείχνουν **live mm:ss** (δεν περιμένουν το επόμενο 30s), μετράντας προς
τα κάτω. Όταν τελειώσει η θέρμανση, το υπόλοιπο γίνεται `0`.

### Προϋπόθεση
Στη φόρμα του blueprint, βάλε:
- **Time left minutes** → `input_number.gsw_time_left_minutes`
- **Time left percent** → `input_number.gsw_time_left_pct` *(προαιρετικό, για τις μπάρες)*

Αν τα αφήσεις **κενά**, ο αυτοματισμός δουλεύει κανονικά — απλώς οι
conditional κάρτες δεν θα έχουν τιμή να δείξουν.

### Πότε εμφανίζονται
Μόνο όταν `input_select.gsw_hotwater_status` ∈ `Heating` / `Boost` / `Defrost`.
Τις υπόλοιπες ώρες **εξαφανίζονται** — καθαρό dashboard.

---

## 🛠️ Troubleshooting

### «Entity not found» / «unknown»
Οι παρακάτω οντότητες είναι **προαιρετικές** και πρέπει να υπάρχουν για να
δείξουν τιμή. Δημιούργησέ τις **μία φορά**:

1. Αντίγραψε το [`helpers/gsw_hotwater.yaml`](../helpers/gsw_hotwater.yaml) στο
   `<config>/packages/gsw_hotwater.yaml`.
2. Στο `configuration.yaml` πρόσθεσε:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
3. Developer Tools → YAML → **Check configuration** → **Reload all**.

Ή φτιάξ’ τες χειροκίνητα: Settings → Devices & Services → **Helpers**.
Οι οντότητες-κλειδιά:

| Helper | Τύπος | Γιατί |
|---|---|---|
| `gsw_time_left_minutes` | input_number (0-180) | Αντίστροφη μέτρηση |
| `gsw_time_left_pct` | input_number (0-100) | Μπάρα υπολοίπου |
| `gsw_last_reason` | input_text | Λόγος τελευταίας ενέργειας |
| `gsw_solar_skip` | input_boolean | Παράλειψη ηλιακού |
| `gsw_boiler_status` | input_select (Θέρμανση/Αναμονή/Έτοιμο) | Ελληνική κατάσταση |

### Το `gsw_time_left_minutes` δείχνει `unknown`
Φυσιολογικό **πριν** τρέξει θέρμανση: ο αυτοματισμός το γράφει μόνο όταν
θερμαίνει. Επίσης, στη φόρμα του blueprint πρέπει να έχεις βάλει
**Time left minutes** → `input_number.gsw_time_left_minutes`.

### «Template error: as_timestamp got invalid input '00:00:00'»
Το διορθώσαμε. Οι κάρτες **δεν** χρησιμοποιούν πλέον `as_timestamp` — δείχνουν
το υπόλοιπο που ήδη μετρά ο αυτοματισμός. Αν το είδες σε **παλιά** έκδοση,
ξανα-επικόλλησε τις κάρτες από το `cards/`.

### Το «Έξυπνος έλεγχος (master)» / ρελέ δείχνουν Off
Αυτό είναι **σωστό** όταν δεν θερμαίνει. Ο master πρέπει να είναι **On** για να
δουλέψει ο αυτοματισμός — άναψέ τον από την κάρτα 03.

---

## Τι κάνει το κάθε στοιχείο (οντότητες)

| Οντότητα | Σημασία | Πού εμφανίζεται |
|---|---|---|
| `input_select.gsw_hotwater_status` | Κατάσταση λέβητα (EN) | 01, 06 |
| `input_select.gsw_boiler_status` | Κατάσταση λέβητα (EL) | 06 |
| `input_number.gsw_hotwater_progress` | Πρόοδος θέρμανσης % | 01, 02, 05, 06 |
| `input_number.gsw_time_left_minutes` | Υπόλοιπο χρόνου (min) * | 01, 06, 11, 12, 13 |
| `input_number.gsw_time_left_pct` | Υπόλοιπο χρόνου % * | 06, 11, 13 |
| `input_datetime.water_heater_on` | Τελευταία ενεργοποίηση | 06 |
| `input_text.gsw_last_reason` | Λόγος τελευταίας ενέργειας * | 01, 06 |
| `sensor.temperature_esp_temperature_esp` | Νερό χρήσης °C | 01, 02, 05, 08 |
| `sensor.temperature_esp_outside_temperature` | Συλλέκτης ηλιακού °C | 01, 02, 05, 08 |
| `sensor.gw2000a_outdoor_temperature` | Εξωτερική °C | 01, 05, 08 |
| `switch.smart_power_outlet_1` | Ρελέ θερμοσίφωνα | 03 |
| `input_boolean.gsw_smart_hotwater_enable` | Master enable | 03 |
| `input_boolean.water_temperature_check` | Μπλοκάρισμα θέρμανσης | 03 |
| `input_boolean.gsw_solar_skip` | Παράλειψη λόγω ηλιακού | 03 |
| `input_button.gsw_hotwater_boost` | Κουμπί άμεσου boost | 04 |
| `input_number.gsw_boost_target_temp` | Στόχος boost | 04 |
| `input_number.gsw_boost_minutes` | Λεπτά boost | 04 |
| `input_select.gsw_boost_mode` | Λειτουργία boost | 04 |
| `sensor.water_heater_cloud_power` | Ισχύς θερμοσίφωνα | 07, 09 |
| `switch.water_heater_cloud` | Cloud έλεγχος | 07 |
| `binary_sensor.rpi_power_status` | Τροφοδοσία Raspberry Pi | 07 |
| `sensor.uptime_4` | Uptime | 07 |
| `automation.gsw_smart_hot_water_v22_elite` | Κύριος αυτοματισμός | 10 |
| `automation.gsw_boiler_safety` | Watchdog ασφαλείας | 10 |

`*` = **προαιρετικό**. Αν δεν το έχεις, σβήσε τις γραμμές του.

---

## Κατάσταση λέβητα — χρώματα & emoji

| Τιμή | Emoji | Σημασία |
|---|---|---|
| `Heating` | 🔥 | Θέρμανση σε εξέλιξη |
| `Target reached` | ✅ | Έφτασε τον στόχο |
| `Idle` | ⏸️ | Σε αναμονή |
| `Blocked` | ⛔ | Μπλοκαρισμένο (νερό ζεστό / αισθητήρας / χειροκίνητο) |
| `Solar skip` | ☀️ | Παράλειψη λόγω ηλιακού |
| `Defrost` | ❄️ | Defrost ηλιακού |
| `Boost` | ⚡ | Χειροκίνητο boost |

---

## Προσαρμογή

- **Διαφορετικά entity ids;** Άλλαξέ τα στο YAML (Find & Replace).
- **Πιο όμορφα γραφήματα;** Αν έχεις `mini-graph-card` / `apexcharts-card` από
  HACS, αντικατέστησε την κάρτα 08 με αυτές.
- **Θέμα;** Τα χρώματα των tiles (05) αλλάζουν εύκολα (`color: red/green/...`).

---

## Έλεγχος εγκυρότητας

Το `tests/run_tests.py` επαληθεύει **αυτόματα** ότι:
- όλα τα YAML αρχεία είναι έγκυρα,
- χρησιμοποιούν **μόνο built-in κάρτες**,
- όλα τα Jinja templates περνούν.

Τρέξε: `python3 tests/run_tests.py`

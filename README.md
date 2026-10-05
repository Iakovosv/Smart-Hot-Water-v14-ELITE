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

### ❓ «Έκανα restart αλλά το blueprint δεν εμφανίζεται»

Το blueprint **δεν** έρχεται από μόνο του με το restart — το τοποθετεί ο
**installer της ενσωμάτωσης**. Έλεγξε με τη σειρά:

1. **Υπάρχει η ενσωμάτωση;** *Settings → Devices & Services* — ψάξε
   **GSW Smart Hot Water**. Αν **δεν** υπάρχει, πρόσθεσέ την:
   **Add Integration → GSW Smart Hot Water → Submit**. Αυτό αντιγράφει **και τα
   δύο** blueprints και μετά κάνε **Developer Tools → YAML → Reload Automations**.
   (Αν δεν υπάρχει ούτε στο HACS, κατέβασέ την από HACS πρώτα — Μέθοδος A.)
2. **Υπάρχουν τα αρχεία;** Με File Editor / Studio Code Server δες τον φάκελο
   `<config>/blueprints/automation/gsw_hotwater/` — πρέπει να έχει
   `gsw_smart_hot_water.yaml` και `gsw_boiler_safety.yaml`.
3. **Έλεγξε το log:** *Settings → System → Logs* — φίλτραρε `gsw_hotwater`.
   Αν δεις `blueprint install failed`, το integration δεν μπόρεσε να γράψει
   (συνήθως δικαιώματα).
4. **Κάνε refresh τη σελίδα Blueprints** (Ctrl+F5) — το μενού μερικές φορές
   κρατά cache.
5. **Fallback χωρίς integration** — *Settings → Automations & Scenes →
   Blueprints → **Import Blueprint*** και δώσε ένα-ένα τα raw URL:
   - `https://raw.githubusercontent.com/Iakovosv/Smart-Hot-Water-v14-ELITE/main/custom_components/gsw_hotwater/blueprints/gsw_smart_hot_water.yaml`
   - `https://raw.githubusercontent.com/Iakovosv/Smart-Hot-Water-v14-ELITE/main/custom_components/gsw_hotwater/blueprints/gsw_boiler_safety.yaml`

   Ή αντίγραψε τα αρχεία χειροκίνητα στον φάκελο του βήματος 2.

> ℹ️ Αν εισάγεις με «Import Blueprint», το HA το αποθηκεύει με δικό του όνομα
> αρχείου (π.χ. `gsw_hotwater/gsw_smart_hot_water.yaml`) — θα το δεις στη λίστα
> **Blueprints** με το όνομα **🔥 GSW: Smart Hot Water ELITE**.

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
| `target_temp_cold` / `target_temp_warm` | Αυτόματο όριο «ανάβει κάτω από» κρύου / ήπιου | `58` / `50 °C` |
| `max_time_cold` / `max_time_warm` | Μέγιστος χρόνος κρύου / ήπιου | `70` / `55 min` |
| `schedule_N_enabled/time/temp` | Πρόγραμμα N (1-6) ενεργό/ώρα/**όριο ανάβει κάτω από** | off / 06:00 / 0=auto |
| `solar_mode` | Λειτουργία ηλιακού | `off` |
| `solar_flag` | Boolean παράλειψης ηλιακού | κενό |
| `solar_temp_sensor` | Αισθητήρας θερμοκρασίας συλλέκτη/panel (προαιρετική 2η συνθήκη) | κενό |
| `solar_temp_threshold` | Όριο συλλέκτη/panel (παράλειψη όταν είναι **πάνω** από αυτό) | `45 °C` |
| `max_water_temp` | **Ζεστό νερό χρήσης (μποιλερ): «μην ανάψει»** αν είναι ≥ | `75 °C` |
| `defrost_enable` | Ενεργοποίηση defrost | `false` |
| `defrost_water_temp` / `defrost_outdoor_temp` | Όρια defrost | `4` / `2 °C` |
| `defrost_start_time` / `defrost_end_time` | Παράθυρο defrost | `03:00` / `05:00` |
| `defrost_check_interval` | Διάρκεια defrost | `5 min` |
| `boost_button` | Κουμπί boost | `input_button.gsw_hotwater_boost` |
| `boost_target_temp` / `boost_minutes` | Στόχος / λεπτά boost | helpers |
| `status_entity` | Helper κατάστασης | `input_select.gsw_hotwater_status` |
| `progress_entity` | Helper προόδου | `input_number.gsw_hotwater_progress` |
| `last_on_entity` | Helper τελευταίας ενεργοποίησης | `input_datetime.water_heater_on` |
| `notify_target` | Συσκευή ειδοποίησης (προαιρετική, `notify.*`) | κενό |
| `last_reason` | Helper λόγου (`input_text`, προαιρετικό) | κενό |
| `boiler_status_entity` | Helper κατάστασης Ελληνικά (`input_select`) | κενό |
| `time_left_entity` | Helper υπολοίπου λεπτών (`input_number`) | κενό |
| `time_left_pct_entity` | Helper υπολοίπου % (`input_number`) | κενό |

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
| `notify_target` | Δεν στέλνεται καμία ειδοποίηση (όλα δουλεύουν κανονικά). |
| `last_reason` | Δεν καταγράφεται ο λόγος της τελευταίας ενέργειας. |
| `boiler_status_entity` | Δεν ενημερώνεται η ελληνική κατάσταση λέβητα. |
| `time_left_entity` / `time_left_pct_entity` | Δεν ενημερώνεται η αντίστροφη μέτρηση. |

> ⚠️ **Προσοχή:** αν αφήσεις κενό `boiler_switch` ή `water_temp_sensor`, ο
> αυτοματισμός **δεν κάνει τίποτα** (σωστά — δεν θερμαίνει «στα τυφλά»).
> Αν έχεις `require_presence = true` με **κενές ζώνες**, δεν θερμαίνει ποτέ.
> Αν δεν θέλεις έλεγχο τοποθεσίας, βάλε `require_presence = false`.

### Θερμοκρασία: απλό όριο «ανάβει κάτω από»

Δεν χρειάζεται αφαίρεση/hysteresis. Δηλώνεις **απλά**:

- **Ώρα** που θέλεις να ελέγξει (`schedule_N_time`, π.χ. `16:03`)
- **Θερμοκρασία νερού χρήσης** (`schedule_N_temp`, π.χ. `45`)

Και ισχύει: **αν το νερό είναι κάτω από 45°C → ανάβει. Αν είναι 45°C ή πάνω →
δεν ανάβει**, ακόμη κι αν ήρθε η ώρα.

- `schedule_N_temp = 0` → **αυτόματο**: χρησιμοποιεί `target_temp_cold`
  (κρύες μέρες) ή `target_temp_warm` (ήπιες), με βάση το `cold_threshold`.

### Ζεστό νερό χρήσης — «μην ανάψει αν είναι ήδη ζεστό»

Το `max_water_temp` (default **75°C**) χρησιμοποιεί τον **αισθητήρα νερού του
μποιλερ (ζεστό νερό χρήσης — ΟΧΙ τον συλλέκτη)**:

> Αν το νερό είναι **ίσο ή πάνω** από αυτό, η θέρμανση **δεν ξεκινά ποτέ** —
> σε **προγράμματα**, **Boost** και **Defrost**.

- Στα προγράμματα: λόγος `sched N: max_temp`.
- Στο Boost/Defrost: ο αυτοματισμός **δεν ανάβει** τον θερμοσίφωνα.
- `0` → απενεργοποιεί το όριο (δεν συνιστάται).

### Δεύτερη (προαιρετική) συνθήκη: θερμοκρασία panel/συλλέκτη

Μπορείς να προσθέσεις **προαιρετικά** δεύτερη μεταβλητή — τη **θερμοκρασία
panel/συλλέκτη** — ώστε να **μην ανάβει** όταν ο ήλιος θα ζεστάνει το νερό.

| Πεδίο | Τι ορίζεις |
|---|---|
| `solar_temp_sensor` | Αισθητήρας θερμοκρασίας panel (κενό = απενεργοποιημένο) |
| `solar_temp_threshold` | Ελάχιστη θερμοκρασία panel (π.χ. `45`) |
| `solar_mode` | `temperature` (ή `both` αν θέλεις και το flag) |

**Κανόνας:** παράλειψη θέρμανσης όταν `panel > solar_temp_threshold`.

**Παράδειγμα (όπως το ζήτησες):**
- Όριο νερού `45`, όριο panel `45`.
- Panel **50°C** (πάνω από 45) και νερό **40°C** → **δεν ανάβει** (θα το
  ζεστάνει ο ήλιος) → λόγος `solar_skip`.
- Panel **44°C** (όχι πάνω από 45) και νερό **40°C** → **ανάβει** → `heating`.
- Panel **45°C** ακριβώς → **δεν** παραλείπεται (χρειάζεται **πάνω** από 45).

> Αν αφήσεις κενό το `solar_temp_sensor`, ο έλεγχος panel **απενεργοποιείται**
> και ο θερμοσίφωνας θερμαίνει κανονικά (δεν κολλάει ποτέ).

### Πώς δουλεύουν τα προγράμματα / How schedules work

- Υπάρχουν **6 ανεξάρτητα** προγράμματα. Ενεργοποίησε όποιον συνδυασμό θέλεις
  (κανένα, ένα, πολλά ή όλα) — δεν επηρεάζουν το ένα το άλλο.
- Η ώρα είναι **ακριβής στο λεπτό** (π.χ. `16:03`). Ο αυτοματισμός έχει
  **ακριβή trigger ώρας** (`platform: time`) — **όχι polling**. Αναβοσβήνει
  ακριβώς εκείνη τη στιγμή.
- **Δεν υπάρχει επανάληψη:** αν κάτι πάει στραβά και **χαθεί** εκείνη η στιγμή
  (π.χ. restart του HA), **δεν ξαναπροσπαθεί**. Ξεκινά ξανά μόνο σε **επόμενο
  ενεργό πρόγραμμα** (μεταγενέστερη ώρα) **και** εφόσον η θερμοκρασία πληροί
  τις προϋποθέσεις (νερό **κάτω από** το όριο) ή με **Boost**.
- Το **defrost** έχει επίσης **ακριβή ώρα** (`defrost_start_time`). Το παράθυρο
  `defrost_start_time`–`defrost_end_time` περιορίζει μόνο τη **διάρκεια**.
- Το `temp = 0` σημαίνει **αυτόματο** (στόχος κρύου/ήπιου καιρού ανάλογα με
  την εξωτερική θερμοκρασία).
- Αν **δεν** ενεργοποιήσεις κανένα πρόγραμμα, ο θερμοσίφωνας ανάβει **μόνο**
  με το κουμπί Boost.

### Ειδοποιήσεις & λόγος ενέργειας (προαιρετικά)

- **`notify_target`** — διάλεξε από το UI συσκευή (π.χ. `notify.iphone_iakovos`).
  Θα λάβεις μήνυμα όταν **ολοκληρωθεί** προγραμματισμένη θέρμανση, **Boost** ή
  **Defrost**. Αν το αφήσεις **κενό**, δεν στέλνεται τίποτα.
- **`last_reason`** — διάλεξε ένα `input_text` helper (π.χ.
  `input_text.gsw_last_reason`, υπάρχει στο `helpers/gsw_hotwater.yaml`).
  Καταγράφει **γιατί** έγινε η τελευταία ενέργεια, π.χ.:
  - `sched 2: heating` — θέρμανε το πρόγραμμα 2
  - `sched 1: temp_ok` — το νερό ήταν ήδη στο/πάνω από το όριο (δεν χρειάστηκε)
  - `sched 3: solar_skip` — παράλειψη λόγω ηλιακού
  - `sched 4: no_presence` — δεν ήταν κάποιος στο σπίτι
  - `sched 5: sensor_bad` / `blocked_check` / `max_temp` / `already_on` / `master_off`
  - `defrost` — έγινε defrost

### Κατάσταση λέβητα & αντίστροφη μέτρηση (προαιρετικά)

- **`boiler_status_entity`** — `input_select` με ελληνικές ενδείξεις
  **`Θέρμανση` / `Αναμονή` / `Έτοιμο`**:
  - `Θέρμανση` → όταν ο λέβητας ανάβει (πρόγραμμα ή boost)
  - `Έτοιμο` → όταν το νερό έφτασε/ξεπέρασε τον στόχο
  - `Αναμονή` → σε κάθε άλλη περίπτωση (μπλοκαρίσματα, παράλειψη, τέλος χρόνου)
- **`time_left_entity`** (`input_number`, λεπτά) και **`time_left_pct_entity`**
  (`input_number`, %) — **αντίστροφη μέτρηση** του χρόνου που απομένει, με βάση
  τον **μέγιστο χρόνο** του τρέχοντος καιρού:
  - κρύο (`< cold_threshold`) → `max_time_cold`
  - ήπιο → `max_time_warm`
  - Γεμίζει κάθε 30 δευτ. και **μηδενίζεται** όταν ολοκληρωθεί η θέρμανση.
  - Το `time_left_pct_entity` είναι ιδανικό για progress bar που **αδειάζει**
    (αντίστροφο).

### Καταστάσεις / Status values

Ο `input_select` πρέπει να έχει **ακριβώς** αυτές τις επιλογές (εμφανίζονται
ως έχουν· η ελληνική σημασία σε παρένθεση):

`Idle` (Σε αναμονή) · `Heating` (Θέρμανση) · `Target reached` (Στόχος) ·
`Blocked` (Μπλοκαρισμένο) · `Solar skip` (Παράλειψη ηλιακού) · `Defrost` ·
`Boost`

---

## Πώς λειτουργεί / How it works

- **Ακριβής ώρα, όχι polling.** Τα **6 προγράμματα** και το **defrost**
  ενεργοποιούνται με trigger `platform: time` στην **ακριβή** ώρα που όρισες.
  Αν χαθεί η στιγμή (π.χ. restart του HA), **δεν** ξαναπροσπαθεί.
- **Boost** — trigger `platform: state` στο κουμπί: θερμαίνει **άμεσα**.
- **Όσο θερμαίνει** (πρόγραμμα ή boost) ο βρόχος ελέγχει κάθε **30 δευτ.** και
  ενημερώνει **πρόοδο %**, **υπόλοιπο λεπτά** και **υπόλοιπο %**.

**Σειρά ελέγχων πριν ανάψει (πρόγραμμα):**
γενικός διακόπτης → παρουσία → αισθητήρας διαθέσιμος → `water_temperature_check`
off → **όχι «ήδη ζεστό» (`max_water_temp`)** → όχι παράλειψη ηλιακού → **νερό
κάτω από το όριο** → **ανάβει** → σταματά σε στόχο / μέγιστο χρόνο / μπλοκάρισμα
/ απώλεια αισθητήρα → **σβήνει**.

**Στο Boost:** γενικός διακόπτης → όχι «ήδη αναμμένο» → αισθητήρας διαθέσιμος →
`water_temperature_check` off → **όχι «ήδη ζεστό»** → ανάβει.

**Στο Defrost:** ενεργό + σωστό trigger → μέσα στο παράθυρο ώρας → νερό ≤
`defrost_water_temp` → εξωτερική ≤ `defrost_outdoor_temp` → `water_temperature_check`
off → **όχι «ήδη ζεστό»** → όχι αναμμένο → ανάβει.

Το `mode: single` εγγυάται ότι μια εκτέλεση **δεν ακυρώνεται** από επόμενες ενεργοποιήσεις.

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

## Ιστορικό εκδόσεων / Changelog
### v1.10.2
- **Ίδια διόρθωση και στο `gsw_boiler_safety.yaml`**: `status_entity` και
  `boiler_switch` περνούν πλέον από ασφαλείς μεταβλητές (`status_target`,
  `boiler_switch_target`) αντί για απευθείας `entity_id`.
- **Exhaustive έλεγχοι «από την αρχή ως το τέλος»**: 512 συνδυασμοί πυλών
  απόφασης + 256 συνδυασμοί defrost + presence/solar με κενά/γεμάτα
  προαιρετικά → **0 mismatches**. Το regression test σαρώνει τώρα **και τα δύο**
  blueprints για κενά-default inputs σε `entity_id`/`service`/`at`.

### v1.10.1
- **Διόρθωση αποθήκευσης blueprint**: τα προαιρετικά πεδία (κενό default) δεν
  περνούν πια αυτούσια ως `entity_id`. Ήταν η αιτία του σφάλματος
  `Message malformed: expected 'all' or 'none' at ... target.entity_id` όταν
  άφηνες κενά `boiler_status_entity`, `last_reason`, `time_left_entity`,
  `time_left_pct_entity` (και ασφαλές για `boiler_switch`, `status_entity`,
  `progress_entity`, `last_on_entity`). Τώρα τα κενά γίνονται `none`.
- Regression test `test_optional_entity_targets`.


### v1.10.0
- **Ζεστό νερό χρήσης — «μην ανάψει αν είναι ήδη ζεστό»**: νέο `max_water_temp`
  (default `75 °C`, `0` = off) στον αισθητήρα νερού **χρήσης/μποιλερ** (όχι
  συλλέκτη). Ισχύει σε **προγράμματα** (`sched N: max_temp`), **Boost** και
  **Defrost**.
- **Ομαδοποίηση θερμοκρασιών** στο UI: cold → warm → collector threshold → DHW cap.
- Tests: νέο template `MAX_TEMP`· **256 gate + 192 αριθμητικοί συνδυασμοί**, 0 mismatches.

### v1.9.1
- **Brand assets**: `icon` / `logo` (+ dark, + @2x) στο
  `custom_components/gsw_hotwater/brand/` (HA 2026.3+) **και** στη ρίζα `brand/`.
  Παράγονται από `tools/make_icon.py`.

### v1.9.0
- **Απλό όριο «ανάβει κάτω από»**: το `schedule_N_temp` είναι threshold —
  νερό **<** τιμή → ανάβει· νερό **≥** τιμή → δεν ανάβει (και `0` = auto cold/warm).
- **Αφαιρέθηκε το `hysteresis`** και η αφαίρεση `target − hysteresis`.
- **Ηλιακός**: αυστηρό `>` (panel **πάνω** από το όριο), προτεραιότητα `solar_skip`.
- Λόγος `target_ok` → **`temp_ok`**.

### v1.8.1
- Διόρθωση `source_url` στο raw YAML· ενότητα «το blueprint δεν εμφανίζεται».

### v1.8.0
- **Ελληνική κατάσταση λέβητα** (`Θέρμανση` / `Αναμονή` / `Έτοιμο`) και
  **αντίστροφη μέτρηση** χρόνου (`time_left_entity`, `time_left_pct_entity`).

### v1.7.0
- Προαιρετική **ειδοποίηση** (`notify_target`) και **λόγος τελευταίας ενέργειας**
  (`last_reason`).

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
  brand/                 # icon.png / logo.png (+ dark, + @2x)
  translations/
brand/                   # same assets at repo root (for HACS / README)
tools/make_icon.py       # regenerates all brand assets (Pillow)
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

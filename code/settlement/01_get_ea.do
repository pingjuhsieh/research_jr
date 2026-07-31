clear all
set more off
* Run from ICMID PingJu project root (folder that contains README.md).
capture confirm file "README.md"
if _rc {
    di as error "cd to ICMID PingJu project root before running this do-file."
    exit 601
}

* ==========================================
* 1. Fetch Societies & Create Master Name Dictionary (incl. alt names & pref name)
* ==========================================
local soc_url "https://raw.githubusercontent.com/D-PLACE/dplace-dataset-ea/6f38b2508711df84033ec13f4aef940572239ac2/raw/societies.csv"
copy "`soc_url'" "./data/ea/ea_societies.csv", replace
import delimited "./data/ea/ea_societies.csv", clear

rename id murdock_id

* Extract primary name (name0) from "orig_name_and_id_in_this_dataset"
gen name0 = substr(orig_name_and_id_in_this_dataset, 1, strpos(orig_name_and_id_in_this_dataset, "(") - 1)
replace name0 = orig_name_and_id_in_this_dataset if strpos(orig_name_and_id_in_this_dataset, "(") == 0

* 🌟 NEW: Append "pref_name_for_society" into the comma-separated alt_names_by_society
* This ensures the preferred name is also treated as a possible alternative name
replace alt_names_by_society = alt_names_by_society + "," + pref_name_for_society if alt_names_by_society != "" & pref_name_for_society != ""
replace alt_names_by_society = pref_name_for_society if alt_names_by_society == "" & pref_name_for_society != ""

* Split alternative names (which now includes pref_name) by comma into name1, name2, name3...
split alt_names_by_society, parse(",") gen(name)

* Keep only ID and all name variations
keep murdock_id name*

* Reshape from wide to long (creates a new row for each name variation)
reshape long name, i(murdock_id) j(name_idx)

rename name ethnic_name
drop if ethnic_name == ""

* Clean strings: uppercase and remove spaces
replace ethnic_name = strtrim(strupper(ethnic_name))

* Drop exact duplicate names to prevent many-to-many merge errors later
duplicates drop ethnic_name, force
save "./data/ea/ea_societies_long.dta", replace


* ==========================================
* 2. Fetch Attributes (v30) - KEEP MISSING VALUES FOR DIAGNOSTICS
* ==========================================
local data_url "https://raw.githubusercontent.com/D-PLACE/dplace-dataset-ea/6f38b2508711df84033ec13f4aef940572239ac2/raw/data.csv"
copy "`data_url'" "./data/ea/ea_raw_data.csv", replace
import delimited "./data/ea/ea_raw_data.csv", clear rowrange(2:) varnames(1)

keep if var_id == "EA030"
rename soc_id murdock_id
rename code v30
destring v30, replace force

* IMPORTANT: We DO NOT drop missing or 9 here so we can diagnose them in Step 5.

gen nomad = 0
replace nomad = 1 if v30 == 1 | v30 == 2
gen settler = 0
replace settler = 1 if v30 >= 3 & v30 <= 8

keep murdock_id nomad settler v30
save "./data/ea/ea_attributes_only.dta", replace


* ==========================================
* 3. Combine Dictionary with Attributes
* ==========================================
use "./data/ea/ea_societies_long.dta", clear
merge m:1 murdock_id using "./data/ea/ea_attributes_only.dta", keep(match) nogen
save "./data/ea/murdock_attributes_with_all_names.dta", replace


* ==========================================
* 4. Match Grid Map with the Master Name Dictionary
* ==========================================
use "./data/ea/pure_grid_to_murdock.dta", clear
rename NAME ethnic_name
replace ethnic_name = strtrim(strupper(ethnic_name))

* Perform the merge but KEEP the _merge variable for diagnostics
merge m:1 ethnic_name using "./data/ea/murdock_attributes_with_all_names.dta", keep(master match)


* ==========================================
* 5. DIAGNOSTICS: Export the CSV files for debugging
* ==========================================
* Reason 1: Non-match (Name not found in dictionary)
preserve
keep if _merge == 1
bysort ethnic_name: gen missing_grid_count = _N
duplicates drop ethnic_name, force
keep ethnic_name missing_grid_count
gsort -missing_grid_count
export delimited using "./data/ea/Reason1_non-match.csv", replace
restore

* Reason 2: v30_NA (Matched, but v30 is missing or 9)
preserve
keep if _merge == 3
keep if v30 == . | v30 == 9
bysort ethnic_name: gen missing_grid_count = _N
duplicates drop ethnic_name, force
keep ethnic_name v30 missing_grid_count
gsort -missing_grid_count
export delimited using "./data/ea/Reason2_v30_NA.csv", replace
restore


* ==========================================
* 6. Clean up & Calculate Mixed Settlement
* ==========================================
* Now we can safely drop the missing data to build the final dataset
drop if _merge == 1
drop if v30 == . | v30 == 9
drop _merge

replace nomad = 0 if nomad == .
replace settler = 0 if settler == .

* Aggregate features within each grid cell
bysort grid_id: egen total_nomads = sum(nomad)
bysort grid_id: egen total_settlers = sum(settler)

* Define settlement type
gen settlement_type = .
replace settlement_type = 1 if total_settlers > 0 & total_nomads == 0  // Green: Settlers only
replace settlement_type = 2 if total_nomads > 0 & total_settlers == 0  // Blue: Nomads only
replace settlement_type = 3 if total_nomads > 0 & total_settlers > 0   // Red: Mixed settlement

label define set_lbl 1 "Settlers only" 2 "Nomads only" 3 "Mixed settlement"
label values settlement_type set_lbl

* Generate final dummy variable
gen mixed_settlement = 0
replace mixed_settlement = 1 if settlement_type == 3

* Collapse to grid level (one row per grid_id)
keep grid_id longitude latitude total_nomads total_settlers settlement_type mixed_settlement
duplicates drop grid_id, force

* Save final replicated dataset
save "./data/ea/my_own_murdock_grid_settlement_with_altnames.dta", replace

di "==========================================================="
di "

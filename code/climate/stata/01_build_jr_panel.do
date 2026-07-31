* ==============================================================================
* Build analysis panel: Eberle replication + JR (1997-2014)
* ==============================================================================
* JR is keyed on Eberle `cell` (from r/01_overlay_jr_on_eberle_cells.R).
* ==============================================================================

clear all
set more off

* Run from ICMID PingJu project root (folder that contains README.md).
capture confirm file "README.md"
if _rc {
    di as error "cd to ICMID PingJu project root before running this do-file."
    exit 601
}
global root     "`c(pwd)'"
global clim     "$root/code/climate"
global clim_out "$root/output/climate"
global eberle   "$root/../Replication_Heat_and_Hate_ReStat_Data"

use "$eberle/source/final_cell_year.dta", clear
keep if inrange(year, 1997, 2014)

merge m:1 cell using "$clim_out/panels/eberle_cell_jr.dta", ///
    keepusing(cross_group_jr n_jr_groups) keep(master match) nogen
replace cross_group_jr = 0 if missing(cross_group_jr)
replace n_jr_groups    = 0 if missing(n_jr_groups)

* Interaction terms
foreach v in T_mixD T_polarization T_jr T_mixD_jr T_njr T_mixD_njr log_njr T_lognjr T_mixD_lognjr {
    cap drop `v'
}
gen double T_mixD          = T * mixD
gen double T_polarization  = T * polarization
gen double T_jr            = T * cross_group_jr
gen double T_mixD_jr       = T * mixD * cross_group_jr
gen double T_njr           = T * n_jr_groups
gen double T_mixD_njr      = T * mixD * n_jr_groups
gen double log_njr         = ln(1 + n_jr_groups)
gen double T_lognjr        = T * log_njr
gen double T_mixD_lognjr   = T * mixD * log_njr

label var conflictD      "ACLED incident (Eberle: battles, riots, VAC)"
label var mixD           "GREG + Murdock mixed settlement (mix2D)"
label var cross_group_jr "Cross-group JR homeland overlaps cell"
label var n_jr_groups    "Count of cross-group JR groups in cell"

save "$clim_out/panels/eberle_jr_panel.dta", replace

qui count
local nobs = r(N)
bysort cell: gen byte _tag = (_n == 1)
qui count if _tag
local ncell = r(N)
drop _tag
di "Wrote eberle_jr_panel.dta | obs: `nobs' | cells: `ncell'"

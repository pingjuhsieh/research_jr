clear all
set more off
* Run from ICMID PingJu project root (folder that contains README.md).
capture confirm file "README.md"
if _rc {
    di as error "cd to ICMID PingJu project root before running this do-file."
    exit 601
}

* ==============================================================================
* Step 3: Descriptive statistics — cross-group JR share by settlement type
* ==============================================================================
* Prerequisite:
*   1. step 1 get ea.do          → my_own_murdock_grid_settlement_with_altnames.dta
*   2. export_cross_group_homelands.py + step2_overlay_jr_on_grid.R
*      → grid_cross_group_jr.dta
* ==============================================================================

use "./data/ea/my_own_murdock_grid_settlement_with_altnames.dta", clear

merge 1:1 grid_id using "./data/ea/grid_cross_group_jr.dta", nogen

replace cross_group_jr = 0 if missing(cross_group_jr)
replace n_jr_groups    = 0 if missing(n_jr_groups)

label variable settlement_type "Settlement type (EA v30)"
label variable cross_group_jr  "Cell intersects a cross-group JR homeland"
label variable n_jr_groups     "Distinct JR groups in cell"

label define set_lbl ///
    1 "Settlers only" ///
    2 "Nomads only" ///
    3 "Mixed settlement"
label values settlement_type set_lbl

* ── Summary table by settlement type (three main categories only) ────────────
preserve
keep if inlist(settlement_type, 1, 2, 3)

collapse ///
    (count) n_cells = grid_id ///
    (sum)   n_cross_group_jr = cross_group_jr ///
    (mean)  share_cross_group_jr = cross_group_jr, ///
    by(settlement_type)

label values settlement_type set_lbl
list settlement_type n_cells n_cross_group_jr share_cross_group_jr, clean noobs

export delimited using "./output/settlement/jr_share_by_settlement_type.csv", replace
restore

* ── Print readable summary ───────────────────────────────────────────────────
di ""
di "================================================================"
di " Cross-group JR share by settlement type"
di "================================================================"

forvalues st = 1/3 {
    count if settlement_type == `st'
    local n_total = r(N)
    count if settlement_type == `st' & cross_group_jr == 1
    local n_jr = r(N)
    local share = `n_jr' / `n_total'
    di " " %-18s `: label set_lbl `st'':"
    di "   Cells (total):              " %8.0f `n_total'
    di "   Cells with cross-group JR:  " %8.0f `n_jr'
    di "   Share:                      " %8.4f `share'
    di ""
}

* ── Overall (all three types) ────────────────────────────────────────────────
count if !missing(settlement_type)
local n_all = r(N)
count if !missing(settlement_type) & cross_group_jr == 1
local n_all_jr = r(N)
di " All settlement types:"
di "   Cells (total):              " %8.0f `n_all'
di "   Cells with cross-group JR:  " %8.0f `n_all_jr'
di "   Share:                      " %8.4f (`n_all_jr'/`n_all')
di "================================================================"

* ── Save merged analysis file ────────────────────────────────────────────────
save "./output/settlement/grid_settlement_jr_merged.dta", replace

di ""
di "Saved merged dataset  → ./output/settlement/grid_settlement_jr_merged.dta"
di "Saved summary table   → ./output/settlement/jr_share_by_settlement_type.csv"

* ==============================================================================
* Climate + JR pipeline (master)
* ==============================================================================
* Run from project root:  do code/climate/stata/00_master.do
*
* Step 1 (R):  overlay JR on Eberle grid cells
* Step 2 (Stata): build panel + estimate
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

cd "$root"
cap mkdir "$clim_out/panels"
cap mkdir "$clim_out/tables"
cap mkdir "$clim_out/figures"

* R: spatial JR overlay on Eberle cells (requires sf, dplyr, haven)
shell Rscript "$clim/r/01_overlay_jr_on_eberle_cells.R"

do "$clim/stata/01_build_jr_panel.do"
do "$clim/stata/03_estimate_jr.do"

di ""
di "Done. Panel: output/climate/panels/eberle_jr_panel.dta"
di "Tables:  output/climate/tables/jr_estimates.csv"

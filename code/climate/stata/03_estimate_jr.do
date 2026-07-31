* ==============================================================================
* Estimate JR extensions to Eberle Eq. (1)
* ==============================================================================
* Baseline (Table 1 col. 4):  conflictD ~ T + T*mixD + T*polarization
* JR binary:                  + T*JR + T*mixD*JR
* JR intensity (count):       + T*n_jr_groups + T*mixD*n_jr_groups
* JR intensity (log):         + T*log(1+n_jr) + T*mixD*log(1+n_jr)
*
* FE: cell + country_year | SE: cluster(cell)  [fast; use acreg for Conley]
* Requires: ssc install reghdfe ftools estout
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

foreach pkg in reghdfe ftools estout {
    cap which `pkg'
    if _rc {
        di as error "Install: ssc install `pkg'"
        exit 198
    }
}

use "$clim_out/panels/eberle_jr_panel.dta", clear
drop if missing(T) | missing(conflictD)

eststo clear

* (1) Eberle baseline
reghdfe conflictD T T_mixD T_polarization, absorb(cell country_year) vce(cluster cell)
eststo m_base

* (2) Binary JR triple interaction
reghdfe conflictD T T_mixD T_polarization T_jr T_mixD_jr, ///
    absorb(cell country_year) vce(cluster cell)
eststo m_jr_bin

* (3) JR intensity: count of groups
reghdfe conflictD T T_mixD T_polarization T_njr T_mixD_njr, ///
    absorb(cell country_year) vce(cluster cell)
eststo m_jr_cnt

* (4) JR intensity: log(1 + count)
reghdfe conflictD T T_mixD T_polarization T_lognjr T_mixD_lognjr, ///
    absorb(cell country_year) vce(cluster cell)
eststo m_jr_log

esttab m_base m_jr_bin m_jr_cnt m_jr_log ///
    using "$clim_out/tables/jr_estimates.tex", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) ///
    order(T T_mixD T_polarization T_jr T_mixD_jr T_njr T_mixD_njr ///
          T_lognjr T_mixD_lognjr) ///
    mtitles("Baseline" "JR binary" "JR count" "JR log") ///
    title("Eberle Eq. (1) with JR interactions")

esttab m_base m_jr_bin m_jr_cnt m_jr_log ///
    using "$clim_out/tables/jr_estimates.csv", replace ///
    se star(* 0.10 ** 0.05 *** 0.01) ///
    order(T T_mixD T_polarization T_jr T_mixD_jr T_njr T_mixD_njr ///
          T_lognjr T_mixD_lognjr)

di ""
di "=== Key coefficient: T x mixD x JR (count spec) ==="
quietly reghdfe conflictD T T_mixD T_polarization T_njr T_mixD_njr, ///
    absorb(cell country_year) vce(cluster cell)
di "  T_mixD_njr = " %8.5f _b[T_mixD_njr] "  (se " %6.4f _se[T_mixD_njr] ")"

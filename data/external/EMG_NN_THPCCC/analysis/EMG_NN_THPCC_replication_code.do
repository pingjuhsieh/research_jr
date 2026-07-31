
* Replication code for "Transhumant Pastoralism, Climate Change, and Conflict in Africa"
*		Eoin McGuirk (Tufts) and Nathan Nunn (UBC), 2023
*		eoinfmcguirk@gmail.com or eoin.mcguirk@tufts.edu; nathan.nunn@ubc.ca


***************************************************
*		Prologue
***************************************************
clear

*	Declare folder [insert filepath]
global folder = "[INSERT FILEPATH HERE]"

*	Set directory 
cd "$folder"

*	Set Stata version
version 17

*	Install additional packages if necessary
/*
ssc install estout,		replace
ssc install reghdfe, 	replace
ssc install acreg, 		replace
*/

*	Set paths
global data =  		"$folder/data"
global output =  	"$folder/output"

*	Set up 
set more off
set seed 12345
cap log close
log using "$folder/output/log_output.txt", text replace


**************************************************
*A.		Load Data
**************************************************

use  "$data/EMG_NN_THPCCC_replication_data.dta", clear

global outcome   		ucdp_all_10 ucdp_state_10 ucdp_nonstate_10  acled_all_10 acled_state_10 acled_nonstate_10
global shortoutcome   	ucdp_all_10 ucdp_state_10 acled_all_10 acled_nonstate_10


**************************************************
*		Table A3	Descriptive Statistics
**************************************************

*	Cell Year
estpost sum ucdp_all_10 ucdp_state_10 ucdp_nonstate_10 acled_all_10 acled_state_10 acled_nonstate_10 prec_gpcc phytomass  temp n1_g_prec_gpcc n1_g_phytomass  n1_g_temp nlights_calib_mean if inrange(year,1989, 2018)  , d
est store desc_cellyear

esttab desc_cellyear using "$output/REP_TABLE_A2a.tex", var(5) replace ///
					mgroups("Cell-Year Level Variables, 1989-2018", pattern(0 1 )  ///
					prefix(\multicolumn{@span}{c}{) suffix(})  ///
					span erepeat(\cmidrule(lr){@span}))  ///
cells("mean(fmt(2) label(Mean)) sd(fmt(2) label(SD)) count(fmt(%9.0fc) label(Count)) min(fmt(2) label(Min)) p50(fmt(2) label(Median))  max(fmt(2) label(Max))" ) label  nonumber noobs booktabs


*	Cell
estpost sum  n1_herdXEApXn12 n1_herdXEApXn1234 bs_np bs_ag ln_pop1990 if  year == 2000 , d
est store desc_cell

esttab desc_cell using "$output/REP_TABLE_A2b.tex", var(5) replace ///
					mgroups("Cell Level Variables", pattern(0 1 )  ///
					prefix(\multicolumn{@span}{c}{) suffix(})  ///
					span erepeat(\cmidrule(lr){@span}))  ///
cells("mean(fmt(2) label(Mean)) sd(fmt(2) label(SD)) count(fmt(%9.0fc) label(Count)) min(fmt(2) label(Min)) p50(fmt(2) label(Median))  max(fmt(2) label(Max))" ) label  nonumber noobs booktabs


*	Ethnic Year
estpost sum g_prec_gpcc g_phytomass g_temp my_EPR_my  if tag_gy == 1  &  inrange(year, 1989, 2018) , d
est store desc_ethnicyear

esttab desc_ethnicyear using "$output/REP_TABLE_A2c.tex", var(5) replace ///
					mgroups("Ethnic-Group-Year Level Variables, 1989-2018", pattern(0 1 )  ///
					prefix(\multicolumn{@span}{c}{) suffix(})  ///
					span erepeat(\cmidrule(lr){@span}))  ///
cells("mean(fmt(2) label(Mean)) sd(fmt(2) label(SD)) count(fmt(%9.0fc) label(Count)) min(fmt(2) label(Min)) p50(fmt(2) label(Median))  max(fmt(2) label(Max))" ) label  nonumber noobs booktabs


*	Ethnic
estpost sum  herdXEApXn12 herdXEApXn1234  EA_ag EA_jh  EA_highgods Muslim Christian SL if tag_gy == 1 & year == 2000 , d
est store desc_ethnic

esttab desc_ethnic using "$output/REP_TABLE_A2d.tex", var(5) replace ///
					mgroups("Ethnic Group Level Variables", pattern(0 1 )  ///
					prefix(\multicolumn{@span}{c}{) suffix(})  ///
					span erepeat(\cmidrule(lr){@span}))  ///
cells("mean(fmt(2) label(Mean)) sd(fmt(2) label(SD)) count(fmt(%9.0fc) label(Count)) min(fmt(2) label(Min)) p50(fmt(2) label(Median))  max(fmt(2) label(Max))" ) label  nonumber noobs booktabs


**************************************************
*		Table A4	Balance Table on THP
**************************************************

*	Cell Year
balancetable (mean if treat==1) (mean if treat==0) (diff treat)  ucdp_all_10 ucdp_state_10 ucdp_nonstate_10 acled_all_10 acled_state_10 acled_nonstate_10  prec_gpcc phytomass  temp n1_g_prec_gpcc n1_g_phytomass  n1_g_temp nlights_calib_mean  if inrange(year,1989, 2018) using "$output/REP_TABLE_A3a.tex", replace ctitles("THP $>$ 0" "THP = 0"   "Difference") varlabels booktabs vce(cluster cell)

*	Cell
balancetable (mean if treat==1) (mean if treat==0) (diff treat)  n1_herdXEApXn12 n1_herdXEApXn1234 bs_np bs_ag ln_pop1990 if   year == 2000 using "$output/REP_TABLE_A3b.tex", replace ctitles(  "THP $>$ 0" "THP = 0""Difference") varlabels booktabs 

*	Ethnic Year
balancetable (mean if treat==1) (mean if treat==0) (diff treat)  g_prec_gpcc g_phytomass g_temp my_EPR_my if   tag_gy == 1  & inrange(year,1989, 2018) using "$output/REP_TABLE_A3c.tex", replace ctitles( "THP $>$ 0" "THP = 0" "Difference") varlabels booktabs vce(cluster MAP_name)

*	Ethnic 
balancetable (mean if treat==1) (mean if treat==0) (diff treat)   EA_ag EA_jh EA_highgods Muslim Christian SL if tag_g == 1 using "$output/REP_TABLE_A3d.tex", replace ctitles(  "THP $>$ 0" "THP = 0" "Difference") varlabels booktabs 


**************************************************
*		TABLE A16	Descriptive Statistics for Country-Year 
**************************************************		

estpost sum AD_CORE_TAG AD_CORE_TNG AD_CORE_IR AD_CORE_FR AD_CORE_CR AD_CORE_LD cy_share_ac cy_np_power  if tag_ctry_y == 1 , d
est store desc_country_year

esttab desc_country_year using "$output/REP_TABLE_A16.tex", var(5) replace ///
					mgroups("Country-Year Level Variables", pattern(0 1 )  ///
					prefix(\multicolumn{@span}{c}{) suffix(})  ///
					span erepeat(\cmidrule(lr){@span}))  ///
cells("mean(fmt(2) label(Mean)) sd(fmt(2) label(SD)) count(fmt(%9.0fc) label(Count)) min(fmt(2) label(Min)) p50(fmt(2) label(Median))  max(fmt(2) label(Max))" ) label  nonumber noobs booktabs


**************************************************
*		TABLE 1
**************************************************

label var n1_herdXEApXn12 	"Neighbor Transhumant Pastoral [$\gamma_{1}$]"
label var n1_herdXEApXn1234 "Neighbor Transhumant Pastoral [$\gamma_{1}$]"
label var herdXEApXn12 		"Transhumant Pastoral [$\gamma_{2}$]"
label var herdXEApXn1234 	"Transhumant Pastoral [$\gamma_{2}$]"

label var ucdp_all_10  			"I(Any)"
label var ucdp_state_10  		"I(State)"
label var ucdp_nonstate_10   	"I(Nonstate)"
label var acled_all_10 			"I(Any)"
label var acled_state_10  		"I(State)"
label var acled_nonstate_10 	"I(Nonstate)"


cap est drop reg*
foreach x1 in n12 n1234  {
foreach y of varlist $outcome  {
		
reghdfe `y'  n1_herdXEApX`x1'  herdXEApX`x1'    ln_pop1990,	vce(cluster cell kg_y) a(year)

		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		estadd local fe "No"
		estadd local yfe "Yes"
		est sto reg`y'
	
				}
							  
esttab  regucdp_all_10  regucdp_state_10  regucdp_nonstate_10  regacled_all_10 regacled_state_10 regacled_nonstate_10  using "$output/REP_TABLE_1_`x1'.tex", replace se  drop(_cons ln_pop1990) ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars(  ///
		    "ymean  \\ Dep. Var. Mean" "yfe Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("UCDP" "ACLED" , pattern(1 0 0 1 0 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(   %10.3f  %~12s  ///
				  %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs depvar noconstant substitute(\_ _) booktabs
}


**************************************************
*		TABLE 2
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var ucdp_nonstate_10   	"\shortstack{ \\ UCDP \\ I(Nonstate)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_state_10  		"\shortstack{ \\ ACLED \\ I(State)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"


label var n1_g_prec_gpcc 					"\hspace{15pt} Rain [$\gamma^{s}_{0}$]"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{1}$]"	
label var g_prec_gpcc 						"\hspace{15pt} Rain [$\gamma^{s}_{2}$]"	
label var g_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{3}$]"	
label var prec_gpcc							"\hspace{15pt} Rain [$\gamma^{s}_{4}$]"	
label var prec_gpcc_X_herdXEApXn12 			"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{5}$]"	

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12  {
cap est drop reg*
foreach y of varlist $outcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10  regucdp_nonstate_10  regacled_all_10 regacled_state_10 regacled_nonstate_10 using "$output/REP_TABLE_2.tex", drop( _cons) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' "\underline{\emph{Own Ethnic Group}} \vspace{-0.4cm}" g_`x1' g_`x1'_X_`x2' "\underline{\emph{Own Cell}} \vspace{-0.4cm}" `x1' `x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nw \hspace{15pt} Rain" "nw_pval \hspace{15pt} p-value" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"sdi_nwnwp [1em]  \hspace{15pt} Rain $+$ Rain $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict" , pattern(1 0 0 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
		 
}
}


**************************************************
*		TABLE 3
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	

foreach x1 of varlist prec_gpcc  {
foreach x2 in  herdXEAp  {
foreach x3 in  n12  {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		summ `y'
		loc ymean = r(mean)
		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 		n1_`x1'_X_`x2'X`x3' 	n1_`x1'_X_`x2' 	n1_`x1'_X_`x3' 	n1_g_`x1'		///
					g_`x1'_X_`x2'X`x3'		g_`x1'_X_`x2'	g_`x1'_X_`x3'	g_`x1' 			///
					`x1'_X_`x2'X`x3' 	 	`x1'_X_`x2'  	`x1'_X_`x3' 	`x1'			///
					,	a(cell cy) cluster(cell kg_y) 
				
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'X`x3'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'X`x3'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'X`x3'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'X`x3'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
	
				}
				
esttab regucdp_all_10  regucdp_state_10   regacled_all_10  regacled_nonstate_10   using "$output/REP_TABLE_3.tex", drop( _cons g_`x1' g_`x1'_X_`x2' g_`x1'_X_`x3' g_`x1'_X_`x2'X`x3' `x1' `x1'_X_`x2' `x1'_X_`x3' `x1'_X_`x2'X`x3') order( "\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1'  n1_`x1'_X_`x2' n1_`x1'_X_`x3' n1_`x1'_X_`x2'X`x3'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ymean  \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict"  , pattern(1 0 0 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt( ///
				 %10.4f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _)	booktabs 
		 
				}
				}
				}	
				
				
**************************************************
*		TABLE 4
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain [$\gamma^{s}_{0}$]"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{1}$]"

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {
	
		loneway `x1' cell
		loc x1sd = r(sd_w)
		

reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				if AG == 1 & !missing( `x2') ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'a
				
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				  if AG == 0  & !missing( `x2')   ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'n
		
				}
			  			
	 
esttab regucdp_all_10a regucdp_state_10a regacled_all_10a regacled_nonstate_10a regucdp_all_10n regucdp_state_10n regacled_all_10n regacled_nonstate_10n using "$output/REP_TABLE_4.tex", drop( _cons g_`x1' g_`x1'_X_`x2' `x1' `x1'_X_`x2') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		 		   scalars( ///
				   "ymean \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Conflict in Agricultural Cells" "Conflict in Non-Agricultural Cells" , pattern(1 0 0 0 1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt( 	 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}
}


**************************************************
*		TABLE 5
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_phytomass	"\hspace{15pt} Phytomass"	
label var n1_g_temp 		"\hspace{15pt} Temperature"

foreach x1 of varlist phytomass temp {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
		
}
esttab regucdp_all_10 regucdp_state_10 regacled_all_10 regacled_nonstate_10 using "$output/REP_TABLE_5`x1'.tex", drop( _cons g_`x1' g_`x1'_X_`x2' `x1' `x1'_X_`x2') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		 		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Shock $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
		 
}
}


**************************************************
*		TABLE 6
**************************************************

label var n1_g_prec_gpcc 					"\hspace{15pt} Annual Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Annual Rain $\times$ Transhumant Pastoral"
label var n1_herdXEApXn12 					"Transhumant Pastoral"	

label var 	gs_n1_g_phytomass 				"\hspace{15pt} Wet Season Phytomass"
label var 	gs_n1_g_prec_gpcc 				"\hspace{15pt} Wet Season Rain"
label var 	ds_n1_g_phytomass 				"\hspace{15pt} Dry Season Phytomass"
label var 	ds_n1_g_prec_gpcc 				"\hspace{15pt} Dry Season Rain"


* a. annual
foreach x1 of varlist prec_gpcc  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

reghdfe gs_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
				
					est sto regg`y'
		
reghdfe ds_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")

					est sto regd`y'

}
esttab reggucdp_all_10 reggucdp2020_num regducdp_all_10 regducdp2020_num  using "$output/REP_TABLE_6a.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 g_`x1' `x1') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' c.n1_g_`x1'#c.n1_herdXEApXn12 ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Growing Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


* b. seasonal 
foreach x1 of varlist prec_gpcc  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

					
reghdfe gs_`y' 		c.gs_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.gs_g_`x1'#c.herdXEApXn12 			///
					c.gs_`x1'#c.herdXEApXn12 				///
					gs_n1_g_`x1' 							///
					gs_g_`x1' 							///
					gs_`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto greg`y'
					
reghdfe ds_`y' 		c.ds_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.ds_g_`x1'#c.herdXEApXn12 			///
					c.ds_`x1'#c.herdXEApXn12 				///
					ds_n1_g_`x1' 							///
					ds_g_`x1' 							///
					ds_`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto dreg`y'
}
esttab  gregucdp_all_10 gregucdp2020_num dregucdp_all_10 dregucdp2020_num using "$output/REP_TABLE_6b.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 *s_g_`x1' *s_`x1' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" gs_n1_g_`x1' c.gs_n1_g_`x1'#c.n1_herdXEApXn12 ds_n1_g_`x1' c.ds_n1_g_`x1'#c.n1_herdXEApXn12) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Growing Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


**************************************************
*		TABLE 7
**************************************************

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist event_jihad_ucdp event_non_jihad  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		est sto reg`y'
		

reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				g_`x1'_X_Muslim		`x1'_X_Muslim		n1_`x1'_X_Muslim ///
				g_`x1'_X_Christian	`x1'_X_Christian	n1_`x1'_X_Christian ///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		* estadd sca sdi_nw = (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		*estadd sca sdi_nwp = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		est sto reg`y'1
				
				}
			  
esttab regevent_jihad_ucdp regevent_non_jihad regevent_jihad_ucdp1 regevent_non_jihad1  using "$output/REP_TABLE_7.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  n1_`x1'_X_Muslim n1_`x1'_X_Christian ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  n1_`x1'_X_Muslim n1_`x1'_X_Christian)  replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///
		   "im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
		   "sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
		   "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for presence of conflict"  , pattern(1 0  0  0  0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s %~12s ///
				%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
	 
				}
				}
	

**************************************************
*		TABLE 8
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {
			
						
reghdfe `y' 	n1_g_`x1' 	n1_`x1'_X_`x2'  		c.n1_`x1'_X_`x2'#c.AD_CORE_TAG 	c.n1_g_`x1'#c.AD_CORE_TAG 	c.n1_`x2'#c.AD_CORE_TAG		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_TNG 	c.n1_g_`x1'#c.AD_CORE_TNG 	c.n1_`x2'#c.AD_CORE_TNG		///
				g_`x1'		g_`x1'_X_`x2'					///
				`x1'		`x1'_X_`x2'					///	
				 ,	a(cell cy) cluster(cell kg_y) 
	
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		est sto reg`y'

				}
			  
esttab regucdp_all_10 regucdp_state_10 regacled_all_10 regacled_nonstate_10   using "$output/REP_TABLE_8.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"	n1_`x1'_X_`x2' 	c.n1_`x1'_X_`x2'#c.AD_CORE_TAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_TNG_cl ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"	n1_`x1'_X_`x2' 	c.n1_`x1'_X_`x2'#c.AD_CORE_TAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_TNG_cl ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars(  "ymean  \\ Dep. Var. Mean"   "fe Cell FE" "cy Country $\times$ Year FE"  "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for presence of conflict"  , pattern(1 0  0  0  0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(   %10.3f   ///
				%~12s  %~12s  %9.0fc  %9.0fc %9.0fc)  /// 
		 label noobs  depvar booktabs
				}
				}


**************************************************
*		TABLE 9
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist  herdXEApXn12 {
foreach var of varlist cy_share_ac   {
cap est drop reg*
foreach y of varlist $shortoutcome  {
			
		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		summ `var' if tag_ctry_y == 1, det
		loc p10  = r(p10)
		loc p90  = r(p90)
				
		
reghdfe `y' 	c.n1_`x1'_X_`x2'#c.`var' c.n1_g_`x1'#c.`var' c.n1_`x2'#c.`var' n1_`x1'_X_`x2'  	n1_g_`x1' ///
				g_`x1'_X_`x2'	g_`x1'  ///
				`x1'_X_`x2'		`x1'	///
				 ,	a(cell cy) cluster(cell kg_y) 
	
					
				lincom n1_`x1'_X_`x2' + c.`var'#c.n1_`x1'_X_`x2' * `p10'
					estadd sca tot_c10 = r(estimate)
					estadd sca tot_s10 = r(se)
					test n1_`x1'_X_`x2' + c.`var'#c.n1_`x1'_X_`x2' * `p10' = 0
					estadd local tot_p10 = trim("[`:display %9.2f r(p)']")	


				lincom n1_`x1'_X_`x2' + c.`var'#c.n1_`x1'_X_`x2' * `p90'
					estadd sca tot_c90 = r(estimate)
					estadd sca tot_s90 = r(se)
					test n1_`x1'_X_`x2' + c.`var'#c.n1_`x1'_X_`x2' * `p90' = 0
					estadd local tot_p90 = trim("[`:display %9.2f r(p)']")	
					
	

		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		estadd sca sdi_nwp10 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.`var'#c.n1_`x1'_X_`x2'] * `x1sd' * `p10'/ `ymean') * 100		
		estadd sca sdi_nwp90 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.`var'#c.n1_`x1'_X_`x2'] * `x1sd' * `p90'/ `ymean') * 100
		
		est sto reg`y'

				}
			  
esttab regucdp_all_10 regucdp_state_10 regacled_all_10 regacled_nonstate_10  using "$output/REP_TABLE_9.tex", drop( _cons  n1_g_`x1'  c.n1_g_`x1'#c.`var' c.n1_`x2'#c.`var' g_`x1'_X_`x2' g_`x1' `x1'_X_`x2'  `x1') ///
	order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  n1_`x1'_X_`x2' c.n1_`x1'_X_`x2'#c.`var'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " ///
		   "im \\  Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:"  ///
		   "sdi_nwp10 [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral when Protected Area at 10th pctile" ///
		   		    "tot_p10 \hspace{25pt} p-value" ///
		   "sdi_nwp90 [1em]\hspace{15pt} Rain $\times$ Transhumant Pastoral when Protected Area at 90th pctile" ///
		   		   "tot_p90 \hspace{25pt} p-value" ///
		   "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE"  "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
				 %10.1f %10.2f   %10.1f %10.2f ///
				 %10.3f  %~12s %~12s  %9.0fc  %9.0fc %9.0fc)  /// 
		 label noobs  depvar booktabs
				}
				}
}


**************************************************
*		TABLE 10
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"


xtset cell year 
foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome   {
			

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		summ cy_np_power if tag_ctry_y == 1, det
		loc p10  = r(p10)
		loc p90  = r(p90)
		
				
reghdfe `y' 	n1_g_`x1' 	n1_`x1'_X_`x2'  		c.n1_`x1'_X_`x2'#c.lcy_np_power 	c.n1_g_`x1'#c.lcy_np_power 	c.n1_`x2'#c.lcy_np_power 		///
				g_`x1'		g_`x1'_X_`x2'					///
				`x1'		`x1'_X_`x2'			///
				 ,	a(cell cy) cluster(cell kg_y) 
	
				lincom n1_`x1'_X_`x2' + c.lcy_np_power#c.n1_`x1'_X_`x2' * `p10'
					estadd sca tot_c10 = r(estimate)
					estadd sca tot_s10 = r(se)
					test n1_`x1'_X_`x2' + c.lcy_np_power#c.n1_`x1'_X_`x2' * `p10' = 0
					estadd local tot_p10 = trim("[`:display %9.2f r(p)']")	

				lincom n1_`x1'_X_`x2' + c.lcy_np_power#c.n1_`x1'_X_`x2' * `p90'
					estadd sca tot_c90 = r(estimate)
					estadd sca tot_s90 = r(se)
					test n1_`x1'_X_`x2' + c.lcy_np_power#c.n1_`x1'_X_`x2' * `p90' = 0
					estadd local tot_p90 = trim("[`:display %9.2f r(p)']")	
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		estadd sca sdi_nwp10 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.lcy_np_power#c.n1_`x1'_X_`x2'] * `x1sd' * `p10'/ `ymean') * 100
		estadd sca sdi_nwp90 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.lcy_np_power#c.n1_`x1'_X_`x2'] * `x1sd' * `p90'/ `ymean') * 100
		est sto reg`y'
		
				}
			  
				
esttab regucdp_all_10 regucdp_state_10 regacled_all_10 regacled_nonstate_10   using "$output/REP_TABLE_10.tex", keep( "\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.1cm}"n1_`x1'_X_`x2' c.n1_`x1'_X_`x2'#c.lcy_np_power) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.1cm}" 	n1_`x1'_X_`x2' c.n1_`x1'_X_`x2'#c.lcy_np_power   ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " ///
		   "im \\  Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:"  ///	
			"sdi_nwp10 [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral when THP Power at 10th pctile" ///
		   		    "tot_p10 \hspace{25pt} p-value" ///	
		   "sdi_nwp90 [1em]\hspace{15pt} Rain $\times$ Transhumant Pastoral when THP Power at 90th pctile" ///
		   		   "tot_p90 \hspace{25pt} p-value" ///
		   "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE"  "clust2 Climate-Zone-Years" "clust1 Cells" "N Observations" )  ///
			mgroups("Indicator for presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
				 %10.1f %10.2f %10.1f %10.2f ///
				 %10.3f   ///
				%~12s %~12s  %9.0fc  %9.0fc %9.0fc)  /// 
		 label noobs  depvar booktabs
}
}


**************************************************
*		TABLE A2
**************************************************

label var phytomass 	"Phytomass"
label var prec_gpcc 	"Rain"
label var temp 			"Temp"

		loneway prec_gpcc cell
		loc x1sd = r(sd_w)
		
		loneway temp cell
		loc x2sd = r(sd_w)
		
reghdfe phytomass 	   				///
				if ES ,	a(cell cy) cluster(cell kg_y) 


		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ phytomass if e(sample)
		loc ymean = r(mean)	
		
cap gen base_r2 = e(r2)
cap gen base_tss = e(tss)
cap gen base_rss = e(rss)
		
		est sto reg_nothing
		
		
reghdfe phytomass 	prec_gpcc   				///
				if ES ,	a(cell cy) cluster(cell kg_y) 


		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ phytomass if e(sample)
		loc ymean = r(mean)	
		
	estadd sca share_resid = 100 * (e(r2) - base_r2)/ (1 - base_r2)
		
		lincom (_b[prec_gpcc] * `x1sd' / `ymean') * 100
		estadd sca sdi_prec = r(estimate)
		lincom (_b[prec_gpcc] * `x1sd' / `ymean') * 100
		estadd local prec_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg_prec
		
reghdfe phytomass 	temp  				///
				if ES  ,	a(cell cy) cluster(cell kg_y) 


		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ phytomass if e(sample)
		loc ymean = r(mean)	
		
	estadd sca share_resid = 100 * (e(r2) - base_r2)/ (1 - base_r2)
	
		lincom (_b[temp] * `x2sd' / `ymean') * 100
		estadd sca sdi_temp = r(estimate)
		lincom (_b[temp] * `x2sd' / `ymean') * 100
		estadd local temp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg_temp
		
reghdfe phytomass 	prec_gpcc  temp 				///
				if ES  ,	a(cell cy) cluster(cell kg_y)  


		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ phytomass if e(sample)
		loc ymean = r(mean)	
		
	estadd sca share_resid = 100 * (e(r2) - base_r2)/ (1 - base_r2)

	lincom (_b[prec_gpcc] * `x1sd' / `ymean') * 100
		estadd sca sdi_prec = r(estimate)
		lincom (_b[prec_gpcc] * `x1sd' / `ymean') * 100
		estadd local prec_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[temp] * `x2sd' / `ymean') * 100
		estadd sca sdi_temp = r(estimate)
		lincom (_b[temp] * `x2sd' / `ymean') * 100
		estadd local temp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg_both
		
				
esttab  reg_prec reg_temp reg_both  using "$output/REP_TABLE_A2.tex", drop( _cons) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "share_resid \\ Share of RSS explained by  \\ weather variable(s) (in \%)" "F [1em] F statistic" "im \hline \\  Effect of 1 Std. Dev. Shock \\ as $\%$ of Dep. Var. Mean:" "sdi_prec \\ Rain" "prec_pval p-value" "sdi_temp [1em] Temp" "temp_pval p-value"  "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Years" "clust1 Cells" "N Observations" )  ///
			mgroups("Phytomass" , pattern(1 0 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt( %10.2f  %10.2f   %~12s  ///
				%10.2f %10.2f  %10.2f %10.2f %10.2f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs nomtitles  modelwidth(6) booktabs


		 
**************************************************
*		TABLE A5
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain [$\gamma^{s}_{0}$]"	
label var n1_prec_gpcc_X_herdXEApXn1234 	"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{1}$]"
label var g_prec_gpcc 						"\hspace{15pt} Rain [$\gamma^{s}_{2}$]"	
label var g_prec_gpcc_X_herdXEApXn1234 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{3}$]"	
label var prec_gpcc							"\hspace{15pt} Rain [$\gamma^{s}_{4}$]"	
label var prec_gpcc_X_herdXEApXn1234 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral [$\gamma^{s}_{5}$]"	

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn1234 {
cap est drop reg*
foreach y of varlist $outcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10  regucdp_nonstate_10  regacled_all_10 regacled_state_10 regacled_nonstate_10 using "$output/REP_TABLE_A5.tex", drop( _cons) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' "\underline{\emph{Own Ethnic Group}} \vspace{-0.4cm}" g_`x1' g_`x1'_X_`x2' "\underline{\emph{Own Cell}} \vspace{-0.4cm}" `x1' `x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nw \hspace{15pt} Rain" "nw_pval \hspace{15pt} p-value" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"sdi_nwnwp [1em]  \hspace{15pt} Rain $+$ Rain $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict" , pattern(1 0 0 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
		 
}
}


**************************************************
*		TABLE A6
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				g_`x1'_X_EA_jh	`x1'_X_EA_jh	n1_`x1'_X_EA_jh ///
				g_`x1'_X_SL	`x1'_X_SL	n1_`x1'_X_SL ///
				g_`x1'_X_EA_gods_4	`x1'_X_EA_gods_4	n1_`x1'_X_EA_gods_4 ///
				g_`x1'_X_EA_gods_5	`x1'_X_EA_gods_5	n1_`x1'_X_EA_gods_5 ///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		est sto reg`y'
	
				}

esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10 using "$output/REP_TABLE_A6.tex", drop( _cons g* `x1'*) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' n1_`x1'_X_EA_jh n1_`x1'_X_SL n1_`x1'_X_EA_gods_4 n1_`x1'_X_EA_gods_5 )  replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	   "im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" "sdi_nw \hspace{15pt} Rain" "nw_pval \hspace{15pt} p-value" "sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" "sdi_nwnwp [1em]  \hspace{15pt} Rain $+$ Rain $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value"  "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict" , pattern(1 0 0 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s %~12s %10.2f    %10.2f %10.2f    %10.2f %10.2f    %10.2f ///
				 %10.4f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

				}
				}
			

**************************************************
*		TABLE A7
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				g_`x1'_X_g_cm_prec	`x1'm_X_c_m_prec_gpcc	n1_`x1'_X_g_cm_prec01 ///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng " "
		estadd local im " "
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		* estadd sca sdi_nw = (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		*estadd sca sdi_nwp = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		est sto reg`y'
			
				}
	
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10 using "$output/REP_TABLE_A7.tex", drop( _cons g* `x1'*) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' n1_`x1'_X_g_cm_prec01 )  replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	   "im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" "sdi_nw \hspace{15pt} Rain" "nw_pval \hspace{15pt} p-value" "sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" "sdi_nwnwp [1em]  \hspace{15pt} Rain $+$ Rain $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value"  "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Years" "clust1 Cells" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict" , pattern(1 0 0 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s %~12s %10.2f    %10.2f %10.2f    %10.2f %10.2f    %10.2f ///
				 %10.4f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

				}
				}
				

**************************************************
*		TABLE A8
**************************************************				
	
label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	
			
foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				p_energy_X_`x2'   	p_energy_X_n1_`x2' 	///
				p_metmin_X_`x2'   	p_metmin_X_n1_`x2' 	///
				p_precmet_X_`x2'  	p_precmet_X_n1_`x2' 	///
				p_agri_X_`x2'   	p_agri_X_n1_`x2' 	///
				year_X_`x2'  		year_X_n1_`x2' 	///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		* estadd sca sdi_nw = (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		*estadd sca sdi_nwp = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		est sto reg`y'
		
				}
		
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10 using "$output/REP_TABLE_A8.tex", drop( _cons g* `x1'* year_X_`x2' p_*_X_`x2') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  year_X_n1_`x2'	p_*_X_n1_`x2')  replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	   "im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" "sdi_nw \hspace{15pt} Rain" "nw_pval \hspace{15pt} p-value" "sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" "sdi_nwnwp [1em]  \hspace{15pt} Rain $+$ Rain $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value"  "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict" , pattern(1 0 0 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s %~12s %10.2f    %10.2f %10.2f    %10.2f %10.2f    %10.2f ///
				 %10.4f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
				}
				}
			
			
**************************************************
*		TABLE A9
**************************************************	

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	
	
*	a.
foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12  {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 ,	a(cell cy) cluster(country) 
					
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
	
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10   using "$output/REP_TABLE_A9a.tex", drop( _cons g_`x1' g_`x1'_X_`x2' `x1' `x1'_X_`x2' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
					"clust1 Country Clusters")  ///
			mgroups("Panel A: Clustering by Country" , pattern(1 0 0 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  	%~12s ///
					%9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}
}

*	b
foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12  {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 ,	a(cell cy) cluster(country KG_climate) 
					
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10   using "$output/REP_TABLE_A9b.tex", drop( _cons g_`x1' g_`x1'_X_`x2' `x1' `x1'_X_`x2' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
					"clust1 Country Clusters" "clust2 Climate-Zone Clusters" )  ///
			mgroups("Panel B: Clustering by Country and Climate-Zone" , pattern(1 0 0 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  	%~12s %~12s ///
					%9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}
}

*	c.
*********************	
preserve
*********************		
rename *herdXEApXn12*  *hpn12* 
foreach x1 of varlist  prec_gpcc  {
foreach x2 of varlist  hpn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {


		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
acreg `y' 		n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 , id(cell) time(year) longitude(x) latitude(y) spatial  dist(1000) lag(30)	pfe1(cell) pfe2(cy) hac

		est sto reg`y'
		
				}
			  
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10   using "$output/REP_TABLE_A9c.tex", drop(g_`x1' g_`x1'_X_`x2' _cons `x1' `x1'_X_`x2') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		    scalars(  "N Observations" )  ///
			mgroups("Panel C: Spatial HAC 1000KM" , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(   ///
				 %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) booktabs
				}
				}	
*********************	
restore
*********************


**************************************************
*		TABLE A10
**************************************************	

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"


foreach x1 of varlist pp_rain      {
foreach x2 of varlist herdXEApXn12  {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng " "
		estadd local im " "
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A10.tex", drop( _cons g_`x1' g_`x1'_X_`x2' `x1' `x1'_X_`x2') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		 		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Suitability Index Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nw \hspace{15pt} Phytomass Suitability Index" "nw_pval \hspace{15pt} p-value" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass Suitability Index $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"sdi_nwnwp [1em]  \hspace{15pt} Phytomass Suitability Index $+$ Phytomass Suitability Index $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
		

}
}


**************************************************
*		TABLE A11
**************************************************	

foreach x1 of varlist  pp_r2    {
foreach x2 of varlist herdXEApXn12  {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				 ,	a(cell cy) cluster(cell kg_y) 

				lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng " "
		estadd local im " "
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A11.tex", drop( _cons g_`x1' g_`x1'_X_`x2' `x1' `x1'_X_`x2') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		 		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Suitability Index Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nw \hspace{15pt} Phytomass Suitability Index" "nw_pval \hspace{15pt} p-value" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass Suitability Index $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"sdi_nwnwp [1em]  \hspace{15pt} Phytomass Suitability Index $+$ Phytomass Suitability Index $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
		

}
}


**************************************************
*		TABLE A12
**************************************************	

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_state_10  		"\shortstack{ \\ UCDP \\ I(State)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	
label var n1_g_temp 						"\hspace{15pt} Temperature"	
label var n1_temp_X_herdXEApXn12 			"\hspace{15pt} Temperature $\times$ Transhumant Pastoral"	

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12  {
foreach x3 of varlist temp  {
cap est drop reg*
foreach y of varlist $shortoutcome  {

		loneway `x1' cell
		loc x1sd = r(sd_w)
		
reghdfe `y' 	n1_g_`x1'		n1_`x1'_X_`x2' 			///
				g_`x1'			g_`x1'_X_`x2'			///
				`x1'	 		`x1'_X_`x2'  			///
				n1_`x3'_X_`x2' 				///
				g_`x3'_X_`x2'				///
				n1_g_`x3'	g_`x3' 	`x3'_X_`x2'  `x3'	///
				 ,	a(cell cy) cluster(cell kg_y) 

					lincom n1_`x1'_X_`x2' + n1_g_`x1'
					estadd sca tot_nwp = r(estimate)
					estadd sca stot_nwp = r(se)
					test n1_`x1'_X_`x2' +  n1_g_`x1' = 0
					estadd local pval = trim("[`:display %9.2f r(p)']")
					
					lincom n1_`x3'_X_`x2' + n1_g_`x3'
					estadd sca tot_nwd = r(estimate)
					estadd sca stot_nwd = r(se)
					test n1_`x3'_X_`x2' +  n1_g_`x3' = 0
					estadd local pvald = trim("[`:display %9.2f r(p)']")
					
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng " "
		estadd local im " "
		estadd local ps " "
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		
		lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nw = r(estimate)
		test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
		estadd sca sdi_nwnwp = r(estimate)
		test (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
		estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_g_`x3'] * `x1sd' / `ymean') * 100
		estadd sca dsdi_nw = r(estimate)
		test (_b[n1_g_`x3'] * `x1sd' / `ymean') * 100 = 0
		estadd local dnw_pval = trim("[`:display %9.2f r(p)']")
		
		lincom (_b[n1_`x3'_X_`x2'] * `x1sd' / `ymean') * 100
		estadd sca dsdi_nwp = r(estimate)
		test (_b[n1_`x3'_X_`x2'] * `x1sd' / `ymean') * 100 = 0
		estadd local dnwp_pval = trim("[`:display %9.2f r(p)']")		
		
		lincom (_b[n1_`x3'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x3'] * `x1sd' / `ymean') * 100
		estadd sca dsdi_nwnwp = r(estimate)
		test (_b[n1_`x3'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x3'] * `x1sd' / `ymean') * 100 = 0
		estadd local dnwnwp_pval = trim("[`:display %9.2f r(p)']")
		
		est sto reg`y'
		
}
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10 using "$output/REP_TABLE_A12.tex", drop( _cons g* `x1'* temp*) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2'  n1_g_`x3' n1_`x3'_X_`x2'  ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nw \hspace{15pt} Rain" "nw_pval \hspace{15pt} p-value" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"sdi_nwnwp [1em]  \hspace{15pt} Rain $+$ Rain $\times$ Transhumant Pastoral" "nwnwp_pval \hspace{15pt} p-value" ///		
				"ps  \\ [1em] Effect of 1 Std. Dev. Temp Shock as $\%$ of Dep. Var. Mean:" ///
				"dsdi_nw \hspace{15pt} Temp" "dnw_pval \hspace{15pt} p-value" ///
				"dsdi_nwp [1em] \hspace{15pt} Temp $\times$ Transhumant Pastoral" "dnwp_pval \hspace{15pt} p-value" ///
				"dsdi_nwnwp [1em]  \hspace{15pt} Temp $+$ Temp $\times$ Transhumant Pastoral" "dnwnwp_pval \hspace{15pt} p-value" ///			
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict" , pattern(1 0  0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
				%~12s ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs
}
}
}	
	
	

**************************************************
*		TABLE A13
**************************************************

label var 	n1_g_phytomass 			"\hspace{15pt} Annual Phytomass"

* a. annual
foreach x1 of varlist phytomass  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

reghdfe gs_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
				
					est sto regg`y'
		
reghdfe ds_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")

					est sto regd`y'

}
esttab reggucdp_all_10 reggucdp2020_num regducdp_all_10 regducdp2020_num  using "$output/REP_TABLE_A13a.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 g_`x1' `x1') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' c.n1_g_`x1'#c.n1_herdXEApXn12 ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}



* b. seasonal 
foreach x1 of varlist phytomass  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

					
reghdfe gs_`y' 		c.gs_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.gs_g_`x1'#c.herdXEApXn12 			///
					c.gs_`x1'#c.herdXEApXn12 				///
					gs_n1_g_`x1' 							///
					gs_g_`x1' 							///
					gs_`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto greg`y'
					
reghdfe ds_`y' 		c.ds_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.ds_g_`x1'#c.herdXEApXn12 			///
					c.ds_`x1'#c.herdXEApXn12 				///
					ds_n1_g_`x1' 							///
					ds_g_`x1' 							///
					ds_`x1'  								///
					if seasonal == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto dreg`y'
}
esttab  gregucdp_all_10 gregucdp2020_num dregucdp_all_10 dregucdp2020_num using "$output/REP_TABLE_A13b.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 *s_g_`x1' *s_`x1' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" gs_n1_g_`x1' c.gs_n1_g_`x1'#c.n1_herdXEApXn12 ds_n1_g_`x1' c.ds_n1_g_`x1'#c.n1_herdXEApXn12) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


**************************************************
*		TABLE A14
**************************************************

* A.1
foreach x1 of varlist prec_gpcc  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

reghdfe gs_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
				
					est sto regg`y'
		
reghdfe ds_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")

					est sto regd`y'

}
esttab reggucdp_all_10 reggucdp2020_num regducdp_all_10 regducdp2020_num  using "$output/REP_TABLE_A14A1.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 g_`x1' `x1') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' c.n1_g_`x1'#c.n1_herdXEApXn12 ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}



* A.2
foreach x1 of varlist prec_gpcc  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

					
reghdfe gs_`y' 		c.gs_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.gs_g_`x1'#c.herdXEApXn12 			///
					c.gs_`x1'#c.herdXEApXn12 				///
					gs_n1_g_`x1' 							///
					gs_g_`x1' 							///
					gs_`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto greg`y'
					
reghdfe ds_`y' 		c.ds_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.ds_g_`x1'#c.herdXEApXn12 			///
					c.ds_`x1'#c.herdXEApXn12 				///
					ds_n1_g_`x1' 							///
					ds_g_`x1' 							///
					ds_`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto dreg`y'
}
esttab  gregucdp_all_10 gregucdp2020_num dregucdp_all_10 dregucdp2020_num using "$output/REP_TABLE_A14A2.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 *s_g_`x1' *s_`x1' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" gs_n1_g_`x1' c.gs_n1_g_`x1'#c.n1_herdXEApXn12 ds_n1_g_`x1' c.ds_n1_g_`x1'#c.n1_herdXEApXn12) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


* B.1
foreach x1 of varlist phytomass  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

reghdfe gs_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
				
					est sto regg`y'
		
reghdfe ds_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")

					est sto regd`y'

}
esttab reggucdp_all_10 reggucdp2020_num regducdp_all_10 regducdp2020_num  using "$output/REP_TABLE_A14B1.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 g_`x1' `x1') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' c.n1_g_`x1'#c.n1_herdXEApXn12 ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}



* B.2
foreach x1 of varlist phytomass  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

					
reghdfe gs_`y' 		c.gs_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.gs_g_`x1'#c.herdXEApXn12 			///
					c.gs_`x1'#c.herdXEApXn12 				///
					gs_n1_g_`x1' 							///
					gs_g_`x1' 							///
					gs_`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto greg`y'
					
reghdfe ds_`y' 		c.ds_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.ds_g_`x1'#c.herdXEApXn12 			///
					c.ds_`x1'#c.herdXEApXn12 				///
					ds_n1_g_`x1' 							///
					ds_g_`x1' 							///
					ds_`x1'  								///
					if seasonal == 1 & AG == 1, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto dreg`y'
}
esttab  gregucdp_all_10 gregucdp2020_num dregucdp_all_10 dregucdp2020_num using "$output/REP_TABLE_A14B2.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 *s_g_`x1' *s_`x1' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" gs_n1_g_`x1' c.gs_n1_g_`x1'#c.n1_herdXEApXn12 ds_n1_g_`x1' c.ds_n1_g_`x1'#c.n1_herdXEApXn12) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


**************************************************
*		TABLE A15
**************************************************

* A.1
foreach x1 of varlist prec_gpcc  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

reghdfe gs_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
				
					est sto regg`y'
		
reghdfe ds_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")

					est sto regd`y'

}
esttab reggucdp_all_10 reggucdp2020_num regducdp_all_10 regducdp2020_num  using "$output/REP_TABLE_A15A1.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 g_`x1' `x1') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' c.n1_g_`x1'#c.n1_herdXEApXn12 ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}



* A.2
foreach x1 of varlist prec_gpcc  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

					
reghdfe gs_`y' 		c.gs_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.gs_g_`x1'#c.herdXEApXn12 			///
					c.gs_`x1'#c.herdXEApXn12 				///
					gs_n1_g_`x1' 							///
					gs_g_`x1' 							///
					gs_`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto greg`y'
					
reghdfe ds_`y' 		c.ds_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.ds_g_`x1'#c.herdXEApXn12 			///
					c.ds_`x1'#c.herdXEApXn12 				///
					ds_n1_g_`x1' 							///
					ds_g_`x1' 							///
					ds_`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto dreg`y'
}
esttab  gregucdp_all_10 gregucdp2020_num dregucdp_all_10 dregucdp2020_num using "$output/REP_TABLE_A15A2.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 *s_g_`x1' *s_`x1' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" gs_n1_g_`x1' c.gs_n1_g_`x1'#c.n1_herdXEApXn12 ds_n1_g_`x1' c.ds_n1_g_`x1'#c.n1_herdXEApXn12) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


* B.1
foreach x1 of varlist phytomass  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

reghdfe gs_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
				
					est sto regg`y'
		
reghdfe ds_`y' 		c.n1_g_`x1'#c.n1_herdXEApXn12		///
					c.g_`x1'#c.herdXEApXn12 			///
					c.`x1'#c.herdXEApXn12 				///
					n1_g_`x1' 							///
					g_`x1' 							///
					`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					
					lincom (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.n1_g_`x1'#c.n1_herdXEApXn12] * `x1sd' / `ymean') * 100 + (_b[n1_g_`x1'] * `x1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")

					est sto regd`y'

}
esttab reggucdp_all_10 reggucdp2020_num regducdp_all_10 regducdp2020_num  using "$output/REP_TABLE_A15B1.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 g_`x1' `x1') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' c.n1_g_`x1'#c.n1_herdXEApXn12 ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0 )  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}



* B.2
foreach x1 of varlist phytomass  {
cap est drop reg*
foreach y of varlist ucdp_all_10 ucdp2020_num   {
		
		loneway gs_`x1' cell
		loc gx1sd = r(sd_w)
		
		loneway ds_`x1' cell
		loc dx1sd = r(sd_w)
					
		loneway `x1' cell
		loc x1sd = r(sd_w)

					
reghdfe gs_`y' 		c.gs_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.gs_g_`x1'#c.herdXEApXn12 			///
					c.gs_`x1'#c.herdXEApXn12 				///
					gs_n1_g_`x1' 							///
					gs_g_`x1' 							///
					gs_`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ gs_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.gs_n1_g_`x1'#c.n1_herdXEApXn12] * `gx1sd' / `ymean') * 100 + (_b[gs_n1_g_`x1'] * `gx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto greg`y'
					
reghdfe ds_`y' 		c.ds_n1_g_`x1'#c.n1_herdXEApXn12		///
					c.ds_g_`x1'#c.herdXEApXn12 			///
					c.ds_`x1'#c.herdXEApXn12 				///
					ds_n1_g_`x1' 							///
					ds_g_`x1' 							///
					ds_`x1'  								///
					if seasonal == 1 & AG == 0, a(cy cell) cluster(cell kg_y)
	
					estadd local cy "Yes"
					estadd local fe "Yes"
					estadd local ng " "
					estadd local im " "
					estadd sca clust1 = e(N_clust1)
					estadd sca clust2 = e(N_clust2)
					estadd ysumm
					summ ds_`y' if e(sample)
					loc ymean = r(mean)	
					lincom (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nw = r(estimate)
					test (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nw_pval = trim("[`:display %9.2f r(p)']")
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwp_pval = trim("[`:display %9.2f r(p)']")		
					
					lincom (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100
					estadd sca sdi_nwnwp = r(estimate)
					test (_b[c.ds_n1_g_`x1'#c.n1_herdXEApXn12] * `dx1sd' / `ymean') * 100 + (_b[ds_n1_g_`x1'] * `dx1sd' / `ymean') * 100 = 0
					estadd local nwnwp_pval = trim("[`:display %9.2f r(p)']")
					
					est sto dreg`y'
}
esttab  gregucdp_all_10 gregucdp2020_num dregucdp_all_10 dregucdp2020_num using "$output/REP_TABLE_A15B2.tex", drop( _cons c.*g_`x1'#c.herdXEApXn12 c.*`x1'#c.herdXEApXn12 *s_g_`x1' *s_`x1' ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" gs_n1_g_`x1' c.gs_n1_g_`x1'#c.n1_herdXEApXn12 ds_n1_g_`x1' c.ds_n1_g_`x1'#c.n1_herdXEApXn12) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( ///
				"ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " 	///   
				"im  [1em] Effect of 1 Std. Dev. Phytomass Shock as $\%$ of Dep. Var. Mean:" ///
				"sdi_nwp [1em] \hspace{15pt} Phytomass $\times$ Transhumant Pastoral" "nwp_pval \hspace{15pt} p-value" ///
				"ymean \hline \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Month FE" "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Wet Season UCDP Conflict" "Dry Season UCDP Conflict" , pattern(1 0 1 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s ///
					%10.2f    %10.2f ///
				 %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc  %9.0fc )  /// 
		 label noobs  depvar modelwidth(6) substitute(\_ _) booktabs

}


**************************************************
*		TABLE A17
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_nonstate_10   	"\shortstack{ \\ UCDP \\ I(Nonstate)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	

foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {
									
reghdfe `y' 	n1_g_`x1' 	n1_`x1'_X_`x2'  		c.n1_`x1'_X_`x2'#c.AD_CORE_IR 	c.n1_g_`x1'#c.AD_CORE_IR 	c.n1_`x2'#c.AD_CORE_IR		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_FR 	c.n1_g_`x1'#c.AD_CORE_FR 	c.n1_`x2'#c.AD_CORE_FR		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_CR 	c.n1_g_`x1'#c.AD_CORE_CR 	c.n1_`x2'#c.AD_CORE_CR		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_LD 	c.n1_g_`x1'#c.AD_CORE_LD 	c.n1_`x2'#c.AD_CORE_LD		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_OAG 	c.n1_g_`x1'#c.AD_CORE_OAG 	c.n1_`x2'#c.AD_CORE_OAG		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_ONG 	c.n1_g_`x1'#c.AD_CORE_ONG 	c.n1_`x2'#c.AD_CORE_ONG		///
				g_`x1'		g_`x1'_X_`x2'					///
				`x1'		`x1'_X_`x2'					///	
				 ,	a(cell cy) cluster(cell kg_y) 
	
		estadd local ct "Yes"
		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		est sto reg`y'

				}
			  
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A17.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" 	n1_`x1'_X_`x2' c.n1_`x1'_X_`x2'#c.AD_CORE_IR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_FR_cl  c.n1_`x1'_X_`x2'#c.AD_CORE_CR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_LD_cl	c.n1_`x1'_X_`x2'#c.AD_CORE_OAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_ONG_cl) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  	n1_`x1'_X_`x2' c.n1_`x1'_X_`x2'#c.AD_CORE_IR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_FR_cl  c.n1_`x1'_X_`x2'#c.AD_CORE_CR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_LD_cl	c.n1_`x1'_X_`x2'#c.AD_CORE_OAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_ONG_cl ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars(  "ymean  \\ Dep. Var. Mean"  "fe Cell FE" "cy Country $\times$ Year FE"  "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(   %10.3f   ///
				%~12s %~12s   %9.0fc  %9.0fc %9.0fc)  /// 
		 label noobs  depvar booktabs
				}
				}
				

**************************************************
*		TABLE A18
**************************************************

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_nonstate_10   	"\shortstack{ \\ UCDP \\ I(Nonstate)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

foreach x1 of varlist 	prec_gpcc  {
foreach x2 of varlist 	herdXEApXn12 {
cap est drop reg*
foreach y of varlist 	$shortoutcome  {
			
						
reghdfe `y' 	n1_g_`x1' 	n1_`x1'_X_`x2'  		c.n1_`x1'_X_`x2'#c.AD_CORE_TAG 	c.n1_g_`x1'#c.AD_CORE_TAG 	c.n1_`x2'#c.AD_CORE_TAG		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_TNG 	c.n1_g_`x1'#c.AD_CORE_TNG 	c.n1_`x2'#c.AD_CORE_TNG		///
				g_`x1'		g_`x1'_X_`x2'																									///
				`x1'		`x1'_X_`x2'																										///	
				c.n1_`x1'_X_`x2'#i.ctry c.n1_`x1'_X_`x2'#i.year c.n1_g_`x1'#i.ctry c.n1_g_`x1'#i.year c.n1_`x2'#i.year 						///
				,	a(cell cy) cluster(cell kg_y) 
				

		est sto reg`y'

				}
			  
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A18a.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"		c.n1_`x1'_X_`x2'#c.AD_CORE_TAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_TNG_cl ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" 	c.n1_`x1'_X_`x2'#c.AD_CORE_TAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_TNG_cl ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
			mgroups("Panel A: Het by Int. Agricultural Aid"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 label noobs  depvar booktabs
				}
				}
											
foreach x1 of varlist prec_gpcc  {
foreach x2 of varlist herdXEApXn12 {
cap est drop reg*
foreach y of varlist $shortoutcome  {
									
reghdfe `y' 	n1_g_`x1' 	n1_`x1'_X_`x2'  		c.n1_`x1'_X_`x2'#c.AD_CORE_IR 	c.n1_g_`x1'#c.AD_CORE_IR 	c.n1_`x2'#c.AD_CORE_IR		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_FR 	c.n1_g_`x1'#c.AD_CORE_FR 	c.n1_`x2'#c.AD_CORE_FR		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_CR 	c.n1_g_`x1'#c.AD_CORE_CR 	c.n1_`x2'#c.AD_CORE_CR		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_LD 	c.n1_g_`x1'#c.AD_CORE_LD 	c.n1_`x2'#c.AD_CORE_LD		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_OAG 	c.n1_g_`x1'#c.AD_CORE_OAG 	c.n1_`x2'#c.AD_CORE_OAG		///
													c.n1_`x1'_X_`x2'#c.AD_CORE_ONG 	c.n1_g_`x1'#c.AD_CORE_ONG 	c.n1_`x2'#c.AD_CORE_ONG		///
				g_`x1'		g_`x1'_X_`x2'																									///
				`x1'		`x1'_X_`x2'																										///	
				c.n1_`x1'_X_`x2'#i.ctry c.n1_`x1'_X_`x2'#i.year c.n1_g_`x1'#i.ctry c.n1_g_`x1'#i.year c.n1_`x2'#i.year 						///
				 ,	a(cell cy) cluster(cell kg_y) 
	
		est sto reg`y'
				}
			  
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A18b.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  c.n1_`x1'_X_`x2'#c.AD_CORE_IR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_FR_cl  c.n1_`x1'_X_`x2'#c.AD_CORE_CR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_LD_cl	c.n1_`x1'_X_`x2'#c.AD_CORE_OAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_ONG_cl) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  c.n1_`x1'_X_`x2'#c.AD_CORE_IR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_FR_cl  c.n1_`x1'_X_`x2'#c.AD_CORE_CR_cl c.n1_`x1'_X_`x2'#c.AD_CORE_LD_cl	c.n1_`x1'_X_`x2'#c.AD_CORE_OAG_cl c.n1_`x1'_X_`x2'#c.AD_CORE_ONG_cl ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
			mgroups("Panel B: Het by Int. Aid Types"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 label noobs  depvar booktabs
				}
				}
				
foreach x1 of varlist 	prec_gpcc  {
foreach x2 of varlist  	herdXEApXn12 {
foreach x3 of varlist 	cy_share_ac   {
cap est drop reg*
foreach y of varlist $shortoutcome  {
			
				
reghdfe `y' 	n1_`x1'_X_`x2'  n1_g_`x1'		c.n1_`x1'_X_`x2'#c.`x3' c.n1_g_`x1'#c.`x3' c.n1_`x2'#c.`x3'  		///
				g_`x1'_X_`x2'	g_`x1'  																				///
				`x1'_X_`x2'		`x1'																					///
				c.n1_`x1'_X_`x2'#i.ctry c.n1_`x1'_X_`x2'#i.year c.n1_g_`x1'#i.ctry c.n1_g_`x1'#i.year c.n1_`x2'#i.year 	///
				 ,	a(cell cy) cluster(cell kg_y) 

		est sto reg`y'
				}
							
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A18c.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  c.n1_`x1'_X_`x2'#c.`x3') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  c.n1_`x1'_X_`x2'#c.`x3' ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
			mgroups("Panel C: Het by Conservation, Country-Year Level"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 label noobs  depvar booktabs
		 
}
}
}			 
			
foreach x1 of varlist 	prec_gpcc  {
foreach x2 of varlist  	herdXEApXn12 {
foreach x3 of varlist 	gcy_share_ac   {
foreach x4 of varlist 	rocy_share_ac   {
cap est drop reg*
foreach y of varlist $shortoutcome  {
			
				
reghdfe `y' 	n1_`x1'_X_`x2'  	n1_g_`x1'		c.n1_`x1'_X_`x2'#c.`x3' c.n1_g_`x1'#c.`x3' c.n1_`x2'#c.`x3' 	`x3' ///
													c.n1_`x1'_X_`x2'#c.`x4' c.n1_g_`x1'#c.`x4' c.n1_`x2'#c.`x4' 	`x4' ///
				g_`x1'_X_`x2'	g_`x1'  ///
				`x1'_X_`x2'		`x1'	///
				c.n1_`x1'_X_`x2'#i.ctry c.n1_`x1'_X_`x2'#i.year c.n1_g_`x1'#i.ctry c.n1_g_`x1'#i.year c.n1_`x2'#i.year 	///
				 ,	a(cell cy) cluster(cell kg_y)  

		est sto reg`y'

				}				 
				 
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A18d.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"   c.n1_`x1'_X_`x2'#c.`x3' c.n1_`x1'_X_`x2'#c.`x4') order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  c.n1_`x1'_X_`x2'#c.`x3' c.n1_`x1'_X_`x2'#c.`x4' ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
			mgroups("Panel D: Het by Conservation, Subnational-Year Level"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 label noobs  depvar booktabs
}
}
}
}

foreach x1 of varlist 	prec_gpcc  {
foreach x2 of varlist 	herdXEApXn12 {
cap est drop reg*
foreach y of varlist 	$shortoutcome   {
							
reghdfe `y' 	n1_g_`x1' 	n1_`x1'_X_`x2'  		c.n1_`x1'_X_`x2'#c.lcy_np_power 	c.n1_g_`x1'#c.lcy_np_power 	c.n1_`x2'#c.lcy_np_power 		///
				g_`x1'		g_`x1'_X_`x2'					///
				`x1'		`x1'_X_`x2'			///
				c.n1_`x1'_X_`x2'#i.ctry c.n1_`x1'_X_`x2'#i.year c.n1_g_`x1'#i.ctry c.n1_g_`x1'#i.year c.n1_`x2'#i.year 	///
				 ,	a(cell cy) cluster(cell kg_y) 
	
		estadd local fe 	"Yes"
		estadd local cy 	"Yes"
		estadd local rtc 	"Yes"
		estadd local rc 	"Yes"
		estadd local rty 	"Yes"
		estadd local ry 	"Yes"
		estadd local ty 	"Yes"
		est sto reg`y'
		
				}
	esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A18e.tex", keep("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"   c.n1_`x1'_X_`x2'#c.lcy_np_power ) order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}"  c.n1_`x1'_X_`x2'#c.lcy_np_power ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars(	"fe Cell FE" ///
					"cy Country $\times$ Year FE"  ///
					"rtc Rain $\times$ Transhumant Pastoralism $\times$ Country FE" ///
					"rc Rain $\times$ Country FE" ///
					"rty Rain $\times$ Transhumant Pastoralism $\times$ Year FE"	///
					"ry Rain $\times$ Year FE"	///
					"ty Transhumant Pastoralism $\times$ Year FE" )  ///
			mgroups("Panel E: Het by THP Political Power"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt( %~12s  %~12s  %~12s  %~12s %~12s  %~12s %~12s)  /// 
		 label noobs  depvar booktabs
}
}

								 
				
**************************************************
*		TABLE A19
**************************************************				

label var ucdp_all_10  			"\shortstack{ \\ UCDP \\ I(Any)}"
label var ucdp_nonstate_10   	"\shortstack{ \\ UCDP \\ I(Nonstate)}"
label var acled_all_10 			"\shortstack{ \\ ACLED \\ I(Any)}"
label var acled_nonstate_10 	"\shortstack{ \\ ACLED \\ I(Nonstate)}"

label var n1_g_prec_gpcc 					"\hspace{15pt} Rain"	
label var n1_prec_gpcc_X_herdXEApXn12 		"\hspace{15pt} Rain $\times$ Transhumant Pastoral"	
				
foreach x1 of varlist 	prec_gpcc  {
foreach x2 of varlist  	herdXEApXn12 {
foreach x3 of varlist 	gcy_share_ac   {
foreach x4 of varlist 	rocy_share_ac   {
cap est drop reg*
foreach y of varlist $shortoutcome  {
			
		loneway `x1' cell
		loc x1sd = r(sd_w)
		
		summ `x3' if tag_cgy == 1, det
		loc p10  = r(p10)
		loc p90  = r(p90)
		
		summ `x4' if tag_cgy == 1, det
		loc cp10  = r(p10)
		loc cp90  = r(p90)
				
		
reghdfe `y' 	c.n1_`x1'_X_`x2'#c.`x3' c.n1_g_`x1'#c.`x3' c.n1_`x2'#c.`x3' n1_`x1'_X_`x2'  	n1_g_`x1'	`x3' ///
				g_`x1'_X_`x2'	g_`x1'  ///
				`x1'_X_`x2'		`x1'	///
				c.n1_`x1'_X_`x2'#c.`x4' c.n1_g_`x1'#c.`x4' c.n1_`x2'#c.`x4' `x4' ///
				 ,	a(cell cy) cluster(cell kg_y)  
				
				lincom n1_`x1'_X_`x2' + c.`x3'#c.n1_`x1'_X_`x2' * `p10'
					estadd sca tot_c10 = r(estimate)
					estadd sca tot_s10 = r(se)
					test n1_`x1'_X_`x2' + c.`x3'#c.n1_`x1'_X_`x2' * `p10' = 0
					estadd local tot_p10 = trim("[`:display %9.2f r(p)']")	
					
				lincom n1_`x1'_X_`x2' + c.`x3'#c.n1_`x1'_X_`x2' * `p90'
					estadd sca tot_c90 = r(estimate)
					estadd sca tot_s90 = r(se)
					test n1_`x1'_X_`x2' + c.`x3'#c.n1_`x1'_X_`x2' * `p90' = 0
					estadd local tot_p90 = trim("[`:display %9.2f r(p)']")		
					
				lincom n1_`x1'_X_`x2' + c.`x4'#c.n1_`x1'_X_`x2' * `cp10'
					estadd sca ctot_c10 = r(estimate)
					estadd sca ctot_s10 = r(se)
					test n1_`x1'_X_`x2' + c.`x4'#c.n1_`x1'_X_`x2' * `cp10' = 0
					estadd local ctot_p10 = trim("[`:display %9.2f r(p)']")	


				lincom n1_`x1'_X_`x2' + c.`x4'#c.n1_`x1'_X_`x2' * `cp90'
					estadd sca ctot_c90 = r(estimate)
					estadd sca ctot_s90 = r(se)
					test n1_`x1'_X_`x2' + c.`x4'#c.n1_`x1'_X_`x2' * `cp90' = 0
					estadd local ctot_p90 = trim("[`:display %9.2f r(p)']")	


		estadd local cy "Yes"
		estadd local fe "Yes"
		estadd local ng ""
		estadd local im ""
		estadd sca clust1 = e(N_clust1)
		estadd sca clust2 = e(N_clust2)
		estadd ysumm
		summ `y' if e(sample)
		loc ymean = r(mean)	
		estadd sca sdi_nwp10 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.`x3'#c.n1_`x1'_X_`x2'] * `x1sd' * `p10'/ `ymean') * 100		
		estadd sca sdi_nwp90 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.`x3'#c.n1_`x1'_X_`x2'] * `x1sd' * `p90'/ `ymean') * 100
		
		estadd sca csdi_nwp10 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.`x4'#c.n1_`x1'_X_`x2'] * `x1sd' * `cp10'/ `ymean') * 100		
		estadd sca csdi_nwp90 = (_b[n1_`x1'_X_`x2'] * `x1sd' / `ymean') * 100 + (_b[c.`x4'#c.n1_`x1'_X_`x2'] * `x1sd' * `cp90'/ `ymean') * 100
		est sto reg`y'

				}
			  
esttab regucdp_all_10  regucdp_state_10    regacled_all_10  regacled_nonstate_10  using "$output/REP_TABLE_A19.tex", drop( _cons  `x4' c.n1_g_`x1'#c.`x3' c.n1_`x2'#c.`x3' `x3' g_`x1'_X_`x2' g_`x1' `x1'_X_`x2'  `x1' c.n1_g_`x1'#c.`x4' c.n1_`x2'#c.`x4') ///
	order("\underline{\emph{Nearest Neighboring Ethnic Group}} \vspace{-0.4cm}" n1_g_`x1' n1_`x1'_X_`x2' c.n1_`x1'_X_`x2'#c.`x3'  c.n1_`x1'_X_`x2'#c.`x4' ) replace se noconstant  ///
		 star(* 0.100 ** 0.050 *** 0.010) b(%10.4f %10.4f)  nonotes   ///
		   scalars( "ng \\ \underline{\emph{Nearest Neighboring Ethnic Group: Additional Calculations}} " ///
		   "im \\  Effect of 1 Std. Dev. Rain Shock as $\%$ of Dep. Var. Mean:"  ///
		   "sdi_nwp10 [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral when Ethnicity Protected Area  at 10th pctile" ///
		   		    "tot_p10 \hspace{25pt} p-value" ///
		   "sdi_nwp90 [1em]\hspace{15pt} Rain $\times$ Transhumant Pastoral when Ethnicity Protected Area at 90th pctile" ///
		   		   "tot_p90 \hspace{25pt} p-value" ///
		   "csdi_nwp10 [1em] \hspace{15pt} Rain $\times$ Transhumant Pastoral when Rest of Country Protected Area  at 10th pctile" ///
		   		    "ctot_p10 \hspace{25pt} p-value" ///
		   "csdi_nwp90 [1em]\hspace{15pt} Rain $\times$ Transhumant Pastoral when Rest of Country Protected Area  at 90th pctile" ///
		   		   "ctot_p90 \hspace{25pt} p-value" ///
		   "ymean \hline \\ Dep. Var. Mean"  "fe Cell FE"  "cy Country $\times$ Year FE"  "clust2 Climate-Zone-Year Clusters" "clust1 Cell Clusters" "N Observations" )  ///
			mgroups("Indicator for the presence of conflict"  , pattern(1 0 0 0)  ///
			prefix(\multicolumn{@span}{c}{) suffix(})  ///
			span erepeat(\cmidrule(lr){@span}))  ///
		 sfmt(  %~12s ///
				%~12s  ///
				 %10.1f %10.2f %10.1f %10.2f %10.1f %10.2f  %10.1f %10.2f ///
				 %10.3f  %~12s %~12s  %~12s %~12s  %9.0fc  %9.0fc %9.0fc)  /// 
		 label noobs  depvar booktabs
				}
				}
				}
				}
				
**************************************************
*		End Log
**************************************************	
		log close
		
		
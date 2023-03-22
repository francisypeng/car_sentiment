import delimited using "regression_df_roberta_scaled.csv", clear

drop v1

est clear

estpost tabstat end_bid sentiment_score num_bids num_bidders num_com milage num_highlights num_equipment num_modifications num_known_flaws num_service_history num_other_items num_owner_history num_videos num_views num_photos, c(stat) stat(sum mean sd min max n)

esttab using "./stata_out/sum_stats.tex", replace cells("mean(fmt(%10.2fc)) sd(fmt(%9.2fc)) min(fmt(%6.0fc)) max(fmt(%8.0fc)) count(fmt(%6.0fc))") nonumber nomtitle nonote noobs label booktabs collabels("Mean" "SD" "Min" "Max" "N")


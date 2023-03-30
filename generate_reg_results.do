import delimited using "regression_df_roberta_scaled.csv", clear

drop v1

est clear

eststo: reg end_bid sentiment_score reserve num_bids num_bidders num_com milage private_seller num_highlights num_equipment num_modifications num_known_flaws num_service_history num_other_items num_owner_history num_videos title_status num_views num_photos year make_acura-icolor_yellow, vce(robust)

esttab using "./stata_out/reg_out1.tex", replace b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) label keep(sentiment_score reserve num_bids num_bidders num_com milage private_seller num_highlights num_equipment num_modifications num_known_flaws num_service_history num_other_items num_owner_history num_videos title_status num_views num_photos)

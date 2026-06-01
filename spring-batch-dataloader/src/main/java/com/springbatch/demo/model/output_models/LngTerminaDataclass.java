package com.springbatch.demo.model.output_models;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class LngTerminaDataclass {

    private String IGGIELGN_id;
    private String name;
    private String countryCode;
    private Double longitude;
    private Double latitude;
    private String from_TSO; 
    private String to_TSO;
    private Double max_cap_store2pipe_M_m3_per_d; 
    private Integer start_year; 



}

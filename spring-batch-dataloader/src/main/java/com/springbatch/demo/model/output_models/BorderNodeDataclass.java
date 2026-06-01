package com.springbatch.demo.model.output_models;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// BorderNodeDataclass
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class BorderNodeDataclass {
    private String IGGIELGN_id;
    private String name;
    private String countryCode;
    private String fromCountry;
    private String toCountry;
    private String fromTSO;
    private String toTSO;
    private Double longitude;
    private Double latitude;

}
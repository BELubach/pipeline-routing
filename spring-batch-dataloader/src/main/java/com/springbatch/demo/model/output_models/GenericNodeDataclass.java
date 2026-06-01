package com.springbatch.demo.model.output_models;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class GenericNodeDataclass {

    private String IGGIELGN_id;
    private String name;
    private String countryCode;
    private Double longitude;
    private Double latitude;

}
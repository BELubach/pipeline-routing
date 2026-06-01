package com.springbatch.demo.model.output_models;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class ShippingLaneDataclass {

    private Integer id;
    private String lane_name;
    private List<Double> pathLong;
    private List<Double> pathLat;
    private Double distance_km; 
}

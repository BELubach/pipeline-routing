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
public class PipeSegmentDataclass {
    private Integer id;
    private String iggielgnId;
    private Integer fromNodeId;
    private Integer toNodeId;
    private String countryCodeFrom;
    private String countryCodeTo;
    private Boolean hGas;
    private Double lengthKm;
    private Double diameterMm;
    private Double maxCapMM3PerD;
    private Double maxPressureBar;
    private Double fromLongitude;
    private Double fromLatitude;
    private Double toLongitude;
    private Double toLatitude;
    private List<Double> pathLong;
    private List<Double> pathLat;
}
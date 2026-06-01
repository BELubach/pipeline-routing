package com.springbatch.demo.model.output_models;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class GEMDataclass {

    private String project_id;
    private String pipeline_name;
    private String segment_name;
    private String wiki;
    private String status;
    private String fuel;
    private String countries_or_areas;
    private String owner;
    private String parent;
    private List<String> parent_entity_ids;         // csv in dataset, converted to List<String>
    private Integer start_year_1;
    private Integer start_year_2;
    private Integer start_year_3;
    private Integer shelved_year;
    private Integer cancelled_year;
    private Integer stop_year;
    private Double capacity;  
    private String capacity_units;
    private Double capacity_bcm_y;  
    private Double capacity_boe_d;  
    private Double length_known_km; 
    private Double length_estimate_km; 
    private Double length_merged_km;  
    private String diameter_raw;  
    private String diameter_units;
    private String start_country_or_area;
    private String start_state_province;
    private String start_prefecture_district;
    private String end_location;
    private String end_country_or_area;
    private String end_state_province;
    private String end_prefecture_district;
    private String route_accuracy;
    private String route_type;
    private List<Double> pathLong;
    private List<Double> pathLat;

}
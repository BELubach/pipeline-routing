package com.springbatch.demo.model.import_models;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class PipeSegmentGeoJsonFeature {
    private String type;
    private Map<String, Object> geometry;
    private PipeSegmentGeoJsonProperties properties;

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Map<String, Object> getGeometry() {
        return geometry;
    }

    public void setGeometry(Map<String, Object> geometry) {
        this.geometry = geometry;
    }

    public PipeSegmentGeoJsonProperties getProperties() {
        return properties;
    }

    public void setProperties(PipeSegmentGeoJsonProperties properties) {
        this.properties = properties;
    }
}
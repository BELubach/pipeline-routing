package com.springbatch.demo.model.import_models;

import java.util.Map;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class GeoJsonFeature {
    private String type;
    private Map<String, Object> geometry;
    private Map<String, Object> properties;

    // Getters and Setters
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public Map<String, Object> getGeometry() { return geometry; }
    public void setGeometry(Map<String, Object> geometry) { this.geometry = geometry; }

    public Map<String, Object> getProperties() { return properties; }
    public void setProperties(Map<String, Object> properties) { this.properties = properties; }
}
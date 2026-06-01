package com.springbatch.demo.model.import_models;

import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class PipeSegmentGeoJsonProperties {
    private String name;
    private String id;

    @JsonProperty("country_code")
    private List<String> countryCode;

    private Map<String, Object> tags;
    private PipeSegmentGeoJsonParam param;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public List<String> getCountryCode() {
        return countryCode;
    }

    public void setCountryCode(List<String> countryCode) {
        this.countryCode = countryCode;
    }

    public Map<String, Object> getTags() {
        return tags;
    }

    public void setTags(Map<String, Object> tags) {
        this.tags = tags;
    }

    public PipeSegmentGeoJsonParam getParam() {
        return param;
    }

    public void setParam(PipeSegmentGeoJsonParam param) {
        this.param = param;
    }
}
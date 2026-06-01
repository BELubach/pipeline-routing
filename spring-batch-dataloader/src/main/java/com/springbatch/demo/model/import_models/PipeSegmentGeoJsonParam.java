package com.springbatch.demo.model.import_models;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class PipeSegmentGeoJsonParam {
    @JsonProperty("diameter_mm")
    private Double diameterMm;

    @JsonProperty("end_year")
    private Integer endYear;

    @JsonProperty("is_H_gas")
    private Integer isHGas;

    @JsonProperty("is_bothDirection")
    private Integer isBothDirection;

    @JsonProperty("lat_mean")
    private Double latMean;

    @JsonProperty("length_km")
    private Double lengthKm;

    @JsonProperty("long_mean")
    private Double longMean;

    @JsonProperty("max_cap_M_m3_per_d")
    private Double maxCapMM3PerD;

    @JsonProperty("max_pressure_bar")
    private Double maxPressureBar;

    @JsonProperty("nuts_id_1")
    private List<String> nutsId1;

    @JsonProperty("nuts_id_2")
    private List<String> nutsId2;

    @JsonProperty("nuts_id_3")
    private List<String> nutsId3;

    @JsonProperty("path_lat")
    private List<Double> pathLat;

    @JsonProperty("path_long")
    private List<Double> pathLong;

    @JsonProperty("start_year")
    private Integer startYear;

    public Double getDiameterMm() {
        return diameterMm;
    }

    public void setDiameterMm(Double diameterMm) {
        this.diameterMm = diameterMm;
    }

    public Integer getEndYear() {
        return endYear;
    }

    public void setEndYear(Integer endYear) {
        this.endYear = endYear;
    }

    public Integer getIsHGas() {
        return isHGas;
    }

    public void setIsHGas(Integer isHGas) {
        this.isHGas = isHGas;
    }

    public Integer getIsBothDirection() {
        return isBothDirection;
    }

    public void setIsBothDirection(Integer isBothDirection) {
        this.isBothDirection = isBothDirection;
    }

    public Double getLatMean() {
        return latMean;
    }

    public void setLatMean(Double latMean) {
        this.latMean = latMean;
    }

    public Double getLengthKm() {
        return lengthKm;
    }

    public void setLengthKm(Double lengthKm) {
        this.lengthKm = lengthKm;
    }

    public Double getLongMean() {
        return longMean;
    }

    public void setLongMean(Double longMean) {
        this.longMean = longMean;
    }

    public Double getMaxCapMM3PerD() {
        return maxCapMM3PerD;
    }

    public void setMaxCapMM3PerD(Double maxCapMM3PerD) {
        this.maxCapMM3PerD = maxCapMM3PerD;
    }

    public Double getMaxPressureBar() {
        return maxPressureBar;
    }

    public void setMaxPressureBar(Double maxPressureBar) {
        this.maxPressureBar = maxPressureBar;
    }

    public List<String> getNutsId1() {
        return nutsId1;
    }

    public void setNutsId1(List<String> nutsId1) {
        this.nutsId1 = nutsId1;
    }

    public List<String> getNutsId2() {
        return nutsId2;
    }

    public void setNutsId2(List<String> nutsId2) {
        this.nutsId2 = nutsId2;
    }

    public List<String> getNutsId3() {
        return nutsId3;
    }

    public void setNutsId3(List<String> nutsId3) {
        this.nutsId3 = nutsId3;
    }

    public List<Double> getPathLat() {
        return pathLat;
    }

    public void setPathLat(List<Double> pathLat) {
        this.pathLat = pathLat;
    }

    public List<Double> getPathLong() {
        return pathLong;
    }

    public void setPathLong(List<Double> pathLong) {
        this.pathLong = pathLong;
    }

    public Integer getStartYear() {
        return startYear;
    }

    public void setStartYear(Integer startYear) {
        this.startYear = startYear;
    }
}
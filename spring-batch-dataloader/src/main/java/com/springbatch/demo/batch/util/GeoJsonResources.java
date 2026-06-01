package com.springbatch.demo.batch.util;

import java.io.IOException;
import java.io.UncheckedIOException;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public final class GeoJsonResources {

    private GeoJsonResources() {
    }

    public static Resource featuresArray(Resource source) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode root = objectMapper.readTree(source.getInputStream());
            JsonNode features = root.path("features");
            if (!features.isArray()) {
                throw new IllegalArgumentException("GeoJSON file must contain a features array");
            }

            return new ByteArrayResource(objectMapper.writeValueAsBytes(features)) {
                @Override
                public String getFilename() {
                    return source.getFilename();
                }
            };
        } catch (IOException exception) {
            throw new UncheckedIOException("Failed to extract features array from GeoJSON resource", exception);
        }
    }
}
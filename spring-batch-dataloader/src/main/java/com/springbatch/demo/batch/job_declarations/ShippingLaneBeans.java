package com.springbatch.demo.batch.job_declarations;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.sql.DataSource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.EnableBatchProcessing;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.launch.support.RunIdIncrementer;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.database.JdbcBatchItemWriter;
import org.springframework.batch.item.json.JacksonJsonObjectReader;
import org.springframework.batch.item.json.JsonItemReader;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.transaction.PlatformTransactionManager;
import com.springbatch.demo.batch.util.GeoJsonResources;
import com.springbatch.demo.batch.util.ImportStepListener;
import com.springbatch.demo.model.import_models.GeoJsonFeature;
import com.springbatch.demo.model.output_models.ShippingLaneDataclass;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@EnableBatchProcessing(dataSourceRef = "batchDataSource", transactionManagerRef = "transactionManager")
@Configuration
public class ShippingLaneBeans {

    @Bean
    public Job importShippingLanesJob(JobRepository jobRepository,
            Step truncateShippingLanesStep,
            Step importShippingLanesStep) {
        return new JobBuilder("importShippingLanes", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(truncateShippingLanesStep)
                .next(importShippingLanesStep)
                .build();

    }

    @Bean
    public Step truncateShippingLanesStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

        return new StepBuilder("truncateShippingLanesStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    log.info("Truncating shipping_lanes table...");
                    jdbcTemplate.execute("TRUNCATE TABLE shipping_lanes");
                    log.info("shipping_lanes table truncated successfully.");
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    @Bean
    public Step importShippingLanesStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource,
            ItemReader<GeoJsonFeature> shippingLaneItemReader,
            ShippinglaneProcessor processor,
            JdbcBatchItemWriter<ShippingLaneDataclass> shippinglaneItemWriter) {
        return new StepBuilder("importShippingLanesStep", jobRepository)
                .<GeoJsonFeature, ShippingLaneDataclass>chunk(10, transactionManager)
                .reader(shippingLaneItemReader)
                .processor(processor)
                .writer(shippinglaneItemWriter)
                .listener(new ImportStepListener())
                .build();
    }

    /**
     * Custom reader that reads GeoJSON features and expands MultiLineString geometries 
     * into individual LineString geometries for separate database rows.
     */
    @Bean
    public ItemReader<GeoJsonFeature> shippingLaneItemReader() {
        return new ItemReader<GeoJsonFeature>() {
            private JsonItemReader<GeoJsonFeature> delegate;
            private List<GeoJsonFeature> expandedFeatures;
            private int currentIndex = 0;
            private boolean initialized = false;

            private void initialize() {
                if (initialized) return;
                
                JacksonJsonObjectReader<GeoJsonFeature> jsonObjectReader = 
                    new JacksonJsonObjectReader<>(GeoJsonFeature.class);

                delegate = new JsonItemReader<>();
                delegate.setResource(
                    GeoJsonResources.featuresArray(new ClassPathResource("data/Shipping_Lanes_v1.geojson")));
                delegate.setJsonObjectReader(jsonObjectReader);
                delegate.setName("geoJsonReader");
                delegate.setStrict(false);
                
                try {
                    delegate.open(new org.springframework.batch.item.ExecutionContext());
                } catch (Exception e) {
                    throw new RuntimeException("Failed to initialize JSON reader", e);
                }
                
                // Read all features and expand MultiLineStrings
                expandedFeatures = new ArrayList<>();
                try {
                    GeoJsonFeature feature;
                    while ((feature = delegate.read()) != null) {
                        expandFeature(feature);
                    }
                } catch (Exception e) {
                    throw new RuntimeException("Failed to read GeoJSON features", e);
                }
                
                initialized = true;
                log.info("Loaded and expanded {} shipping lane features", expandedFeatures.size());
            }

            private void expandFeature(GeoJsonFeature feature) {
                Map<String, Object> geometry = feature.getGeometry();
                if (geometry == null) {
                    expandedFeatures.add(feature);
                    return;
                }

                String geometryType = (String) geometry.get("type");
                
                if ("MultiLineString".equals(geometryType)) {
                    @SuppressWarnings("unchecked")
                    List<List<List<Double>>> multiLineCoordinates = 
                        (List<List<List<Double>>>) geometry.get("coordinates");
                    
                    if (multiLineCoordinates != null) {
                        for (List<List<Double>> lineStringCoordinates : multiLineCoordinates) {
                            if (lineStringCoordinates == null || lineStringCoordinates.isEmpty()) {
                                continue;
                            }
                            
                            GeoJsonFeature expandedFeature = new GeoJsonFeature();
                            expandedFeature.setType(feature.getType());
                            expandedFeature.setProperties(feature.getProperties());
                            
                            Map<String, Object> lineStringGeometry = new java.util.HashMap<>();
                            lineStringGeometry.put("type", "LineString");
                            lineStringGeometry.put("coordinates", lineStringCoordinates);
                            expandedFeature.setGeometry(lineStringGeometry);
                            
                            expandedFeatures.add(expandedFeature);
                        }
                    }
                } else {
                    // LineString or other geometry types
                    expandedFeatures.add(feature);
                }
            }

            @Override
            public GeoJsonFeature read() throws Exception {
                initialize();
                
                if (currentIndex < expandedFeatures.size()) {
                    return expandedFeatures.get(currentIndex++);
                }
                return null;
            }
        };
    }

    /**
     * takes geojson data
     * converts linestring to list of coordinates and stores in the database as a
     * stringified list of coordinate pairs
     * example: [[lon1, lat1], [lon2, lat2], ...
     * also calculates the distance of the shipping lane and stores it in the
     * database
     */
    @Component
    public class ShippinglaneProcessor implements ItemProcessor<GeoJsonFeature, ShippingLaneDataclass> {

        @Override
        @SuppressWarnings("unchecked")
        public ShippingLaneDataclass process(GeoJsonFeature feature) {
            if (feature == null) {
                return null;
            }
            Map<String, Object> geometry = feature.getGeometry();

            ShippingLaneDataclass shippingLane = new ShippingLaneDataclass();
            List<List<Double>> coordinates = geometry != null ? extractLineCoordinates(geometry.get("coordinates"))
                    : null;

            if (coordinates == null || coordinates.isEmpty()) {
                return null;
            }

            List<Double> pathLong = new ArrayList<>(coordinates.size());
            List<Double> pathLat = new ArrayList<>(coordinates.size());
            for (List<Double> coordinate : coordinates) {
                if (coordinate == null || coordinate.size() < 2 || coordinate.get(0) == null
                        || coordinate.get(1) == null) {
                    return null;
                }
                pathLong.add(coordinate.get(0));
                pathLat.add(coordinate.get(1));
            }

            shippingLane.setPathLong(pathLong);
            shippingLane.setPathLat(pathLat);
            shippingLane.setLane_name(null); // Can be derived from properties if available
            shippingLane.setDistance_km(0.0); // Will be calculated by PostGIS in the database
            
            return shippingLane;
        }
    }

    @Bean
    public JdbcBatchItemWriter<ShippingLaneDataclass> shippinglaneItemWriter(@Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<ShippingLaneDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql(
                "INSERT INTO shipping_lanes (lane_name, geom, distance_km) VALUES " + 
                "(?, ST_SetSRID(ST_MakeLine(ARRAY(SELECT ST_MakePoint(lon, lat) "+ 
                "FROM unnest(CAST(? AS double precision[]), CAST(? AS double precision[])) AS coords(lon, lat))), 4326), ?)");
         writer.setItemPreparedStatementSetter((item, statement) -> {
                statement.setString(1, item.getLane_name());
                statement.setArray(2, statement.getConnection().createArrayOf("float8", item.getPathLong().toArray(new Double[0])));
                statement.setArray(3, statement.getConnection().createArrayOf("float8", item.getPathLat().toArray(new Double[0])));
                statement.setDouble(4, item.getDistance_km());
            
        });

        return writer;

    }

    @SuppressWarnings("unchecked")
    private List<List<Double>> extractLineCoordinates(Object coordinatesObject) {
        if (!(coordinatesObject instanceof List<?> rawCoordinates) || rawCoordinates.size() < 2) {
            return null;
        }

        List<List<Double>> coordinates = new ArrayList<>(rawCoordinates.size());
        for (Object rawCoordinate : rawCoordinates) {
            if (!(rawCoordinate instanceof List<?> point) || point.size() < 2) {
                return null;
            }
            Double longitude = toDouble(point.get(0));
            Double latitude = toDouble(point.get(1));
            if (longitude == null || latitude == null) {
                return null;
            }
            coordinates.add(List.of(longitude, latitude));
        }

        return coordinates;
    }

    private Double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value instanceof String text) {
            String trimmed = text.trim();
            if (!trimmed.isEmpty()) {
                try {
                    return Double.valueOf(trimmed);
                } catch (NumberFormatException ex) {
                    log.debug("Unable to parse double value '{}'", trimmed, ex);
                }
            }
        }
        return null;
    }

}
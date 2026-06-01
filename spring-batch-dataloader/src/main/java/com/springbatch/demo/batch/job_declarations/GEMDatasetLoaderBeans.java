package com.springbatch.demo.batch.job_declarations;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.sql.DataSource;

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
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;

import com.springbatch.demo.batch.util.GeoJsonResources;
import com.springbatch.demo.batch.util.ImportStepListener;
import com.springbatch.demo.model.import_models.GeoJsonFeature;
import com.springbatch.demo.model.output_models.GEMDataclass;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@EnableBatchProcessing(dataSourceRef = "batchDataSource", transactionManagerRef = "transactionManager")
@Configuration
public class GEMDatasetLoaderBeans {

    private static final String GEM_PIPELINE_INSERT_SQL = "INSERT INTO gem_pipeline_segments (" +
            "project_id, pipeline_name, segment_name, wiki, status, fuel, countries_or_areas, owner, parent, parent_entity_ids, "
            +
            "start_year_1, start_year_2, start_year_3, shelved_year, cancelled_year, stop_year, capacity, capacity_units, "
            +
            "capacity_bcm_y, capacity_boe_d, length_known_km, length_estimate_km, length_merged_km, diameter_raw, diameter_units, "
            +
            "start_country_or_area, start_state_province, start_prefecture_district, end_location, end_country_or_area, "
            +
            "end_state_province, end_prefecture_district, route_accuracy, route_type, geom" +
            ") VALUES (" +
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, " +
            "ST_SetSRID(ST_MakeLine(ARRAY(" +
            "SELECT ST_MakePoint(path_long, path_lat) " +
            "FROM unnest(CAST(? AS double precision[]), CAST(? AS double precision[])) WITH ORDINALITY AS points(path_long, path_lat, ord) "
            +
            "ORDER BY ord" +
            ")), 4326)" +
            ")";

    /**
     * Job definition for importing GEM dataset items. This job consists of two
     * steps:
     * 1. truncate step: A tasklet step that truncates the table before import to
     * ensure a clean slate.
     * 2. import Step: A chunk-oriented step that reads GeoJSON features
     * from a file, processes them and writes them to the database.
     */
    @Bean
    public Job importGEMDataJob(JobRepository jobRepository,
            Step truncateGEMDataStep,
            Step importGEMDataStep) {
        return new JobBuilder("importGEMDataJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(truncateGEMDataStep)
                .next(importGEMDataStep)
                .build();
    }

    /**
     * Step definition for truncating the table. This step uses a
     * tasklet to execute a SQL command that truncates the table and resets the
     * identity sequence. This ensures that each run of the import job starts with a
     * clean slate.
     */
    @Bean
    public Step truncateGEMDataStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

        return new StepBuilder("truncateGEMDataStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    int deleted = jdbcTemplate.update("TRUNCATE TABLE gem_pipeline_segments RESTART IDENTITY CASCADE");
                    log.info("Truncated gem_pipeline_segments before import; JDBC update count={}", deleted);
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    /**
     * Step definition for importing generic nodes from a GeoJSON file. This step is
     * a chunk-oriented step that reads GeoJSON features, processes them into
     * GEMDataclass objects, and writes them to the database. The step is
     * configured to be fault-tolerant, skipping any records that cause
     * DataIntegrityViolationException
     * during the write phase, allowing the import to continue even if some records
     * fail to insert due to integrity constraints.
     */
    @Bean
    public Step importGEMDataStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            JsonItemReader<GeoJsonFeature> GEMDataReader,
            GEMdataProcessor processor,
            JdbcBatchItemWriter<GEMDataclass> GEMDataWriter) {
        return new StepBuilder("importGEMDataStep", jobRepository)
                .<GeoJsonFeature, GEMDataclass>chunk(10, transactionManager)
                .reader(GEMDataReader)
                .processor(processor)
                .writer(GEMDataWriter)
                .faultTolerant()
                .skip(DataIntegrityViolationException.class)
                .skipLimit(Integer.MAX_VALUE)
                .listener(new ImportStepListener())
                .build();
    }

    /**
     * Bean definition for the JsonItemReader that reads GeoJSON features from a
     * file.
     */
    @Bean
    public JsonItemReader<GeoJsonFeature> GEMDataReader() {
        JacksonJsonObjectReader<GeoJsonFeature> jsonObjectReader = new JacksonJsonObjectReader<>(GeoJsonFeature.class);

        JsonItemReader<GeoJsonFeature> reader = new JsonItemReader<>();
        reader.setResource(
                GeoJsonResources.featuresArray(new ClassPathResource("data/GEM-GGIT-Gas-Pipelines-2025-11.geojson")));
        reader.setJsonObjectReader(jsonObjectReader);
        reader.setName("geoJsonReader");
        reader.setStrict(false);

        return reader;
    }

    /**
     * ItemProcessor implementation that transforms GeoJsonFeature objects into
     * GEMDataclass objects suitable for database insertion. The processor
     * extracts relevant properties from the GeoJsonFeature, including geometry and
     * attributes, and maps them to the corresponding fields in the GEMDataclass.
     */
    @Component
    public class GEMdataProcessor implements ItemProcessor<GeoJsonFeature, GEMDataclass> {
        @Override
        @SuppressWarnings("unchecked")
        public GEMDataclass process(GeoJsonFeature feature) {
            if (feature == null) {
                return null;
            }

            Map<String, Object> geometry = feature.getGeometry();
            Map<String, Object> properties = feature.getProperties();
            List<List<Double>> coordinates = geometry != null ? extractLineCoordinates(geometry.get("coordinates"))
                    : null;

            if (properties == null || coordinates == null || coordinates.size() < 2) {
                return null;
            }

            GEMDataclass segment = new GEMDataclass();
            segment.setProject_id(getString(properties, "project_id", "ProjectID"));
            segment.setPipeline_name(getString(properties, "pipeline_name", "PipelineName"));
            segment.setSegment_name(getString(properties, "segment_name", "SegmentName"));
            segment.setWiki(getString(properties, "wiki", "Wiki"));
            segment.setStatus(getString(properties, "status", "Status"));
            segment.setFuel(getString(properties, "fuel", "Fuel"));
            segment.setCountries_or_areas(getString(properties, "countries_or_areas", "CountriesOrAreas"));
            segment.setOwner(getString(properties, "owner", "Owner"));
            segment.setParent(getString(properties, "parent", "Parent"));
            String parentEntityIdsStr = getString(properties, "parent_entity_ids", "ParentEntityIDs");
            if (parentEntityIdsStr != null) {
                List<String> parentEntityIds = splitCsv(parentEntityIdsStr);
                segment.setParent_entity_ids(parentEntityIds.isEmpty() ? null : parentEntityIds);
            }

            segment.setStart_year_1(getInteger(properties, "StartYear1", "start_year_1"));
            segment.setStart_year_2(getInteger(properties, "StartYear2", "start_year_2"));
            segment.setStart_year_3(getInteger(properties, "StartYear3", "start_year_3"));
            segment.setShelved_year(getInteger(properties, "ShelvedYear", "shelved_year"));
            segment.setCancelled_year(getInteger(properties, "CancelledYear", "cancelled_year"));
            segment.setStop_year(getInteger(properties, "StopYear", "stop_year"));
            segment.setCapacity(getDouble(properties, "Capacity", "capacity"));
            segment.setCapacity_units(getString(properties, "CapacityUnits", "capacity_units"));
            segment.setCapacity_bcm_y(getDouble(properties, "CapacityBcm/y", "capacity_bcm_y"));
            segment.setCapacity_boe_d(getDouble(properties, "CapacityBOEd", "capacity_boe_d"));
            segment.setLength_known_km(getDouble(properties, "LengthKnownKm", "length_known_km"));
            segment.setLength_estimate_km(getDouble(properties, "LengthEstimateKm", "length_estimate_km"));
            segment.setLength_merged_km(getDouble(properties, "LengthMergedKm", "length_merged_km"));
            segment.setDiameter_raw(getString(properties, "Diameter", "diameter_raw"));
            segment.setDiameter_units(getString(properties, "DiameterUnits", "diameter_units"));
            segment.setStart_country_or_area(getString(properties, "StartCountryOrArea", "start_country_or_area"));
            segment.setStart_state_province(getString(properties, "StartState/Province", "start_state_province"));
            segment.setStart_prefecture_district(
                    getString(properties, "StartPrefecture/District", "start_prefecture_district"));
            segment.setEnd_location(getString(properties, "EndLocation", "end_location"));
            segment.setEnd_country_or_area(getString(properties, "EndCountryOrArea", "end_country_or_area"));
            segment.setEnd_state_province(getString(properties, "EndState/Province", "end_state_province"));
            segment.setEnd_prefecture_district(
                    getString(properties, "EndPrefecture/District", "end_prefecture_district"));
            segment.setRoute_accuracy(getString(properties, "RouteAccuracy", "route_accuracy"));
            segment.setRoute_type(getString(properties, "RouteType", "route_type"));

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

            segment.setPathLong(pathLong);
            segment.setPathLat(pathLat);
            return segment;
        }
    }

    @Bean
    public JdbcBatchItemWriter<GEMDataclass> GEMDataWriter(@Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<GEMDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql(GEM_PIPELINE_INSERT_SQL);
        writer.setItemPreparedStatementSetter((item, statement) -> {
            statement.setString(1, item.getProject_id());
            statement.setString(2, item.getPipeline_name());
            statement.setString(3, item.getSegment_name());
            statement.setString(4, item.getWiki());
            statement.setString(5, item.getStatus());
            statement.setString(6, item.getFuel());
            statement.setString(7, item.getCountries_or_areas());
            statement.setString(8, item.getOwner());
            statement.setString(9, item.getParent());
            if (item.getParent_entity_ids() != null && !item.getParent_entity_ids().isEmpty()) {
                statement.setArray(10,
                        statement.getConnection().createArrayOf("text",
                                item.getParent_entity_ids().toArray(new String[0])));
            } else {
                statement.setArray(10, null);
            }
            statement.setObject(11, item.getStart_year_1());
            statement.setObject(12, item.getStart_year_2());
            statement.setObject(13, item.getStart_year_3());
            statement.setObject(14, item.getShelved_year());
            statement.setObject(15, item.getCancelled_year());
            statement.setObject(16, item.getStop_year());
            statement.setObject(17, item.getCapacity());
            statement.setString(18, item.getCapacity_units());
            statement.setObject(19, item.getCapacity_bcm_y());
            statement.setObject(20, item.getCapacity_boe_d());
            statement.setObject(21, item.getLength_known_km());
            statement.setObject(22, item.getLength_estimate_km());
            statement.setObject(23, item.getLength_merged_km());
            statement.setString(24, item.getDiameter_raw());
            statement.setString(25, item.getDiameter_units());
            statement.setString(26, item.getStart_country_or_area());
            statement.setString(27, item.getStart_state_province());
            statement.setString(28, item.getStart_prefecture_district());
            statement.setString(29, item.getEnd_location());
            statement.setString(30, item.getEnd_country_or_area());
            statement.setString(31, item.getEnd_state_province());
            statement.setString(32, item.getEnd_prefecture_district());
            statement.setString(33, item.getRoute_accuracy());
            statement.setString(34, item.getRoute_type());
            statement.setArray(35,
                    statement.getConnection().createArrayOf("float8", item.getPathLong().toArray(new Double[0])));
            statement.setArray(36,
                    statement.getConnection().createArrayOf("float8", item.getPathLat().toArray(new Double[0])));
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

    private List<String> splitCsv(String value) {
        List<String> values = new ArrayList<>();
        for (String token : value.split(",")) {
            String trimmed = token.trim();
            if (!trimmed.isEmpty()) {
                values.add(trimmed);
            }
        }
        return values;
    }

    private String getString(Map<String, Object> properties, String... keys) {
        for (String key : keys) {
            Object value = properties.get(key);
            if (value != null) {
                String text = value.toString().trim();
                if (!text.isEmpty()) {
                    return text;
                }
            }
        }
        return null;
    }

    private Integer getInteger(Map<String, Object> properties, String... keys) {
        for (String key : keys) {
            Integer value = toInteger(properties.get(key));
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private Double getDouble(Map<String, Object> properties, String... keys) {
        for (String key : keys) {
            Double value = toDouble(properties.get(key));
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private Integer toInteger(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value instanceof String text) {
            String trimmed = text.trim();
            if (!trimmed.isEmpty()) {
                try {
                    return Integer.valueOf(trimmed);
                } catch (NumberFormatException ex) {
                    log.debug("Unable to parse integer value '{}'", trimmed, ex);
                }
            }
        }
        return null;
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

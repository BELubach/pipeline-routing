/*
 * Copyright 2023 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.springbatch.demo.batch.job_declarations;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import javax.sql.DataSource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.batch.item.json.JacksonJsonObjectReader;
import org.springframework.batch.item.json.JsonItemReader;
import org.springframework.batch.item.database.JdbcCursorItemReader;
import org.springframework.jdbc.core.RowMapper;

import com.springbatch.demo.batch.util.GeoJsonResources;
import com.springbatch.demo.batch.util.ImportStepListener;
import com.springbatch.demo.model.import_models.PipeSegmentGeoJsonFeature;
import com.springbatch.demo.model.import_models.PipeSegmentGeoJsonParam;
import com.springbatch.demo.model.import_models.PipeSegmentGeoJsonProperties;
import com.springbatch.demo.model.output_models.PipeSegmentDataclass;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.EnableBatchProcessing;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.launch.support.RunIdIncrementer;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.database.JdbcBatchItemWriter;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;

import org.springframework.dao.DataIntegrityViolationException;

@Configuration
@EnableBatchProcessing(dataSourceRef = "batchDataSource", transactionManagerRef = "transactionManager")
public class PipeSegmentsBeans {

    private static final Logger log = LoggerFactory.getLogger(PipeSegmentsBeans.class);
    private static final int FILTER_LOG_SAMPLE_LIMIT = 25;

    @Value("${pipe.segment.snap-distance-meters:5000}")
    private double snapDistanceMeters;

    private static final String PIPE_SEGMENT_INSERT_SQL = "INSERT INTO pipeline_segments (" +
            "\"IGGIELGN_id\", country_code_from, country_code_to, \"is_H_gas\", length_km, diameter_mm, \"max_cap_M_m3_per_d\", max_pressure_bar, geom"
            +
            ") VALUES (" +
            "?, ?, ?, ?, ?, ?, ?, ?, " +
            "ST_SetSRID(ST_MakeLine(ARRAY(" +
            "SELECT ST_MakePoint(path_long, path_lat) " +
            "FROM unnest(CAST(? AS double precision[]), CAST(? AS double precision[])) WITH ORDINALITY AS points(path_long, path_lat, ord) "
            +
            "ORDER BY ord" +
            ")), 4326)" +
            ")";

    /**
     * Job definition for importing pipe segments from GeoJSON file and snapping
     * them to nearest nodes.
     * The job consists of three steps:
     * 1) truncatePipelineSegmentsStep: Clears existing pipe segments from the
     * database to ensure a clean state for the import.
     * 2) importPipeSegmentsStep: Imports pipe segments from GeoJSON file and stores
     * them in the database, including creating the geometry from the path
     * coordinates.
     * 3) snapPipeSegmentsToNodesStep: For segments that were not snapped to nodes
     * in the initial import, attempts to snap them to the nearest nodes based on
     * from/to coordinates.
     */
    @Bean
    public Job importPipeSegmentsJob(JobRepository jobRepository,
            Step truncatePipelineSegmentsStep,
            Step importPipeSegmentsStep,
            Step snapPipeSegmentsToNodesStep) {
        return new JobBuilder("importPipeSegmentsJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(truncatePipelineSegmentsStep)
                .next(importPipeSegmentsStep)
                .next(snapPipeSegmentsToNodesStep)
                .build();
    }

    /**
     * Step definition to clear any existing pipe segments from the database before
     * importing new ones
     * prevents creating duplicate entries if the job is run multiple times and
     * ensures a clean state for the import.
     */
    @Bean
    public Step truncatePipelineSegmentsStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

        return new StepBuilder("truncatePipelineSegmentsStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    int deleted = jdbcTemplate.update("TRUNCATE TABLE pipeline_segments RESTART IDENTITY");
                    log.info("Truncated pipeline_segments before import; JDBC update count={}", deleted);
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    /**
     * Geojson ItemReader to read pipe segments from GeoJSON file.
     * Reads features and maps them to PipeSegmentGeoJsonFeature objects for
     * processing in the pipeline segment import step.
     */
    @Bean
    public JsonItemReader<PipeSegmentGeoJsonFeature> pipeSegmentReader() {
        JacksonJsonObjectReader<PipeSegmentGeoJsonFeature> jsonObjectReader = new JacksonJsonObjectReader<>(
                PipeSegmentGeoJsonFeature.class);

        JsonItemReader<PipeSegmentGeoJsonFeature> reader = new JsonItemReader<>();
        reader.setResource(GeoJsonResources.featuresArray(new ClassPathResource("data/IGGIELGN_PipeSegments.geojson")));
        reader.setJsonObjectReader(jsonObjectReader);
        reader.setName("geoJsonReader");
        reader.setStrict(false);

        return reader;
    }

    /**
     * ItemProcessor that converts PipeSegmentGeoJsonFeature items read from the
     * GeoJSON file into PipeSegmentDataclass items for writing to the database.
     * The processor handles the mapping of properties and geometry, including
     * constructing the path arrays and handling potential issues with the input
     * data.
     */
    @Component
    public class PipelineGeoJsonProcessor implements ItemProcessor<PipeSegmentGeoJsonFeature, PipeSegmentDataclass> {

        private final AtomicInteger filteredCount = new AtomicInteger();

        @Override
        @SuppressWarnings("unchecked")
        public PipeSegmentDataclass process(PipeSegmentGeoJsonFeature feature) {
            if (feature == null) {
                logFilteredSegment("feature is null", null, null, null, null);
                return null;
            }

            Map<String, Object> geometry = feature.getGeometry();
            PipeSegmentGeoJsonProperties properties = feature.getProperties();
            PipeSegmentGeoJsonParam param = properties != null ? properties.getParam() : null;
            List<List<Double>> coordinates = geometry != null ? (List<List<Double>>) geometry.get("coordinates") : null;

            if (coordinates == null || coordinates.size() < 2) {
                logFilteredSegment("geometry coordinates missing or too short", feature, coordinates, null, null);
                return null;
            }

            List<Double> startCoordinate = coordinates.get(0);
            List<Double> endCoordinate = coordinates.get(1);

            if (startCoordinate == null || startCoordinate.size() < 2 || endCoordinate == null
                    || endCoordinate.size() < 2) {
                logFilteredSegment("start or end coordinate invalid", feature, coordinates, null, null);
                return null;
            }

            List<Double> pathLong = new ArrayList<>();
            List<Double> pathLat = new ArrayList<>();
            pathLong.add(startCoordinate.get(0));
            pathLat.add(startCoordinate.get(1));

            List<Double> intermediatePathLong = param != null ? param.getPathLong() : null;
            List<Double> intermediatePathLat = param != null ? param.getPathLat() : null;
            boolean hasIntermediatePath = intermediatePathLong != null && !intermediatePathLong.isEmpty()
                    || intermediatePathLat != null && !intermediatePathLat.isEmpty();

            if (hasIntermediatePath) {
                if (intermediatePathLong != null && intermediatePathLat != null
                        && intermediatePathLong.size() == intermediatePathLat.size()) {
                    pathLong.addAll(intermediatePathLong);
                    pathLat.addAll(intermediatePathLat);
                } else {
                    log.warn(
                            "Ignoring malformed intermediate path arrays for pipeline segment {} [{}]: pathLong={}, pathLat={}",
                            properties != null ? properties.getId() : "<unknown>",
                            properties != null ? properties.getName() : "<unknown>",
                            intermediatePathLong != null ? intermediatePathLong.size() : -1,
                            intermediatePathLat != null ? intermediatePathLat.size() : -1);
                }
            }

            pathLong.add(endCoordinate.get(0));
            pathLat.add(endCoordinate.get(1));

            if (pathLong.size() < 2 || pathLat.size() < 2 || pathLong.size() != pathLat.size()) {
                logFilteredSegment("path arrays invalid", feature, coordinates, pathLong, pathLat);
                return null;
            }

            PipeSegmentDataclass segment = new PipeSegmentDataclass();
            segment.setIggielgnId(properties.getId());
            if (properties.getCountryCode() != null && !properties.getCountryCode().isEmpty()) {
                segment.setCountryCodeFrom(properties.getCountryCode().get(0));
                segment.setCountryCodeTo(properties.getCountryCode().size() > 1
                        ? properties.getCountryCode().get(1)
                        : properties.getCountryCode().get(0));
            }

            if (param != null) {
                segment.setHGas(param.getIsHGas() != null && param.getIsHGas() == 1);
                segment.setLengthKm(param.getLengthKm());
                segment.setDiameterMm(param.getDiameterMm());
                segment.setMaxCapMM3PerD(param.getMaxCapMM3PerD());
                segment.setMaxPressureBar(param.getMaxPressureBar());
            }

            segment.setFromLongitude(pathLong.get(0));
            segment.setFromLatitude(pathLat.get(0));
            segment.setToLongitude(pathLong.get(pathLong.size() - 1));
            segment.setToLatitude(pathLat.get(pathLat.size() - 1));
            segment.setPathLong(pathLong);
            segment.setPathLat(pathLat);

            return segment;
        }

        private void logFilteredSegment(String reason, PipeSegmentGeoJsonFeature feature,
                List<List<Double>> coordinates,
                List<Double> pathLong, List<Double> pathLat) {
            int count = filteredCount.incrementAndGet();
            PipeSegmentGeoJsonProperties properties = feature != null ? feature.getProperties() : null;
            String id = properties != null ? properties.getId() : "<unknown>";
            String name = properties != null ? properties.getName() : "<unknown>";
            int coordinateCount = coordinates != null ? coordinates.size() : -1;
            int pathLongCount = pathLong != null ? pathLong.size() : -1;
            int pathLatCount = pathLat != null ? pathLat.size() : -1;

            if (count <= FILTER_LOG_SAMPLE_LIMIT) {
                log.warn(
                        "Filtering pipeline segment {} [{}]: reason='{}', coordinates={}, pathLong={}, pathLat={}",
                        id,
                        name,
                        reason,
                        coordinateCount,
                        pathLongCount,
                        pathLatCount);
                if (count == FILTER_LOG_SAMPLE_LIMIT) {
                    log.warn(
                            "Reached filter log sample limit of {}; further filtered segments will be summarized every 100 records.",
                            FILTER_LOG_SAMPLE_LIMIT);
                }
                return;
            }

            if (count % 100 == 0) {
                log.warn("Filtered {} pipeline segments so far; latest was {} [{}] with reason='{}'.",
                        count,
                        id,
                        name,
                        reason);
            }
        }
    }

    /**
     * JdbcBatchItemWriter to write pipe segments to the database.
     * Maps PipeSegmentDataclass fields to the corresponding database columns AND
     * handles the geometry creation from the path coordinates.
     */
    @Bean
    public JdbcBatchItemWriter<PipeSegmentDataclass> pipeSegmentWriter(
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<PipeSegmentDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql(PIPE_SEGMENT_INSERT_SQL);
        writer.setItemPreparedStatementSetter((item, statement) -> {
            statement.setString(1, item.getIggielgnId());
            statement.setString(2, item.getCountryCodeFrom());
            statement.setString(3, item.getCountryCodeTo());
            statement.setObject(4, item.getHGas());
            statement.setObject(5, item.getLengthKm());
            statement.setObject(6, item.getDiameterMm());
            statement.setObject(7, item.getMaxCapMM3PerD());
            statement.setObject(8, item.getMaxPressureBar());
            statement.setArray(9,
                    statement.getConnection().createArrayOf("float8", item.getPathLong().toArray(new Double[0])));
            statement.setArray(10,
                    statement.getConnection().createArrayOf("float8", item.getPathLat().toArray(new Double[0])));
        });
        return writer;

    }

    /**
     * Step definiation import pipe segments from GeoJSON file.
     * Reads features and stores plain segments values AND
     * creates a geom object from the start/end coordinates plus path if available.
     */
    @Bean
    public Step importPipeSegmentsStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            JsonItemReader<PipeSegmentGeoJsonFeature> pipeSegmentReader,
            PipelineGeoJsonProcessor processor,
            JdbcBatchItemWriter<PipeSegmentDataclass> pipeSegmentWriter) {
        return new StepBuilder("importPipeSegmentsStep", jobRepository)
                .<PipeSegmentGeoJsonFeature, PipeSegmentDataclass>chunk(10, transactionManager)
                .reader(pipeSegmentReader)
                .processor(processor)
                .writer(pipeSegmentWriter)
                .faultTolerant()
                .skip(DataIntegrityViolationException.class)
                .skipLimit(Integer.MAX_VALUE)
                .listener(new ImportStepListener())
                .build();
    }

    // ============================================
    // STEP 2: Snap pipe segments to nodes
    // ============================================

    /**
     * JdbcCursorItemReader to read pipe segments that were not snapped to nodes
     * that either not have a from_node_id or to_node_id
     */
    @Bean
    public JdbcCursorItemReader<PipeSegmentDataclass> pipeSegmentDatabaseReader(
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcCursorItemReader<PipeSegmentDataclass> reader = new JdbcCursorItemReader<>();
        reader.setDataSource(dataSource);
        reader.setSql("SELECT id, \"IGGIELGN_id\", from_node_id, to_node_id, country_code_from, country_code_to, " +
                "\"is_H_gas\", length_km, diameter_mm, \"max_cap_M_m3_per_d\", max_pressure_bar, " +
                "ST_X(ST_PointN(geom, 1)) as from_longitude, ST_Y(ST_PointN(geom, 1)) as from_latitude, " +
                "ST_X(ST_PointN(geom, -1)) as to_longitude, ST_Y(ST_PointN(geom, -1)) as to_latitude " +
                "FROM pipeline_segments WHERE from_node_id IS NULL OR to_node_id IS NULL");
        reader.setRowMapper(pipeSegmentRowMapper());
        reader.setName("pipeSegmentDatabaseReader");
        return reader;
    }

    /**
     * ItemProcessor that attempts to snap pipe segments to the nearest nodes based
     * on from/to coordinates for segments that were not snapped in the initial
     * import.
     * The processor uses a JDBC template to query for the nearest node within the
     * configured snap distance and updates the segment's from_node_id and
     * to_node_id accordingly.
     * 
     */
    @Component
    public class PipeSegmentSnappingProcessor implements ItemProcessor<PipeSegmentDataclass, PipeSegmentDataclass> {

        private final JdbcTemplate jdbcTemplate;
        private final AtomicInteger snappedCount = new AtomicInteger();
        private final AtomicInteger unsnappedCount = new AtomicInteger();

        public PipeSegmentSnappingProcessor(@Qualifier("appDataSource") DataSource dataSource) {
            this.jdbcTemplate = new JdbcTemplate(dataSource);
        }

        @Override
        public PipeSegmentDataclass process(PipeSegmentDataclass segment) {
            if (segment.getFromNodeId() == null) {
                Integer fromNodeId = findNearestNode(segment.getFromLongitude(), segment.getFromLatitude());
                segment.setFromNodeId(fromNodeId);
                if (fromNodeId != null) {
                    snappedCount.incrementAndGet();
                } else {
                    unsnappedCount.incrementAndGet();
                    log.warn("Could not snap FROM endpoint of segment {} [{}] at ({}, {}) within {} meters",
                            segment.getIggielgnId(),
                            segment.getId(),
                            segment.getFromLongitude(),
                            segment.getFromLatitude(),
                            snapDistanceMeters);
                }
            }

            if (segment.getToNodeId() == null) {
                Integer toNodeId = findNearestNode(segment.getToLongitude(), segment.getToLatitude());
                segment.setToNodeId(toNodeId);
                if (toNodeId != null) {
                    snappedCount.incrementAndGet();

                } else {
                    unsnappedCount.incrementAndGet();
                    log.warn("Could not snap TO endpoint of segment {} [{}] at ({}, {}) within {} meters",
                            segment.getIggielgnId(),
                            segment.getId(),
                            segment.getToLongitude(),
                            segment.getToLatitude(),
                            snapDistanceMeters);
                }
            }

            if (segment.getFromNodeId() == null || segment.getToNodeId() == null) {
                return null;
            }

            return segment;
        }

        private Integer findNearestNode(double longitude, double latitude) {
            String sql = "SELECT id FROM generic_nodes " +
                    "WHERE ST_DWithin(CAST(geom AS geography), CAST(ST_SetSRID(ST_MakePoint(?, ?), 4326) AS geography), ?) "
                    +
                    "ORDER BY ST_Distance(CAST(geom AS geography), CAST(ST_SetSRID(ST_MakePoint(?, ?), 4326) AS geography)) "
                    +
                    "LIMIT 1";

            List<Integer> results = jdbcTemplate.queryForList(sql, Integer.class,
                    longitude, latitude, snapDistanceMeters, longitude, latitude);

            return results.isEmpty() ? null : results.get(0);
        }
    }

    /**
     * JdbcBatchItemWriter to update pipe segments with snapped node IDs after
     * processing.
     * This writer is used in the snapPipeSegmentsToNodesStep to persist the updated
     * from_node_id and to_node_id for each segment that was successfully snapped to
     * nearby nodes.
     * Saves PipeSegmentDataclass items by executing an UPDATE statement that sets
     * the from_node_id and to_node_id based on the segment's id.
     */
    @Bean
    public JdbcBatchItemWriter<PipeSegmentDataclass> pipeSegmentNodeUpdater(
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<PipeSegmentDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql("UPDATE pipeline_segments SET from_node_id = ?, to_node_id = ? WHERE id = ?");
        writer.setItemPreparedStatementSetter((item, statement) -> {
            statement.setInt(1, item.getFromNodeId());
            statement.setInt(2, item.getToNodeId());
            statement.setInt(3, item.getId());
        });
        return writer;
    }

    /**
     * Step to snap pipe segments to nearest nodes based on from/to coordinates for
     * segments that were not snapped in the initial import.
     * The processor attempts to find the nearest node within the configured snap
     * distance and updates the segment's from_node_id and to_node_id accordingly.
     * 
     * @param jobRepository
     * @param transactionManager
     * @param pipeSegmentDatabaseReader
     * @param snappingProcessor
     * @param pipeSegmentNodeUpdater
     * @return step to snap pipe segments to nearest nodes
     */
    @Bean
    public Step snapPipeSegmentsToNodesStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            JdbcCursorItemReader<PipeSegmentDataclass> pipeSegmentDatabaseReader,
            PipeSegmentSnappingProcessor snappingProcessor,
            JdbcBatchItemWriter<PipeSegmentDataclass> pipeSegmentNodeUpdater) {
        return new StepBuilder("snapPipeSegmentsToNodesStep", jobRepository)
                .<PipeSegmentDataclass, PipeSegmentDataclass>chunk(10, transactionManager)
                .reader(pipeSegmentDatabaseReader)
                .processor(snappingProcessor)
                .writer(pipeSegmentNodeUpdater)
                .listener(new ImportStepListener())
                .build();
    }

    // ============================================
    // Helper methods
    // ============================================

    /**
     * Helper method to map SQL result set rows to PipeSegmentDataclass instances.
     * Used to read items in the second phase by the JdbcCursorItemReader to read
     * segments that need snapping.
     * 
     * @return a RowMapper that converts SQL result set rows into
     *         PipeSegmentDataclass objects, handling potential nulls appropriately
     */
    private RowMapper<PipeSegmentDataclass> pipeSegmentRowMapper() {
        return (rs, rowNum) -> {
            PipeSegmentDataclass segment = new PipeSegmentDataclass();
            segment.setId(rs.getInt("id"));
            segment.setIggielgnId(rs.getString("IGGIELGN_id"));

            // On read the from_node_id and to_node_id can be null, so we use getObject and
            // cast to Integer to handle nulls properly
            // If we used getInt, it would return 0 for nulls, which could lead to incorrect
            // snapping logic
            // also, if we skip these fields entirely we need to snap all preexisting
            // segments, right now either from and to could have a valid node id,
            // so we want to preserve that if it exists and only snap the null endpoint
            Integer fromNodeId = (Integer) rs.getObject("from_node_id");
            Integer toNodeId = (Integer) rs.getObject("to_node_id");
            segment.setFromNodeId(fromNodeId);
            segment.setToNodeId(toNodeId);

            segment.setCountryCodeFrom(rs.getString("country_code_from"));
            segment.setCountryCodeTo(rs.getString("country_code_to"));
            segment.setHGas((Boolean) rs.getObject("is_H_gas"));
            segment.setLengthKm(getDoubleOrNull(rs, "length_km"));
            segment.setDiameterMm(getDoubleOrNull(rs, "diameter_mm"));
            segment.setMaxCapMM3PerD(getDoubleOrNull(rs, "max_cap_M_m3_per_d"));
            segment.setMaxPressureBar(getDoubleOrNull(rs, "max_pressure_bar"));
            segment.setFromLongitude(rs.getDouble("from_longitude"));
            segment.setFromLatitude(rs.getDouble("from_latitude"));
            segment.setToLongitude(rs.getDouble("to_longitude"));
            segment.setToLatitude(rs.getDouble("to_latitude"));
            return segment;
        };

    }

    /**
     * Helper method to safely get Double values from a ResultSet, returning null if
     * the
     * 
     * @param rs
     * @param columnName
     * @return Double value from the ResultSet for the given column name, or null if
     *         the value is SQL NULL or not a number
     * @throws SQLException
     */
    private Double getDoubleOrNull(java.sql.ResultSet rs, String columnName) throws SQLException {
        Object value = rs.getObject(columnName);
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return null;
    }

}
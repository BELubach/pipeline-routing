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

import java.util.List;
import java.util.Map;

import javax.sql.DataSource;

import org.springframework.batch.item.json.JacksonJsonObjectReader;
import org.springframework.batch.item.json.JsonItemReader;
import org.springframework.batch.repeat.RepeatStatus;

import com.springbatch.demo.batch.util.GeoJsonResources;
import com.springbatch.demo.batch.util.ImportStepListener;
import com.springbatch.demo.model.import_models.GeoJsonFeature;
import com.springbatch.demo.model.output_models.BorderNodeDataclass;

import lombok.extern.slf4j.Slf4j;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.EnableBatchProcessing;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.launch.support.RunIdIncrementer;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.database.BeanPropertyItemSqlParameterSourceProvider;
import org.springframework.batch.item.database.JdbcBatchItemWriter;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;

@Slf4j
@Configuration
@EnableBatchProcessing(dataSourceRef = "batchDataSource", transactionManagerRef = "transactionManager")
public class BorderCrossingBeans {

    /**
     * Job definition for importing border crossing nodes. This job consists of two
     * steps:
     * 1) Truncate the border_nodes table to ensure a clean slate for the new
     * import.
     * 2) Read border crossing points from a GeoJSON file, process them into a
     * format
     * suitable for database insertion, and write them to the border_nodes table.
     */
    @Bean
    public Job importBorderCrossingJob(JobRepository jobRepository,
            Step truncateBorderCrossingStep,
            Step importGeoJsonStep) {
        return new JobBuilder("importBorderCrossingJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(truncateBorderCrossingStep)
                .next(importGeoJsonStep)
                .build();
    }

    /**
     * Step definition for truncating the border_nodes table before import.
     * This ensures that each run of the job starts with a clean slate, preventing
     * duplicate entries and ensuring data consistency.
     */
    @Bean
    public Step truncateBorderCrossingStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

        return new StepBuilder("truncateBorderCrossingStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    int deleted = jdbcTemplate.update("TRUNCATE TABLE border_nodes RESTART IDENTITY");
                    log.info("Truncated border_nodes before import; JDBC update count={}", deleted);
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    /**
     * Step definition for importing border crossing nodes from a GeoJSON file.
     * This step reads features from the specified GeoJSON resource, processes them
     * into BorderNodeDataclass objects,
     * and writes them to the border_nodes table in the database. The step is
     * fault-tolerant and will skip any records that cause
     * DataIntegrityViolationException,
     * allowing the import to continue even if some records fail due to issues like
     * duplicate keys or constraint violations.
     */
    @Bean
    public Step importGeoJsonStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            JsonItemReader<GeoJsonFeature> reader,
            GeoJsonProcessor processor,
            JdbcBatchItemWriter<BorderNodeDataclass> writer) {
        return new StepBuilder("importGeoJsonStep", jobRepository)
                .<GeoJsonFeature, BorderNodeDataclass>chunk(10, transactionManager)
                .reader(reader)
                .processor(processor)
                .writer(writer)
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
    public JsonItemReader<GeoJsonFeature> reader() {
        JacksonJsonObjectReader<GeoJsonFeature> jsonObjectReader = new JacksonJsonObjectReader<>(GeoJsonFeature.class);

        JsonItemReader<GeoJsonFeature> reader = new JsonItemReader<>();
        reader.setResource(GeoJsonResources.featuresArray(new ClassPathResource("data/IGGIELGN_BorderPoints.geojson")));
        reader.setJsonObjectReader(jsonObjectReader);
        reader.setName("geoJsonReader");
        reader.setStrict(false);

        return reader;
    }

    /**
     * ItemProcessor implementation that transforms GeoJsonFeature objects into
     * BorderNodeDataclass objects suitable for database insertion. The processor
     * extracts relevant properties from the GeoJsonFeature, including geometry and
     * attributes, and maps them to the corresponding fields in the
     * BorderNodeDataclass.
     */
    @Component
    public class GeoJsonProcessor implements ItemProcessor<GeoJsonFeature, BorderNodeDataclass> {
        @Override
        public BorderNodeDataclass process(GeoJsonFeature feature) {
            Map<String, Object> geometry = feature.getGeometry();
            Map<String, Object> properties = feature.getProperties();
            Map<String, Object> param = (Map<String, Object>) properties.get("param");

            List<Double> coordinates = (List<Double>) geometry.get("coordinates");

            BorderNodeDataclass node = new BorderNodeDataclass();
            node.setIGGIELGN_id((String) properties.get("id"));
            node.setName((String) properties.get("name"));
            node.setCountryCode((String) properties.get("country_code"));
            node.setFromCountry((String) param.get("from_country"));
            node.setToCountry((String) param.get("to_country"));
            node.setFromTSO((String) param.get("from_TSO"));
            node.setToTSO((String) param.get("to_TSO"));
            node.setLongitude(coordinates.get(0));
            node.setLatitude(coordinates.get(1));

            return node;
        }
    }

    /**
     * Bean definition for the JdbcBatchItemWriter that writes BorderNodeDataclass
     * objects to the database.
     * The writer is configured with an SQL statement that inserts records into the
     * border_nodes table,
     * mapping the properties of BorderNodeDataclass to the corresponding columns in
     * the database.
     * The geometry is stored using PostGIS functions to convert longitude and
     * latitude into a geometry point with the appropriate spatial reference ID
     * (SRID 4326).
     */
    @Bean
    public JdbcBatchItemWriter<BorderNodeDataclass> writer(@Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<BorderNodeDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql(
                "INSERT INTO border_nodes (\"IGGIELGN_id\", name, geom, country_code, from_country, to_country, \"from_TSO\", \"to_TSO\") "
                        +
                        "VALUES (:IGGIELGN_id, :name, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), :countryCode, :fromCountry, :toCountry, :fromTSO, :toTSO)");
        writer.setItemSqlParameterSourceProvider(new BeanPropertyItemSqlParameterSourceProvider<>());
        return writer;
    }

}
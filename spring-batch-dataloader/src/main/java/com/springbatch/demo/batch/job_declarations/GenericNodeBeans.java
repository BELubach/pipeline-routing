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
import com.springbatch.demo.model.output_models.GenericNodeDataclass;

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
public class GenericNodeBeans {

    /**
     * Job definition for importing generic nodes. This job consists of two steps:
     * 1. truncateGenericNodesStep: A tasklet step that truncates the generic
     * nodes table before import to ensure a clean slate.
     * 2. importGenericNodesStep: A chunk-oriented step that reads GeoJSON features
     * from a file, processes them into GenericNodeDataclass objects, and writes
     * them to the database.
     */
    @Bean
    public Job importGenericNodesJob(JobRepository jobRepository,
            Step truncateGenericNodesStep,
            Step importGenericNodesStep) {
        return new JobBuilder("importGenericNodesJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(truncateGenericNodesStep)
                .next(importGenericNodesStep)
                .build();
    }

    /**
     * Step definition for truncating the generic_nodes table. This step uses a
     * tasklet to execute a SQL command that truncates the table and resets the
     * identity sequence. This ensures that each run of the import job starts with a
     * clean slate.
     */
    @Bean
    public Step truncateGenericNodesStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

        return new StepBuilder("truncateGenericNodesStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    int deleted = jdbcTemplate.update("TRUNCATE TABLE generic_nodes RESTART IDENTITY CASCADE");
                    log.info("Truncated generic_nodes before import; JDBC update count={}", deleted);
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    /**
     * Step definition for importing generic nodes from a GeoJSON file. This step is
     * a chunk-oriented step that reads GeoJSON features, processes them into
     * GenericNodeDataclass objects, and writes them to the database. The step is
     * configured to be fault-tolerant, skipping any records that cause
     * DataIntegrityViolationException
     * during the write phase, allowing the import to continue even if some records
     * fail to insert due to integrity constraints.
     */
    @Bean
    public Step importGenericNodesStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            JsonItemReader<GeoJsonFeature> genericNodeReader,
            GeoJsonProcessor processor,
            JdbcBatchItemWriter<GenericNodeDataclass> genericNodeWriter) {
        return new StepBuilder("importGenericNodesStep", jobRepository)
                .<GeoJsonFeature, GenericNodeDataclass>chunk(10, transactionManager)
                .reader(genericNodeReader)
                .processor(processor)
                .writer(genericNodeWriter)
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
    public JsonItemReader<GeoJsonFeature> genericNodeReader() {
        JacksonJsonObjectReader<GeoJsonFeature> jsonObjectReader = new JacksonJsonObjectReader<>(GeoJsonFeature.class);

        JsonItemReader<GeoJsonFeature> reader = new JsonItemReader<>();
        reader.setResource(GeoJsonResources.featuresArray(new ClassPathResource("data/IGGIELGN_Nodes.geojson")));
        reader.setJsonObjectReader(jsonObjectReader);
        reader.setName("geoJsonReader");
        reader.setStrict(false);

        return reader;
    }

    /**
     * ItemProcessor implementation that transforms GeoJsonFeature objects into
     * GenericNodeDataclass objects suitable for database insertion. The processor
     * extracts relevant properties from the GeoJsonFeature, including geometry and
     * attributes, and maps them to the corresponding fields in the
     * GenericNodeDataclass.
     */
    @Component
    public class GeoJsonProcessor implements ItemProcessor<GeoJsonFeature, GenericNodeDataclass> {
        @Override
        public GenericNodeDataclass process(GeoJsonFeature feature) {
            Map<String, Object> geometry = feature.getGeometry();
            Map<String, Object> properties = feature.getProperties();
            List<Double> coordinates = (List<Double>) geometry.get("coordinates");

            GenericNodeDataclass node = new GenericNodeDataclass();
            node.setIGGIELGN_id((String) properties.get("id"));
            node.setName((String) properties.get("name"));
            node.setCountryCode((String) properties.get("country_code"));

            node.setLongitude(coordinates.get(0));
            node.setLatitude(coordinates.get(1));

            return node;
        }
    }

    /**
     * Bean definition for the JdbcBatchItemWriter that writes GenericNodeDataclass
     * objects to the database.
     */

    @Bean
    public JdbcBatchItemWriter<GenericNodeDataclass> genericNodeWriter(
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<GenericNodeDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql(
                "INSERT INTO generic_nodes (\"IGGIELGN_id\", name, geom, country_code) "
                        +
                        "VALUES (:IGGIELGN_id, :name, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), :countryCode)");
        writer.setItemSqlParameterSourceProvider(new BeanPropertyItemSqlParameterSourceProvider<>());
        return writer;
    }

}
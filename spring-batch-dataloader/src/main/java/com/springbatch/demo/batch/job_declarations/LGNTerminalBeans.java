package com.springbatch.demo.batch.job_declarations;

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
import org.springframework.batch.item.database.BeanPropertyItemSqlParameterSourceProvider;
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
import com.springbatch.demo.model.output_models.LngTerminaDataclass;

import lombok.extern.slf4j.Slf4j;

@Configuration
@EnableBatchProcessing(dataSourceRef = "batchDataSource", transactionManagerRef = "transactionManager")
@Slf4j
public class LGNTerminalBeans {

    @Bean
    public Job importLngTerminalsJob(JobRepository jobRepository,
            Step truncateLngTerminalStep,
            Step importLngTerminalsStep) {
        return new JobBuilder("importLngTerminalsJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(truncateLngTerminalStep)
                .next(importLngTerminalsStep)
                .build();
    }

    @Bean
    public Step truncateLngTerminalStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

        return new StepBuilder("truncateLngTerminalsStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    int deleted = jdbcTemplate.update("TRUNCATE TABLE lng_terminals RESTART IDENTITY CASCADE");
                    log.info("Truncated lng_terminals before import; JDBC update count={}", deleted);
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }

    @Bean
    public Step importLngTerminalsStep(JobRepository jobRepository,
            @Qualifier("transactionManager") PlatformTransactionManager transactionManager,
            JsonItemReader<GeoJsonFeature> lngNodeReader,
            GeoJsonProcessor processor,
            JdbcBatchItemWriter<LngTerminaDataclass> lngTerminalWriter) {
        return new StepBuilder("importLngTerminalsStep", jobRepository)
                .<GeoJsonFeature, LngTerminaDataclass>chunk(10, transactionManager)
                .reader(lngNodeReader)
                .processor(processor)
                .writer(lngTerminalWriter)
                .faultTolerant()
                .skip(DataIntegrityViolationException.class)
                .skipLimit(Integer.MAX_VALUE)
                .listener(new ImportStepListener())
                .build();
    }

    @Bean
    public JsonItemReader<GeoJsonFeature> lngNodeReader() {
        JacksonJsonObjectReader<GeoJsonFeature> jsonObjectReader = new JacksonJsonObjectReader<>(GeoJsonFeature.class);

        JsonItemReader<GeoJsonFeature> reader = new JsonItemReader<>();
        reader.setResource(GeoJsonResources.featuresArray(new ClassPathResource("data/IGGIELGN_LNGs.geojson")));
        reader.setJsonObjectReader(jsonObjectReader);
        reader.setName("geoJsonReader");
        reader.setStrict(false);

        return reader;
    }

    @Component
    public class GeoJsonProcessor implements ItemProcessor<GeoJsonFeature, LngTerminaDataclass> {
        @Override
        public LngTerminaDataclass process(GeoJsonFeature feature) {
            Map<String, Object> geometry = feature.getGeometry();
            Map<String, Object> properties = feature.getProperties();
            Map<String, Object> param = (Map<String, Object>) properties.get("param");
            List<Double> coordinates = (List<Double>) geometry.get("coordinates");

            LngTerminaDataclass node = new LngTerminaDataclass();
            node.setIGGIELGN_id((String) properties.get("id"));
            node.setName((String) properties.get("name"));
            node.setCountryCode((String) properties.get("country_code"));

            node.setLongitude(coordinates.get(0));
            node.setLatitude(coordinates.get(1));
            node.setFrom_TSO((String) param.get("from_TSO"));
            node.setTo_TSO((String) param.get("to_TSO"));
            node.setMax_cap_store2pipe_M_m3_per_d(param.get("max_cap_store2pipe_M_m3_per_d") != null
                    ? ((Number) param.get("max_cap_store2pipe_M_m3_per_d")).doubleValue()
                    : null);
            node.setStart_year(param.get("start_year") != null
                    ? ((Number) param.get("start_year")).intValue()
                    : null);

            return node;
        }
    }

    @Bean
    public JdbcBatchItemWriter<LngTerminaDataclass> lngTerminalWriter(
            @Qualifier("appDataSource") DataSource dataSource) {
        JdbcBatchItemWriter<LngTerminaDataclass> writer = new JdbcBatchItemWriter<>();
        writer.setDataSource(dataSource);
        writer.setSql(
                "INSERT INTO lng_terminals (\"IGGIELGN_id\", name, geom, country_code, \"from_TSO\", \"to_TSO\", \"max_cap_store2pipe_M_m3_per_d\", \"start_year\") "
                        +
                        "VALUES (:IGGIELGN_id, :name, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326), :countryCode, :from_TSO, :to_TSO, :max_cap_store2pipe_M_m3_per_d, :start_year)");
        writer.setItemSqlParameterSourceProvider(new BeanPropertyItemSqlParameterSourceProvider<>());
        return writer;
    }
}

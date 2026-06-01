package com.springbatch.demo.batch.job_declarations;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.job.flow.Flow;
import org.springframework.batch.core.launch.support.RunIdIncrementer;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import lombok.extern.slf4j.Slf4j;

/**
 * Master job configuration that accepts a dynamically built Flow.
 * The actual flow construction is done in FlowBuilderConfig based on which steps are enabled.
 */
@Slf4j
@Configuration
public class MasterJobConfig {

    @Bean
    public Job dataImportJob(JobRepository jobRepository, Flow dataImportFlow) {
        return new JobBuilder("dataImportJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .start(dataImportFlow)
                .end()
                .build();
    }
}

package com.springbatch.demo.batch.joblaunchers;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import lombok.extern.slf4j.Slf4j;

/**
 * Unified job launcher that runs the dataImportJob with a dynamically built flow.
 * 
 * The flow is constructed in FlowBuilderConfig based on the job.steps property.
 * 
 * Usage:
 * - All steps (default):    mvn spring-boot:run
 * - All steps (explicit):   mvn spring-boot:run -Dspring-boot.run.arguments="--job.steps=all"
 * - Border crossing only:   mvn spring-boot:run -Dspring-boot.run.arguments="--job.steps=border-crossing"
 * - Generic nodes only:     mvn spring-boot:run -Dspring-boot.run.arguments="--job.steps=generic-node"
 * - Pipeline segments only: mvn spring-boot:run -Dspring-boot.run.arguments="--job.steps=pipeline-segment"
 * - Multiple steps:         mvn spring-boot:run -Dspring-boot.run.arguments="--job.steps=border-crossing,generic-node"
 * - No execution:           mvn spring-boot:run -Dspring-boot.run.arguments="--job.enabled=false"
 */
@Slf4j
@Component
public class UnifiedJobLauncher implements CommandLineRunner {

    @Value("${job.enabled:true}")
    private boolean jobEnabled;

    @Value("${job.steps:all}")
    private String enabledSteps;

    private final JobLauncher jobLauncher;
    private final Job dataImportJob;

    public UnifiedJobLauncher(
            JobLauncher jobLauncher,
            @Qualifier("dataImportJob") Job dataImportJob) {
        this.jobLauncher = jobLauncher;
        this.dataImportJob = dataImportJob;
    }

    @Override
    public void run(String... args) throws Exception {
        if (!jobEnabled) {
            log.info("Job execution disabled (job.enabled=false)");
            return;
        }

        log.info("Starting data import job with steps: {}", enabledSteps);
        
        JobParameters jobParameters = new JobParametersBuilder()
                .addLong("time", System.currentTimeMillis())
                .addString("enabledSteps", enabledSteps)
                .toJobParameters();

        jobLauncher.run(dataImportJob, jobParameters);
        
        log.info("Successfully completed data import job");
    }
}

package com.springbatch.demo.batch.joblaunchers;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;


import org.springframework.beans.factory.annotation.Qualifier;

/**
 * A CommandLineRunner that triggers the job when the application starts.
 * It creates a unique JobParameters instance using the current timestamp to ensure job execution.
 * Only runs when batch.job.generic-node.enabled=true
 */
@Deprecated
@Component
@ConditionalOnProperty(name = "batch.job.generic-node.enabled", havingValue = "true", matchIfMissing = false)
public class GenericNodeJobRunner implements CommandLineRunner {

    private final JobLauncher jobLauncher;
    private final Job job; 
    
    public GenericNodeJobRunner(JobLauncher jobLauncher, @Qualifier("importGenericNodesJob") Job job) {
        this.jobLauncher = jobLauncher;
        this.job = job;
    }

    @Override
    public void run(String... args) throws Exception {
        System.out.println("Triggering the job...");
        JobParameters jobParameters = new JobParametersBuilder()
            .addLong("time", System.currentTimeMillis()) // unique param to avoid collision
            .toJobParameters();

        jobLauncher.run(job, jobParameters);
    }
}
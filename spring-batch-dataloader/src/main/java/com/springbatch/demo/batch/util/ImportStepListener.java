package com.springbatch.demo.batch.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


import org.springframework.batch.core.ExitStatus;
import org.springframework.batch.core.StepExecution;
import org.springframework.batch.core.StepExecutionListener;


public class ImportStepListener implements StepExecutionListener {
    private static final Logger log = LoggerFactory.getLogger(ImportStepListener.class);

    @Override
    public ExitStatus afterStep(StepExecution stepExecution) {
        long readCount = stepExecution.getReadCount();
        long writeCount = stepExecution.getWriteCount();
        long skipCount = stepExecution.getSkipCount();
        
        log.info("Import Summary:");
        log.info("  Total read: {}", readCount);
        log.info("  Successfully inserted: {}", writeCount);
        log.info("  Skipped (conflicts): {}", skipCount);
        
        if (skipCount > 0) {
            log.warn("{} conflict records were skipped", skipCount);
        }
        
        return stepExecution.getExitStatus();
    }
}
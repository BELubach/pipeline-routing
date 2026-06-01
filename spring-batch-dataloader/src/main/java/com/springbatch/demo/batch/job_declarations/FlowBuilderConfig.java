package com.springbatch.demo.batch.job_declarations;

import org.springframework.batch.core.Step;
import org.springframework.batch.core.job.builder.FlowBuilder;
import org.springframework.batch.core.job.flow.Flow;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import lombok.extern.slf4j.Slf4j;

/**
 * Dynamically builds the execution flow based on which jobs are enabled.
 * 
 * Configuration:
 * job.steps=border-crossing,generic-node,pipeline-segment (default: all)
 * 
 * Examples:
 * - All steps: --job.steps=all
 * - Only border crossing: --job.steps=border-crossing
 * - Nodes only: --job.steps=border-crossing,generic-node
 * - Multiple: --job.steps=generic-node,pipeline-segment
 */
@Slf4j
@Configuration
public class FlowBuilderConfig {

    @Value("${job.steps:all}")
    private String enabledSteps;

    @Bean
    public Flow dataImportFlow(
            // Border crossing steps
            Step truncateBorderCrossingStep,
            Step importGeoJsonStep,
            // Generic node steps
            Step truncateGenericNodesStep,
            Step importGenericNodesStep,
            // Pipeline segment steps
            Step truncatePipelineSegmentsStep,
            Step importPipeSegmentsStep,
            Step snapPipeSegmentsToNodesStep,
            // LNG terminal steps
            Step truncateLngTerminalStep,
            Step importLngTerminalsStep, 
        
            // GEM data steps
            Step truncateGEMDataStep,
            Step importGEMDataStep, 

            // Shipping lane steps
            Step truncateShippingLanesStep,
            Step importShippingLanesStep
            ) {

        boolean includeBorderCrossing = shouldInclude("border-crossing");
        boolean includeGenericNode = shouldInclude("generic-node");
        boolean includePipelineSegment = shouldInclude("pipeline-segment");
        boolean includeLngTerminal = shouldInclude("lng-terminal");
        boolean includeGEMdata = shouldInclude("gem-data");
        boolean includeShippingLanes = shouldInclude("shipping-lanes");



        log.info("Building flow with: border-crossing={}, generic-node={}, pipeline-segment={}, lng-terminal={}, gem-data={}, shipping-lanes={}", 
                 includeBorderCrossing, includeGenericNode, includePipelineSegment, includeLngTerminal, includeGEMdata, includeShippingLanes);

        FlowBuilder<Flow> flowBuilder = new FlowBuilder<>("dataImportFlow");
        boolean firstStep = true;

        // Phase 1: Border crossing nodes
        if (includeBorderCrossing) {
            if (firstStep) {
                flowBuilder.start(truncateBorderCrossingStep);
                firstStep = false;
            } else {
                flowBuilder.next(truncateBorderCrossingStep);
            }
            flowBuilder.next(importGeoJsonStep);
        }

        // Phase 2: Generic nodes
        if (includeGenericNode) {
            if (firstStep) {
                flowBuilder.start(truncateGenericNodesStep);
                firstStep = false;
            } else {
                flowBuilder.next(truncateGenericNodesStep);
            }
            flowBuilder.next(importGenericNodesStep);
        }

        // Phase 3: Pipeline segments
        if (includePipelineSegment) {
            if (firstStep) {
                flowBuilder.start(truncatePipelineSegmentsStep);
                firstStep = false;
            } else {
                flowBuilder.next(truncatePipelineSegmentsStep);
            }
            flowBuilder.next(importPipeSegmentsStep);
            flowBuilder.next(snapPipeSegmentsToNodesStep);
        }

        // Phase 4: LNG terminals
        if (includeLngTerminal) {
            if (firstStep) {
                flowBuilder.start(truncateLngTerminalStep);
                firstStep = false;
            } else {
                flowBuilder.next(truncateLngTerminalStep);
            }
            flowBuilder.next(importLngTerminalsStep);
        }


        // Phase 5: GEM data
        if (includeGEMdata) {
            if (firstStep) {
                flowBuilder.start(truncateGEMDataStep);
                firstStep = false;
            } else {
                flowBuilder.next(truncateGEMDataStep);
            }
            flowBuilder.next(importGEMDataStep);
        }

        // Phase 6: Shipping lanes
        if (includeShippingLanes) {
            if (firstStep) {
                flowBuilder.start(truncateShippingLanesStep);
                firstStep = false;
            } else {
                flowBuilder.next(truncateShippingLanesStep);
            }
            flowBuilder.next(importShippingLanesStep);
        }


        if (firstStep) {
            log.warn("No steps enabled! Flow will be empty.");
        }

        return flowBuilder.build();
    }

    private boolean shouldInclude(String stepName) {
        String steps = enabledSteps.toLowerCase();
        return steps.equals("all") || 
               steps.equals("full") || 
               steps.contains(stepName);
    }
}

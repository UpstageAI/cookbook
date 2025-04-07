#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import * as dotenv from 'dotenv';
import { DPSagemakerStack } from '../lib/dp-sagemaker-endpoint-stack';  
import { S3InferenceAutomationStack } from '../lib/s3-inference-automation-stack';

dotenv.config();

// check if the environment variables are set
function checkEnvVariables(...args: string[]) {
    const missingVariables = args.filter(arg => !process.env[arg]);
    if (missingVariables.length > 0) {
      throw new Error(`The following environment variables are not set yet: ${missingVariables.map(v => v).join(', ')}. Please set them in .env file or pipeline environments.`);
    }
};
checkEnvVariables('CDK_PROJECT_NAME', 'CDK_DEFAULT_ACCOUNT', 'CDK_DEFAULT_REGION', 'DP_MODEL_PACKAGE_NAME', 'DP_INSTANCE_TYPE', 'DP_INSTANCE_COUNT');

const app = new cdk.App();

const projectName = process.env.CDK_PROJECT_NAME;

// Create stacks in the correct order and pass required properties
const dpSagemaker = new DPSagemakerStack(app, `${projectName}/DP-Sagemaker`, {});

// Create the merged S3 and Lambda stack
const s3InferenceAutomation = new S3InferenceAutomationStack(app, `${projectName}/S3-Inference-Automation`, {
  endpointName: dpSagemaker.endpointName,
  endpointArn: dpSagemaker.endpointArn,
});


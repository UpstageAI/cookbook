import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import { Construct } from 'constructs';
import * as path from 'path';

/**
 * Properties for the S3 Inference Automation Stack
 */
export interface S3InferenceAutomationStackProps extends cdk.StackProps {
  /** SageMaker endpoint name */
  endpointName: string;
  /** SageMaker endpoint arn */
  endpointArn: string;
}

/**
* Creates S3 buckets and Lambda for document processing
*/
export class S3InferenceAutomationStack extends cdk.Stack {
    /** Input bucket for documents */
    public readonly inputBucket: s3.Bucket;
    
    /** Output bucket for processed results */
    public readonly outputBucket: s3.Bucket;

    /** Lambda function for document processing */
    public readonly processingFunction: lambda.Function;
    
    constructor(scope: Construct, id: string, props: S3InferenceAutomationStackProps) {
        super(scope, id, props);

        const projectName = process.env.CDK_PROJECT_NAME;
        
        // Create input bucket
        this.inputBucket = new s3.Bucket(this, 'InputBucket', {
            bucketName: `${projectName}-input-bucket`,
            removalPolicy: cdk.RemovalPolicy.RETAIN,
            autoDeleteObjects: false,
            cors: [
                {
                    allowedMethods: [
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                    ],
                    allowedOrigins: ['*'],
                    allowedHeaders: ['*'],
                },
            ],
        });
        
        // Create output bucket
        this.outputBucket = new s3.Bucket(this, 'OutputBucket', {
            bucketName: `${projectName}-output-bucket`,
            removalPolicy: cdk.RemovalPolicy.RETAIN,
            autoDeleteObjects: false,
            cors: [
                {
                    allowedMethods: [
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                    ],
                    allowedOrigins: ['*'],
                    allowedHeaders: ['*'],
                },
            ],
        });
        
        // Create Lambda function
        this.processingFunction = new lambda.Function(this, 'DocumentProcessingFunction', {
          functionName: `${projectName}-document-processing-function`,
          runtime: lambda.Runtime.PYTHON_3_12,
          handler: 'index.handler',
          code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/dp_processing')),
          timeout: cdk.Duration.minutes(5),
          environment: {
            SAGEMAKER_ENDPOINT: props.endpointName,
            OUTPUT_BUCKET: this.outputBucket.bucketName,
            INPUT_BUCKET: this.inputBucket.bucketName,
          },
          memorySize: 8192,
        });

        // Grant permissions to Lambda
        this.inputBucket.grantRead(this.processingFunction);
        this.inputBucket.grantWrite(this.processingFunction);
        this.outputBucket.grantWrite(this.processingFunction);
        
        // Add permission to invoke SageMaker endpoint
        this.processingFunction.addToRolePolicy(
          new iam.PolicyStatement({
            actions: ['sagemaker:InvokeEndpoint'],
            resources: [props.endpointArn],
          })
        );
        
        // Set up S3 event trigger to invoke Lambda when file is uploaded to input bucket
        this.inputBucket.addEventNotification(
          s3.EventType.OBJECT_CREATED, 
          new s3n.LambdaDestination(this.processingFunction)
        );
        
        // Output bucket names
        new cdk.CfnOutput(this, 'InputBucketName', {
            value: this.inputBucket.bucketName,
            description: 'Input bucket for documents',
        });
        
        new cdk.CfnOutput(this, 'OutputBucketName', {
            value: this.outputBucket.bucketName,
            description: 'Output bucket for processed results',
        });

        // Output Lambda function name
        new cdk.CfnOutput(this, 'DocumentProcessingFunctionName', {
          value: this.processingFunction.functionName,
          description: 'Document Processing Lambda Function',
        });
    }
}
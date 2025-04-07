import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import { Duration } from "aws-cdk-lib";
import { Construct } from "constructs";
import { Environment } from "../config/environments";
/**
 * Properties for the Lambda Stack
 */
export interface LambdaStackProps extends cdk.StackProps {
  /** SageMaker endpoint name for inference */
  endpointName: string;
  context: Environment;
}

/**
 * Creates a Lambda function for handling inference requests
 * Configures necessary IAM roles and permissions
 */
export class SolarLambdaStack extends cdk.Stack {
  /** Lambda function for handling inference requests */
  public readonly inferenceFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: LambdaStackProps) {
    super(scope, id, props);
    const region = process.env.CDK_DEFAULT_REGION || "us-west-2";
    // Create Lambda execution role
    const lambdaRole = new iam.Role(this, "LambdaRole", {
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AWSLambdaBasicExecutionRole"
        ),
      ],
    });

    // Add SageMaker invoke permissions
    lambdaRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["sagemaker:InvokeEndpoint"],
        resources: ["*"], // Consider restricting to specific endpoint ARN in production
      })
    );

    // Create Lambda function
    const handler = "index_llm.handler";

    const timeout = 900;

    // Validate API key value
    if (!process.env.API_KEY_VALUE) {
      throw new Error("API_KEY_VALUE is not set in environment variables");
    }

    if (!process.env.CDK_DEFAULT_REGION) {
      throw new Error("AWS_REGION is not set in environment variables");
    }

    this.inferenceFunction = new lambda.Function(this, "InferenceFunction", {
      runtime: lambda.Runtime.NODEJS_22_X,
      handler: handler,
      code: lambda.Code.fromAsset("lib/stacks/lambda"),
      role: lambdaRole,
      timeout: Duration.seconds(timeout),
      environment: {
        SAGEMAKER_ENDPOINT_NAME: props.endpointName,
        API_KEY_VALUE: process.env.API_KEY_VALUE,
        AWS_REGION: process.env.CDK_DEFAULT_REGION,
      },
    });

    // Add function URL with NONE auth type and streaming support
    const functionUrl = this.inferenceFunction.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      invokeMode: lambda.InvokeMode.RESPONSE_STREAM
    });

    // Add function URL output
    new cdk.CfnOutput(this, "InferenceFunctionUrl", {
      value: functionUrl.url,
      description: "Inference Function URL",
    });
  }
}

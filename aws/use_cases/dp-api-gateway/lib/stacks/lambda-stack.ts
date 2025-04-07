import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import { Duration } from "aws-cdk-lib";
import { Construct } from "constructs";

/**
 * Properties for the Lambda Stack
 */
export interface LambdaStackProps extends cdk.StackProps {
  /** SageMaker endpoint name for inference */
  endpointName: string;
}

/**
 * Creates a Lambda function for handling inference requests
 * Configures necessary IAM roles and permissions
 */
export class LambdaStack extends cdk.Stack {
  /** Lambda function for handling inference requests */
  public readonly inferenceFunction: lambda.Function;

  constructor(scope: Construct, id: string, props: LambdaStackProps) {
    super(scope, id, props);

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
    this.inferenceFunction = new lambda.Function(this, "InferenceFunction", {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset("lib/stacks/lambda"),
      role: lambdaRole,
      timeout: Duration.seconds(60),
      environment: {
        SAGEMAKER_ENDPOINT_NAME: props.endpointName,
      },
    });
  }
}

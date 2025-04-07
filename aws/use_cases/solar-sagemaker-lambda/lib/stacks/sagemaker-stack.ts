import * as cdk from "aws-cdk-lib";
import * as sagemaker from "aws-cdk-lib/aws-sagemaker";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { Environment } from "../config/environments";

/**
 * Properties for the SageMaker Stack
 */
export interface SageMakerStackProps extends cdk.StackProps {
  /** Environment configuration */
  context: Environment;
}

/**
 * Creates SageMaker resources including model, endpoint configuration, and endpoint
 */
export class SolarSageMakerStack extends cdk.Stack {
  /** Name of the created SageMaker endpoint */
  public readonly endpointName: string;

  constructor(scope: Construct, id: string, props: SageMakerStackProps) {
    super(scope, id, props);

    // Map of region to model package ARNs
    const packageArnMap: { [key: string]: string } = {
      "us-east-1": `arn:aws:sagemaker:us-east-1:865070037744:model-package/${props.context.modelPackageName}`,
      "us-east-2": `arn:aws:sagemaker:us-east-2:057799348421:model-package/${props.context.modelPackageName}`,
      "us-west-1": `arn:aws:sagemaker:us-west-1:382657785993:model-package/${props.context.modelPackageName}`,
      "us-west-2": `arn:aws:sagemaker:us-west-2:594846645681:model-package/${props.context.modelPackageName}`,
      "ca-central-1": `arn:aws:sagemaker:ca-central-1:470592106596:model-package/${props.context.modelPackageName}`,
      "eu-central-1": `arn:aws:sagemaker:eu-central-1:446921602837:model-package/${props.context.modelPackageName}`,
      "eu-west-1": `arn:aws:sagemaker:eu-west-1:985815980388:model-package/${props.context.modelPackageName}`,
      "eu-west-2": `arn:aws:sagemaker:eu-west-2:856760150666:model-package/${props.context.modelPackageName}`,
      "eu-west-3": `arn:aws:sagemaker:eu-west-3:843114510376:model-package/${props.context.modelPackageName}`,
      "eu-north-1": `arn:aws:sagemaker:eu-north-1:136758871317:model-package/${props.context.modelPackageName}`,
      "ap-southeast-1": `arn:aws:sagemaker:ap-southeast-1:192199979996:model-package/${props.context.modelPackageName}`,
      "ap-southeast-2": `arn:aws:sagemaker:ap-southeast-2:666831318237:model-package/${props.context.modelPackageName}`,
      "ap-northeast-2": `arn:aws:sagemaker:ap-northeast-2:745090734665:model-package/${props.context.modelPackageName}`,
      "ap-northeast-1": `arn:aws:sagemaker:ap-northeast-1:977537786026:model-package/${props.context.modelPackageName}`,
      "ap-south-1": `arn:aws:sagemaker:ap-south-1:077584701553:model-package/${props.context.modelPackageName}`,
      "sa-east-1": `arn:aws:sagemaker:sa-east-1:270155090741:model-package/${props.context.modelPackageName}`,
    };

    const region = process.env.CDK_DEFAULT_REGION || "us-west-2";

    const packageArn = packageArnMap[region];

    // Create SageMaker execution role
    const sagemakerRole = new iam.Role(this, "SageMakerRole", {
      assumedBy: new iam.ServicePrincipal("sagemaker.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSageMakerFullAccess"),
      ],
    });

    // Create model
    const modelName = `solar-chat-${Date.now()}`;

    const model = new sagemaker.CfnModel(this, "Model", {
      executionRoleArn: sagemakerRole.roleArn,
      primaryContainer: {
        modelPackageName: packageArn,
      },
      modelName: modelName,
      enableNetworkIsolation: true,
    });

    // Create endpoint configuration
    const endpointConfig = new sagemaker.CfnEndpointConfig(
      this,
      "EndpointConfig",
      {
        productionVariants: [
          {
            initialVariantWeight: 1.0,
            modelName: model.attrModelName,
            variantName: "AllTraffic",
            instanceType: props.context.instanceType,
            initialInstanceCount: 1,
          },
        ],
      }
    );

    // Create endpoint
    const endpoint = new sagemaker.CfnEndpoint(this, "Endpoint", {
      endpointConfigName: endpointConfig.attrEndpointConfigName,
      endpointName: modelName,
    });

    this.endpointName = endpoint.attrEndpointName;

    // Output endpoint name
    new cdk.CfnOutput(this, "EndpointName", {
      value: this.endpointName,
      description: "SageMaker Endpoint Name",
    });
  }
}

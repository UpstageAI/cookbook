import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { env, Environment } from "./config/environments";
import { SageMakerStack } from "./stacks/sagemaker-stack";
import { LambdaStack } from "./stacks/lambda-stack";
import { ApiGatewayStack } from "./stacks/api-gateway-stack";

export interface DocaiEnterpriseSystemProps extends cdk.StageProps {}

export interface SetupResourceStageProps extends cdk.StackProps {
  context: Environment;
}

export class SetupResourceStage extends cdk.Stage {
  constructor(scope: Construct, id: string, props: SetupResourceStageProps) {
    super(scope, id, props);
    const env = {
      account: props.context.account.accountId,
      region: props.context.account.region,
    };

    const sagemakerStack = new SageMakerStack(this, "SageMakerStack", {
      env,
      context: props.context,
    });

    const lambdaStack = new LambdaStack(this, "LambdaStack", {
      env,
      endpointName: sagemakerStack.endpointName,
    });

    // API Gateway 스택 생성
    new ApiGatewayStack(this, "ApiGatewayStack", {
      env,
      inferenceFunction: lambdaStack.inferenceFunction,
    });
  }
}

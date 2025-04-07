import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { env, Environment } from "./config/environments";
import { SolarSageMakerStack } from "./stacks/sagemaker-stack";
import { SolarLambdaStack } from "./stacks/lambda-stack";

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

    const sagemakerStack = new SolarSageMakerStack(this, "SolarSageMakerStack", {
      env,
      context: props.context,
    });

    const lambdaStack = new SolarLambdaStack(this, "SolarLambdaStack", {
      env,
      endpointName: sagemakerStack.endpointName,
      context: props.context,
    });
  }
}

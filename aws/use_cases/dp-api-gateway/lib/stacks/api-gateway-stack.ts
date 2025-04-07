import * as cdk from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";

/**
 * Properties for the API Gateway Stack
 */
export interface ApiGatewayStackProps extends cdk.StackProps {
  /** Lambda function to handle inference requests */
  inferenceFunction: lambda.Function;
}

/**
 * Creates an API Gateway for handling inference requests
 * Configures REST API with binary support and CORS
 */
export class ApiGatewayStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ApiGatewayStackProps) {
    super(scope, id, props);

    // Create usage plan
    const plan = new apigateway.UsagePlan(this, "UsagePlan", {
      name: "Document AI API Usage Plan",
      throttle: {
        rateLimit: 10, // 10 requests per second
        burstLimit: 20, // maximum 20 concurrent requests
      },
      quota: {
        limit: 1000 * 1000 * 1000, // 1,000,000,000 requests
        period: apigateway.Period.MONTH, // per month
      },
    });

    // Create API key
    const key = new apigateway.ApiKey(this, "ApiKey", {
      apiKeyName: `document-ai-key-${cdk.Stack.of(this).region}`,
      description: "API Key for Document AI API",
      enabled: true,
      value: process.env.API_KEY_VALUE, // Get API key value from environment variable
    });

    // Validate API key value
    if (!process.env.API_KEY_VALUE) {
      throw new Error("API_KEY_VALUE is not set in environment variables");
    }

    // Create REST API
    const api = new apigateway.RestApi(this, "InferenceApi", {
      restApiName: "Document AI API",
      description: "API for Document AI services",
      // Enable binary support for multipart/form-data
      binaryMediaTypes: ["*/*"],
      // Configure CORS
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: apigateway.Cors.DEFAULT_HEADERS,
      },
      // Configure deployment stage
      deployOptions: {
        stageName: "v1",
        description: "Version 1",
        metricsEnabled: false,
        loggingLevel: apigateway.MethodLoggingLevel.OFF,
        dataTraceEnabled: false,
      },
      // Enable API key requirement by default
      apiKeySourceType: apigateway.ApiKeySourceType.HEADER,
    });

    // Create resource path: /document-ai
    const documentAi = api.root.addResource("document-ai");

    // Add document-parse endpoint
    const documentParse = documentAi.addResource("document-parse");

    // Configure Lambda integration
    const lambdaIntegration = new apigateway.LambdaIntegration(
      props.inferenceFunction,
      {
        proxy: true,
        contentHandling: apigateway.ContentHandling.CONVERT_TO_BINARY,
      }
    );

    // Add POST method with API key requirement
    documentParse.addMethod("POST", lambdaIntegration, {
      authorizationType: apigateway.AuthorizationType.NONE,
      apiKeyRequired: true, // Require API key
    });

    // Add API to usage plan
    plan.addApiKey(key);
    plan.addApiStage({
      stage: api.deploymentStage,
    });

    // Output API URLs and key
    new cdk.CfnOutput(this, "ApiUrl", {
      value: `https://${api.restApiId}.execute-api.${
        cdk.Stack.of(this).region
      }.amazonaws.com`,
      description: "Base API Gateway URL",
    });

    new cdk.CfnOutput(this, "EndpointUrl", {
      value: `https://${api.restApiId}.execute-api.${
        cdk.Stack.of(this).region
      }.amazonaws.com/v1/document-ai/document-parse`,
      description: "Complete Document Parse endpoint URL",
    });
  }
}

#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { env } from "../lib/config/environments";
import { SetupResourceStage } from "../lib/resource";

const app = new cdk.App();

new SetupResourceStage(app, "SetupResourceStage", {
  env: {
    account: env.account.accountId,
    region: env.account.region,
  },
  context: env,
});

app.synth();

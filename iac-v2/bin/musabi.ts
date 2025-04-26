#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { SfnStack } from "../lib/sfn-stack";
import { EcrStack } from "../lib/ecr-stack";

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
};
const app = new cdk.App();
const ecrStack = new EcrStack(app, "EcrStack", { env });
new SfnStack(app, "SfnStack", {
  env,
  genTextRepository: ecrStack.genTextRepository,
  genImgRepository: ecrStack.genImgRepository,
  editImgRepository: ecrStack.editImgRepository,
  pubImgRepository: ecrStack.pubImgRepository,
});

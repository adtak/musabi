import * as cdk from "aws-cdk-lib";
import type { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as events_targets from "aws-cdk-lib/aws-events-targets";
import type * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as sfn_tasks from "aws-cdk-lib/aws-stepfunctions-tasks";

type SfnStackProps = cdk.StackProps & {
  genTextRepository: ecr.Repository;
  genImgRepository: ecr.Repository;
  editImgRepository: ecr.Repository;
  pubImgRepository: ecr.Repository;
};

export class SfnStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: SfnStackProps) {
    super(scope, id, props);

    const bucket = new s3.Bucket(this, "MusabiBucket", {
      bucketName: "musabi-bucket",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
    });
    const genTextFunction = createGenTextFunction(
      this,
      props.genTextRepository,
    );
    const genImgFunction = createGenImgFunction(
      this,
      props.genImgRepository,
      bucket,
    );
    const editImgFunction = createEditImgFunction(
      this,
      props.editImgRepository,
      bucket,
    );
    const pubImgFunction = createPubImgFunction(
      this,
      props.pubImgRepository,
      bucket,
    );
    const stateMachine = createStateMachine(
      this,
      genTextFunction,
      genImgFunction,
      editImgFunction,
      pubImgFunction,
      bucket.bucketName,
    );

    new events.Rule(this, "MusabiEventsRule", {
      schedule: events.Schedule.cron({ hour: "3", minute: "0" }),
      targets: [
        new events_targets.SfnStateMachine(stateMachine, {
          input: events.RuleTargetInput.fromObject({
            DryRun: false,
          }),
          maxEventAge: cdk.Duration.minutes(10),
          retryAttempts: 0,
        }),
      ],
    });
  }
}

const createGenTextFunction = (scope: Construct, ecrRepo: ecr.Repository) => {
  const genTextFunction = new lambda.DockerImageFunction(
    scope,
    "GenTextLambda",
    {
      code: lambda.DockerImageCode.fromEcr(ecrRepo),
      timeout: cdk.Duration.minutes(3),
    },
  );
  genTextFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["ssm:GetParameter"],
      resources: [
        `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/openai/musabi/*`,
      ],
    }),
  );
  return genTextFunction;
};

const createGenImgFunction = (
  scope: Construct,
  ecrRepo: ecr.Repository,
  bucket: s3.Bucket,
) => {
  const genImgFunction = new lambda.DockerImageFunction(scope, "GenImgLambda", {
    code: lambda.DockerImageCode.fromEcr(ecrRepo),
    timeout: cdk.Duration.minutes(3),
    environment: {
      IMAGE_BUCKET: bucket.bucketName,
    },
  });
  genImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["s3:PutObject"],
      resources: [bucket.arnForObjects("*")],
    }),
  );
  genImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["ssm:GetParameter"],
      resources: [
        `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/google/gemini/musabi/*`,
      ],
    }),
  );
  return genImgFunction;
};

const createEditImgFunction = (
  scope: Construct,
  ecrRepo: ecr.Repository,
  bucket: s3.Bucket,
) => {
  const editImgFunction = new lambda.DockerImageFunction(
    scope,
    "EditImgLambda",
    {
      code: lambda.DockerImageCode.fromEcr(ecrRepo),
      timeout: cdk.Duration.minutes(3),
      environment: {
        IMAGE_BUCKET: bucket.bucketName,
      },
    },
  );
  editImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["s3:GetObject", "s3:PutObject"],
      resources: [bucket.arnForObjects("*")],
    }),
  );
  return editImgFunction;
};

const createPubImgFunction = (
  scope: Construct,
  ecrRepo: ecr.Repository,
  bucket: s3.Bucket,
) => {
  const pubImgFunction = new lambda.DockerImageFunction(scope, "PubImgLambda", {
    code: lambda.DockerImageCode.fromEcr(ecrRepo),
    timeout: cdk.Duration.minutes(3),
    environment: {
      IMAGE_BUCKET: bucket.bucketName,
    },
  });
  pubImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["s3:GetObject"],
      resources: [bucket.arnForObjects("*")],
    }),
  );
  pubImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["ssm:GetParameter"],
      resources: [
        `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/meta/musabi/*`,
      ],
    }),
  );
  return pubImgFunction;
};

const createStateMachine = (
  scope: Construct,
  genTextFunction: lambda.IFunction,
  genImgFunction: lambda.IFunction,
  editImgFunction: lambda.IFunction,
  pubImgFunction: lambda.IFunction,
  bucketName: string,
) => {
  const genTextStep = new sfn_tasks.LambdaInvoke(scope, "GenText", {
    lambdaFunction: genTextFunction,
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
    resultPath: "$.GenTextResults",
  });
  const genImgStep = new sfn_tasks.LambdaInvoke(scope, "GenImg", {
    lambdaFunction: genImgFunction,
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
    payload: sfn.TaskInput.fromObject({
      DishName: sfn.JsonPath.stringAt("$.GenTextResults.Payload.DishName"),
      Ingredients: sfn.JsonPath.stringAt(
        "$.GenTextResults.Payload.Ingredients",
      ),
      ExecName: sfn.JsonPath.stringAt("$$.Execution.Name"),
    }),
    resultPath: "$.GenImgResults",
  });
  const editImgStep = new sfn_tasks.LambdaInvoke(scope, "EditImg", {
    lambdaFunction: editImgFunction,
    payload: sfn.TaskInput.fromObject({
      ImgKey: sfn.JsonPath.stringAt("$.GenImgResults.Payload.ImgKey"),
      DishName: sfn.JsonPath.stringAt("$.GenTextResults.Payload.DishName"),
      BucketName: bucketName,
      ExecName: sfn.JsonPath.stringAt("$$.Execution.Name"),
    }),
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
    resultPath: "$.EditImgResults",
  });
  const pubImgStep = new sfn_tasks.LambdaInvoke(scope, "PubImg", {
    lambdaFunction: pubImgFunction,
    payload: sfn.TaskInput.fromObject({
      DishName: sfn.JsonPath.stringAt("$.GenTextResults.Payload.DishName"),
      Ingredients: sfn.JsonPath.stringAt(
        "$.GenTextResults.Payload.Ingredients",
      ),
      Steps: sfn.JsonPath.stringAt("$.GenTextResults.Payload.Steps"),
      TitleImgKey: sfn.JsonPath.stringAt(
        "$.EditImgResults.Payload.TitleImgKey",
      ),
      ImgKey: sfn.JsonPath.stringAt("$.GenImgResults.Payload.ImgKey"),
      DryRun: sfn.JsonPath.stringAt("$.DryRun"),
    }),
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
  });
  const successState = new sfn.Succeed(scope, "Succeded");
  return new sfn.StateMachine(scope, "MusabiStateMachine", {
    stateMachineName: "musabi-statemachine",
    definitionBody: sfn.DefinitionBody.fromChainable(
      genTextStep
        .next(genImgStep)
        .next(editImgStep)
        .next(pubImgStep)
        .next(successState),
    ),
    timeout: cdk.Duration.minutes(10),
  });
};

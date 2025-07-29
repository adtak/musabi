import * as cdk from "aws-cdk-lib";
import type * as ecr from "aws-cdk-lib/aws-ecr";
import * as events from "aws-cdk-lib/aws-events";
import * as events_targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as sfn_tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import type { Construct } from "constructs";

const PARALLEL_COUNT = 4;

type SfnStackProps = cdk.StackProps & {
  genTextRepository: ecr.Repository;
  genImgRepository: ecr.Repository;
  selectImgRepository: ecr.Repository;
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
    const selectImgFunction = createSelectImgFunction(
      this,
      props.selectImgRepository,
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
      selectImgFunction,
      editImgFunction,
      pubImgFunction,
      bucket.bucketName,
    );

    new events.Rule(this, "MusabiEventsRule", {
      schedule: events.Schedule.cron({ hour: "2,11", minute: "0" }),
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
      functionName: "GenTextFunction",
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
        `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/langsmith/musabi/*`,
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
    functionName: "GenImgFunction",
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

const createSelectImgFunction = (
  scope: Construct,
  ecrRepo: ecr.Repository,
  bucket: s3.Bucket,
) => {
  const selectImgFunction = new lambda.DockerImageFunction(
    scope,
    "SelectImgLambda",
    {
      functionName: "SelectImgFunction",
      code: lambda.DockerImageCode.fromEcr(ecrRepo),
      timeout: cdk.Duration.minutes(3),
      memorySize: 256,
      environment: {
        IMAGE_BUCKET: bucket.bucketName,
      },
    },
  );
  selectImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["s3:GetObject"],
      resources: [bucket.arnForObjects("*")],
    }),
  );
  selectImgFunction.addToRolePolicy(
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["ssm:GetParameter"],
      resources: [
        `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/google/gemini/musabi/*`,
      ],
    }),
  );
  return selectImgFunction;
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
      functionName: "EditImgFunction",
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
    functionName: "PubImgFunction",
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

const createParallelGenImgStep = (
  scope: Construct,
  genImgFunction: lambda.IFunction,
) => {
  const parallelGenImgStep = new sfn.Parallel(scope, "ParallelGenImg", {
    resultPath: "$.ParallelGenImgResults",
  });
  for (let i = 0; i < PARALLEL_COUNT; i++) {
    const genImgStep = new sfn_tasks.LambdaInvoke(scope, `GenImg-${i}`, {
      lambdaFunction: genImgFunction,
      integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
      payload: sfn.TaskInput.fromObject({
        DishName: sfn.JsonPath.stringAt("$.GenTextResults.Payload.DishName"),
        Ingredients: sfn.JsonPath.stringAt(
          "$.GenTextResults.Payload.Ingredients",
        ),
        ExecName: sfn.JsonPath.stringAt("$$.Execution.Name"),
        ParallelIndex: i,
      }),
    });
    parallelGenImgStep.branch(genImgStep);
  }
  return parallelGenImgStep;
};

const createStateMachine = (
  scope: Construct,
  genTextFunction: lambda.IFunction,
  genImgFunction: lambda.IFunction,
  selectImgFunction: lambda.IFunction,
  editImgFunction: lambda.IFunction,
  pubImgFunction: lambda.IFunction,
  bucketName: string,
) => {
  const genTextStep = new sfn_tasks.LambdaInvoke(scope, "GenText", {
    lambdaFunction: genTextFunction,
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
    resultPath: "$.GenTextResults",
  });

  const parallelGenImgStep = createParallelGenImgStep(scope, genImgFunction);

  const selectImgStep = new sfn_tasks.LambdaInvoke(scope, "SelectImg", {
    lambdaFunction: selectImgFunction,
    payload: sfn.TaskInput.fromObject({
      ImageKeys: sfn.JsonPath.listAt(
        "$.ParallelGenImgResults[*].Payload.ImgKey",
      ),
    }),
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
    resultPath: "$.SelectImgResults",
  });

  const editImgStep = new sfn_tasks.LambdaInvoke(scope, "EditImg", {
    lambdaFunction: editImgFunction,
    payload: sfn.TaskInput.fromObject({
      ImgKey: sfn.JsonPath.stringAt("$.SelectImgResults.Payload.ImgKey"),
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
      Genres: sfn.JsonPath.stringAt("$.GenTextResults.Payload.Genres"),
      MainFood: sfn.JsonPath.stringAt("$.GenTextResults.Payload.MainFood"),
      Theme: sfn.JsonPath.stringAt("$.GenTextResults.Payload.Theme"),
      TitleImgKey: sfn.JsonPath.stringAt(
        "$.EditImgResults.Payload.TitleImgKey",
      ),
      ImgKey: sfn.JsonPath.stringAt("$.SelectImgResults.Payload.ImgKey"),
      DryRun: sfn.JsonPath.stringAt("$.DryRun"),
    }),
    integrationPattern: sfn.IntegrationPattern.REQUEST_RESPONSE,
  });

  const successState = new sfn.Succeed(scope, "Succeded");

  return new sfn.StateMachine(scope, "MusabiStateMachine", {
    stateMachineName: "musabi-statemachine",
    definitionBody: sfn.DefinitionBody.fromChainable(
      genTextStep
        .next(parallelGenImgStep)
        .next(selectImgStep)
        .next(editImgStep)
        .next(pubImgStep)
        .next(successState),
    ),
    timeout: cdk.Duration.minutes(10),
  });
};
